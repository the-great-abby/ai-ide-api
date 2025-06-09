import json
import logging
import os
import shutil
import tempfile
import uuid
from datetime import datetime
from typing import Dict, List, Optional
import re
import enum
from sqlalchemy import create_engine

from fastapi import (Body, Depends, FastAPI, File, Form, HTTPException, Path,
                     UploadFile, Request, Header, status, APIRouter)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field, Extra
from sqlalchemy.orm import Session
import requests
import secrets
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import RequestValidationError as FastAPIRequestValidationError

import scripts.suggest_rules as suggest_rules
from db import BugReport as DBBugReport
from db import Enhancement as DBEnhancement
from db import Proposal as DBProposal
from db import Rule as DBRule
from db import SessionLocal, init_db
from rule_proposal_feedback import RuleProposalFeedback
from db import MemorySessionLocal, MemoryVector, MemoryEdge, init_memorydb
from db import ApiErrorLog, ApiAccessToken
from db import UseCase
from db import ProjectOnboardingProgress
import threading
from db import get_db, resolve_project_id, resolve_team_id, project_defaults_from_name
from utils.serialization import serialize_uuids
from onboarding import router as onboarding_router
from rules import router as rules_router
from tokens import router as tokens_router
from rule_proposals import router as rule_proposals_router, pirate_validation_exception_handler
from utils.normalization import clean_examples_field, clean_list_field, normalize_rule_dict, str_to_list, is_valid_uuid
from misc_endpoints import router as misc_router

logging.getLogger("examples_normalization").setLevel(logging.DEBUG)

app = FastAPI(
    title="Rule Proposal API",
    description="""
# Onboarding & User Stories

- [External Project Onboarding](docs/user_stories/external_project_onboarding.md)
- [Internal Developer Onboarding](docs/user_stories/internal_dev_onboarding.md)
- [AI Agent Onboarding](docs/user_stories/ai_agent_onboarding.md)
- [Full User Story Index](docs/user_stories/INDEX.md)

See these user stories for step-by-step onboarding, automation, and best practices for all client types.
"""
)

# --- Router includes (ensure all are present and correct) ---
app.include_router(onboarding_router)  # prefix='/onboarding' in onboarding.py
app.include_router(rules_router)       # prefix='/rules' in rules.py
app.include_router(tokens_router)      # prefix='/admin' in tokens.py
app.include_router(rule_proposals_router)  # prefix='/api/rule_proposals' in rule_proposals.py
app.include_router(misc_router)

"""
CORS Configuration via Environment Variables:
- CORS_ORIGINS: Comma-separated list of allowed origins (default: '*')
- CORS_METHODS: Comma-separated list of allowed methods (default: '*')
- CORS_HEADERS: Comma-separated list of allowed headers (default: '*')
- CORS_ALLOW_CREDENTIALS: 'true' or 'false' (default: 'true')
"""

# CORS middleware for frontend integration (configurable via env)
def parse_env_list(var, default):
    val = os.environ.get(var)
    if val is None:
        return default
    if val.strip() == '*':
        return ["*"]
    return [v.strip() for v in val.split(",") if v.strip()]

allow_origins = parse_env_list("CORS_ORIGINS", ["*"])
allow_methods = parse_env_list("CORS_METHODS", ["*"])
allow_headers = parse_env_list("CORS_HEADERS", ["*"])
allow_credentials = os.environ.get("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=allow_methods,
    allow_headers=allow_headers,
)

# File paths for storing rules and proposals
RULES_FILE = "rules.json"
PROPOSALS_FILE = "proposals.json"
ONBOARDING_PATHS_FILE = "onboarding_paths.json"


# Ensure files exist
def ensure_file(path, default):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(default, f)


ensure_file(RULES_FILE, [])
ensure_file(PROPOSALS_FILE, [])


# Pydantic models
class RuleProposal(BaseModel, extra=Extra.allow):
    rule_type: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    diff: str = Field(..., min_length=1)
    submitted_by: str = Field(..., min_length=1)
    # All other fields are optional
    categories: list[str] = []
    tags: list[str] = []
    examples: list[str] = []
    applies_to: list[str] = []
    applies_to_rationale: str | None = None
    user_story: str | None = None
    reason_for_change: str | None = None
    references: str | None = None
    current_rule: str | None = None
    scope_level: str | None = None
    scope_id: str | None = None
    parent_rule_id: str | None = None
    project: str | None = None
    version: int | None = None
    rule_id: str | None = None


class Rule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rule_type: str
    description: str
    diff: str
    added_by: Optional[str] = None
    project: Optional[str] = None  # New: project context
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    version: int = 1
    categories: List[str] = []
    tags: List[str] = []
    examples: List[str] = []
    applies_to: List[str] = []
    applies_to_rationale: Optional[str] = None
    user_story: Optional[str] = None
    # Hierarchical scope fields
    scope_level: str = "global"  # Allowed: 'global', 'team', 'project', 'machine'
    scope_id: Optional[str] = None
    parent_rule_id: Optional[str] = None
    submitted_by: Optional[str] = None


class BugReportModel(BaseModel):
    description: str
    reporter: Optional[str] = None
    page: Optional[str] = None
    user_story: Optional[str] = None
    timestamp: Optional[str] = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )


class EnhancementModel(BaseModel):
    description: str
    suggested_by: Optional[str] = None
    page: Optional[str] = None
    tags: Optional[List[str]] = []
    categories: Optional[List[str]] = []
    timestamp: Optional[datetime] = None
    status: Optional[str] = "open"
    proposal_id: Optional[str] = None
    project: Optional[str] = None  # Project association
    examples: Optional[str] = None  # New field for examples
    user_story: Optional[str] = None
    diff: Optional[str] = None  # New: diff for enhancements


# Add this Pydantic model for partial updates
class RuleUpdate(BaseModel):
    rule_type: Optional[str] = None
    description: Optional[str] = None
    diff: Optional[str] = None
    project: Optional[str] = None
    examples: Optional[List[str]] = None
    applies_to: Optional[List[str]] = None
    applies_to_rationale: Optional[str] = None
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    reason_for_change: Optional[str] = None
    references: Optional[str] = None
    current_rule: Optional[str] = None
    user_story: Optional[str] = None
    # Hierarchical scope fields
    scope_level: Optional[str] = None  # Allowed: 'global', 'team', 'project', 'machine'
    scope_id: Optional[str] = None
    parent_rule_id: Optional[str] = None


# ARR! feedback_type be a plain string, not an enum, by project decree!
class RuleProposalFeedbackCreate(BaseModel):
    feedback_type: str
    comments: Optional[str] = None


class RuleProposalFeedbackResponse(BaseModel):
    id: str
    rule_proposal_id: str
    feedback_type: str
    comments: Optional[str] = None
    created_at: datetime


# Utility functions to load/save JSON
def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# Utility functions for categories/tags
# Hardened: If applies_to is a list of single characters spelling 'all', treat as ['all']
def list_to_str(lst):
    if lst and isinstance(lst, list):
        # Fix: If applies_to is ['a','l','l'], treat as ['all']
        if len(lst) > 1 and all(isinstance(x, str) and len(x) == 1 for x in lst):
            joined = "".join(lst)
            if joined == "all":
                return "all"
        return ",".join(lst)
    return ""


def str_to_list(s):
    if not s:
        return []
    return [x.strip() for x in s.split(",") if x.strip()]


# Dependency to get DB session
def get_db():
    db_user = os.environ.get("POSTGRES_USER", "postgres")
    db_password = os.environ.get("POSTGRES_PASSWORD", "postgres")
    db_host = os.environ.get("POSTGRES_HOST")
    if not db_host:
        db_host = "test-db" if os.environ.get("ENVIRONMENT") == "test" else "db"
    db_port = os.environ.get("POSTGRES_PORT", "5432")
    db_name = os.environ.get("POSTGRES_DB", "rulesdb")
    database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    db = SessionLocal(bind=create_engine(database_url))
    try:
        yield db
    finally:
        db.close()


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rule_api_server")


# Endpoint: Get environment
@app.get("/env")
def get_env():
    return {"environment": os.environ.get("ENVIRONMENT", "production")}


# Endpoint: Get rule version history
@app.get("/rules/{rule_id}/history")
def get_rule_history(rule_id: str, db: Session = Depends(get_db)):
    if not is_valid_uuid(rule_id):
        raise HTTPException(status_code=404, detail="Invalid rule_id (not a valid UUID)")
    rule = db.query(DBRule).filter(DBRule.id == rule_id).first()
    if not rule:
        return Response(status_code=404)
    from db import RuleVersion

    # ARR! Always cast rule_id to str for DB query to avoid varchar=uuid errors
    versions = (
        db.query(RuleVersion)
        .filter(RuleVersion.rule_id == str(rule_id))
        .order_by(RuleVersion.version.desc())
        .all()
    )
    if not versions:
        raise HTTPException(status_code=404, detail="Rule history not found")
    result = []
    for version in versions:
        data = version.__dict__.copy()
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        data = strip_sqla_state(data)
        data = normalize_rule_dict(data)
        logging.getLogger("examples_normalization").debug(f"[get_rule_history] normalized: {data}")
        result.append(data)
    result = serialize_uuids(result)
    return result


# Endpoint: Submit a bug report
@app.post("/bug-report")
def submit_bug_report(report: BugReportModel, db: Session = Depends(get_db)):
    ts = report.timestamp
    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts)
    db_bug = DBBugReport(
        description=report.description,
        reporter=report.reporter,
        page=report.page,
        user_story=report.user_story,
        timestamp=ts,
    )
    db.add(db_bug)
    db.commit()
    db.refresh(db_bug)
    data = db_bug.__dict__.copy()
    data.pop("_sa_instance_state", None)
    if isinstance(data.get("timestamp"), datetime):
        data["timestamp"] = data["timestamp"].isoformat()
    data = serialize_uuids(data)
    return data


# Endpoint: List all bug reports
@app.get("/bug-reports")
def list_bug_reports(db: Session = Depends(get_db)):
    bugs = db.query(DBBugReport).order_by(DBBugReport.timestamp.desc()).all()
    result = []
    for b in bugs:
        data = b.__dict__.copy()
        data.pop("_sa_instance_state", None)
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        result.append(
            {
                "id": data["id"],
                "description": data["description"],
                "reporter": data["reporter"],
                "page": data["page"],
                "user_story": data.get("user_story"),
                "timestamp": data["timestamp"],
            }
        )
    result = serialize_uuids(result)
    return result


# Endpoint: Suggest an enhancement
@app.post("/suggest-enhancement")
def suggest_enhancement(enh: EnhancementModel, db: Session = Depends(get_db)):
    ts = enh.timestamp
    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts)
    db_enh = DBEnhancement(
        description=enh.description,
        suggested_by=enh.suggested_by,
        page=enh.page,
        tags=",".join(enh.tags) if enh.tags else "",
        categories=",".join(enh.categories) if enh.categories else "",
        timestamp=ts,
        project=enh.project,
        examples=enh.examples,  # New field
        user_story=enh.user_story,
        diff=enh.diff,  # New: diff for enhancements
    )
    db.add(db_enh)
    db.commit()
    db.refresh(db_enh)
    data = db_enh.__dict__.copy()
    data.pop("_sa_instance_state", None)
    if isinstance(data.get("timestamp"), datetime):
        data["timestamp"] = data["timestamp"].isoformat()
    data = serialize_uuids(data)
    return data


# Endpoint: List all enhancements
@app.get("/enhancements")
def list_enhancements(db: Session = Depends(get_db)):
    enhancements = (
        db.query(DBEnhancement).order_by(DBEnhancement.timestamp.desc()).all()
    )
    result = []
    for e in enhancements:
        data = e.__dict__.copy()
        data.pop("_sa_instance_state", None)
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        data["tags"] = str_to_list(data.get("tags", ""))
        data["categories"] = str_to_list(data.get("categories", ""))
        data["applies_to"] = str_to_list(data.get("applies_to", ""))
        data["applies_to_rationale"] = data.get("applies_to_rationale", "")
        data["user_story"] = e.user_story
        data["diff"] = e.diff  # New: include diff in API response
        if 'status' in data:
            data['status'] = enum_to_str(data['status'])
        data = serialize_uuids(data)
        result.append(data)
    return result


# Endpoint: Transfer an enhancement to a proposal
@app.post("/enhancement-to-proposal/{enhancement_id}")
def enhancement_to_proposal(enhancement_id: str, db: Session = Depends(get_db)):
    if not is_valid_uuid(enhancement_id):
        raise HTTPException(status_code=404, detail="Invalid enhancement_id (not a valid UUID)")
    enh = db.query(DBEnhancement).filter(DBEnhancement.id == enhancement_id).first()
    if not enh:
        raise HTTPException(status_code=404, detail="Enhancement not found.")
    if enh.status == "transferred":
        raise HTTPException(status_code=400, detail="Enhancement already transferred.")
    # Create a new proposal from enhancement fields
    import uuid

    from db import Proposal

    now = datetime.utcnow()
    proposal = Proposal(
        id=str(uuid.uuid4()),
        rule_type="enhancement",
        description=enh.description,
        diff="",  # Optionally allow editing diff later
        status="pending",
        submitted_by=enh.suggested_by,
        project=None,
        timestamp=now,
        version=1,
        categories=enh.categories,
        tags=enh.tags,
        applies_to=list_to_str(enh.applies_to),
        applies_to_rationale=enh.applies_to_rationale,
        scope_level=enh.scope_level,
        scope_id=enh.scope_id,
        parent_rule_id=enh.parent_rule_id,
    )
    db.add(proposal)
    enh.status = "transferred"
    db.commit()
    db.refresh(proposal)
    return {"status": "proposed", "id": enh.id}


# Endpoint: Reject an enhancement
@app.post("/reject-enhancement/{enhancement_id}")
def reject_enhancement(enhancement_id: str, db: Session = Depends(get_db)):
    if not is_valid_uuid(enhancement_id):
        raise HTTPException(status_code=404, detail="Invalid enhancement_id (not a valid UUID)")
    enh = db.query(DBEnhancement).filter(DBEnhancement.id == enhancement_id).first()
    if not enh:
        raise HTTPException(status_code=404, detail="Enhancement not found.")
    if enh.status == "rejected":
        raise HTTPException(status_code=400, detail="Enhancement already rejected.")
    if enh.status == "transferred":
        raise HTTPException(status_code=400, detail="Enhancement already transferred.")
    enh.status = "rejected"
    db.commit()
    return {"status": "rejected", "id": enh.id}


# Endpoint: Revert a proposal to enhancement
@app.post("/proposal-to-enhancement/{proposal_id}")
def proposal_to_enhancement(proposal_id: str, db: Session = Depends(get_db)):
    if not is_valid_uuid(proposal_id):
        raise HTTPException(status_code=404, detail="Invalid proposal_id (not a valid UUID)")
    proposal = db.query(DBProposal).filter(DBProposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found.")
    if proposal.status not in ["pending", "rejected"]:
        raise HTTPException(
            status_code=400,
            detail="Only pending or rejected proposals can be reverted to enhancement.",
        )
    # Create enhancement from proposal
    from db import Enhancement

    enh = Enhancement(
        description=proposal.description,
        suggested_by=proposal.submitted_by,
        page=None,
        tags=proposal.tags,
        categories=proposal.categories,
        timestamp=proposal.timestamp,
        status="open",
        proposal_id=proposal.id,
        applies_to=str_to_list(proposal.applies_to),
        applies_to_rationale=proposal.applies_to_rationale,
        scope_level=proposal.scope_level,
        scope_id=proposal.scope_id,
        parent_rule_id=proposal.parent_rule_id,
    )
    db.add(enh)
    proposal.status = "reverted_to_enhancement"
    db.commit()
    db.refresh(enh)
    return {"status": "enhancement", "id": enh.id}


# Endpoint: Accept an enhancement
@app.post("/accept-enhancement/{enhancement_id}")
def accept_enhancement(enhancement_id: str, db: Session = Depends(get_db)):
    if not is_valid_uuid(enhancement_id):
        raise HTTPException(status_code=404, detail="Invalid enhancement_id (not a valid UUID)")
    enh = db.query(DBEnhancement).filter(DBEnhancement.id == enhancement_id).first()
    if not enh:
        raise HTTPException(status_code=404, detail="Enhancement not found.")
    if enh.status != "open":
        raise HTTPException(
            status_code=400, detail="Only open enhancements can be accepted."
        )
    enh.status = "accepted"
    db.commit()
    return {"status": "accepted", "id": enh.id}


# Endpoint: Complete an enhancement
@app.post("/complete-enhancement/{enhancement_id}")
def complete_enhancement(enhancement_id: str, db: Session = Depends(get_db)):
    if not is_valid_uuid(enhancement_id):
        raise HTTPException(status_code=404, detail="Invalid enhancement_id (not a valid UUID)")
    enh = db.query(DBEnhancement).filter(DBEnhancement.id == enhancement_id).first()
    if not enh:
        raise HTTPException(status_code=404, detail="Enhancement not found.")
    if enh.status != "accepted":
        raise HTTPException(
            status_code=400, detail="Only accepted enhancements can be completed."
        )
    enh.status = "completed"
    db.commit()
    return {"status": "completed", "id": enh.id}


# Endpoint: Get changelog as Markdown
@app.get("/changelog", response_class=JSONResponse)
def get_changelog_markdown():
    try:
        with open("CHANGELOG.md", "r") as f:
            content = f.read()
        # Return as Markdown content type
        return Response(content, media_type="text/markdown")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not read changelog: {e}")


# Endpoint: Get changelog as JSON
@app.get("/changelog.json")
def get_changelog_json():
    try:
        with open("CHANGELOG.md", "r") as f:
            content = f.read()
        # Simple parser: split by headings and bullet points
        changelog = []
        current_section = None
        current_subsection = None
        for line in content.splitlines():
            if line.startswith("# "):
                current_section = {"title": line[2:].strip(), "subsections": []}
                changelog.append(current_section)
            elif line.startswith("## "):
                current_subsection = {"title": line[3:].strip(), "entries": []}
                if current_section:
                    current_section["subsections"].append(current_subsection)
            elif line.startswith("### "):
                # Treat as a sub-subsection
                subsub = {"title": line[4:].strip(), "entries": []}
                if current_subsection:
                    current_subsection["entries"].append(subsub)
                    current_subsection = subsub
            elif line.strip().startswith("-"):
                entry = line.strip()[1:].strip()
                if current_subsection:
                    current_subsection.setdefault("entries", []).append(entry)
                elif current_section:
                    current_section.setdefault("entries", []).append(entry)
        return changelog
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not parse changelog: {e}")


# Run with: uvicorn rule_api_server:app --reload

class EnhancementUpdate(BaseModel):
    description: Optional[str] = None
    suggested_by: Optional[str] = None
    page: Optional[str] = None
    tags: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    timestamp: Optional[datetime] = None
    status: Optional[str] = None
    proposal_id: Optional[str] = None
    project: Optional[str] = None
    examples: Optional[str] = None
    user_story: Optional[str] = None
    diff: Optional[str] = None  # New: diff for enhancements

@app.patch("/enhancements/{enhancement_id}")
def update_enhancement(enhancement_id: str, update: EnhancementUpdate, db: Session = Depends(get_db)):
    if not is_valid_uuid(enhancement_id):
        raise HTTPException(status_code=404, detail="Invalid enhancement_id (not a valid UUID)")
    enh = db.query(DBEnhancement).filter(DBEnhancement.id == enhancement_id).first()
    if not enh:
        raise HTTPException(status_code=404, detail="Enhancement not found")
    data = update.dict(exclude_unset=True)
    for field, value in data.items():
        if field in ["categories", "tags"] and value is not None:
            setattr(enh, field, list_to_str(value))
        elif value is not None:
            setattr(enh, field, value)
    db.commit()
    db.refresh(enh)
    # Return as dict to match list_enhancements
    result = enh.__dict__.copy()
    result.pop("_sa_instance_state", None)
    if isinstance(result.get("timestamp"), datetime):
        result["timestamp"] = result["timestamp"].isoformat()
    result["tags"] = str_to_list(result.get("tags", ""))
    result["categories"] = str_to_list(result.get("categories", ""))
    result["applies_to"] = str_to_list(result.get("applies_to", ""))
    result["applies_to_rationale"] = result.get("applies_to_rationale", "")
    result["user_story"] = enh.user_story
    result["diff"] = enh.diff  # New: include diff in PATCH response
    if 'status' in result:
        result['status'] = enum_to_str(result['status'])
    result = serialize_uuids(result)
    # In all endpoints before 'return result':
    result["examples"] = ensure_examples_list(result.get("examples"))
    return result

# --- Memory Graph API ---

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
    embedding: Optional[List[float]] = None
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

# Helper to generate embedding using Ollama
OLLAMA_EMBEDDING_URL = "http://host.docker.internal:11434/api/embeddings"
OLLAMA_EMBEDDING_MODEL = "nomic-embed-text:latest"

def get_embedding_ollama(text: str) -> List[float]:
    response = requests.post(
        OLLAMA_EMBEDDING_URL,
        json={"model": OLLAMA_EMBEDDING_MODEL, "prompt": text}
    )
    response.raise_for_status()
    return response.json()["embedding"]

@app.post("/memory/nodes", response_model=MemoryNodeOut)
def create_memory_node(node: MemoryNodeCreate):
    """
    Create a new memory node. The 'embedding' is always generated server-side from the 'content' field. Do NOT provide 'embedding' in the request body.
    """
    try:
        # Generate embedding from content
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
        result = {
            "id": str(db_node.id) if isinstance(db_node.id, uuid.UUID) else db_node.id,
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
        result.append({
            "id": str(db_node.id) if isinstance(db_node.id, uuid.UUID) else db_node.id,
            "namespace": db_node.namespace,
            "content": db_node.content,
            "embedding": embedding,
            "meta": db_node.meta,
            "created_at": db_node.created_at,
        })
    session.close()
    return result

def enum_to_str(x):
    if hasattr(x, 'value'):
        return x.value
    return str(x)

def ensure_examples_list(val):
    import json
    def parse_item(item):
        if isinstance(item, str):
            try:
                parsed = json.loads(item)
                if isinstance(parsed, list):
                    return parsed
                elif isinstance(parsed, dict):
                    # If dict has a single key and empty value, treat key as the example string
                    if len(parsed) == 1 and list(parsed.values())[0] in (None, ""):
                        return [list(parsed.keys())[0]]
                    return [parsed]
                elif isinstance(parsed, str):
                    return [parsed]
                else:
                    return [str(parsed)]
            except Exception:
                # Fallback: treat as comma-separated or single value
                if ',' in item:
                    return [v.strip() for v in item.split(',') if v.strip()]
                return [item]
        elif isinstance(item, dict):
            # If dict has a single key and empty value, treat key as the example string
            if len(item) == 1 and list(item.values())[0] in (None, ""):
                return [list(item.keys())[0]]
            return [item]
        elif isinstance(item, list):
            flat = []
            for sub in item:
                flat.extend(parse_item(sub))
            return flat
        elif item is None:
            return []
        return [str(item)]
    if isinstance(val, list):
        flat = []
        for item in val:
            flat.extend(parse_item(item))
        return flat
    return parse_item(val)

def strip_sqla_state(data):
    # Remove SQLAlchemy internal state and any non-serializable fields
    if isinstance(data, dict):
        return {k: v for k, v in data.items() if not k.startswith('_sa_') and not k.endswith('_state')}
    return data

def get_project_onboarding_progress(db: Session, project_name: str, path: str):
    try:
        uuid.UUID(project_name)
        project_id = resolve_project_id(db, project_name)
    except Exception:
        project_id = resolve_project_id(db, project_name, **project_defaults_from_name(project_name))
    # ... existing logic ...

# ARR! Register pirate validation handler for all 422s
app.add_exception_handler(RequestValidationError, pirate_validation_exception_handler)
