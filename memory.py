import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

import requests
from fastapi import Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from db import (
    ApiAccessToken,
    MemoryEdge,
    MemorySessionLocal,
    MemoryVector,
    NamespacePermission,
    Project,
    get_db,
)

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
                NamespacePermission.active == 1,
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
                Project.active == 1,
                Project.has_llm_access == 1,
            )
            .first()
        )
        if project:
            return True

    raise HTTPException(
        status_code=403, detail="LLM access not available for this token or project"
    )
