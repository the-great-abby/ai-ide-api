from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import require_api_token, require_role
from db import ApiAccessToken, get_db

router = APIRouter(tags=["basic"])


@router.get("/")
def root():
    """Root endpoint with welcome message and onboarding instructions."""
    return {
        "message": "Welcome to the API!",
        "onboarding": "Visit /onboarding/docs to get started.",
        "health": "Visit /healthz to check API health.",
    }


@router.get("/healthz")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@router.get("/protected")
def protected_endpoint(token: ApiAccessToken = Depends(require_api_token)):
    """Protected endpoint that requires a valid API token."""
    return {
        "message": "This is a protected endpoint",
        "token_info": {
            "role": token.role,
            "project_id": token.project_id,
            "has_llm_access": token.has_llm_access,
        },
    }


@router.get("/admin")
def admin_endpoint(token: ApiAccessToken = Depends(require_role(["admin"]))):
    """Admin-only endpoint."""
    return {
        "message": "This is an admin-only endpoint",
        "token_info": {
            "role": token.role,
            "project_id": token.project_id,
            "has_llm_access": token.has_llm_access,
        },
    }
