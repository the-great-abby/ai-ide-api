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
import os

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
    confidence: Optional[float] = None
    categories: Optional[List[str]] = []
    tags: Optional[List[str]] = []


class MemoryNodeOut(BaseModel):
    id: str
    namespace: str
    content: str
    meta: Optional[str] = None
    created_at: datetime
    confidence: Optional[float] = None
    categories: Optional[List[str]] = []
    tags: Optional[List[str]] = []


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


class MemoryNodeSearchOut(MemoryNodeOut):
    similarity: Optional[float] = None


# Helper to generate embedding using Ollama
OLLAMA_EMBEDDING_URL = (
    os.environ.get("OLLAMA_FUNCTIONS_URL", "http://ollama-functions:8000")
    + "/embed-text"
)
OLLAMA_EMBEDDING_MODEL = "nomic-embed-text:latest"


def get_embedding_ollama(text: str) -> List[float]:
    response = requests.post(
        OLLAMA_EMBEDDING_URL, json={"text": text, "model": OLLAMA_EMBEDDING_MODEL}
    )
    response.raise_for_status()
    data = response.json()
    if isinstance(data, dict) and "embedding" in data:
        return data["embedding"]
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(f"Unexpected embedding response format: {data}")


# Helper to call the Ollama LLM for text generation (not just embeddings)
OLLAMA_URL = os.environ.get(
    "OLLAMA_URL", "http://host.docker.internal:11434/api/generate"
)
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b-instruct-q6_K")


def call_ollama_llm(prompt: str) -> str:
    """
    Call the Ollama LLM server for text generation.
    Handles streaming JSON responses.
    """
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt},
            timeout=120,
            stream=True,
        )
        response.raise_for_status()
        answer = ""
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                answer += chunk.get("response", "")
        return answer
    except Exception as e:
        logger.error(f"[ERROR] Ollama LLM call failed: {e}")
        raise


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


def create_namespace_permission(
    permission: NamespacePermissionCreate, db: Session = Depends(get_db)
):
    # Resolve project_id and allowed_project_id
    try:
        uuid.UUID(permission.project_id)
        resolved_project_id = resolve_project_id(db, permission.project_id)
    except Exception:
        resolved_project_id = resolve_project_id(
            db,
            permission.project_id,
            **project_defaults_from_name(permission.project_id),
        )
    resolved_allowed_project_id = None
    if permission.allowed_project_id:
        try:
            uuid.UUID(permission.allowed_project_id)
            resolved_allowed_project_id = resolve_project_id(
                db, permission.allowed_project_id
            )
        except Exception:
            resolved_allowed_project_id = resolve_project_id(
                db,
                permission.allowed_project_id,
                **project_defaults_from_name(permission.allowed_project_id),
            )
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


def vector_search_memory_nodes(embedding, namespace=None, limit=5):
    """
    Perform a vector search in memorydb using pgvector's <=> operator.
    Args:
        embedding (list[float]): The query embedding.
        namespace (str|None): Optional namespace filter.
        limit (int): Max number of results.
    Returns:
        list[dict]: List of memory node dicts with distance and confidence.
    """
    session = MemorySessionLocal()
    sql = "SELECT *, embedding <=> CAST(:query_vec AS vector) AS distance FROM memory_vectors"
    params = {"query_vec": embedding, "limit": limit}
    if namespace:
        sql += " WHERE namespace = :namespace"
        params["namespace"] = namespace
    sql += " ORDER BY distance ASC LIMIT :limit"
    results = session.execute(text(sql), params)
    nodes = []
    for row in results:
        row_dict = dict(row._mapping)
        distance = row_dict.get("distance")
        confidence = 1.0 - distance if distance is not None else None
        row_dict["confidence"] = confidence
        nodes.append(row_dict)
    session.close()
    return nodes
