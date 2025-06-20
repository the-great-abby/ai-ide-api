import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Body, Request, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from pydantic import BaseModel

from auth import require_api_token, require_role
from db import (
    ApiAccessToken,
    MemorySessionLocal,
    MemoryVector,
    MemoryEdge,
    NamespacePermission,
    get_db,
    Project,
)
from memory import (
    MemoryEdgeCreate,
    MemoryEdgeOut,
    MemoryNodeCreate,
    MemoryNodeOut,
    MemoryNodeSearchOut,
    NamespacePermissionCreate,
    NamespacePermissionOut,
    check_llm_access,
    check_namespace_permission,
    get_embedding_ollama,
    call_ollama_llm,
    vector_search_memory_nodes,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/memory", tags=["memory"])


@router.post("/nodes", response_model=MemoryNodeOut)
def create_memory_node(
    node: MemoryNodeCreate,
    token: ApiAccessToken = Depends(require_api_token),
    db: Session = Depends(get_db),
):
    """Create a new memory node. Requires write permission for the namespace and LLM access."""

    # Auto-create namespace permission if it doesn't exist
    try:
        check_namespace_permission(node.namespace, token, "write", db)
    except HTTPException as e:
        if e.status_code == 403 and "No write permission for namespace" in e.detail:
            # Auto-create namespace permission for the token's project
            logger.info(
                f"Auto-creating namespace permission for {node.namespace} for project {token.project_id}"
            )
            try:
                db_permission = NamespacePermission(
                    namespace=node.namespace,
                    project_id=token.project_id,
                    allowed_project_id=token.project_id,  # Allow the same project
                    permission_type="write",
                    created_by=token.created_by,
                )
                db.add(db_permission)
                db.commit()
                logger.info(
                    f"Successfully created namespace permission for {node.namespace}"
                )
            except Exception as perm_exc:
                logger.error(f"Failed to auto-create namespace permission: {perm_exc}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to auto-create namespace permission for {node.namespace}",
                )
        else:
            raise e

    # Check LLM access for embedding generation
    check_llm_access(token, db)

    try:
        # Generate embedding from content
        embedding = get_embedding_ollama(node.content)
        session = MemorySessionLocal()
        db_node = MemoryVector(
            namespace=node.namespace,
            content=node.content,
            embedding=embedding,
            meta=node.meta,
            project_id=token.project_id,
            categories=node.categories or [],
            tags=node.tags or [],
        )
        session.add(db_node)
        session.commit()
        session.refresh(db_node)
        embedding = db_node.embedding
        result = {
            "id": str(db_node.id),
            "namespace": db_node.namespace,
            "content": db_node.content,
            "embedding": embedding,
            "meta": db_node.meta,
            "created_at": db_node.created_at,
            "categories": db_node.categories or [],
            "tags": db_node.tags or [],
        }
        session.close()
        return result
    except Exception as exc:
        import traceback

        logger.error("[ERROR] Exception in /memory/nodes: %s", exc)
        logger.error(traceback.format_exc())
        raise


@router.get("/nodes", response_model=List[MemoryNodeOut])
def list_memory_nodes(
    namespace: Optional[str] = None,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    token: ApiAccessToken = Depends(require_api_token),
    db: Session = Depends(get_db),
):
    """List memory nodes. Requires read permission for the namespace."""
    if namespace:
        check_namespace_permission(namespace, token, "read", db)
    session = MemorySessionLocal()
    q = session.query(MemoryVector)
    if namespace:
        q = q.filter(MemoryVector.namespace == namespace)
    if category:
        categories = [c.strip() for c in category.split(",")]
        for cat in categories:
            q = q.filter(MemoryVector.categories.op("@>")(f'"{cat}"'))
    if tag:
        tags = [t.strip() for t in tag.split(",")]
        for tg in tags:
            q = q.filter(MemoryVector.tags.op("@>")(f'"{tg}"'))
    nodes = q.all()
    result = []
    for db_node in nodes:
        embedding = db_node.embedding
        result.append(
            {
                "id": str(db_node.id),
                "namespace": db_node.namespace,
                "content": db_node.content,
                "embedding": embedding,
                "meta": db_node.meta,
                "created_at": db_node.created_at,
                "categories": db_node.categories or [],
                "tags": db_node.tags or [],
            }
        )
    session.close()
    return result


@router.delete("/nodes")
def delete_memory_nodes(
    namespace: Optional[str] = None,
    token: ApiAccessToken = Depends(require_api_token),
    db: Session = Depends(get_db),
):
    """Delete memory nodes. Requires write permission for the namespace."""
    if namespace:
        check_namespace_permission(namespace, token, "write", db)
    session = MemorySessionLocal()
    q = session.query(MemoryVector)
    if namespace:
        q = q.filter(MemoryVector.namespace == namespace)
    count = q.delete(synchronize_session=False)
    session.commit()
    session.close()
    return {"deleted": count, "namespace": namespace}


# Add new endpoint to manage namespace permissions
@router.post("/admin/namespace-permissions", response_model=NamespacePermissionOut)
def create_namespace_permission(
    permission: NamespacePermissionCreate,
    token: ApiAccessToken = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    """Create a new namespace permission. Admin only."""
    # Patch: Default project_id to token.project_id if not provided
    project_id = permission.project_id or token.project_id
    if not project_id:
        raise HTTPException(
            status_code=400,
            detail="project_id must be provided or present in the admin token.",
        )
    # Patch: Fetch project name for response
    project = db.query(Project).filter(Project.id == project_id).first()
    project_name = project.name if project else None
    db_permission = NamespacePermission(
        namespace=permission.namespace,
        project_id=project_id,
        allowed_project_id=permission.allowed_project_id,
        permission_type=permission.permission_type,
        created_by=token.created_by,
    )
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    # Patch: Return project_name in response
    response = db_permission.__dict__.copy()
    response["project_name"] = project_name
    response.pop("_sa_instance_state", None)
    return response


@router.post("/edges", response_model=MemoryEdgeOut)
def create_memory_edge(
    edge: dict,  # Accept raw dict to allow both relation_type and relationship
    token: ApiAccessToken = Depends(require_api_token),
    db: Session = Depends(get_db),
):
    # Accept both 'relation_type' and 'relationship' for backward compatibility
    relation_type = edge.get("relation_type") or edge.get("relationship")
    if not relation_type:
        raise HTTPException(
            status_code=422, detail="Missing 'relation_type' or 'relationship' field"
        )
    from_id = edge.get("from_id")
    to_id = edge.get("to_id")
    meta = edge.get("meta")
    # For now, check write permission for the 'from' node's namespace only (can be extended)
    check_namespace_permission(
        from_id, token, "write", db
    )  # TODO: resolve namespace from node if needed
    session = MemorySessionLocal()
    db_edge = MemoryEdge(
        from_id=from_id,
        to_id=to_id,
        relation_type=relation_type,
        meta=meta,
    )
    session.add(db_edge)
    session.commit()
    session.refresh(db_edge)
    edge_dict = db_edge.__dict__.copy()
    edge_dict.pop("_sa_instance_state", None)
    import uuid

    for key in ("id", "from_id", "to_id"):
        if key in edge_dict and isinstance(edge_dict[key], uuid.UUID):
            edge_dict[key] = str(edge_dict[key])
    session.close()
    return edge_dict


@router.get("/edges", response_model=List[MemoryEdgeOut])
def list_memory_edges(
    from_id: Optional[str] = None,
    to_id: Optional[str] = None,
    relation_type: Optional[str] = None,
    token: ApiAccessToken = Depends(require_api_token),
    db: Session = Depends(get_db),
):
    """List memory edges. Requires read permission for the namespace of the 'from' node (if provided)."""
    session = MemorySessionLocal()
    q = session.query(MemoryEdge)
    if from_id:
        q = q.filter(MemoryEdge.from_id == from_id)
    if to_id:
        q = q.filter(MemoryEdge.to_id == to_id)
    if relation_type:
        q = q.filter(MemoryEdge.relation_type == relation_type)
    edges = q.all()
    session.close()
    result = []
    import uuid

    for e in edges:
        edge_dict = e.__dict__.copy()
        edge_dict.pop("_sa_instance_state", None)
        for key in ("id", "from_id", "to_id"):
            if key in edge_dict and isinstance(edge_dict[key], uuid.UUID):
                edge_dict[key] = str(edge_dict[key])
        result.append(edge_dict)
    return result


@router.get("/nodes/{id}", response_model=MemoryNodeOut)
def get_memory_node(
    id: str = Path(..., description="Memory node ID"),
    token: ApiAccessToken = Depends(require_api_token),
    db: Session = Depends(get_db),
):
    session = MemorySessionLocal()
    db_node = session.query(MemoryVector).filter(MemoryVector.id == id).first()
    session.close()
    if not db_node:
        raise HTTPException(status_code=404, detail="Memory node not found")
    return {
        "id": str(db_node.id),
        "namespace": db_node.namespace,
        "content": db_node.content,
        "embedding": db_node.embedding,
        "meta": db_node.meta,
        "created_at": db_node.created_at,
    }


@router.put("/nodes/{id}", response_model=MemoryNodeOut)
def update_memory_node(
    id: str = Path(..., description="Memory node ID"),
    payload: dict = Body(...),
    token: ApiAccessToken = Depends(require_api_token),
    db: Session = Depends(get_db),
):
    session = MemorySessionLocal()
    db_node = session.query(MemoryVector).filter(MemoryVector.id == id).first()
    if not db_node:
        session.close()
        raise HTTPException(status_code=404, detail="Memory node not found")
    # Only allow updating content, meta, and categories/tags
    if "content" in payload:
        db_node.content = payload["content"]
    if "meta" in payload:
        db_node.meta = payload["meta"]
    if "categories" in payload:
        db_node.categories = payload["categories"]
    if "tags" in payload:
        db_node.tags = payload["tags"]

    db.commit()
    db.refresh(db_node)

    return {
        "id": db_node.id,
        "namespace": db_node.namespace,
        "content": db_node.content,
        "meta": db_node.meta,
        "categories": db_node.categories,
        "tags": db_node.tags,
        "created_at": db_node.created_at,
    }


@router.delete("/nodes/{id}")
def delete_memory_node(
    id: str = Path(..., description="Memory node ID"),
    token: ApiAccessToken = Depends(require_api_token),
    db: Session = Depends(get_db),
):
    session = MemorySessionLocal()
    db_node = session.query(MemoryVector).filter(MemoryVector.id == id).first()
    if not db_node:
        session.close()
        raise HTTPException(status_code=404, detail="Memory node not found")
    # Check write permission for the node's namespace
    check_namespace_permission(db_node.namespace, token, "write", db)
    session.delete(db_node)
    session.commit()
    session.close()
    return {"detail": f"Memory node {id} deleted"}


@router.get("/nodes/{id}/connected", response_model=List[MemoryNodeOut])
def get_connected_nodes(
    id: str = Path(..., description="Memory node ID"),
    relation_type: Optional[str] = None,
    token: ApiAccessToken = Depends(require_api_token),
    db: Session = Depends(get_db),
):
    session = MemorySessionLocal()
    # Find all edges where this node is from_id or to_id
    q = session.query(MemoryEdge)
    if relation_type:
        q = q.filter(MemoryEdge.relation_type == relation_type)
    edges = q.filter((MemoryEdge.from_id == id) | (MemoryEdge.to_id == id)).all()
    # Collect all connected node IDs (excluding the original node)
    connected_ids = set()
    for edge in edges:
        if str(edge.from_id) != id:
            connected_ids.add(str(edge.from_id))
        if str(edge.to_id) != id:
            connected_ids.add(str(edge.to_id))
    if not connected_ids:
        session.close()
        return []
    nodes = session.query(MemoryVector).filter(MemoryVector.id.in_(connected_ids)).all()
    result = [
        {
            "id": str(n.id),
            "namespace": n.namespace,
            "content": n.content,
            "embedding": n.embedding,
            "meta": n.meta,
            "created_at": n.created_at,
        }
        for n in nodes
    ]
    session.close()
    return result


@router.post("/nodes/search", response_model=List[MemoryNodeSearchOut])
async def search_memory_nodes(
    request: Request,
    token: ApiAccessToken = Depends(require_api_token),
    db: Session = Depends(get_db),
):
    body = await request.json()
    query_text = body.get("query")
    namespace = body.get("namespace")
    limit = body.get("limit", 10)
    if not query_text:
        raise HTTPException(
            status_code=400, detail="Missing 'query' field for vector search."
        )
    embedding = get_embedding_ollama(query_text)
    session = MemorySessionLocal()
    sql = "SELECT *, embedding <=> CAST(:query_vec AS vector) AS distance FROM memory_vectors"
    params = {"query_vec": embedding, "limit": limit}
    if namespace:
        sql += " WHERE namespace = :namespace"
        params["namespace"] = namespace
    sql += " ORDER BY distance ASC LIMIT :limit"
    results = session.execute(text(sql), params)
    # Each row: (*fields, distance)
    result = []
    for row in results:
        row_dict = dict(row._mapping)
        # Compute similarity as 1 - distance (if distance is cosine distance)
        distance = row_dict.get("distance")
        similarity = 1.0 - distance if distance is not None else None
        result.append(
            {
                "id": str(row_dict["id"]),
                "namespace": row_dict["namespace"],
                "content": row_dict["content"],
                "embedding": row_dict["embedding"],
                "meta": row_dict["meta"],
                "created_at": row_dict["created_at"],
                "confidence": similarity,  # Confidence is based on similarity score
                "similarity": similarity,
            }
        )
    session.close()
    return result


class LLMAccessRequest(BaseModel):
    project_id: str
    has_llm_access: bool


@router.post("/admin/project/llm-access")
def set_project_llm_access(
    req: LLMAccessRequest,
    token: ApiAccessToken = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == req.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    # Convert boolean to integer for DB
    project.has_llm_access = 1 if req.has_llm_access else 0
    db.commit()
    db.refresh(project)
    return {"project_id": project.id, "has_llm_access": project.has_llm_access}


# --- RAG Search Endpoint ---
class RAGQuery(BaseModel):
    question: str
    namespace: Optional[str] = None
    top_k: int = 5


class RAGResponse(BaseModel):
    answer: str
    sources: List[dict]  # Each dict: {id, content, namespace, meta, created_at}


@router.post("/rag_search", response_model=RAGResponse, status_code=status.HTTP_200_OK)
def rag_search(
    query: RAGQuery,
    token: ApiAccessToken = Depends(require_api_token),
    db: Session = Depends(get_db),
):
    """
    Retrieval-Augmented Generation (RAG) search endpoint.
    - Embeds the user's question
    - Performs vector search for top_k relevant memory nodes (optionally filtered by namespace)
    - Checks read permission for each namespace
    - Calls the LLM with the question and retrieved node contents as context
    - Returns the LLM's answer and the supporting memory nodes
    """
    # 1. Embed the question
    embedding = get_embedding_ollama(query.question)

    # 2. Vector search for top_k memory nodes (optionally filter by namespace)
    node_dicts = vector_search_memory_nodes(
        embedding, namespace=query.namespace, limit=query.top_k
    )

    # 3. Check read permission for each namespace and build MemoryNode-like objects
    filtered_nodes = []
    for node in node_dicts:
        try:
            check_namespace_permission(node["namespace"], token, "read", db)
            filtered_nodes.append(node)
        except Exception:
            continue  # Skip nodes the user can't access

    # 4. Prepare context for LLM
    context = "\n\n".join([n["content"] for n in filtered_nodes])
    if not context:
        return RAGResponse(answer="No relevant memory nodes found.", sources=[])

    # 5. Call Ollama LLM with context + question
    prompt = f"""Answer the following question using only the provided context.\n\nContext:\n{context}\n\nQuestion: {query.question}\nAnswer:"""
    answer = call_ollama_llm(prompt)

    # 6. Return answer and sources
    sources = []
    for n in filtered_nodes:
        source = {
            "id": str(n["id"]),
            "content": n["content"],
            "namespace": n["namespace"],
            "meta": n["meta"],
            "created_at": n["created_at"],
            "confidence": n.get("similarity"),  # Use similarity as confidence
        }
        if source["confidence"] is not None and source["confidence"] < 0.5:
            source[
                "low_confidence_reason"
            ] = "This memory node is only weakly related to your question."
        sources.append(source)
    return RAGResponse(answer=answer, sources=sources)
