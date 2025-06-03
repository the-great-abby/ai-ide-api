import json
from typing import List, Optional

from fastapi import Depends, Header, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from db import ApiAccessToken, NamespacePermission, get_db


def require_api_token(
    authorization: Optional[str] = Header(None), db: Session = Depends(get_db)
):
    """Check if the API token is valid and active."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    token = authorization.split(" ", 1)[1]
    db_token = db.query(ApiAccessToken).filter_by(token=token, active=1).first()
    if not db_token:
        raise HTTPException(status_code=401, detail="Invalid or inactive token")
    return db_token


def require_role(roles: List[str]):
    """Check if the token has one of the required roles."""

    def dependency(
        authorization: Optional[str] = Header(None), db: Session = Depends(get_db)
    ):
        token_obj = require_api_token(authorization, db)
        if token_obj.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return token_obj

    return dependency


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


def check_llm_access(token: ApiAccessToken, db: Session = Depends(get_db)):
    """Check if the token has LLM access."""
    if not token.has_llm_access:
        raise HTTPException(status_code=403, detail="Token does not have LLM access")
    return True
