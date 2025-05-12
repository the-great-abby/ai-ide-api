import uuid
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException, Path, UploadFile, File, Form, Body
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import os
import tempfile
import shutil
import scripts.suggest_rules as suggest_rules
from fastapi.responses import JSONResponse
from db import SessionLocal, Rule as DBRule, Proposal as DBProposal, StatusEnum, init_db, BugReport as DBBugReport, Enhancement as DBEnhancement
from sqlalchemy.orm import Session
from fastapi import Depends
from fastapi.middleware.cors import CORSMiddleware
import logging

app = FastAPI(title="Rule Proposal API")

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev, allow all. For prod, restrict to ["http://localhost:3000"] or your domain.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# File paths for storing rules and proposals
RULES_FILE = "rules.json"
PROPOSALS_FILE = "proposals.json"

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

class BugReportModel(BaseModel):
    description: str
    reporter: Optional[str] = None
    page: Optional[str] = None
    timestamp: Optional[str] = Field(default_factory=lambda: datetime.utcnow().isoformat())

class EnhancementModel(BaseModel):
    description: str
    suggested_by: Optional[str] = None
    page: Optional[str] = None
    tags: Optional[list[str]] = []
    categories: Optional[list[str]] = []
    timestamp: Optional[str] = Field(default_factory=lambda: datetime.utcnow().isoformat())

# Utility functions to load/save JSON
def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# Utility functions for categories/tags
def list_to_str(lst):
    return ",".join(lst) if lst else ""

def str_to_list(s):
    return [x for x in (s or "").split(",") if x]

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
    )
    db.add(db_proposal)
    db.commit()
    db.refresh(db_proposal)
    # Remove keys that will be overridden
    data = db_proposal.__dict__.copy()
    data.pop('_sa_instance_state', None)
    data.pop('timestamp', None)
    data.pop('categories', None)
    data.pop('tags', None)
    return RuleProposal(
        **data,
        timestamp=db_proposal.timestamp.isoformat() if isinstance(db_proposal.timestamp, datetime) else db_proposal.timestamp,
        categories=str_to_list(db_proposal.categories),
        tags=str_to_list(db_proposal.tags),
    )

# Endpoint: List all pending proposals
@app.get("/pending-rule-changes", response_model=List[RuleProposal])
def list_pending_proposals(db: Session = Depends(get_db)):
    proposals = db.query(DBProposal).filter(DBProposal.status == StatusEnum.pending).all()
    result = []
    for p in proposals:
        data = p.__dict__.copy()
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        data["categories"] = str_to_list(data.get("categories", ""))
        data["tags"] = str_to_list(data.get("tags", ""))
        result.append(RuleProposal(**data))
    return result

# Endpoint: Approve a proposal (with versioning)
@app.post("/approve-rule-change/{proposal_id}")
def approve_rule_change(proposal_id: str = Path(..., description="Proposal ID"), db: Session = Depends(get_db)):
    from db import RuleVersion
    proposal = db.query(DBProposal).filter(DBProposal.id == proposal_id).first()
    logger.info(f"APPROVE: proposal.id={proposal.id}, proposal.rule_id={getattr(proposal, 'rule_id', None)}, payload={proposal.__dict__}")
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found.")
    if proposal.status != StatusEnum.pending:
        raise HTTPException(status_code=400, detail="Proposal already processed.")
    proposal.status = StatusEnum.approved
    # Use rule_id for versioning if present
    target_rule_id = proposal.rule_id if getattr(proposal, 'rule_id', None) else proposal.id
    existing_rule = db.query(DBRule).filter(DBRule.id == target_rule_id).first()
    logger.info(f"APPROVE: existing_rule for id={target_rule_id}: {existing_rule.__dict__ if existing_rule else None}")
    new_version = 1
    if existing_rule:
        # Save previous version
        db.add(RuleVersion(
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
        ))
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
    )
    db.add(db_rule)
    db.commit()
    logger.info(f"APPROVE: new rule version for id={target_rule_id}: {new_version}")
    return {"message": "Proposal approved and rule added.", "version": new_version}

# Endpoint: Reject a proposal
@app.post("/reject-rule-change/{proposal_id}")
def reject_rule_change(proposal_id: str = Path(..., description="Proposal ID"), db: Session = Depends(get_db)):
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
def list_rules(project: Optional[str] = None, category: Optional[str] = None, tag: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(DBRule)
    if project:
        query = query.filter(DBRule.project == project)
    rules = query.all()
    result = []
    for r in rules:
        data = r.__dict__.copy()
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        data["categories"] = str_to_list(data.get("categories", ""))
        data["tags"] = str_to_list(data.get("tags", ""))
        # Filtering by category/tag
        if category and category not in data["categories"]:
            continue
        if tag and tag not in data["tags"]:
            continue
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
def review_code_snippet(
    filename: str = Body(...),
    code: str = Body(...)
):
    """
    Accepts a filename and code string, runs rule suggestion/linting, returns suggestions.
    """
    import tempfile
    suggestions = []
    # Write code to a temp file and use scan_file
    with tempfile.NamedTemporaryFile(suffix='.py', mode='w+', delete=False) as tmp:
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
    versions = db.query(RuleVersion).filter(RuleVersion.rule_id == rule_id).order_by(RuleVersion.version.desc()).all()
    result = []
    for v in versions:
        data = v.__dict__.copy()
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        data["categories"] = str_to_list(data.get("categories", ""))
        data["tags"] = str_to_list(data.get("tags", ""))
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
        timestamp=ts,
    )
    db.add(db_bug)
    db.commit()
    db.refresh(db_bug)
    return {"status": "received", "id": db_bug.id}

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
    )
    db.add(db_enh)
    db.commit()
    db.refresh(db_enh)
    return {"status": "received", "id": db_enh.id}

# Endpoint: List all enhancements
@app.get("/enhancements")
def list_enhancements(db: Session = Depends(get_db)):
    enhancements = db.query(DBEnhancement).order_by(DBEnhancement.timestamp.desc()).all()
    result = []
    for e in enhancements:
        data = e.__dict__.copy()
        data.pop('_sa_instance_state', None)
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        data["tags"] = str_to_list(data.get("tags", ""))
        data["categories"] = str_to_list(data.get("categories", ""))
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
    from db import Proposal, StatusEnum
    import uuid
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
        raise HTTPException(status_code=400, detail="Only pending or rejected proposals can be reverted to enhancement.")
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
        proposal_id=proposal.id
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
        raise HTTPException(status_code=400, detail="Only open enhancements can be accepted.")
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
        raise HTTPException(status_code=400, detail="Only accepted enhancements can be completed.")
    enh.status = "completed"
    db.commit()
    return {"status": "completed", "id": enh.id}

# Run with: uvicorn rule_api_server:app --reload 