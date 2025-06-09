import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

import requests
from fastapi import Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from db import (
    ApiAccessToken,
    MemoryEdge,
    MemorySessionLocal,
    MemoryVector,
    NamespacePermission,
    Project,
    get_db,
    resolve_project_id,
    project_defaults_from_name,
)
from utils.serialization import serialize_uuids
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Memory Graph API Models ---
class MemoryNodeCreate(BaseModel):
    """
    Request model for creating a memory node.
    NOTE: The 'embedding' field is NOT accepted in the request body. Embedding is always generated server-side from the 'content' field.
    """

    namespace: str
    content: str
    meta: Optional[str] = None


class MemoryNodeOut(BaseModel):
    id: str
    namespace: str
    content: str
    meta: Optional[str] = None
    created_at: datetime


class MemoryEdgeCreate(BaseModel):
    from_id: str
    to_id: str
    relation_type: str
    meta: Optional[str] = None


class MemoryEdgeOut(BaseModel):
    id: str
    from_id: str
    to_id: str
    relation_type: str
    meta: Optional[str] = None
    created_at: datetime


class NamespacePermissionOut(BaseModel):
    """Response model for namespace permissions."""

    id: str
    namespace: str
    project_id: str
    allowed_project_id: Optional[str]
    permission_type: str
    created_at: datetime
    created_by: Optional[str]
    active: int


class NamespacePermissionCreate(BaseModel):
    """Request model for creating a namespace permission."""

    namespace: str
    project_id: str
    allowed_project_id: Optional[str] = None  # None means public
    permission_type: str  # "read" or "write"


# Helper to generate embedding using Ollama
OLLAMA_EMBEDDING_URL = "http://host.docker.internal:11434/api/embeddings"
OLLAMA_EMBEDDING_MODEL = "nomic-embed-text:latest"


def get_embedding_ollama(text: str) -> List[float]:
    response = requests.post(
        OLLAMA_EMBEDDING_URL, json={"model": OLLAMA_EMBEDDING_MODEL, "prompt": text}
    )
    response.raise_for_status()
    return response.json()["embedding"]


# --- Memory Graph API Security Dependencies ---
def check_namespace_permission(
    namespace: str,
    token: ApiAccessToken,
    required_permission: str = "read",
    db: Session = Depends(get_db),
):
    """Check if the token has permission to access the namespace."""
    # Admin role has full access
    if token.role == "admin":
        return True

    # Check if token is scoped to a project
    if token.project_id:
        # Check namespace permissions
        permission = (
            db.query(NamespacePermission)
            .filter(
                NamespacePermission.namespace == namespace,
                NamespacePermission.active == True,
                or_(
                    NamespacePermission.allowed_project_id == token.project_id,
                    NamespacePermission.allowed_project_id == None,  # Public namespace
                ),
                NamespacePermission.permission_type == required_permission,
            )
            .first()
        )
        if not permission:
            raise HTTPException(
                status_code=403,
                detail=f"No {required_permission} permission for namespace {namespace}",
            )
        return True

    # Check token's allowed namespaces
    if token.allowed_namespaces and namespace not in token.allowed_namespaces:
        raise HTTPException(
            status_code=403, detail=f"Token not authorized for namespace {namespace}"
        )

    # Check token's namespace permissions
    if token.namespace_permissions:
        try:
            permissions = json.loads(token.namespace_permissions)
            if (
                namespace not in permissions
                or permissions[namespace] != required_permission
            ):
                raise HTTPException(
                    status_code=403,
                    detail=f"No {required_permission} permission for namespace {namespace}",
                )
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500, detail="Invalid namespace permissions format"
            )

    return True


# --- LLM Access Check Dependency ---
def check_llm_access(token: ApiAccessToken, db: Session = Depends(get_db)):
    """Check if the token has LLM access."""
    if token.role == "admin":
        return True

    if token.has_llm_access:
        return True

    if token.project_id:
        project = (
            db.query(Project)
            .filter(
                Project.id == token.project_id,
                Project.active == True,
                Project.has_llm_access == 1,
            )
            .first()
        )
        if project:
            return True

    raise HTTPException(
        status_code=403, detail="LLM access not available for this token or project"
    )


def create_namespace_permission(permission: NamespacePermissionCreate, db: Session = Depends(get_db)):
    # Resolve project_id and allowed_project_id
    try:
        uuid.UUID(permission.project_id)
        resolved_project_id = resolve_project_id(db, permission.project_id)
    except Exception:
        resolved_project_id = resolve_project_id(db, permission.project_id, **project_defaults_from_name(permission.project_id))
    resolved_allowed_project_id = None
    if permission.allowed_project_id:
        try:
            uuid.UUID(permission.allowed_project_id)
            resolved_allowed_project_id = resolve_project_id(db, permission.allowed_project_id)
        except Exception:
            resolved_allowed_project_id = resolve_project_id(db, permission.allowed_project_id, **project_defaults_from_name(permission.allowed_project_id))
    # Use resolved_project_id and resolved_allowed_project_id for DB operations
    # ... existing logic ...

# For each endpoint that returns a SQLAlchemy object or dict, apply serialize_uuids before returning.
# Example for a single object:
# data = obj.__dict__.copy()
# data.pop("_sa_instance_state", None)
# data = serialize_uuids(data)
# return data
#
# Example for a list:
# return [serialize_uuids(obj.__dict__.copy()) for obj in objects]

# You should apply this to all endpoints returning MemoryNodeOut, MemoryEdgeOut, NamespacePermissionOut, or any dict/SQLAlchemy object.

# Patch: Wrap outgoing dict/list responses with serialize_uuids

# --- Patch create_memory_node ---
@app.post("/memory/nodes", response_model=MemoryNodeOut)
def create_memory_node(node: MemoryNodeCreate):
    try:
        embedding = get_embedding_ollama(node.content)
        session = MemorySessionLocal()
        db_node = MemoryVector(
            namespace=node.namespace,
            content=node.content,
            embedding=embedding,
            meta=node.meta,
        )
        session.add(db_node)
        session.commit()
        session.refresh(db_node)
        embedding = db_node.embedding
        if isinstance(embedding, str):
            import ast
            embedding = ast.literal_eval(embedding)
        result = db_node.__dict__.copy()
        result.pop("_sa_instance_state", None)
        result["embedding"] = embedding
        # Explicitly convert id to string
        if "id" in result and isinstance(result["id"], uuid.UUID):
            result["id"] = str(result["id"])
        session.close()
        return serialize_uuids(result)
    except Exception as exc:
        import traceback
        logger.error("[ERROR] Exception in /memory/nodes: %s", exc)
        logger.error(traceback.format_exc())
        raise

# --- Patch list_memory_nodes ---
@app.get("/memory/nodes", response_model=List[MemoryNodeOut])
def list_memory_nodes(namespace: Optional[str] = None):
    session = MemorySessionLocal()
    q = session.query(MemoryVector)
    if namespace:
        q = q.filter(MemoryVector.namespace == namespace)
    nodes = q.all()
    result = []
    for db_node in nodes:
        embedding = db_node.embedding
        if isinstance(embedding, str):
            import ast
            embedding = ast.literal_eval(embedding)
        node_dict = db_node.__dict__.copy()
        node_dict.pop("_sa_instance_state", None)
        node_dict["embedding"] = embedding
        # Explicitly convert id to string
        if "id" in node_dict and isinstance(node_dict["id"], uuid.UUID):
            node_dict["id"] = str(node_dict["id"])
        result.append(serialize_uuids(node_dict))
    session.close()
    return result

# --- Patch search_memory_nodes ---
@app.post("/memory/nodes/search", response_model=List[MemoryNodeOut])
def search_memory_nodes(request: MemoryNodeSearchRequest):
    if not request.text and not request.embedding:
        raise HTTPException(status_code=400, detail="Must provide either 'text' or 'embedding' for search.")
    if request.text:
        embedding = get_embedding_ollama(request.text)
    else:
        embedding = request.embedding
    session = MemorySessionLocal()
    sql = "SELECT * FROM memory_vectors"
    if request.namespace:
        sql += " WHERE namespace = :namespace"
    sql += " ORDER BY embedding <=> CAST(:query_vec AS vector) LIMIT :limit"
    params = {"query_vec": embedding, "limit": request.limit}
    if request.namespace:
        params["namespace"] = request.namespace
    results = session.execute(text(sql), params)
    ids = [row[0] for row in results]
    nodes = session.query(MemoryVector).filter(MemoryVector.id.in_(ids)).all()
    session.close()
    result = []
    for db_node in nodes:
        embedding = db_node.embedding
        if isinstance(embedding, str):
            import ast
            embedding = ast.literal_eval(embedding)
        node_dict = db_node.__dict__.copy()
        node_dict.pop("_sa_instance_state", None)
        node_dict["embedding"] = embedding
        # Explicitly convert id to string
        if "id" in node_dict and isinstance(node_dict["id"], uuid.UUID):
            node_dict["id"] = str(node_dict["id"])
        result.append(serialize_uuids(node_dict))
    return result

# --- Patch create_memory_edge ---
@app.post("/memory/edges", response_model=MemoryEdgeOut)
def create_memory_edge(edge: MemoryEdgeCreate):
    session = MemorySessionLocal()
    db_edge = MemoryEdge(
        from_id=edge.from_id,
        to_id=edge.to_id,
        relation_type=edge.relation_type,
        meta=edge.meta,
    )
    session.add(db_edge)
    session.commit()
    session.refresh(db_edge)
    edge_dict = db_edge.__dict__.copy()
    edge_dict.pop("_sa_instance_state", None)
    # Explicitly convert id, from_id, to_id to string
    for key in ("id", "from_id", "to_id"):
        if key in edge_dict and isinstance(edge_dict[key], uuid.UUID):
            edge_dict[key] = str(edge_dict[key])
    session.close()
    return serialize_uuids(edge_dict)

# --- Patch list_memory_edges ---
@app.get("/memory/edges", response_model=List[MemoryEdgeOut])
def list_memory_edges(from_id: Optional[str] = None, to_id: Optional[str] = None, relation_type: Optional[str] = None):
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
    for e in edges:
        edge_dict = e.__dict__.copy()
        edge_dict.pop("_sa_instance_state", None)
        for key in ("id", "from_id", "to_id"):
            if key in edge_dict and isinstance(edge_dict[key], uuid.UUID):
                edge_dict[key] = str(edge_dict[key])
        result.append(serialize_uuids(edge_dict))
    return result
