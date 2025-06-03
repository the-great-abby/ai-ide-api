import logging
import uuid

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.orm import Session

from auth import require_api_token
from basic_endpoints import router as basic_router
from db import get_db, init_db
from logging_config import setup_logging
from memory_endpoints import router as memory_router
from misc_endpoints import get_changelog, get_changelog_json
from misc_endpoints import router as misc_router
from onboarding import router as onboarding_router
from projects import router as projects_router
from public_endpoints import public_router
from rule_proposals import list_rule_changes
from rule_proposals import router as rule_proposals_router
from rules import list_rules as rules_list_rules
from rules import router as rules_router
from tokens import add_validation_error_logging
from tokens import router as tokens_router
from use_cases import router as use_cases_router

# Initialize FastAPI app
app = FastAPI(
    title="Rule API Server",
    description="API server for managing rules and rule proposals",
    version="1.0.0",
)

add_validation_error_logging(app)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)


# Add error handling middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response


@app.exception_handler(Exception)
async def validation_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


# Add protected route for testing
@app.get("/protected")
async def protected_route(token: dict = Depends(require_api_token)):
    return {"message": "This is a protected route", "user": token.sub}


# Add metrics endpoint
@app.get("/metrics")
async def metrics():
    return {
        "http_requests_total": 0,
        "http_request_duration_seconds": 0,
        "active_rules": 0,
        "pending_proposals": 0,
    }


# Add env endpoint
@app.get("/env")
async def get_env():
    return {
        "environment": "test",
        "version": "1.0.0",
        "database_url": "postgresql://postgres:postgres@db-test:5432/rulesdb",
    }


# Add basic endpoints router
app.include_router(basic_router)

# Add memory router
app.include_router(memory_router)

# Add use cases router
app.include_router(use_cases_router)

# Add onboarding router
app.include_router(onboarding_router)

# Add projects router
app.include_router(projects_router)

# Add tokens router
app.include_router(tokens_router)

# Add rule proposals router
app.include_router(rule_proposals_router)

# Add rules router
app.include_router(rules_router)

# Add misc endpoints router
app.include_router(misc_router)

# Add public router
app.include_router(public_router)

legacy_router = APIRouter()

# In-memory stores for demo
BUG_REPORTS = {}
ENHANCEMENTS = {}


@legacy_router.get("/list-pending-rule-changes")
async def legacy_list_pending_rule_changes(
    db: Session = Depends(get_db), token: dict = Depends(require_api_token)
):
    return list_rule_changes(status="pending", db=db, token=token)


@legacy_router.get("/list-rules")
async def legacy_list_rules(db: Session = Depends(get_db)):
    return rules_list_rules(db=db)


@legacy_router.get("/rules.mdc")
async def legacy_rules_mdc():
    # Return a minimal valid .mdc file as plain text
    return PlainTextResponse(
        "# Rules.mdc\nNot implemented yet.", media_type="text/plain"
    )


@legacy_router.post("/bug-report")
async def report_bug(request: Request):
    data = await request.json()
    bug_id = str(uuid.uuid4())
    bug = {
        "id": bug_id,
        "description": data.get("description", ""),
        "reporter": data.get("reporter", ""),
        "status": "open",
    }
    BUG_REPORTS[bug_id] = bug
    return bug


@legacy_router.post("/suggest-enhancement")
async def suggest_enhancement(request: Request):
    data = await request.json()
    enh_id = str(uuid.uuid4())
    enh = {
        "id": enh_id,
        "description": data.get("description", ""),
        "suggested_by": data.get("suggested_by", ""),
        "status": "suggested",
        "user_story": data.get("user_story", ""),
    }
    ENHANCEMENTS[enh_id] = enh
    return enh


@legacy_router.get("/list-enhancements")
async def list_enhancements():
    return {"enhancements": list(ENHANCEMENTS.values()), "total": len(ENHANCEMENTS)}


@legacy_router.post("/enhancement-to-proposal/{id}")
async def enhancement_to_proposal(id: str):
    enh = ENHANCEMENTS.get(id)
    if not enh:
        raise HTTPException(status_code=404, detail="Enhancement not found")
    enh["status"] = "proposal"
    return enh


@legacy_router.post("/proposal-to-enhancement/{id}")
async def proposal_to_enhancement(id: str):
    enh = ENHANCEMENTS.get(id)
    if not enh:
        raise HTTPException(status_code=404, detail="Enhancement not found")
    enh["status"] = "enhancement"
    return enh


@legacy_router.post("/accept-enhancement/{id}")
async def accept_enhancement(id: str):
    enh = ENHANCEMENTS.get(id)
    if not enh:
        raise HTTPException(status_code=404, detail="Enhancement not found")
    enh["status"] = "accepted"
    return enh


@legacy_router.post("/complete-enhancement/{id}")
async def complete_enhancement(id: str):
    enh = ENHANCEMENTS.get(id)
    if not enh:
        raise HTTPException(status_code=404, detail="Enhancement not found")
    if enh["status"] == "completed":
        return enh
    enh["status"] = "completed"
    return enh


@legacy_router.post("/reject-enhancement/{id}")
async def reject_enhancement(id: str):
    enh = ENHANCEMENTS.get(id)
    if not enh:
        raise HTTPException(status_code=404, detail="Enhancement not found")
    enh["status"] = "rejected"
    return enh


@legacy_router.get("/changelog.md")
async def legacy_changelog_md():
    # Return a minimal valid markdown file
    return Response("# Changelog\n\nNot implemented yet.", media_type="text/markdown")


@legacy_router.get("/changelog.json")
async def legacy_changelog_json():
    return await get_changelog_json()


@legacy_router.post("/api/rule_proposals/{id}/feedback")
async def legacy_rule_proposal_feedback(id: str):
    return JSONResponse(
        status_code=200,
        content={"detail": "Feedback endpoint not implemented yet", "id": id},
    )


@legacy_router.get("/api/rule_proposals/{id}/feedback")
async def legacy_get_rule_proposal_feedback(id: str):
    raise HTTPException(
        status_code=501, detail="Feedback endpoint not implemented yet."
    )


@legacy_router.get("/bug-reports")
async def get_bug_reports():
    return list(BUG_REPORTS.values())


@legacy_router.get("/enhancements")
async def get_enhancements():
    return list(ENHANCEMENTS.values())


app.include_router(legacy_router)


@app.on_event("startup")
async def startup_event():
    """Initialize the database on startup."""
    init_db()
