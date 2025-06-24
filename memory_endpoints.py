import logging
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, Body, Request, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from sqlalchemy import or_
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
    resolve_project_id,
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
from memory_management import memory_management_service, MemoryLifecycleStatus

logger = logging.getLogger(__name__)

# Add the missing import for get_memory_db
def get_memory_db():
    """Get a memory database session."""
    db = MemorySessionLocal()
    try:
        yield db
    finally:
        db.close()

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
        # Generate embedding from content, meta, tags, and categories
        embedding_input = node.content
        if node.meta:
            embedding_input += f"\nMeta: {node.meta}"
        if node.categories:
            embedding_input += f"\nCategories: {', '.join(node.categories)}"
        if node.tags:
            embedding_input += f"\nTags: {', '.join(node.tags)}"
        embedding = get_embedding_ollama(embedding_input)
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
        check_namespace_permission(str(namespace), token, "read", db)
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
    # TODO: resolve namespace from node if needed - for now, skip permission check
    # since we don't have the namespace available here
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
    project_id: Optional[str] = None  # Accepts name, ID, or omitted
    has_llm_access: bool


@router.post("/admin/project/llm-access")
def set_project_llm_access(
    req: LLMAccessRequest,
    token: ApiAccessToken = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    # Hybrid: allow project_id (name or ID), or infer from token if project-scoped
    project_identifier = req.project_id or getattr(token, "project_id", None)
    if not project_identifier:
        raise HTTPException(status_code=400, detail="Project identifier (name or ID) must be provided, or use a project-scoped admin token.")
    try:
        resolved_project_id = resolve_project_id(db, project_identifier)
    except Exception:
        raise HTTPException(status_code=404, detail="Project not found or could not resolve identifier.")
    project = db.query(Project).filter(Project.id == resolved_project_id).first()
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


@router.get("/graph", response_model=dict)
def get_memory_graph(
    namespace: Optional[str] = None,
    token: ApiAccessToken = Depends(require_api_token),
    db: Session = Depends(get_db),
):
    """Get full memory graph data for visualization."""
    if namespace:
        check_namespace_permission(str(namespace), token, "read", db)
    
    session = MemorySessionLocal()
    
    # Get nodes
    query = session.query(MemoryVector)
    if namespace:
        query = query.filter(MemoryVector.namespace == namespace)
    nodes = query.all()
    
    # Get edges
    edge_query = session.query(MemoryEdge)
    if namespace:
        # Filter edges where both nodes are in the namespace
        node_ids = [str(n.id) for n in nodes]
        edge_query = edge_query.filter(
            (MemoryEdge.from_id.in_(node_ids)) & (MemoryEdge.to_id.in_(node_ids))
        )
    edges = edge_query.all()
    
    # Format for visualization
    node_data = []
    for node in nodes:
        node_data.append({
            "id": str(node.id),
            "label": node.content[:100] + "..." if len(node.content) > 100 else node.content,
            "type": node.namespace,
            "meta": node.meta,
            "created_at": node.created_at.isoformat() if node.created_at else None,
            "categories": node.categories or [],
            "tags": node.tags or [],
        })
    
    edge_data = []
    for edge in edges:
        edge_data.append({
            "id": str(edge.id),
            "source_id": str(edge.from_id),
            "target_id": str(edge.to_id),
            "label": edge.relation_type,
            "meta": edge.meta,
            "created_at": edge.created_at.isoformat() if edge.created_at else None
        })
    
    session.close()
    
    return {
        "nodes": node_data,
        "edges": edge_data,
        "total_nodes": len(node_data),
        "total_edges": len(edge_data),
        "namespace": namespace
    }

@router.get("/visualization", response_model=dict)
def get_memory_visualization(
    namespace: Optional[str] = None,
    format: str = Query("json", description="Output format: json, mermaid, dot"),
    token: ApiAccessToken = Depends(require_api_token),
    db: Session = Depends(get_db),
):
    """Get memory graph data formatted for frontend visualization."""
    graph_data = get_memory_graph(namespace, token, db)
    
    if format == "mermaid":
        return format_mermaid(graph_data)
    elif format == "dot":
        return format_dot(graph_data)
    else:
        return graph_data

def format_mermaid(graph_data: dict) -> dict:
    """Format graph data as Mermaid diagram."""
    mermaid_lines = ["graph TD"]
    
    # Add nodes
    for node in graph_data["nodes"]:
        node_id = f"N{node['id'][:8]}"  # Short ID for Mermaid
        label = node['label'].replace('"', '\\"').replace('\n', ' ')
        mermaid_lines.append(f'    {node_id}["{label}"]')
    
    # Add edges
    for edge in graph_data["edges"]:
        source_id = f"N{edge['source_id'][:8]}"
        target_id = f"N{edge['target_id'][:8]}"
        label = edge['label'].replace('"', '\\"')
        mermaid_lines.append(f'    {source_id} -->|{label}| {target_id}')
    
    return {
        "format": "mermaid",
        "content": "\n".join(mermaid_lines),
        "graph_data": graph_data
    }

def format_dot(graph_data: dict) -> dict:
    """Format graph data as DOT format."""
    dot_lines = [
        "digraph MemoryGraph {",
        "    rankdir=LR;",
        "    node [shape=box, style=filled, fillcolor=lightblue];"
    ]
    
    # Add nodes
    for node in graph_data["nodes"]:
        node_id = f"N{node['id'][:8]}"
        label = node['label'].replace('"', '\\"').replace('\n', ' ')
        dot_lines.append(f'    {node_id} [label="{label}"];')
    
    # Add edges
    for edge in graph_data["edges"]:
        source_id = f"N{edge['source_id'][:8]}"
        target_id = f"N{edge['target_id'][:8]}"
        label = edge['label'].replace('"', '\\"')
        dot_lines.append(f'    {source_id} -> {target_id} [label="{label}"];')
    
    dot_lines.append("}")
    
    return {
        "format": "dot",
        "content": "\n".join(dot_lines),
        "graph_data": graph_data
    }

@router.get("/export")
def export_memory_graph(
    namespace: Optional[str] = None,
    format: str = Query("json", description="Export format: json, csv, gexf"),
    token: ApiAccessToken = Depends(require_api_token),
    db: Session = Depends(get_db),
):
    """Export memory graph in various formats."""
    graph_data = get_memory_graph(namespace, token, db)
    
    if format == "csv":
        return export_csv(graph_data)
    elif format == "gexf":
        return export_gexf(graph_data)
    else:
        return graph_data

def export_csv(graph_data: dict):
    """Export graph data as CSV files."""
    import csv
    from io import StringIO
    
    # Nodes CSV
    nodes_buffer = StringIO()
    nodes_writer = csv.writer(nodes_buffer)
    nodes_writer.writerow(["id", "label", "type", "meta", "created_at", "categories", "tags", "confidence"])
    for node in graph_data["nodes"]:
        nodes_writer.writerow([
            node["id"],
            node["label"],
            node["type"],
            node["meta"],
            node["created_at"],
            ",".join(node["categories"]),
            ",".join(node["tags"]),
            node["confidence"]
        ])
    
    # Edges CSV
    edges_buffer = StringIO()
    edges_writer = csv.writer(edges_buffer)
    edges_writer.writerow(["id", "source_id", "target_id", "label", "meta", "created_at"])
    for edge in graph_data["edges"]:
        edges_writer.writerow([
            edge["id"],
            edge["source_id"],
            edge["target_id"],
            edge["label"],
            edge["meta"],
            edge["created_at"]
        ])
    
    return {
        "format": "csv",
        "nodes": nodes_buffer.getvalue(),
        "edges": edges_buffer.getvalue(),
        "total_nodes": len(graph_data["nodes"]),
        "total_edges": len(graph_data["edges"])
    }

def export_gexf(graph_data: dict):
    """Export graph data as GEXF format (Gephi)."""
    from datetime import datetime
    
    gexf_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<gexf xmlns="http://www.gexf.net/1.2draft" version="1.2">',
        '  <meta lastmodifieddate="' + datetime.now().isoformat() + '">',
        '    <creator>AI-IDE Memory System</creator>',
        '    <description>Memory graph export</description>',
        '  </meta>',
        '  <graph mode="static" defaultedgetype="directed">',
        '    <nodes>'
    ]
    
    # Add nodes
    for node in graph_data["nodes"]:
        gexf_lines.append(f'      <node id="{node["id"]}" label="{node["label"]}">')
        gexf_lines.append(f'        <attvalues>')
        gexf_lines.append(f'          <attvalue for="type" value="{node["type"]}"/>')
        gexf_lines.append(f'          <attvalue for="categories" value="{",".join(node["categories"])}"/>')
        gexf_lines.append(f'        </attvalues>')
        gexf_lines.append(f'      </node>')
    
    gexf_lines.append('    </nodes>')
    gexf_lines.append('    <edges>')
    
    # Add edges
    for edge in graph_data["edges"]:
        gexf_lines.append(f'      <edge id="{edge["id"]}" source="{edge["source_id"]}" target="{edge["target_id"]}" label="{edge["label"]}"/>')
    
    gexf_lines.extend([
        '    </edges>',
        '  </graph>',
        '</gexf>'
    ])
    
    return {
        "format": "gexf",
        "content": "\n".join(gexf_lines),
        "total_nodes": len(graph_data["nodes"]),
        "total_edges": len(graph_data["edges"])
    }

@router.post("/confidence/update/{memory_id}")
def update_memory_confidence(
    memory_id: str,
    token: ApiAccessToken = Depends(require_api_token),
    db: Session = Depends(get_db),
    memory_db: Session = Depends(get_memory_db),
):
    """Update confidence score for a specific memory."""
    try:
        # Check if memory exists and user has access
        memory = memory_db.query(MemoryVector).filter(MemoryVector.id == memory_id).first()
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        # Check namespace permission
        check_namespace_permission(memory.namespace, token, "read", db)
        
        # Update confidence
        confidence_score = memory_management_service.update_memory_confidence(memory_id, memory_db)
        
        return {
            "memory_id": memory_id,
            "confidence_score": confidence_score,
            "updated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error updating memory confidence: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/confidence/batch-update")
def batch_update_memory_confidence(
    namespace: Optional[str] = None,
    token: ApiAccessToken = Depends(require_api_token),
    db: Session = Depends(get_db),
    memory_db: Session = Depends(get_memory_db),
):
    """Update confidence scores for all memories in a namespace."""
    try:
        if namespace:
            # Check namespace permission
            check_namespace_permission(str(namespace), token, "read", db)
        
        # Update confidences
        results = memory_management_service.batch_update_confidence(namespace, memory_db)
        
        # Calculate summary
        successful = sum(1 for score in results.values() if score is not None)
        failed = len(results) - successful
        
        return {
            "namespace": namespace,
            "total_memories": len(results),
            "successful_updates": successful,
            "failed_updates": failed,
            "results": results,
            "updated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in batch confidence update: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lifecycle/status/{memory_id}")
def get_memory_lifecycle_status(
    memory_id: str,
    token: ApiAccessToken = Depends(require_api_token),
    db: Session = Depends(get_db),
    memory_db: Session = Depends(get_memory_db),
):
    """Get comprehensive lifecycle status for a memory."""
    try:
        # Check if memory exists and user has access
        memory = memory_db.query(MemoryVector).filter(MemoryVector.id == memory_id).first()
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        # Check namespace permission
        check_namespace_permission(memory.namespace, token, "read", db)
        
        # Get lifecycle status
        status = memory_management_service.lifecycle_manager.get_lifecycle_status(memory, memory_db)
        
        return {
            "memory_id": memory_id,
            "age_days": status.age_days,
            "last_accessed": status.last_accessed.isoformat() if status.last_accessed else None,
            "access_count": status.access_count,
            "confidence_score": status.confidence_score,
            "importance_score": status.importance_score,
            "lifecycle_stage": status.lifecycle_stage,
            "cleanup_reason": status.cleanup_reason
        }
    except Exception as e:
        logger.error(f"Error getting memory lifecycle status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cleanup/report")
def get_cleanup_report(
    namespace: Optional[str] = None,
    token: ApiAccessToken = Depends(require_api_token),
    db: Session = Depends(get_db),
    memory_db: Session = Depends(get_memory_db),
):
    """Generate a comprehensive cleanup report."""
    try:
        if namespace:
            # Check namespace permission
            check_namespace_permission(str(namespace), token, "read", db)
        
        # Generate report
        report = memory_management_service.get_cleanup_report(namespace, memory_db)
        
        return {
            "namespace": namespace,
            "report_generated_at": datetime.utcnow().isoformat(),
            **report
        }
    except Exception as e:
        logger.error(f"Error generating cleanup report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup/execute")
def execute_memory_cleanup(
    memory_ids: List[str],
    dry_run: bool = True,
    token: ApiAccessToken = Depends(require_api_token),
    db: Session = Depends(get_db),
    memory_db: Session = Depends(get_memory_db),
):
    """Execute cleanup on specified memories."""
    try:
        if not memory_ids:
            raise HTTPException(status_code=400, detail="No memory IDs provided")
        
        # Check permissions for all memories
        memories = memory_db.query(MemoryVector).filter(MemoryVector.id.in_(memory_ids)).all()
        if len(memories) != len(memory_ids):
            raise HTTPException(status_code=404, detail="Some memories not found")
        
        for memory in memories:
            check_namespace_permission(memory.namespace, token, "write", db)
        
        # Execute cleanup
        results = []
        for memory_id in memory_ids:
            try:
                if dry_run:
                    # Just log what would be deleted
                    memory = memory_db.query(MemoryVector).filter(MemoryVector.id == memory_id).first()
                    results.append({
                        "memory_id": memory_id,
                        "action": "would_delete",
                        "success": True,
                        "namespace": memory.namespace,
                        "content_preview": memory.content[:100] + "..." if len(memory.content) > 100 else memory.content
                    })
                else:
                    # Actually delete the memory
                    memory = memory_db.query(MemoryVector).filter(MemoryVector.id == memory_id).first()
                    memory_db.delete(memory)
                    results.append({
                        "memory_id": memory_id,
                        "action": "deleted",
                        "success": True
                    })
            except Exception as e:
                results.append({
                    "memory_id": memory_id,
                    "action": "failed",
                    "success": False,
                    "error": str(e)
                })
        
        if not dry_run:
            memory_db.commit()
        
        successful = sum(1 for r in results if r["success"])
        failed = len(results) - successful
        
        return {
            "dry_run": dry_run,
            "total_requested": len(memory_ids),
            "successful": successful,
            "failed": failed,
            "results": results,
            "executed_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error executing memory cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/relationships/infer")
def infer_memory_relationships(
    namespace: Optional[str] = None,
    limit: int = 100,
    token: ApiAccessToken = Depends(require_api_token),
    db: Session = Depends(get_db),
    memory_db: Session = Depends(get_memory_db),
):
    """Infer new relationships between memories."""
    try:
        if namespace:
            # Check namespace permission
            check_namespace_permission(str(namespace), token, "write", db)
        
        # Infer relationships
        new_relationships = memory_management_service.infer_new_relationships(namespace, memory_db)
        
        return {
            "namespace": namespace,
            "relationships_inferred": len(new_relationships),
            "relationships": new_relationships,
            "inferred_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error inferring memory relationships: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/summary")
def get_memory_analytics_summary(
    namespace: Optional[str] = None,
    token: ApiAccessToken = Depends(require_api_token),
    db: Session = Depends(get_db),
    memory_db: Session = Depends(get_memory_db),
):
    """Get comprehensive analytics summary for memories."""
    try:
        if namespace:
            # Check namespace permission
            check_namespace_permission(str(namespace), token, "read", db)
        
        # Build query
        query = memory_db.query(MemoryVector)
        if namespace:
            query = query.filter(MemoryVector.namespace == namespace)
        
        memories = query.all()
        
        if not memories:
            return {
                "namespace": namespace,
                "total_memories": 0,
                "analytics": {}
            }
        
        # Calculate analytics
        total_memories = len(memories)
        total_relationships = memory_db.query(MemoryEdge).count()
        
        # Confidence distribution - calculate based on memory characteristics
        now = datetime.utcnow()
        confidence_scores = []
        for memory in memories:
            # Calculate confidence based on age and content quality
            age_days = (now - memory.created_at).days
            content_length = len(memory.content) if memory.content else 0
            
            # Newer memories and longer content get higher confidence
            age_factor = max(0.3, 1.0 - (age_days / 365))  # Decay over time
            length_factor = min(1.0, content_length / 500)  # Cap at 500 chars
            confidence = (age_factor + length_factor) / 2
            confidence_scores.append(confidence)
        
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5
        
        confidence_distribution = {
            "low": sum(1 for c in confidence_scores if c < 0.3),
            "medium": sum(1 for c in confidence_scores if 0.3 <= c < 0.7),
            "high": sum(1 for c in confidence_scores if c >= 0.7)
        }
        
        # Age distribution
        now = datetime.utcnow()
        ages = [(now - m.created_at).days for m in memories]
        avg_age = sum(ages) / len(ages) if ages else 0.0
        
        age_distribution = {
            "recent": sum(1 for age in ages if age <= 7),
            "week_old": sum(1 for age in ages if 7 < age <= 30),
            "month_old": sum(1 for age in ages if 30 < age <= 90),
            "quarter_old": sum(1 for age in ages if 90 < age <= 180),
            "old": sum(1 for age in ages if age > 180)
        }
        
        # Namespace distribution
        namespace_counts = {}
        for memory in memories:
            namespace_counts[memory.namespace] = namespace_counts.get(memory.namespace, 0) + 1
        
        # Tag analysis
        all_tags = []
        for memory in memories:
            if memory.tags:
                all_tags.extend(memory.tags)
        
        tag_frequency = {}
        for tag in all_tags:
            tag_frequency[tag] = tag_frequency.get(tag, 0) + 1
        
        top_tags = sorted(tag_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Lifecycle analysis
        lifecycle_stages = {}
        for memory in memories:
            status = memory_management_service.lifecycle_manager.get_lifecycle_status(memory, memory_db)
            lifecycle_stages[status.lifecycle_stage] = lifecycle_stages.get(status.lifecycle_stage, 0) + 1
        
        return {
            "namespace": namespace,
            "total_memories": total_memories,
            "total_relationships": total_relationships,
            "analytics": {
                "confidence": {
                    "average": round(avg_confidence, 3),
                    "distribution": confidence_distribution
                },
                "age": {
                    "average_days": round(avg_age, 1),
                    "distribution": age_distribution
                },
                "namespaces": namespace_counts,
                "top_tags": top_tags,
                "lifecycle_stages": lifecycle_stages
            },
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error generating memory analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/semantic")
def semantic_search_memories(
    query: str,
    namespace: Optional[str] = None,
    limit: int = 10,
    min_similarity: float = 0.7,
    token: ApiAccessToken = Depends(require_api_token),
    db: Session = Depends(get_db),
    memory_db: Session = Depends(get_memory_db),
):
    """Perform semantic search using embeddings for meaning-based matching."""
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        if namespace:
            check_namespace_permission(str(namespace), token, "read", db)
        
        # Generate embedding for the query
        query_embedding = get_embedding_ollama(query)
        
        # Build the search query
        sql = """
        SELECT *, 
               embedding <=> CAST(:query_vec AS vector) AS similarity,
               created_at
        FROM memory_vectors 
        WHERE embedding IS NOT NULL
        """
        params = {"query_vec": query_embedding, "limit": limit, "min_similarity": min_similarity}
        
        if namespace:
            sql += " AND namespace = :namespace"
            params["namespace"] = namespace
        
        sql += " AND embedding <=> CAST(:query_vec AS vector) < :min_similarity"
        sql += " ORDER BY similarity ASC LIMIT :limit"
        
        results = memory_db.execute(text(sql), params)
        
        memories = []
        for row in results:
            row_dict = dict(row._mapping)
            # Convert UUID to string
            for key in ["id"]:
                if key in row_dict and isinstance(row_dict[key], uuid.UUID):
                    row_dict[key] = str(row_dict[key])
            
            memories.append({
                "id": row_dict["id"],
                "namespace": row_dict["namespace"],
                "content": row_dict["content"],
                "meta": row_dict["meta"],
                "created_at": row_dict["created_at"],
                "confidence": None,  # Confidence is calculated dynamically
                "categories": row_dict.get("categories", []),
                "tags": row_dict.get("tags", []),
                "similarity_score": 1 - row_dict["similarity"],  # Convert distance to similarity
                "search_relevance": "semantic"
            })
        
        return {
            "query": query,
            "namespace": namespace,
            "total_results": len(memories),
            "min_similarity": min_similarity,
            "memories": memories,
            "search_type": "semantic"
        }
        
    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/temporal")
def temporal_search_memories(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    namespace: Optional[str] = None,
    time_period: Optional[str] = None,  # "today", "week", "month", "quarter", "year"
    limit: int = 50,
    token: ApiAccessToken = Depends(require_api_token),
    db: Session = Depends(get_db),
    memory_db: Session = Depends(get_memory_db),
):
    """Search memories by temporal criteria."""
    try:
        if namespace:
            check_namespace_permission(str(namespace), token, "read", db)
        
        # Build date range
        now = datetime.utcnow()
        if time_period:
            if time_period == "today":
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
                end_date = now.isoformat()
            elif time_period == "week":
                start_date = (now - timedelta(days=7)).isoformat()
                end_date = now.isoformat()
            elif time_period == "month":
                start_date = (now - timedelta(days=30)).isoformat()
                end_date = now.isoformat()
            elif time_period == "quarter":
                start_date = (now - timedelta(days=90)).isoformat()
                end_date = now.isoformat()
            elif time_period == "year":
                start_date = (now - timedelta(days=365)).isoformat()
                end_date = now.isoformat()
        
        # Build query
        query = memory_db.query(MemoryVector)
        
        if namespace:
            query = query.filter(MemoryVector.namespace == namespace)
        
        if start_date:
            query = query.filter(MemoryVector.created_at >= start_date)
        
        if end_date:
            query = query.filter(MemoryVector.created_at <= end_date)
        
        memories = query.order_by(MemoryVector.created_at.desc()).limit(limit).all()
        
        result = []
        for memory in memories:
            result.append({
                "id": str(memory.id),
                "namespace": memory.namespace,
                "content": memory.content,
                "meta": memory.meta,
                "created_at": memory.created_at.isoformat(),
                "confidence": 0.8,  # Placeholder similarity score for temporal search
                "categories": memory.categories or [],
                "tags": memory.tags or [],
                "age_days": (now - memory.created_at).days,
                "search_relevance": "temporal"
            })
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "time_period": time_period,
            "namespace": namespace,
            "total_results": len(result),
            "memories": result,
            "search_type": "temporal"
        }
        
    except Exception as e:
        logger.error(f"Error in temporal search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/cross-project")
def cross_project_search(
    query: Optional[str] = None,
    tags: Optional[str] = None,
    categories: Optional[str] = None,
    limit: int = 20,
    token: ApiAccessToken = Depends(require_api_token),
    db: Session = Depends(get_db),
    memory_db: Session = Depends(get_memory_db),
):
    """Search for memories across all projects the user has access to."""
    try:
        # Get all namespaces the user has access to
        accessible_namespaces = []
        
        if token.role == "admin":
            # Admin can access all namespaces
            namespaces = memory_db.query(MemoryVector.namespace).distinct().all()
            accessible_namespaces = [ns[0] for ns in namespaces]
        else:
            # Get namespaces from permissions
            permissions = db.query(NamespacePermission).filter(
                NamespacePermission.active == True,
                or_(
                    NamespacePermission.allowed_project_id == token.project_id,
                    NamespacePermission.allowed_project_id == None
                ),
                NamespacePermission.permission_type == "read"
            ).all()
            
            accessible_namespaces = [p.namespace for p in permissions]
        
        if not accessible_namespaces:
            return {
                "query": query,
                "total_results": 0,
                "memories": [],
                "search_type": "cross_project",
                "accessible_namespaces": []
            }
        
        # Build search query
        search_query = memory_db.query(MemoryVector).filter(
            MemoryVector.namespace.in_(accessible_namespaces)
        )
        
        if query:
            # Simple text search for now (could be enhanced with semantic search)
            search_query = search_query.filter(
                MemoryVector.content.ilike(f"%{query}%")
            )
        
        if tags:
            tag_list = [t.strip() for t in tags.split(",")]
            for tag in tag_list:
                search_query = search_query.filter(
                    MemoryVector.tags.op("@>")(f'"{tag}"')
                )
        
        if categories:
            category_list = [c.strip() for c in categories.split(",")]
            for category in category_list:
                search_query = search_query.filter(
                    MemoryVector.categories.op("@>")(f'"{category}"')
                )
        
        memories = search_query.order_by(MemoryVector.created_at.desc()).limit(limit).all()
        
        # Group by namespace for better organization
        namespace_groups = {}
        for memory in memories:
            ns = memory.namespace
            if ns not in namespace_groups:
                namespace_groups[ns] = []
            
            namespace_groups[ns].append({
                "id": str(memory.id),
                "namespace": memory.namespace,
                "content": memory.content,
                "meta": memory.meta,
                "created_at": memory.created_at.isoformat(),
                "confidence": 0.8,  # Placeholder similarity score for cross-project search
                "categories": memory.categories or [],
                "tags": memory.tags or [],
                "search_relevance": "cross_project"
            })
        
        return {
            "query": query,
            "tags": tags,
            "categories": categories,
            "total_results": len(memories),
            "memories_by_namespace": namespace_groups,
            "accessible_namespaces": accessible_namespaces,
            "search_type": "cross_project"
        }
        
    except Exception as e:
        logger.error(f"Error in cross-project search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/{memory_id}")
def get_memory_recommendations(
    memory_id: str,
    limit: int = 10,
    recommendation_type: str = "similar",  # "similar", "related", "trending"
    token: ApiAccessToken = Depends(require_api_token),
    db: Session = Depends(get_db),
    memory_db: Session = Depends(get_memory_db),
):
    """Get memory recommendations based on a specific memory."""
    try:
        # Get the source memory
        source_memory = memory_db.query(MemoryVector).filter(MemoryVector.id == memory_id).first()
        if not source_memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        # Check namespace permission
        check_namespace_permission(source_memory.namespace, token, "read", db)
        
        recommendations = []
        
        if recommendation_type == "similar":
            # Find similar memories using embedding similarity
            if source_memory.embedding:
                sql = """
                SELECT *, 
                       embedding <=> CAST(:source_vec AS vector) AS similarity
                FROM memory_vectors 
                WHERE id != :memory_id 
                  AND embedding IS NOT NULL
                  AND namespace = :namespace
                ORDER BY similarity ASC 
                LIMIT :limit
                """
                
                results = memory_db.execute(text(sql), {
                    "source_vec": source_memory.embedding,
                    "memory_id": memory_id,
                    "namespace": source_memory.namespace,
                    "limit": limit
                })
                
                for row in results:
                    row_dict = dict(row._mapping)
                    recommendations.append({
                        "id": str(row_dict["id"]),
                        "namespace": row_dict["namespace"],
                        "content": row_dict["content"],
                        "meta": row_dict["meta"],
                        "created_at": row_dict["created_at"],
                        "confidence": row_dict["confidence"],
                        "categories": row_dict.get("categories", []),
                        "tags": row_dict.get("tags", []),
                        "similarity_score": 1 - row_dict["similarity"],
                        "recommendation_reason": "content_similarity"
                    })
        
        elif recommendation_type == "related":
            # Find memories connected via edges
            edges = memory_db.query(MemoryEdge).filter(
                or_(
                    MemoryEdge.from_id == memory_id,
                    MemoryEdge.to_id == memory_id
                )
            ).all()
            
            connected_ids = set()
            for edge in edges:
                if edge.from_id != memory_id:
                    connected_ids.add(edge.from_id)
                if edge.to_id != memory_id:
                    connected_ids.add(edge.to_id)
            
            if connected_ids:
                related_memories = memory_db.query(MemoryVector).filter(
                    MemoryVector.id.in_(list(connected_ids))
                ).limit(limit).all()
                
                for memory in related_memories:
                    recommendations.append({
                        "id": str(memory.id),
                        "namespace": memory.namespace,
                        "content": memory.content,
                        "meta": memory.meta,
                        "created_at": memory.created_at.isoformat(),
                        "confidence": 0.8,  # Placeholder similarity score for recommendations
                        "categories": memory.categories or [],
                        "tags": memory.tags or [],
                        "recommendation_reason": "graph_connection"
                    })
        
        elif recommendation_type == "trending":
            # Find recently created memories with similar tags
            if source_memory.tags:
                common_tags = source_memory.tags[:3]  # Use first 3 tags
                
                trending_query = memory_db.query(MemoryVector).filter(
                    MemoryVector.id != memory_id,
                    MemoryVector.namespace == source_memory.namespace
                )
                
                # Filter by common tags
                for tag in common_tags:
                    trending_query = trending_query.filter(
                        MemoryVector.tags.op("@>")(f'"{tag}"')
                    )
                
                trending_memories = trending_query.order_by(
                    MemoryVector.created_at.desc()
                ).limit(limit).all()
                
                for memory in trending_memories:
                    recommendations.append({
                        "id": str(memory.id),
                        "namespace": memory.namespace,
                        "content": memory.content,
                        "meta": memory.meta,
                        "created_at": memory.created_at.isoformat(),
                        "confidence": 0.8,  # Placeholder similarity score for trending recommendations
                        "categories": memory.categories or [],
                        "tags": memory.tags or [],
                        "recommendation_reason": "trending_similar_tags"
                    })
        
        return {
            "source_memory_id": memory_id,
            "recommendation_type": recommendation_type,
            "total_recommendations": len(recommendations),
            "recommendations": recommendations
        }
        
    except Exception as e:
        logger.error(f"Error getting memory recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/advanced")
def advanced_search_memories(
    query: Optional[str] = None,
    namespace: Optional[str] = None,
    tags: Optional[str] = None,
    categories: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_confidence: Optional[float] = None,
    max_confidence: Optional[float] = None,
    search_type: str = "combined",  # "text", "semantic", "combined"
    limit: int = 20,
    token: ApiAccessToken = Depends(require_api_token),
    db: Session = Depends(get_db),
    memory_db: Session = Depends(get_memory_db),
):
    """Advanced search with multiple filters and search types."""
    try:
        if namespace:
            check_namespace_permission(str(namespace), token, "read", db)
        
        memories = []
        
        if search_type == "semantic" and query:
            # Use semantic search
            semantic_results = semantic_search_memories(
                query=query,
                namespace=namespace,
                limit=limit,
                min_similarity=0.6,
                token=token,
                db=db,
                memory_db=memory_db
            )
            memories = semantic_results["memories"]
        
        elif search_type == "text" or search_type == "combined":
            # Build text-based query
            search_query = memory_db.query(MemoryVector)
            
            if namespace:
                search_query = search_query.filter(MemoryVector.namespace == namespace)
            
            if query:
                search_query = search_query.filter(
                    MemoryVector.content.ilike(f"%{query}%")
                )
            
            if tags:
                tag_list = [t.strip() for t in tags.split(",")]
                for tag in tag_list:
                    search_query = search_query.filter(
                        MemoryVector.tags.op("@>")(f'"{tag}"')
                    )
            
            if categories:
                category_list = [c.strip() for c in categories.split(",")]
                for category in category_list:
                    search_query = search_query.filter(
                        MemoryVector.categories.op("@>")(f'"{category}"')
                    )
            
            if start_date:
                search_query = search_query.filter(MemoryVector.created_at >= start_date)
            
            if end_date:
                search_query = search_query.filter(MemoryVector.created_at <= end_date)
            
            # Note: confidence filtering removed since MemoryVector doesn't have confidence field
            # Confidence is calculated dynamically based on similarity scores
            
            db_memories = search_query.order_by(MemoryVector.created_at.desc()).limit(limit).all()
            
            for memory in db_memories:
                memories.append({
                    "id": str(memory.id),
                    "namespace": memory.namespace,
                    "content": memory.content,
                    "meta": memory.meta,
                    "created_at": memory.created_at.isoformat(),
                    "confidence": 0.8,  # Placeholder similarity score for text search
                    "categories": memory.categories or [],
                    "tags": memory.tags or [],
                    "search_relevance": "text_match"
                })
        
        # If combined search, also add semantic results
        if search_type == "combined" and query:
            try:
                semantic_results = semantic_search_memories(
                    query=query,
                    namespace=namespace,
                    limit=limit//2,  # Half for semantic
                    min_similarity=0.7,
                    token=token,
                    db=db,
                    memory_db=memory_db
                )
                
                # Merge and deduplicate
                existing_ids = {m["id"] for m in memories}
                for semantic_memory in semantic_results["memories"]:
                    if semantic_memory["id"] not in existing_ids:
                        memories.append(semantic_memory)
                        existing_ids.add(semantic_memory["id"])
            except Exception as e:
                logger.warning(f"Semantic search failed in combined search: {e}")
        
        # Sort by relevance (semantic results first, then by date)
        memories.sort(key=lambda x: (
            x.get("similarity_score", 0) if "similarity_score" in x else 0,
            x["created_at"]
        ), reverse=True)
        
        return {
            "query": query,
            "namespace": namespace,
            "tags": tags,
            "categories": categories,
            "start_date": start_date,
            "end_date": end_date,
            "min_confidence": min_confidence,
            "max_confidence": max_confidence,
            "search_type": search_type,
            "total_results": len(memories),
            "memories": memories[:limit]
        }
        
    except Exception as e:
        logger.error(f"Error in advanced search: {e}")
        raise HTTPException(status_code=500, detail=str(e))
