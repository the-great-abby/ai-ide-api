import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import require_api_token, require_role
from db import (
    ApiAccessToken,
    MemorySessionLocal,
    MemoryVector,
    NamespacePermission,
    get_db,
)
from memory import (
    MemoryEdgeCreate,
    MemoryEdgeOut,
    MemoryNodeCreate,
    MemoryNodeOut,
    NamespacePermissionCreate,
    NamespacePermissionOut,
    check_llm_access,
    check_namespace_permission,
    get_embedding_ollama,
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
    # Check namespace permission
    check_namespace_permission(node.namespace, token, "write", db)

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
        )
        session.add(db_node)
        session.commit()
        session.refresh(db_node)
        # --- Patch: ensure embedding is a list ---
        embedding = db_node.embedding
        result = {
            "id": db_node.id,
            "namespace": db_node.namespace,
            "content": db_node.content,
            "embedding": embedding,
            "meta": db_node.meta,
            "created_at": db_node.created_at,
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
    nodes = q.all()
    result = []
    for db_node in nodes:
        embedding = db_node.embedding
        result.append(
            {
                "id": db_node.id,
                "namespace": db_node.namespace,
                "content": db_node.content,
                "embedding": embedding,
                "meta": db_node.meta,
                "created_at": db_node.created_at,
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
    db_permission = NamespacePermission(
        namespace=permission.namespace,
        project_id=permission.project_id,
        allowed_project_id=permission.allowed_project_id,
        permission_type=permission.permission_type,
        created_by=token.created_by,
    )
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission
