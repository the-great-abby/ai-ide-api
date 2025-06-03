import json
import logging
import uuid
from datetime import datetime
from typing import List, Literal, Optional, Union

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.exception_handlers import RequestValidationError
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.orm import Session

from auth import require_api_token, require_role
from db import Proposal, Rule, RuleVersion, get_db
from rule_proposal_feedback import RuleProposalFeedback
from rules import validate_uuid

router = APIRouter(tags=["rule-proposals"])


class ProposalModel(BaseModel):
    rule_type: str = Field(..., min_length=1, description="Type of the rule")
    description: str = Field(..., min_length=1, description="Description of the rule")
    diff: str = Field(..., min_length=1, description="Diff or pattern for the rule")
    submitted_by: str = Field(..., min_length=1, description="User submitting the rule")
    categories: Optional[List[str]] = []
    tags: Optional[List[str]] = []
    examples: Optional[List[str]] = []
    applies_to: Optional[List[str]] = []
    applies_to_rationale: Optional[str] = None
    user_story: Optional[str] = None
    scope_level: str = Field("global", min_length=1)
    scope_id: Optional[str] = Field(
        None,
        description="Team or project association ID, required for team/project scope",
    )
    parent_rule_id: Optional[str] = None
    reason_for_change: str = Field(
        ..., min_length=1, description="Reason for proposing this rule change"
    )
    references: str = Field(
        ..., min_length=1, description="References for this rule proposal"
    )

    class Config:
        extra = "ignore"


class ProposalOut(ProposalModel):
    id: str
    status: str
    version: int
    timestamp: str


class FeedbackIn(BaseModel):
    feedback_type: Literal[
        "accept", "reject", "needs_changes", "suggestion", "question", "concern"
    ]
    comments: str = ""


class FeedbackOut(BaseModel):
    id: str
    rule_proposal_id: str
    feedback_type: str
    comments: str
    created_at: str


def parse_list_field(val):
    if not val:
        return []
    if isinstance(val, list):
        return [str(e) for e in val if e]
    if isinstance(val, str):
        s = val.strip()
        # Try JSON array
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return [str(e) for e in parsed if e]
        except Exception:
            pass
        # Handle set-like string: {"a","b"}
        if s.startswith("{") and s.endswith("}"):
            s = s[1:-1]
        # Split on comma, strip quotes and whitespace
        return [e.strip().strip('"').strip("'") for e in s.split(",") if e.strip()]
    return [str(val)]


def serialize_proposal(obj):
    # Serialize a Proposal SQLAlchemy object to dict, handling UUIDs and enums
    fields = [
        "id",
        "rule_type",
        "description",
        "diff",
        "submitted_by",
        "categories",
        "tags",
        "examples",
        "applies_to",
        "applies_to_rationale",
        "user_story",
        "scope_level",
        "scope_id",
        "parent_rule_id",
        "reason_for_change",
        "references",
        "status",
        "version",
        "timestamp",
    ]
    result = {}
    for f in fields:
        val = getattr(obj, f, None)
        if isinstance(val, uuid.UUID):
            val = str(val)
        if hasattr(val, "value"):  # Enum
            val = val.value
        result[f] = val
    # Parse lists
    for key in ["categories", "tags", "applies_to", "examples"]:
        if result.get(key) is None:
            result[key] = []
        elif isinstance(result[key], str):
            # Try JSON, else comma/line split
            try:
                parsed = json.loads(result[key])
                if isinstance(parsed, list):
                    result[key] = [str(e) for e in parsed if e]
            except Exception:
                if key == "examples":
                    result[key] = [
                        e.strip() for e in result[key].split("\n") if e.strip()
                    ]
                else:
                    result[key] = [
                        e.strip() for e in result[key].split(",") if e.strip()
                    ]
    # Stringify timestamp
    if isinstance(result.get("timestamp"), datetime):
        result["timestamp"] = result["timestamp"].isoformat()
    return result


@router.post("/propose-rule-change", response_model=ProposalOut)
async def propose_rule_change(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
        logging.warning(f"[DEBUG] Incoming /propose-rule-change payload: {payload}")
    except Exception as e:
        logging.error(f"[DEBUG] Error reading payload: {e}")
        raise
    # Validate required fields
    required_fields = [
        "rule_type",
        "description",
        "diff",
        "submitted_by",
        "reason_for_change",
        "references",
    ]
    for field in required_fields:
        value = payload.get(field)
        logging.warning(f"[DEBUG] Field '{field}' value: {value!r}")
        if value is None or (isinstance(value, str) and not value.strip()):
            logging.error(
                f"[DEBUG] 422: Field '{field}' is missing or empty in payload: {payload}"
            )
            raise HTTPException(
                status_code=422,
                detail=f"Field '{field}' is required and cannot be empty.",
            )
    # Validate scope_id for team/project scope
    if payload.get("scope_level") in ("team", "project") and not payload.get(
        "scope_id"
    ):
        logging.error(
            f"[DEBUG] 422: scope_id missing for scope_level={payload.get('scope_level')}, payload: {payload}"
        )
        raise HTTPException(
            status_code=422,
            detail="scope_id (team_or_project_assoc_id) is required for team or project scope.",
        )

    # Validate parent_rule_id if provided
    if payload.get("parent_rule_id"):
        parent_rule = (
            db.query(Rule).filter(Rule.id == payload.get("parent_rule_id")).first()
        )
        if not parent_rule:
            logging.error(
                f"[DEBUG] 422: parent_rule_id does not exist: {payload.get('parent_rule_id')}, payload: {payload}"
            )
            raise HTTPException(
                status_code=422, detail="parent_rule_id does not exist in rules table"
            )

    # Conflict check: approved rules
    existing_rule = (
        db.query(Rule)
        .filter(
            Rule.rule_type == payload.get("rule_type"),
            Rule.diff == payload.get("diff"),
            Rule.scope_level == payload.get("scope_level"),
            Rule.scope_id == payload.get("scope_id"),
            Rule.status == "approved",
        )
        .first()
    )
    if existing_rule:
        raise HTTPException(
            status_code=422,
            detail="A rule with the same type, diff, and scope already exists (conflict). Please modify your rule or scope.",
        )

    # Conflict check: pending proposals
    existing_proposal = (
        db.query(Proposal)
        .filter(
            Proposal.rule_type == payload.get("rule_type"),
            Proposal.diff == payload.get("diff"),
            Proposal.scope_level == payload.get("scope_level"),
            Proposal.scope_id == payload.get("scope_id"),
            Proposal.status == "pending",
        )
        .first()
    )
    if existing_proposal:
        raise HTTPException(
            status_code=422,
            detail="A pending proposal with the same type, diff, and scope already exists (conflict). Please wait for review or modify your proposal.",
        )

    try:
        proposal_id = str(uuid.uuid4())
        new_proposal = Proposal(
            id=proposal_id,
            rule_type=payload.get("rule_type"),
            description=payload.get("description"),
            diff=payload.get("diff"),
            submitted_by=payload.get("submitted_by"),
            categories=",".join(payload.get("categories"))
            if payload.get("categories")
            else None,
            tags=",".join(payload.get("tags")) if payload.get("tags") else None,
            examples=payload.get("examples"),
            applies_to=",".join(payload.get("applies_to"))
            if payload.get("applies_to")
            else None,
            applies_to_rationale=payload.get("applies_to_rationale"),
            user_story=payload.get("user_story"),
            scope_level=payload.get("scope_level"),
            scope_id=payload.get("scope_id"),
            parent_rule_id=payload.get("parent_rule_id"),
            reason_for_change=payload.get("reason_for_change"),
            references=payload.get("references"),
            status="pending",
            version=1,
            timestamp=datetime.utcnow(),
        )
        db.add(new_proposal)
        db.commit()
        db.refresh(new_proposal)
    except ValidationError as ve:
        raise HTTPException(status_code=422, detail=f"Validation error: {ve.errors()}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    data = serialize_proposal(new_proposal)
    logging.warning(f"[DEBUG] approve_rule_change response data: {data}")
    return data


@router.get("/rule-changes", response_model=List[ProposalOut])
def list_rule_changes(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    token: dict = Depends(require_api_token),
):
    """List all rule changes with optional status filter."""
    query = db.query(Proposal)
    if status:
        query = query.filter(Proposal.status == status)

    proposals = query.order_by(Proposal.timestamp.desc()).all()
    result = []
    for proposal in proposals:
        data = serialize_proposal(proposal)
        result.append(data)
    return result


@router.get("/rule-changes/{change_id}", response_model=ProposalOut)
def get_rule_change(
    change_id: str,
    db: Session = Depends(get_db),
    token: dict = Depends(require_api_token),
):
    """Get a specific rule change by ID."""
    # Validate UUID format
    if not validate_uuid(change_id):
        raise HTTPException(status_code=422, detail="Invalid UUID format")

    proposal = db.query(Proposal).filter(Proposal.id == change_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Rule change not found")

    data = serialize_proposal(proposal)
    return data


@router.put("/rule-changes/{change_id}/approve", response_model=ProposalOut)
def approve_rule_change(
    change_id: str,
    db: Session = Depends(get_db),
    token: dict = Depends(require_role("admin")),
):
    """Approve a rule change."""
    # Validate UUID format
    if not validate_uuid(change_id):
        raise HTTPException(status_code=422, detail="Invalid UUID format")

    proposal = db.query(Proposal).filter(Proposal.id == change_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Rule change not found")

    if proposal.status != "pending":
        raise HTTPException(
            status_code=400, detail="Only pending changes can be approved"
        )

    logging.warning(f"[DEBUG] approve_rule_change raw proposal object: {proposal}")
    # Create or update the rule
    rule = (
        db.query(Rule).filter(Rule.id == proposal.parent_rule_id).first()
        if proposal.parent_rule_id
        else None
    )

    if rule:
        # Update existing rule
        rule.version = (rule.version or 1) + 1
        rule.rule_type = proposal.rule_type
        rule.description = proposal.description
        rule.diff = proposal.diff
        rule.categories = proposal.categories
        rule.tags = proposal.tags
        rule.examples = proposal.examples
        rule.applies_to = proposal.applies_to
        rule.applies_to_rationale = proposal.applies_to_rationale
        rule.user_story = proposal.user_story
        rule.scope_level = proposal.scope_level
        rule.scope_id = proposal.scope_id
        rule.timestamp = datetime.utcnow()
        # Create version history entry
        version = RuleVersion(
            rule_id=rule.id,
            version=rule.version,
            rule_type=rule.rule_type,
            description=rule.description,
            diff=rule.diff,
            status=rule.status,
            submitted_by=rule.submitted_by,
            added_by=rule.added_by,
            project=rule.project,
            timestamp=rule.timestamp,
            categories=rule.categories,
            tags=rule.tags,
            examples=rule.examples,
            applies_to=rule.applies_to,
            applies_to_rationale=rule.applies_to_rationale,
            user_story=rule.user_story,
            scope_level=rule.scope_level,
            scope_id=rule.scope_id,
            parent_rule_id=rule.parent_rule_id,
        )
        db.add(version)
        # Link proposal to new rule for future versioning
        proposal.parent_rule_id = rule.id
    else:
        # Create new rule
        rule_id = str(uuid.uuid4())
        rule = Rule(
            id=rule_id,
            rule_type=proposal.rule_type,
            description=proposal.description,
            diff=proposal.diff,
            submitted_by=proposal.submitted_by,
            categories=proposal.categories,
            tags=proposal.tags,
            examples=proposal.examples,
            applies_to=proposal.applies_to,
            applies_to_rationale=proposal.applies_to_rationale,
            user_story=proposal.user_story,
            scope_level=proposal.scope_level,
            scope_id=proposal.scope_id,
            status="approved",
            version=1,
            timestamp=datetime.utcnow(),
        )
        db.add(rule)
        db.flush()  # Ensure rule is written to DB before setting parent_rule_id
        # Create version history entry (include all fields for consistency)
        version = RuleVersion(
            rule_id=rule.id,
            version=1,
            rule_type=rule.rule_type,
            description=rule.description,
            diff=rule.diff,
            status=rule.status,
            submitted_by=rule.submitted_by,
            added_by=getattr(rule, "added_by", None),
            project=getattr(rule, "project", None),
            timestamp=rule.timestamp,
            categories=rule.categories,
            tags=rule.tags,
            examples=rule.examples,
            applies_to=rule.applies_to,
            applies_to_rationale=rule.applies_to_rationale,
            user_story=rule.user_story,
            scope_level=rule.scope_level,
            scope_id=rule.scope_id,
            parent_rule_id=rule.parent_rule_id,
        )
        db.add(version)
        # Link proposal to new rule for future versioning
        proposal.parent_rule_id = rule.id

    # Update proposal status
    proposal.status = "approved"
    db.commit()

    data = serialize_proposal(proposal)
    logging.warning(f"[DEBUG] approve_rule_change proposal data: {data}")
    return data


@router.put("/rule-changes/{change_id}/reject", response_model=ProposalOut)
def reject_rule_change(
    change_id: str,
    db: Session = Depends(get_db),
    token: dict = Depends(require_role("admin")),
):
    """Reject a rule change."""
    proposal = db.query(Proposal).filter(Proposal.id == change_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Rule change not found")

    if proposal.status != "pending":
        raise HTTPException(
            status_code=400, detail="Only pending changes can be rejected"
        )

    proposal.status = "rejected"
    db.commit()

    data = serialize_proposal(proposal)
    return data


@router.post("/api/rule_proposals/{proposal_id}/feedback", response_model=FeedbackOut)
def submit_rule_proposal_feedback(
    proposal_id: str,
    feedback: FeedbackIn = Body(...),
    db: Session = Depends(get_db),
    token: dict = Depends(require_api_token),
):
    # Validate UUID format
    if not validate_uuid(proposal_id):
        logging.error(
            f"[DEBUG] 422: Invalid UUID format for proposal_id: {proposal_id}"
        )
        raise HTTPException(status_code=422, detail="Invalid UUID format")
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        logging.error(f"[DEBUG] 404: Proposal not found for proposal_id: {proposal_id}")
        raise HTTPException(status_code=404, detail="Proposal not found")
    # Accept any string for feedback_type
    fb = RuleProposalFeedback(
        id=str(uuid.uuid4()),
        rule_proposal_id=str(proposal_id),
        user_id=getattr(token, "sub", None),
        feedback_type=feedback.feedback_type,
        comments=feedback.comments,
        created_at=datetime.utcnow(),
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return FeedbackOut(
        id=str(fb.id),
        rule_proposal_id=str(fb.rule_proposal_id),
        feedback_type=str(fb.feedback_type),
        comments=fb.comments or "",
        created_at=fb.created_at.isoformat(),
    )


@router.get(
    "/api/rule_proposals/{proposal_id}/feedback", response_model=List[FeedbackOut]
)
def list_rule_proposal_feedback(
    proposal_id: str,
    db: Session = Depends(get_db),
    token: dict = Depends(require_api_token),
):
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    feedbacks = (
        db.query(RuleProposalFeedback)
        .filter(RuleProposalFeedback.rule_proposal_id == proposal_id)
        .order_by(RuleProposalFeedback.created_at.asc())
        .all()
    )
    return [
        FeedbackOut(
            id=str(fb.id),
            rule_proposal_id=str(fb.rule_proposal_id),
            feedback_type=str(fb.feedback_type),
            comments=fb.comments or "",
            created_at=fb.created_at.isoformat(),
        )
        for fb in feedbacks
    ]
