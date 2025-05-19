import json
import logging
import os
import shutil
import tempfile
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import (Body, Depends, FastAPI, File, Form, HTTPException, Path,
                     UploadFile, Request, Header)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
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
from db import SessionLocal, StatusEnum, init_db
from rule_proposal_feedback import FeedbackType, RuleProposalFeedback
from db import MemorySessionLocal, MemoryVector, MemoryEdge, init_memorydb
from db import ApiErrorLog, ApiAccessToken
from db import UseCase
from db import ProjectOnboardingProgress
import threading

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
class RuleProposal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: Optional[str] = None  # New: reference to rule being updated
    rule_type: str
    description: str
    diff: str
    status: str = "pending"  # pending, approved, rejected
    submitted_by: Optional[str] = None
    project: Optional[str] = None  # New: project context
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    version: int = 1
    categories: List[str] = []
    tags: List[str] = []
    examples: Optional[str] = None
    applies_to: List[str] = []
    applies_to_rationale: Optional[str] = None
    reason_for_change: Optional[str] = None
    references: Optional[str] = None
    current_rule: Optional[str] = None
    user_story: Optional[str] = None


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
    examples: Optional[str] = None
    applies_to: List[str] = []
    applies_to_rationale: Optional[str] = None
    user_story: Optional[str] = None


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
    examples: Optional[str] = None
    applies_to: Optional[List[str]] = None
    applies_to_rationale: Optional[str] = None
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    reason_for_change: Optional[str] = None
    references: Optional[str] = None
    current_rule: Optional[str] = None
    user_story: Optional[str] = None


class RuleProposalFeedbackCreate(BaseModel):
    feedback_type: FeedbackType
    comments: Optional[str] = None


class RuleProposalFeedbackResponse(BaseModel):
    id: str
    rule_proposal_id: str
    feedback_type: FeedbackType
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
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Endpoint: Propose a rule change
@app.post("/propose-rule-change", response_model=RuleProposal)
def propose_rule_change(proposal: RuleProposal, db: Session = Depends(get_db)):
    ts = proposal.timestamp
    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts)
    db_proposal = DBProposal(
        id=proposal.id,
        rule_id=proposal.rule_id,  # Store rule_id if present
        rule_type=proposal.rule_type,
        description=proposal.description,
        diff=proposal.diff,
        status=StatusEnum.pending,
        submitted_by=proposal.submitted_by,
        project=proposal.project,
        timestamp=ts,
        version=proposal.version,
        categories=list_to_str(proposal.categories),
        tags=list_to_str(proposal.tags),
        examples=proposal.examples,
        applies_to=list_to_str(proposal.applies_to),
        applies_to_rationale=proposal.applies_to_rationale,
        reason_for_change=proposal.reason_for_change,
        references=proposal.references,
        current_rule=proposal.current_rule,
        user_story=proposal.user_story,
    )
    db.add(db_proposal)
    db.commit()
    db.refresh(db_proposal)
    # Remove keys that will be overridden
    data = db_proposal.__dict__.copy()
    data.pop("_sa_instance_state", None)
    data.pop("timestamp", None)
    data.pop("categories", None)
    data.pop("tags", None)
    data.pop("applies_to", None)
    data.pop("applies_to_rationale", None)
    data["timestamp"] = (
        db_proposal.timestamp.isoformat()
        if isinstance(db_proposal.timestamp, datetime)
        else db_proposal.timestamp
    )
    data["categories"] = str_to_list(data.get("categories", ""))
    data["tags"] = str_to_list(data.get("tags", ""))
    data["applies_to"] = str_to_list(data.get("applies_to", ""))
    data["applies_to_rationale"] = data.get("applies_to_rationale", "")
    data["user_story"] = db_proposal.user_story
    return RuleProposal(**data)


# Endpoint: List all pending proposals
@app.get("/pending-rule-changes", response_model=List[RuleProposal])
def list_pending_proposals(db: Session = Depends(get_db)):
    proposals = (
        db.query(DBProposal).filter(DBProposal.status == StatusEnum.pending).all()
    )
    result = []
    for p in proposals:
        data = p.__dict__.copy()
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        data["categories"] = str_to_list(data.get("categories", ""))
        data["tags"] = str_to_list(data.get("tags", ""))
        data["applies_to"] = str_to_list(data.get("applies_to", ""))
        data["applies_to_rationale"] = data.get("applies_to_rationale", "")
        data["reason_for_change"] = data.get("reason_for_change", None)
        data["references"] = data.get("references", None)
        data["current_rule"] = data.get("current_rule", None)
        data["user_story"] = data.get("user_story", None)
        result.append(RuleProposal(**data))
    return result


# Endpoint: Approve a proposal (with versioning)
@app.post("/approve-rule-change/{proposal_id}")
def approve_rule_change(
    proposal_id: str = Path(..., description="Proposal ID"),
    db: Session = Depends(get_db),
):
    from db import RuleVersion

    proposal = db.query(DBProposal).filter(DBProposal.id == proposal_id).first()
    logger.info(
        f"APPROVE: proposal.id={proposal.id}, proposal.rule_id={getattr(proposal, 'rule_id', None)}, payload={proposal.__dict__}"
    )
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found.")
    if proposal.status != StatusEnum.pending:
        raise HTTPException(status_code=400, detail="Proposal already processed.")
    proposal.status = StatusEnum.approved
    # Use rule_id for versioning if present
    target_rule_id = (
        proposal.rule_id if getattr(proposal, "rule_id", None) else proposal.id
    )
    existing_rule = db.query(DBRule).filter(DBRule.id == target_rule_id).first()
    logger.info(
        f"APPROVE: existing_rule for id={target_rule_id}: {existing_rule.__dict__ if existing_rule else None}"
    )
    new_version = 1
    if existing_rule:
        # Save previous version
        db.add(
            RuleVersion(
                rule_id=existing_rule.id,
                version=existing_rule.version,
                rule_type=existing_rule.rule_type,
                description=existing_rule.description,
                diff=existing_rule.diff,
                status=existing_rule.status,
                submitted_by=existing_rule.submitted_by,
                added_by=existing_rule.added_by,
                project=existing_rule.project,
                timestamp=existing_rule.timestamp,
                categories=existing_rule.categories,
                tags=existing_rule.tags,
                examples=existing_rule.examples,
            )
        )
        new_version = existing_rule.version + 1
        db.delete(existing_rule)
    # Add to rules
    ts = proposal.timestamp
    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts)
    db_rule = DBRule(
        id=target_rule_id,
        rule_type=proposal.rule_type,
        description=proposal.description,
        diff=proposal.diff,
        status=StatusEnum.approved,
        submitted_by=proposal.submitted_by,
        added_by=proposal.submitted_by,
        project=proposal.project,
        timestamp=ts,
        version=new_version,
        categories=proposal.categories,
        tags=proposal.tags,
        examples=proposal.examples,
        applies_to=list_to_str(proposal.applies_to),
        applies_to_rationale=proposal.applies_to_rationale,
        user_story=proposal.user_story,
        # Optionally store reason_for_change, references, current_rule in Rule if desired
    )
    db.add(db_rule)
    db.commit()
    logger.info(f"APPROVE: new rule version for id={target_rule_id}: {new_version}")
    return {"message": "Proposal approved and rule added.", "version": new_version}


# Endpoint: Reject a proposal
@app.post("/reject-rule-change/{proposal_id}")
def reject_rule_change(
    proposal_id: str = Path(..., description="Proposal ID"),
    db: Session = Depends(get_db),
):
    proposal = db.query(DBProposal).filter(DBProposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found.")
    if proposal.status != StatusEnum.pending:
        raise HTTPException(status_code=400, detail="Proposal already processed.")
    proposal.status = StatusEnum.rejected
    db.commit()
    return {"message": "Proposal rejected."}


# Endpoint: List all rules (for reference)
@app.get("/rules", response_model=List[Rule])
def list_rules(
    project: Optional[str] = None,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(DBRule)
    if project:
        query = query.filter(DBRule.project == project)
    rules = query.all()
    result = []
    # Support multi-category filtering
    category_list = [c.strip() for c in category.split(",")] if category else []
    for r in rules:
        data = r.__dict__.copy()
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        data["categories"] = str_to_list(data.get("categories", ""))
        data["tags"] = str_to_list(data.get("tags", ""))
        data["applies_to"] = str_to_list(data.get("applies_to", ""))
        data["applies_to_rationale"] = data.get("applies_to_rationale", "")
        # Filtering by category/tag
        if category_list and not any(
            cat in data["categories"] for cat in category_list
        ):
            continue
        if tag and tag not in data["tags"]:
            continue
        data["user_story"] = r.user_story
        result.append(Rule(**data))
    return result


# Endpoint: List all rules in MDC format (as a list of strings)
@app.get("/rules-mdc", response_model=List[str])
def list_rules_mdc(project: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(DBRule)
    if project:
        query = query.filter(DBRule.project == project)
    rules = query.all()
    return [r.diff for r in rules if r.diff]


# Endpoint: Review multiple code files (file upload)
@app.post("/review-code-files")
def review_code_files(files: list[UploadFile] = File(...)):
    """
    Accepts multiple files, runs rule suggestion/linting on each, returns dict of filename -> suggestions.
    """
    results = {}
    for upload in files:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            shutil.copyfileobj(upload.file, tmp)
            tmp_path = tmp.name
        suggestions = suggest_rules.scan_file(tmp_path)
        results[upload.filename] = suggestions
    return JSONResponse(content=results)


# Endpoint: Review a code snippet (raw code, for AI/IDE integration)
@app.post("/review-code-snippet")
def review_code_snippet(filename: str = Body(...), code: str = Body(...)):
    """
    Accepts a filename and code string, runs rule suggestion/linting, returns suggestions.
    """
    import tempfile

    suggestions = []
    # Write code to a temp file and use scan_file
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as tmp:
        tmp.write(code)
        tmp.flush()
        suggestions = suggest_rules.scan_file(tmp.name)
    return JSONResponse(content=suggestions)


# Endpoint: Get environment
@app.get("/env")
def get_env():
    return {"environment": os.environ.get("ENVIRONMENT", "production")}


# Endpoint: Get rule version history
@app.get("/rules/{rule_id}/history")
def get_rule_history(rule_id: str, db: Session = Depends(get_db)):
    from db import RuleVersion

    versions = (
        db.query(RuleVersion)
        .filter(RuleVersion.rule_id == rule_id)
        .order_by(RuleVersion.version.desc())
        .all()
    )
    result = []
    for v in versions:
        data = v.__dict__.copy()
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        data["categories"] = str_to_list(data.get("categories", ""))
        data["tags"] = str_to_list(data.get("tags", ""))
        data["applies_to"] = str_to_list(data.get("applies_to", ""))
        data["applies_to_rationale"] = data.get("applies_to_rationale", "")
        result.append(data)
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
    return {"status": "received", "id": db_bug.id}


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
        # applies_to and applies_to_rationale are not present in EnhancementModel
    )
    db.add(db_enh)
    db.commit()
    db.refresh(db_enh)
    return {"status": "received", "id": db_enh.id}


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
        result.append(data)
    return result


# Endpoint: Transfer an enhancement to a proposal
@app.post("/enhancement-to-proposal/{enhancement_id}")
def enhancement_to_proposal(enhancement_id: str, db: Session = Depends(get_db)):
    enh = db.query(DBEnhancement).filter(DBEnhancement.id == enhancement_id).first()
    if not enh:
        raise HTTPException(status_code=404, detail="Enhancement not found.")
    if enh.status == "transferred":
        raise HTTPException(status_code=400, detail="Enhancement already transferred.")
    # Create a new proposal from enhancement fields
    import uuid

    from db import Proposal, StatusEnum

    now = datetime.utcnow()
    proposal = Proposal(
        id=str(uuid.uuid4()),
        rule_type="enhancement",
        description=enh.description,
        diff="",  # Optionally allow editing diff later
        status=StatusEnum.pending,
        submitted_by=enh.suggested_by,
        project=None,
        timestamp=now,
        version=1,
        categories=enh.categories,
        tags=enh.tags,
        applies_to=list_to_str(enh.applies_to),
        applies_to_rationale=enh.applies_to_rationale,
    )
    db.add(proposal)
    enh.status = "transferred"
    db.commit()
    db.refresh(proposal)
    return {"status": "transferred", "proposal_id": proposal.id}


# Endpoint: Reject an enhancement
@app.post("/reject-enhancement/{enhancement_id}")
def reject_enhancement(enhancement_id: str, db: Session = Depends(get_db)):
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
    proposal = db.query(DBProposal).filter(DBProposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found.")
    if proposal.status not in [StatusEnum.pending, StatusEnum.rejected]:
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
    )
    db.add(enh)
    proposal.status = StatusEnum.reverted_to_enhancement
    db.commit()
    db.refresh(enh)
    return {"status": "reverted", "enhancement_id": enh.id}


# Endpoint: Accept an enhancement
@app.post("/accept-enhancement/{enhancement_id}")
def accept_enhancement(enhancement_id: str, db: Session = Depends(get_db)):
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
        from fastapi.responses import Response

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
        import re

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


# Endpoint: Update a rule
@app.patch("/rules/{rule_id}", response_model=Rule)
def update_rule(rule_id: str, update: RuleUpdate, db: Session = Depends(get_db)):
    rule = db.query(DBRule).filter(DBRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    data = update.dict(exclude_unset=True)
    for field, value in data.items():
        if field in ["categories", "tags", "applies_to"] and value is not None:
            setattr(rule, field, list_to_str(value))
        elif value is not None:
            setattr(rule, field, value)
    db.commit()
    db.refresh(rule)
    # Convert DBRule to Pydantic Rule for response
    result = rule.__dict__.copy()
    result["categories"] = str_to_list(result.get("categories", ""))
    result["tags"] = str_to_list(result.get("tags", ""))
    result["applies_to"] = str_to_list(result.get("applies_to", ""))
    result["applies_to_rationale"] = result.get("applies_to_rationale", "")
    if isinstance(result.get("timestamp"), datetime):
        result["timestamp"] = result["timestamp"].isoformat()
    return Rule(**result)


# Endpoint: Submit rule proposal feedback
@app.post(
    "/api/rule_proposals/{proposal_id}/feedback",
    response_model=RuleProposalFeedbackResponse,
)
def submit_rule_proposal_feedback(
    proposal_id: str,
    feedback: RuleProposalFeedbackCreate,
    db: Session = Depends(get_db),
):
    db_feedback = RuleProposalFeedback(
        id=str(uuid.uuid4()),
        rule_proposal_id=proposal_id,
        feedback_type=feedback.feedback_type,
        comments=feedback.comments,
    )
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return RuleProposalFeedbackResponse(
        id=db_feedback.id,
        rule_proposal_id=db_feedback.rule_proposal_id,
        feedback_type=db_feedback.feedback_type,
        comments=db_feedback.comments,
        created_at=db_feedback.created_at,
    )


# Endpoint: List rule proposal feedback
@app.get(
    "/api/rule_proposals/{proposal_id}/feedback",
    response_model=List[RuleProposalFeedbackResponse],
)
def list_rule_proposal_feedback(
    proposal_id: str,
    db: Session = Depends(get_db),
):
    feedbacks = (
        db.query(RuleProposalFeedback)
        .filter(RuleProposalFeedback.rule_proposal_id == proposal_id)
        .all()
    )
    return [
        RuleProposalFeedbackResponse(
            id=f.id,
            rule_proposal_id=f.rule_proposal_id,
            feedback_type=f.feedback_type,
            comments=f.comments,
            created_at=f.created_at,
        )
        for f in feedbacks
    ]


# Pass-through endpoint to Ollama LLM functions service
OLLAMA_FUNCTIONS_URL = os.environ.get("OLLAMA_FUNCTIONS_URL", "http://ollama-functions:8000")

@app.post("/suggest-llm-rules")
async def passthrough_suggest_llm_rules(request: Request):
    """
    Pass-through endpoint to the Ollama LLM functions service.
    """
    try:
        payload = await request.json()
        resp = requests.post(f"{OLLAMA_FUNCTIONS_URL}/suggest-llm-rules", json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


@app.post("/review-code-files-llm")
def review_code_files_llm(files: list[UploadFile] = File(...)):
    """
    Accepts multiple files, sends each file to the ollama-functions service for LLM review, and returns feedback per file.
    """
    import requests
    import os
    import json

    OLLAMA_FUNCTIONS_URL = os.environ.get("OLLAMA_FUNCTIONS_URL", "http://ollama-functions:8000")
    results = {}
    for upload in files:
        upload.file.seek(0)
        files_payload = {"file": (upload.filename, upload.file.read(), upload.content_type or "text/plain")}
        try:
            resp = requests.post(f"{OLLAMA_FUNCTIONS_URL}/review-code-file", files=files_payload, timeout=120)
            resp.raise_for_status()
            feedback = resp.json()
        except Exception as e:
            feedback = [f"[ERROR] ollama-functions call failed: {e}"]
        results[upload.filename] = feedback
    return JSONResponse(content=results)


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
        # --- Patch: ensure embedding is a list ---
        embedding = db_node.embedding
        if isinstance(embedding, str):
            import ast
            embedding = ast.literal_eval(embedding)
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
            "id": db_node.id,
            "namespace": db_node.namespace,
            "content": db_node.content,
            "embedding": embedding,
            "meta": db_node.meta,
            "created_at": db_node.created_at,
        })
    session.close()
    return result

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
    session.close()
    return db_edge

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
    return edges

from sqlalchemy import text

class MemoryNodeSearchRequest(BaseModel):
    """
    Request model for searching memory nodes by similarity.
    Provide either 'text' (preferred) or 'embedding'.
    If 'text' is provided, the server will generate the embedding.
    If 'embedding' is provided, it will be used directly.
    """
    text: Optional[str] = None
    embedding: Optional[List[float]] = None
    namespace: Optional[str] = None
    limit: int = 5

@app.post("/memory/nodes/search", response_model=List[MemoryNodeOut])
def search_memory_nodes(request: MemoryNodeSearchRequest):
    """
    Search for similar memory nodes. Provide either 'text' (preferred) or 'embedding'.
    If 'text' is provided, the server will generate the embedding.
    If 'embedding' is provided, it will be used directly.
    """
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
        result.append({
            "id": db_node.id,
            "namespace": db_node.namespace,
            "content": db_node.content,
            "embedding": embedding,
            "meta": db_node.meta,
            "created_at": db_node.created_at,
        })
    return result

@app.delete("/memory/nodes")
def delete_memory_nodes(namespace: Optional[str] = None):
    session = MemorySessionLocal()
    q = session.query(MemoryVector)
    if namespace:
        q = q.filter(MemoryVector.namespace == namespace)
    count = q.delete(synchronize_session=False)
    session.commit()
    session.close()
    return {"deleted": count, "namespace": namespace}

# --- Error logging middleware ---
@app.middleware("http")
async def error_logging_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        import traceback
        error_id = str(uuid.uuid4())
        stack = traceback.format_exc()
        logger.error(f"[ERROR] Middleware caught exception: {exc}\n{stack}")
        # Log to DB
        db = SessionLocal()
        try:
            log = ApiErrorLog(
                id=error_id,
                timestamp=datetime.utcnow(),
                path=str(request.url.path),
                method=request.method,
                status_code=500,
                message=str(exc),
                stack_trace=stack,
                user_id=None,  # Optionally extract from request if available
            )
            db.add(log)
            db.commit()
        except Exception as log_exc:
            db.rollback()
        finally:
            db.close()
        # Return error ID to client
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error. Reference ID: {error_id}"}
        )

# --- API Token Auth Dependency ---
def require_api_token(authorization: str = Header(...), db: Session = Depends(get_db)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    token = authorization.split(" ", 1)[1]
    db_token = db.query(ApiAccessToken).filter_by(token=token, active=1).first()
    if not db_token:
        raise HTTPException(status_code=401, detail="Invalid or inactive token")
    return db_token

def require_role(roles):
    def dependency(authorization: str = Header(...), db: Session = Depends(get_db)):
        token_obj = require_api_token(authorization, db)
        if token_obj.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return token_obj
    return dependency

# --- Endpoint: Generate API Token ---
@app.post("/admin/generate-token")
def generate_token(description: str = "", created_by: str = None, role: str = "admin", db: Session = Depends(get_db)):
    token = secrets.token_urlsafe(32)
    db_token = ApiAccessToken(token=token, description=description, created_by=created_by, active=1, role=role)
    db.add(db_token)
    db.commit()
    return {"token": token, "description": description, "role": role}

# --- Endpoint: Lookup Error Log by ID (token protected) ---
@app.get("/admin/errors/{error_id}")
def get_error_log(error_id: str, db: Session = Depends(get_db), auth=Depends(require_api_token)):
    log = db.query(ApiErrorLog).filter(ApiErrorLog.id == error_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Error not found")
    return {
        "id": log.id,
        "timestamp": log.timestamp,
        "path": log.path,
        "method": log.method,
        "status_code": log.status_code,
        "message": log.message,
        "stack_trace": log.stack_trace,
        "user_id": log.user_id,
    }

@app.exception_handler(RequestValidationError)
async def custom_validation_exception_handler(request: Request, exc: RequestValidationError):
    import uuid
    from db import SessionLocal, ApiErrorLog
    import traceback
    error_id = str(uuid.uuid4())
    db = SessionLocal()
    try:
        log = ApiErrorLog(
            id=error_id,
            timestamp=datetime.utcnow(),
            path=str(request.url.path),
            method=request.method,
            status_code=422,
            message=f"Validation error: {exc.errors()}",
            stack_trace=traceback.format_exc(),
            user_id=None,
        )
        db.add(log)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "body": exc.body,
            "path": str(request.url.path),
            "message": "Validation failed. Please check your input and try again.",
            "error_id": error_id
        },
    )

class ExampleWorkflowItem(BaseModel):
    endpoint: str
    method: str
    payload: Optional[dict] = None

class UseCaseModel(BaseModel):
    title: str
    description: str
    example_workflow: List[ExampleWorkflowItem]
    tags: Optional[List[str]] = []
    categories: Optional[List[str]] = []
    submitted_by: Optional[str] = None
    source: Optional[str] = None

class UseCaseOut(UseCaseModel):
    id: str
    status: str
    timestamp: str

@app.get("/use-cases", response_model=List[UseCaseOut])
def list_use_cases(db: Session = Depends(get_db)):
    use_cases = db.query(UseCase).filter(UseCase.status == "approved").order_by(UseCase.timestamp.desc()).all()
    result = []
    for uc in use_cases:
        data = uc.__dict__.copy()
        data.pop("_sa_instance_state", None)
        data["tags"] = str_to_list(data.get("tags", ""))
        data["categories"] = str_to_list(data.get("categories", ""))
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        result.append(data)
    return result

@app.post("/use-cases", response_model=UseCaseOut)
def submit_use_case(use_case: UseCaseModel, db: Session = Depends(get_db)):
    db_uc = UseCase(
        id=str(uuid.uuid4()),
        title=use_case.title,
        description=use_case.description,
        example_workflow=[ew.dict() for ew in use_case.example_workflow],
        tags=list_to_str(use_case.tags),
        categories=list_to_str(use_case.categories),
        submitted_by=use_case.submitted_by,
        status="pending",
        source=use_case.source,
    )
    db.add(db_uc)
    db.commit()
    db.refresh(db_uc)
    data = db_uc.__dict__.copy()
    data.pop("_sa_instance_state", None)
    data["tags"] = str_to_list(data.get("tags", ""))
    data["categories"] = str_to_list(data.get("categories", ""))
    if isinstance(data.get("timestamp"), datetime):
        data["timestamp"] = data["timestamp"].isoformat()
    return data

@app.get("/use-cases/pending", response_model=List[UseCaseOut])
def list_pending_use_cases(db: Session = Depends(get_db)):
    use_cases = db.query(UseCase).filter(UseCase.status == "pending").order_by(UseCase.timestamp.desc()).all()
    result = []
    for uc in use_cases:
        data = uc.__dict__.copy()
        data.pop("_sa_instance_state", None)
        data["tags"] = str_to_list(data.get("tags", ""))
        data["categories"] = str_to_list(data.get("categories", ""))
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        result.append(data)
    return result

@app.post("/use-cases/{use_case_id}/approve", response_model=UseCaseOut)
def approve_use_case(use_case_id: str, db: Session = Depends(get_db), auth=Depends(require_role(["admin", "moderator"]))):
    uc = db.query(UseCase).filter(UseCase.id == use_case_id).first()
    if not uc:
        raise HTTPException(status_code=404, detail="Use-case not found.")
    if uc.status == "approved":
        raise HTTPException(status_code=400, detail="Use-case already approved.")
    uc.status = "approved"
    db.commit()
    db.refresh(uc)
    data = uc.__dict__.copy()
    data.pop("_sa_instance_state", None)
    data["tags"] = str_to_list(data.get("tags", ""))
    data["categories"] = str_to_list(data.get("categories", ""))
    if isinstance(data.get("timestamp"), datetime):
        data["timestamp"] = data["timestamp"].isoformat()
    return data

@app.post("/use-cases/{use_case_id}/reject", response_model=UseCaseOut)
def reject_use_case(use_case_id: str, db: Session = Depends(get_db), auth=Depends(require_role(["admin", "moderator"]))):
    uc = db.query(UseCase).filter(UseCase.id == use_case_id).first()
    if not uc:
        raise HTTPException(status_code=404, detail="Use-case not found.")
    if uc.status == "rejected":
        raise HTTPException(status_code=400, detail="Use-case already rejected.")
    uc.status = "rejected"
    db.commit()
    db.refresh(uc)
    data = uc.__dict__.copy()
    data.pop("_sa_instance_state", None)
    data["tags"] = str_to_list(data.get("tags", ""))
    data["categories"] = str_to_list(data.get("categories", ""))
    if isinstance(data.get("timestamp"), datetime):
        data["timestamp"] = data["timestamp"].isoformat()
    return data

# --- Onboarding Progress Pydantic Schemas ---
class OnboardingProgressBase(BaseModel):
    project_id: str
    path: str  # New: onboarding process type
    step: str
    completed: bool = False
    details: Optional[dict] = None

class OnboardingProgressCreate(OnboardingProgressBase):
    pass

class OnboardingProgressUpdate(BaseModel):
    path: Optional[str] = None  # Allow updating path if needed
    completed: Optional[bool] = None
    details: Optional[dict] = None

class OnboardingProgressOut(OnboardingProgressBase):
    id: str
    timestamp: datetime

# --- Onboarding Progress Endpoints ---
@app.get("/onboarding/progress", response_model=List[OnboardingProgressOut])
def list_onboarding_progress(project_id: Optional[str] = None, path: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(ProjectOnboardingProgress)
    if project_id:
        query = query.filter(ProjectOnboardingProgress.project_id == project_id)
    if path:
        query = query.filter(ProjectOnboardingProgress.path == path)
    records = query.all()
    return [OnboardingProgressOut(
        id=r.id,
        project_id=r.project_id,
        path=r.path,
        step=r.step,
        completed=r.completed,
        timestamp=r.timestamp,
        details=r.details,
    ) for r in records]

@app.get("/onboarding/progress/{project_id}", response_model=List[OnboardingProgressOut])
def get_project_onboarding_progress(project_id: str, path: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(ProjectOnboardingProgress).filter(ProjectOnboardingProgress.project_id == project_id)
    if path:
        query = query.filter(ProjectOnboardingProgress.path == path)
    records = query.all()
    return [OnboardingProgressOut(
        id=r.id,
        project_id=r.project_id,
        path=r.path,
        step=r.step,
        completed=r.completed,
        timestamp=r.timestamp,
        details=r.details,
    ) for r in records]

@app.post("/onboarding/progress", response_model=OnboardingProgressOut)
def create_onboarding_progress(progress: OnboardingProgressCreate, db: Session = Depends(get_db)):
    record = ProjectOnboardingProgress(
        id=str(uuid.uuid4()),
        project_id=progress.project_id,
        path=progress.path,
        step=progress.step,
        completed=progress.completed,
        timestamp=datetime.utcnow(),
        details=progress.details,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return OnboardingProgressOut(
        id=record.id,
        project_id=record.project_id,
        path=record.path,
        step=record.step,
        completed=record.completed,
        timestamp=record.timestamp,
        details=record.details,
    )

@app.patch("/onboarding/progress/{progress_id}", response_model=OnboardingProgressOut)
def update_onboarding_progress(progress_id: str, update: OnboardingProgressUpdate, db: Session = Depends(get_db)):
    record = db.query(ProjectOnboardingProgress).filter(ProjectOnboardingProgress.id == progress_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Onboarding progress not found.")
    if update.path is not None:
        record.path = update.path
    if update.completed is not None:
        record.completed = update.completed
    if update.details is not None:
        record.details = update.details
    db.commit()
    db.refresh(record)
    return OnboardingProgressOut(
        id=record.id,
        project_id=record.project_id,
        path=record.path,
        step=record.step,
        completed=record.completed,
        timestamp=record.timestamp,
        details=record.details,
    )

@app.delete("/onboarding/progress/{progress_id}")
def delete_onboarding_progress(progress_id: str, db: Session = Depends(get_db)):
    record = db.query(ProjectOnboardingProgress).filter(ProjectOnboardingProgress.id == progress_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Onboarding progress not found.")
    db.delete(record)
    db.commit()
    return {"message": "Onboarding progress deleted."}

@app.post("/onboarding/init", response_model=List[OnboardingProgressOut])
def init_onboarding(
    project_id: str = Body(...),
    path: str = Body(...),
    steps: Optional[List[str]] = Body(None),
    db: Session = Depends(get_db),
):
    # Load steps from file if not provided
    if steps is None:
        try:
            with open(ONBOARDING_PATHS_FILE) as f:
                all_paths = json.load(f)
            steps = all_paths.get(path)
            if not steps:
                raise HTTPException(status_code=400, detail=f"No steps found for path '{path}' in onboarding_paths.json")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Could not load onboarding_paths.json: {e}")
    created = []
    for step in steps:
        # Check if already exists
        existing = db.query(ProjectOnboardingProgress).filter_by(project_id=project_id, path=path, step=step).first()
        if existing:
            created.append(OnboardingProgressOut(
                id=existing.id,
                project_id=existing.project_id,
                path=existing.path,
                step=existing.step,
                completed=existing.completed,
                timestamp=existing.timestamp,
                details=existing.details,
            ))
        else:
            record = ProjectOnboardingProgress(
                id=str(uuid.uuid4()),
                project_id=project_id,
                path=path,
                step=step,
                completed=False,
                timestamp=datetime.utcnow(),
                details={},
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            created.append(OnboardingProgressOut(
                id=record.id,
                project_id=record.project_id,
                path=record.path,
                step=record.step,
                completed=record.completed,
                timestamp=record.timestamp,
                details=record.details,
            ))
    return created
