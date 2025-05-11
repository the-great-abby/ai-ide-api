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
from db import SessionLocal, Rule as DBRule, Proposal as DBProposal, StatusEnum, init_db
from sqlalchemy.orm import Session
from fastapi import Depends
from fastapi.middleware.cors import CORSMiddleware

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
    rule_type: str
    description: str
    diff: str
    status: str = "pending"  # pending, approved, rejected
    submitted_by: Optional[str] = None
    project: Optional[str] = None  # New: project context
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class Rule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rule_type: str
    description: str
    diff: str
    added_by: Optional[str] = None
    project: Optional[str] = None  # New: project context
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

# Utility functions to load/save JSON
def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoint: Propose a rule change
@app.post("/propose-rule-change", response_model=RuleProposal)
def propose_rule_change(proposal: RuleProposal, db: Session = Depends(get_db)):
    # Ensure timestamp is a datetime object
    ts = proposal.timestamp
    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts)
    db_proposal = DBProposal(
        id=proposal.id,
        rule_type=proposal.rule_type,
        description=proposal.description,
        diff=proposal.diff,
        status=StatusEnum.pending,
        submitted_by=proposal.submitted_by,
        project=proposal.project,
        timestamp=ts,
    )
    db.add(db_proposal)
    db.commit()
    db.refresh(db_proposal)
    return proposal

# Endpoint: List all pending proposals
@app.get("/pending-rule-changes", response_model=List[RuleProposal])
def list_pending_proposals(db: Session = Depends(get_db)):
    proposals = db.query(DBProposal).filter(DBProposal.status == StatusEnum.pending).all()
    result = []
    for p in proposals:
        data = p.__dict__.copy()
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        result.append(RuleProposal(**data))
    return result

# Endpoint: Approve a proposal
@app.post("/approve-rule-change/{proposal_id}")
def approve_rule_change(proposal_id: str = Path(..., description="Proposal ID"), db: Session = Depends(get_db)):
    proposal = db.query(DBProposal).filter(DBProposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found.")
    if proposal.status != StatusEnum.pending:
        raise HTTPException(status_code=400, detail="Proposal already processed.")
    proposal.status = StatusEnum.approved
    # Add to rules
    ts = proposal.timestamp
    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts)
    db_rule = DBRule(
        id=proposal.id,
        rule_type=proposal.rule_type,
        description=proposal.description,
        diff=proposal.diff,
        status=StatusEnum.approved,
        submitted_by=proposal.submitted_by,
        added_by=proposal.submitted_by,
        project=proposal.project,
        timestamp=ts,
    )
    db.add(db_rule)
    db.commit()
    return {"message": "Proposal approved and rule added."}

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
def list_rules(project: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(DBRule)
    if project:
        query = query.filter(DBRule.project == project)
    rules = query.all()
    result = []
    for r in rules:
        data = r.__dict__.copy()
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
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

# Run with: uvicorn rule_api_server:app --reload 