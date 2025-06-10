import json
import logging
import uuid
from datetime import datetime
from typing import List, Literal, Optional, Union
import traceback

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.exception_handlers import RequestValidationError
from fastapi.exceptions import RequestValidationError as FastAPIRequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError, field_validator, validator
from sqlalchemy.orm import Session

from auth import require_api_token, require_role
from db import Proposal, Rule, RuleVersion, get_db, get_or_create_project_by_name, get_or_create_team_by_name, resolve_project_id, resolve_team_id, project_defaults_from_name
from rule_proposal_feedback import RuleProposalFeedback
from rules import validate_uuid
from utils.serialization import serialize_uuids
from utils.normalization import clean_examples_field, normalize_rule_dict

router = APIRouter(tags=["rule-proposals"])

logger = logging.getLogger(__name__)

# Allowed feedback types for rule proposal feedback
ALLOWED_FEEDBACK_TYPES = {"suggestion", "question", "concern"}


# ARR! All IDs and foreign keys be strings, not UUID columns. Pass UUIDs as strings, or ye walk the plank! See ONBOARDING_INTERNAL.md and rules/db_types.mdc for the tale.
class ProposalModel(BaseModel):
    """
    ARR! Pirate warning: The 'project' field may be a project name or a UUID string. It will be resolved to a UUID in the endpoint logic.
    Only 'parent_rule_id' and 'scope_id' are strictly validated as UUIDs here.
    """
    rule_type: str = Field(..., min_length=1, description="Type of the rule")
    description: str = Field(..., min_length=1, description="Description of the rule")
    diff: str = Field(..., min_length=1, description="Diff or pattern for the rule")
    submitted_by: str = Field(..., min_length=1, description="User submitting the rule")
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    examples: Optional[List[str]] = None
    applies_to: Optional[List[str]] = None
    applies_to_rationale: Optional[str] = None
    user_story: Optional[str] = None
    scope_level: Optional[str] = None
    scope_id: Optional[str] = None
    parent_rule_id: Optional[str] = None
    reason_for_change: Optional[str] = None
    references: Optional[str] = None
    project: Optional[str] = None

    @staticmethod
    def _validate_uuid_field(value, field_name):
        if value is None or value == "":
            return None
        try:
            uuid.UUID(str(value))
            return value
        except Exception:
            raise ValueError(f"Field '{field_name}' must be a valid UUID string.")

    @field_validator("parent_rule_id", "scope_id", mode="before")
    @classmethod
    def validate_uuid_fields(cls, v, info):
        return cls._validate_uuid_field(v, info.field_name)

    class Config:
        extra = "allow"


class ProposalOut(ProposalModel):
    id: str
    status: str
    version: int
    timestamp: str
    rule_id: Optional[str] = None


class FeedbackIn(BaseModel):
    feedback_type: str  # Must be one of ALLOWED_FEEDBACK_TYPES
    comments: str = ""

    @validator("feedback_type")
    def validate_feedback_type(cls, v):
        if v not in ALLOWED_FEEDBACK_TYPES:
            raise ValueError(f"Invalid feedback_type: {v}. Allowed: {sorted(ALLOWED_FEEDBACK_TYPES)}")
        return v


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


def ensure_list(val):
    if val is None:
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        # Try to parse as JSON list
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass
        # Fallback: comma split, or wrap as single-item list if no comma
        if ',' in val:
            return [v.strip() for v in val.split(',') if v.strip()]
        if val.strip():
            return [val.strip()]
        return []
    return [val]


def normalize_proposal_fields(data):
    if hasattr(data, '__dict__'):
        data = data.__dict__.copy()
    for field in ['categories', 'tags', 'examples', 'applies_to']:
        data[field] = ensure_list(data.get(field))
    return data


@router.post("/propose-rule-change", response_model=ProposalOut)
async def propose_rule_change(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
        logger.warning(f"[DEBUG] Incoming /propose-rule-change payload: {payload}")
    except Exception as e:
        logger.error(f"[DEBUG] Error reading payload: {e}")
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
        logger.warning(f"[DEBUG] Field '{field}' value: {value!r}")
        if value is None or (isinstance(value, str) and not value.strip()):
            logger.error(
                f"[DEBUG] 422: Field '{field}' is missing or empty in payload: {payload}"
            )
            raise HTTPException(
                status_code=422,
                detail=f"Field '{field}' is required and cannot be empty.",
            )
    # Strictly validate UUID fields if present (except 'project', which can be a name or UUID)
    for uuid_field in ["parent_rule_id", "scope_id"]:
        if payload.get(uuid_field):
            try:
                uuid.UUID(str(payload[uuid_field]))
            except Exception:
                raise HTTPException(status_code=422, detail=f"Field '{uuid_field}' must be a valid UUID string.")
    # Validate scope_id for team/project scope
    if payload.get("scope_level") in ("team", "project") and not payload.get(
        "scope_id"
    ):
        logger.error(
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
            logger.error(
                f"[DEBUG] 404: parent_rule_id does not exist: {payload.get('parent_rule_id')}, payload: {payload}"
            )
            raise HTTPException(
                status_code=404, detail="parent_rule_id does not exist in rules table"
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

    # Resolve scope_id if needed
    if payload.get("scope_level") == "project" and payload.get("scope_id"):
        try:
            uuid.UUID(payload["scope_id"])
            payload["scope_id"] = resolve_project_id(db, payload["scope_id"])
        except Exception:
            payload["scope_id"] = resolve_project_id(db, payload["scope_id"], **project_defaults_from_name(payload["scope_id"]))
    elif payload.get("scope_level") == "team" and payload.get("scope_id"):
        payload["scope_id"] = resolve_team_id(db, payload["scope_id"])
    # Patch: Always resolve project to UUID if set
    if payload.get("project"):
        try:
            uuid.UUID(payload["project"])
            payload["project"] = resolve_project_id(db, payload["project"])
        except Exception:
            payload["project"] = resolve_project_id(db, payload["project"], **project_defaults_from_name(payload["project"]))

    try:
        proposal_id = str(uuid.uuid4())
        new_proposal = Proposal(
            id=proposal_id,
            rule_type=payload.get("rule_type"),
            description=payload.get("description"),
            diff=payload.get("diff"),
            submitted_by=payload.get("submitted_by"),
            categories=ensure_list(payload.get("categories")),
            tags=ensure_list(payload.get("tags")),
            examples=ensure_list(payload.get("examples")),
            applies_to=ensure_list(payload.get("applies_to")),
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
            project=payload.get("project"),
        )
        db.add(new_proposal)
        db.commit()
        db.refresh(new_proposal)
    except ValidationError as ve:
        raise HTTPException(status_code=422, detail=f"Validation error: {ve.errors()}")
    except Exception as e:
        logger.error(f"[ERROR] Exception in /propose-rule-change: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

    data = serialize_proposal(new_proposal)
    data = normalize_rule_dict(data)
    logger.debug(f"[propose_rule_change] normalized: {data}")
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
        data = normalize_rule_dict(data)
        logger.debug(f"[list_rule_changes] normalized: {data}")
        result.append(data)
    return result


@router.get("/rule-changes/{change_id}", response_model=ProposalOut)
def get_rule_change(
    change_id: str,
    db: Session = Depends(get_db),
    token: dict = Depends(require_api_token),
):
    # Validate UUID format
    if not validate_uuid(change_id):
        raise HTTPException(status_code=422, detail="Invalid UUID format")
    proposal = db.query(Proposal).filter(Proposal.id == change_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Rule change not found")
    data = serialize_proposal(proposal)
    data = normalize_rule_dict(data)
    logger.debug(f"[get_rule_change] normalized: {data}")
    return data


@router.put("/rule-changes/{change_id}/approve", response_model=ProposalOut)
def approve_rule_change(
    change_id: str,
    db: Session = Depends(get_db),
    token: dict = Depends(require_role("admin")),
):
    # Validate UUID format
    if not validate_uuid(change_id):
        raise HTTPException(status_code=422, detail="Invalid UUID format")
    proposal = db.query(Proposal).filter(Proposal.id == change_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    # Normalize list fields before saving
    for field in ['categories', 'tags', 'examples', 'applies_to']:
        if hasattr(proposal, field):
            setattr(proposal, field, ensure_list(getattr(proposal, field)))
    if proposal.status != "pending":
        raise HTTPException(
            status_code=400, detail="Only pending changes can be approved"
        )
    logger.debug("Entered approve_rule_change endpoint")
    # Debug: Log incoming proposal ID
    logger.debug(f"Approve called for proposal_id={change_id}")
    all_proposals = db.query(Proposal).all()
    logger.debug(f"Proposal count in DB: {len(all_proposals)}")
    logger.debug(f"All proposal IDs: {[str(p.id) for p in all_proposals]}")

    logger.warning(f"[DEBUG] approve_rule_change raw proposal object: {proposal}")
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
        rule.status = "approved"
        # Always create version history entry on approval
        version = RuleVersion(
            rule_id=str(rule.id),
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
        # Patch: Always resolve project to UUID if set
        project_uuid = None
        if proposal.project:
            project_name = proposal.project
            try:
                uuid.UUID(project_name)
                project_uuid = resolve_project_id(db, project_name)
            except Exception:
                project_uuid = resolve_project_id(db, project_name, **project_defaults_from_name(project_name))
        rule = Rule(
            id=rule_id,
            rule_type=proposal.rule_type,
            description=proposal.description,
            diff=proposal.diff,
            status="approved",
            submitted_by=proposal.submitted_by,
            added_by=getattr(token, "sub", None) if token else None,
            project=project_uuid,
            timestamp=datetime.utcnow(),
            version=1,
            categories=ensure_list(proposal.categories),
            tags=ensure_list(proposal.tags),
            examples=ensure_list(proposal.examples),
            applies_to=ensure_list(proposal.applies_to),
            applies_to_rationale=proposal.applies_to_rationale,
            user_story=proposal.user_story,
            scope_level=proposal.scope_level,
            scope_id=proposal.scope_id,
            parent_rule_id=proposal.parent_rule_id,
        )
        db.add(rule)
        db.flush()
        # Always create version history entry on approval
        version = RuleVersion(
            rule_id=str(rule.id),
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

    # Always fetch the current rule object for response
    if not rule and proposal.parent_rule_id:
        rule = db.query(Rule).filter(Rule.id == proposal.parent_rule_id).first()

    data = serialize_proposal(proposal)
    data = normalize_rule_dict(data)
    logger.debug(f"[approve_rule_change] normalized: {data}")
    # Always include 'rule_id' in the response, set to None if no rule
    data["rule_id"] = str(rule.id) if rule and getattr(rule, "id", None) else None
    return data


@router.put("/rule-changes/{change_id}/reject", response_model=ProposalOut)
def reject_rule_change(
    change_id: str,
    db: Session = Depends(get_db),
    token: dict = Depends(require_role("admin")),
):
    # Validate UUID format
    if not validate_uuid(change_id):
        raise HTTPException(status_code=422, detail="Invalid UUID format")
    proposal = db.query(Proposal).filter(Proposal.id == change_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    # Normalize list fields before saving
    for field in ['categories', 'tags', 'examples', 'applies_to']:
        if hasattr(proposal, field):
            setattr(proposal, field, ensure_list(getattr(proposal, field)))
    if proposal.status != "pending":
        raise HTTPException(
            status_code=400, detail="Only pending changes can be rejected"
        )
    proposal.status = "rejected"
    db.commit()

    data = serialize_proposal(proposal)
    data = normalize_rule_dict(data)
    logger.debug(f"[reject_rule_change] normalized: {data}")
    return data


@router.post("/api/rule_proposals/{proposal_id}/feedback", response_model=FeedbackOut)
def submit_rule_proposal_feedback(
    proposal_id: str,
    feedback: FeedbackIn = Body(...),
    db: Session = Depends(get_db),
    token: dict = Depends(require_api_token),
):
    logger.debug(f"[FEEDBACK-DEBUG] Called with proposal_id={proposal_id}, feedback={feedback.dict()}, token={token}")
    # Validate UUID format
    if not validate_uuid(proposal_id):
        logger.error(f"[FEEDBACK-DEBUG] Invalid UUID: {proposal_id}")
        raise HTTPException(status_code=422, detail="Invalid UUID format")
    logger.debug(f"[FEEDBACK-DEBUG] UUID validated: {proposal_id}")
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    logger.debug(f"[FEEDBACK-DEBUG] DB query for proposal_id={proposal_id} returned: {proposal}")
    if not proposal:
        logger.error(f"[FEEDBACK-DEBUG] Proposal not found: {proposal_id}")
        raise HTTPException(status_code=404, detail="Proposal not found")
    logger.debug(f"[FEEDBACK-DEBUG] Proposal exists: {proposal_id}")
    # Enforce allowed feedback types at API level (defense-in-depth)
    if feedback.feedback_type not in ALLOWED_FEEDBACK_TYPES:
        logger.error(f"[FEEDBACK-DEBUG] Invalid feedback_type: {feedback.feedback_type}")
        raise HTTPException(status_code=422, detail=f"Invalid feedback_type: {feedback.feedback_type}. Allowed: {sorted(ALLOWED_FEEDBACK_TYPES)}")
    logger.debug(f"[FEEDBACK-DEBUG] feedback_type validated: {feedback.feedback_type}")
    # All checks passed, perform feedback creation
    try:
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
        logger.info(f"[FEEDBACK-DEBUG] Feedback created for proposal {proposal_id}")
        return FeedbackOut(
            id=str(fb.id),
            rule_proposal_id=str(fb.rule_proposal_id),
            feedback_type=str(fb.feedback_type),
            comments=fb.comments or "",
            created_at=fb.created_at.isoformat(),
        )
    except Exception as e:
        logger.error(f"[FEEDBACK-DEBUG] Internal server error: {e}")
        raise HTTPException(status_code=500, detail=f"ARR! Failed to create feedback: {e}")
    logger.error(f"[FEEDBACK-DEBUG] Unexpected fall-through in submit_rule_proposal_feedback for proposal {proposal_id}")
    raise HTTPException(status_code=500, detail="Unexpected error in submit_rule_proposal_feedback")


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


def pirate_validation_exception_handler(request, exc):
    # Convert all error contexts to string to avoid non-serializable objects
    errors = exc.errors()
    for err in errors:
        if 'ctx' in err and err['ctx']:
            for k, v in err['ctx'].items():
                if isinstance(v, Exception):
                    err['ctx'][k] = str(v)
    logger.error(f"[PIRATE-DEBUG] Feedback validation error: {errors} | body: {getattr(exc, 'body', None)}")
    return JSONResponse(
        status_code=422,
        content={"detail": errors, "body": getattr(exc, 'body', None)},
    )
