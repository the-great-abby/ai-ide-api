import json
from typing import List, Optional
import logging
from fnmatch import fnmatch

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session

from db import ApiAccessToken, NamespacePermission, get_db


def require_api_token(
    authorization: Optional[str] = Header(None, convert_underscores=False), db: Session = Depends(get_db)
):
    """Check if the API token is valid and active."""
    logger = logging.getLogger("auth.require_api_token")
    logger.debug(f"[require_api_token] DB session id: {id(db)}")
    # Accept both 'authorization' and 'Authorization' headers (case-insensitive)
    logger.debug(f"[require_api_token] Authorization header: {authorization}")
    if not authorization:
        logger.warning("[require_api_token] Missing auth header")
        raise HTTPException(status_code=401, detail="Invalid auth header")
    if not authorization.startswith("Bearer "):
        logger.warning(f"[require_api_token] Malformed auth header: {authorization}")
        raise HTTPException(status_code=401, detail="Invalid auth header")
    token = authorization.split(" ", 1)[1]
    logger.debug(f"[require_api_token] Token value: {token}")
    db_token = db.query(ApiAccessToken).filter_by(token=token, active=True).first()
    logger.debug(f"[require_api_token] DB token lookup result: {db_token}")
    if db_token:
        logger.debug(f"[require_api_token] Token role: {db_token.role}, active: {db_token.active}")
    if not db_token:
        logger.warning(f"[require_api_token] Invalid or inactive token: {token}")
        raise HTTPException(status_code=401, detail="Invalid or inactive token")
    logger.info(f"[require_api_token] Valid token: {token}, role: {db_token.role}, active: {db_token.active}")
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
    """Check if the token has permission to access the namespace, supporting wildcards."""
    logger = logging.getLogger("auth.check_namespace_permission")
    logger.setLevel(logging.DEBUG)
    # Admin role has full access
    if token.role == "admin":
        logger.debug(f"[check_namespace_permission] Admin token, access granted for {namespace}")
        return True

    # Check if token is scoped to a project
    if token.project_id:
        # Check namespace permissions (support wildcards)
        permissions = db.query(NamespacePermission).filter(
            NamespacePermission.active == True,
            NamespacePermission.permission_type == required_permission,
            NamespacePermission.project_id == token.project_id,
        ).all()
        logger.debug(f"[check_namespace_permission] Project token {token.project_id}, checking {len(permissions)} permissions for namespace '{namespace}' and permission '{required_permission}'")
        for perm in permissions:
            logger.debug(f"[check_namespace_permission] Checking pattern '{perm.namespace}' against '{namespace}'")
            if fnmatch(namespace, perm.namespace):
                logger.debug(f"[check_namespace_permission] MATCH: '{namespace}' matches '{perm.namespace}'")
                return True
        logger.warning(f"[check_namespace_permission] No matching permission for {namespace} (project {token.project_id})")
        raise HTTPException(
            status_code=403,
            detail=f"No {required_permission} permission for namespace {namespace}",
        )

    # Check token's allowed namespaces (support wildcards)
    if token.allowed_namespaces:
        if not any(fnmatch(namespace, ns) for ns in token.allowed_namespaces):
            raise HTTPException(
                status_code=403, detail=f"Token not authorized for namespace {namespace}"
            )

    # Check token's namespace permissions (support wildcards)
    if token.namespace_permissions:
        try:
            permissions = json.loads(token.namespace_permissions)
            for ns_pattern, perm_type in permissions.items():
                if fnmatch(namespace, ns_pattern) and perm_type == required_permission:
                    return True
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
