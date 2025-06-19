import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import or_, and_, cast, String, func, Column
from sqlalchemy.orm import Session, aliased
from sqlalchemy.sql import select, literal_column, lateral

from auth import require_api_token, require_role
from db import (
    Rule,
    RuleVersion,
    get_db,
    resolve_project_id,
    resolve_team_id,
    project_defaults_from_name,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["rules"])


class RuleModel(BaseModel):
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
    scope_id: Optional[str] = None
    parent_rule_id: Optional[str] = None


class RuleOut(RuleModel):
    id: str
    status: str
    version: int
    timestamp: str


class RuleUpdateModel(BaseModel):
    description: Optional[str] = Field(None, min_length=1)
    diff: Optional[str] = Field(None, min_length=1)
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    examples: Optional[List[str]] = None
    applies_to: Optional[List[str]] = None
    applies_to_rationale: Optional[str] = None
    user_story: Optional[str] = None
    scope_level: Optional[str] = Field(None, min_length=1)
    scope_id: Optional[str] = None
    submitted_by: Optional[str] = Field(None, min_length=1)
    reason_for_change: Optional[str] = None
    references: Optional[str] = None


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


def serialize_uuids(d):
    # Recursively convert UUIDs to strings in dicts and lists
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, uuid.UUID):
                d[k] = str(v)
            elif isinstance(v, dict):
                d[k] = serialize_uuids(v)
            elif isinstance(v, list):
                d[k] = [serialize_uuids(i) for i in v]
    elif isinstance(d, list):
        d = [serialize_uuids(i) for i in d]
    return d


def validate_uuid(value: str) -> bool:
    """Validate that a string is a valid UUID."""
    try:
        uuid_obj = uuid.UUID(value)
        return str(uuid_obj) == value
    except (ValueError, AttributeError, TypeError):
        return False


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
        if "," in val:
            return [v.strip() for v in val.split(",") if v.strip()]
        if val.strip():
            return [val.strip()]
        return []
    return [val]


def normalize_rule_fields(data):
    if hasattr(data, "__dict__"):
        data = data.__dict__.copy()
    for field in ["categories", "tags", "examples", "applies_to"]:
        data[field] = ensure_list(data.get(field))
    return data


@router.get("/rules", response_model=List[RuleOut])
def list_rules(
    category: Optional[str] = None,
    tag: Optional[str] = None,
    scope_level: Optional[str] = None,
    scope_id: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all approved rules with optional filtering and search."""
    query = db.query(Rule).filter(Rule.status == "approved")

    if category:
        categories = [c.strip() for c in category.split(",")]
        category_filters = [
            Rule.categories.op("@>")(json.dumps([cat])) for cat in categories
        ]
        if len(category_filters) == 1:
            query = query.filter(category_filters[0])
        else:
            query = query.filter(or_(*category_filters))

    if tag:
        tags = [t.strip() for t in tag.split(",")]
        tag_filters = [Rule.tags.op("@>")(json.dumps([tag])) for tag in tags]
        if len(tag_filters) == 1:
            query = query.filter(tag_filters[0])
        else:
            query = query.filter(or_(*tag_filters))

    if scope_level:
        query = query.filter(Rule.scope_level == scope_level)

    if scope_id:
        # Accept both UUID and string for scope_id
        # If scope_level is project or team, resolve to UUID if needed
        if scope_level == "project":
            # If not a valid UUID, treat as project name
            if not validate_uuid(scope_id):
                try:
                    scope_id = resolve_project_id(
                        db, scope_id, **project_defaults_from_name(scope_id)
                    )
                except Exception:
                    raise HTTPException(
                        status_code=422,
                        detail=f"Could not resolve project name '{scope_id}' to UUID.",
                    )
        elif scope_level == "team":
            # If not a valid UUID, treat as team name
            if not validate_uuid(scope_id):
                try:
                    scope_id = resolve_team_id(db, scope_id)
                except Exception:
                    raise HTTPException(
                        status_code=422,
                        detail=f"Could not resolve team name '{scope_id}' to UUID.",
                    )
        try:
            import uuid as uuidlib

            uuid_val = str(uuidlib.UUID(scope_id))
            query = query.filter(
                or_(Rule.scope_id == scope_id, Rule.scope_id == uuid_val)
            )
        except Exception:
            query = query.filter(Rule.scope_id == scope_id)

    if search:
        search_term = f"%{search.lower()}%"
        # Lateral join for tags
        tags_lateral = select(
            func.jsonb_array_elements_text(Rule.tags).label("tag_elem")
        ).lateral()
        applies_to_lateral = select(
            func.jsonb_array_elements_text(Rule.applies_to).label("applies_to_elem")
        ).lateral()
        query = query.outerjoin(tags_lateral, literal_column("true")).outerjoin(
            applies_to_lateral, literal_column("true")
        )
        query = query.filter(
            or_(
                Rule.description.ilike(search_term),
                Rule.diff.ilike(search_term),
                literal_column("tag_elem").ilike(search_term),
                literal_column("applies_to_elem").ilike(search_term),
            )
        )

    # Before executing the query, log the SQL for debugging
    try:
        logger.debug(
            f"[FILTER-DEBUG] SQL: {str(query.statement.compile(compile_kwargs={'literal_binds': True}))}"
        )
    except Exception as e:
        logger.error(f"[FILTER-DEBUG] Could not compile SQL: {e}")
    rules = query.order_by(Rule.timestamp.desc()).all()
    result = []
    for rule in rules:
        data = serialize_uuids(rule.__dict__.copy())
        data = normalize_rule_fields(data)
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        result.append(data)
    return result


@router.get("/rules/{rule_id}", response_model=RuleOut)
def get_rule(rule_id: str, db: Session = Depends(get_db)):
    """Get a specific rule by ID."""
    # Validate UUID format
    if not validate_uuid(rule_id):
        raise HTTPException(status_code=422, detail="Invalid UUID format")
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    data = serialize_uuids(rule.__dict__.copy())
    data = normalize_rule_fields(data)
    if isinstance(data.get("timestamp"), datetime):
        data["timestamp"] = data["timestamp"].isoformat()
    return data


@router.get("/rules/{rule_id}/history", response_model=List[RuleOut])
def get_rule_history(
    rule_id: str,
    db: Session = Depends(get_db),
    token: dict = Depends(require_role("admin")),
):
    """Get version history for a rule."""
    # Validate UUID format
    if not validate_uuid(rule_id):
        raise HTTPException(status_code=422, detail="Invalid UUID format")

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
        data = serialize_uuids(version.__dict__.copy())
        data = normalize_rule_fields(data)
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        result.append(data)
    return result


@router.patch("/rules/{rule_id}", response_model=RuleOut)
async def update_rule(
    rule_id: str,
    update: RuleUpdateModel = Body(...),
    request: Request = None,
    db: Session = Depends(get_db),
    token: dict = Depends(require_role("admin")),
):
    logger.debug(
        f"[UPDATE-DEBUG] Called with rule_id={rule_id}, update={update.dict()}, token={token}"
    )
    # Validate UUID format
    if not validate_uuid(rule_id):
        logger.error(f"[UPDATE-DEBUG] Invalid UUID: {rule_id}")
        raise HTTPException(status_code=422, detail="Invalid UUID format for rule_id.")
    logger.debug(f"[UPDATE-DEBUG] UUID validated: {rule_id}")
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    logger.debug(f"[UPDATE-DEBUG] DB query for rule_id={rule_id} returned: {rule}")
    if not rule:
        logger.error(f"[UPDATE-DEBUG] Rule not found: {rule_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Rule not found: {rule_id}. Did you approve the proposal first?",
        )
    # Log the raw incoming payload for debugging
    try:
        raw_payload = (
            await request.json()
            if request and hasattr(request, "json") and callable(request.json)
            else None
        )
    except Exception:
        raw_payload = None
    logger.debug(f"[UPDATE-DEBUG] Raw incoming payload: {raw_payload}")
    # Allowed fields for update (now includes 'rule_type')
    allowed_fields = {
        "description",
        "diff",
        "categories",
        "tags",
        "examples",
        "applies_to",
        "applies_to_rationale",
        "user_story",
        "scope_level",
        "scope_id",
        "submitted_by",
        "reason_for_change",
        "references",
        "rule_type",
    }
    # Only version and id are immutable now
    immutable_fields = {"version", "id"}
    if raw_payload:
        for key in raw_payload:
            if key not in allowed_fields:
                logger.error(f"[UPDATE-DEBUG] Unknown field in update payload: {key}")
                raise HTTPException(
                    status_code=422,
                    detail=f"Unknown field '{key}' in update.",
                )
            if key in immutable_fields:
                logger.error(
                    f"[UPDATE-DEBUG] Attempt to update immutable field in payload: {key}"
                )
                raise HTTPException(
                    status_code=422,
                    detail=f"Field '{key}' is immutable and cannot be updated.",
                )
    # Prevent updates to immutable fields (for extra safety)
    for field in immutable_fields:
        if field in update.__fields_set__:
            logger.error(f"[UPDATE-DEBUG] Attempt to update immutable field: {field}")
            raise HTTPException(
                status_code=422,
                detail=f"Field '{field}' is immutable and cannot be updated.",
            )
    # Validate required string fields are not set to empty string
    required_string_fields = ["description", "diff"]
    for field in required_string_fields:
        if field in update.__fields_set__:
            value = getattr(update, field)
            if value is not None and isinstance(value, str) and value.strip() == "":
                logger.error(f"[UPDATE-DEBUG] Field '{field}' cannot be empty string.")
                raise HTTPException(
                    status_code=422,
                    detail=f"Field '{field}' cannot be empty.",
                )
    # Validate list fields are not set to None
    list_fields = ["categories", "tags", "examples", "applies_to"]
    for field in list_fields:
        if field in update.__fields_set__:
            value = getattr(update, field)
            if value is None:
                logger.error(f"[UPDATE-DEBUG] Field '{field}' cannot be None.")
                raise HTTPException(
                    status_code=422,
                    detail=f"Field '{field}' cannot be None.",
                )
    # Validate no unknown fields are present
    for field in update.__fields_set__:
        if field not in allowed_fields:
            logger.error(f"[UPDATE-DEBUG] Unknown field in update: {field}")
            raise HTTPException(
                status_code=422,
                detail=f"Unknown field '{field}' in update.",
            )
    logger.debug(f"[UPDATE-DEBUG] All checks passed for rule {rule_id}")
    # All checks passed, perform update
    try:
        # ARR! Apply all updates from the request, or walk the plank!
        for field in update.__fields_set__:
            value = getattr(update, field)
            # Normalize list fields
            if (
                field in ["categories", "tags", "examples", "applies_to"]
                and value is not None
            ):
                value = ensure_list(value)
            setattr(rule, field, value)
        logger.warning(
            f"[PIRATE-PATCH] Rule {rule_id} updated with fields: {list(update.__fields_set__)}"
        )
        for field in ["categories", "tags", "examples", "applies_to"]:
            if hasattr(rule, field):
                setattr(rule, field, ensure_list(getattr(rule, field)))
        db.commit()
        db.refresh(rule)
        data = serialize_uuids(rule.__dict__.copy())
        data = normalize_rule_fields(data)
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        logger.info(f"[UPDATE-DEBUG] Update successful for rule {rule_id}")
        return data
    except ValidationError as ve:
        logger.error(f"[UPDATE-DEBUG] Validation error: {ve.errors()}")
        raise HTTPException(status_code=422, detail=f"Validation error: {ve.errors()}")
    except Exception as e:
        logger.error(f"[UPDATE-DEBUG] Internal server error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    logger.error(
        f"[UPDATE-DEBUG] Unexpected fall-through in update_rule for rule {rule_id}"
    )
    raise HTTPException(status_code=500, detail="Unexpected error in update_rule")


@router.post("/rules/{rule_id}/promote", response_model=RuleOut)
async def promote_rule(
    rule_id: str,
    request: Request,
    db: Session = Depends(get_db),
    token: dict = Depends(require_role("admin")),
):
    logger.debug(f"[PROMOTE-DEBUG] Called with rule_id={rule_id}, token={token}")
    # Validate UUID format
    if not validate_uuid(rule_id):
        logger.error(f"[PROMOTE-DEBUG] Invalid UUID: {rule_id}")
        raise HTTPException(status_code=422, detail="Invalid UUID format")
    logger.debug(f"[PROMOTE-DEBUG] UUID validated: {rule_id}")
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    logger.debug(f"[PROMOTE-DEBUG] DB query for rule_id={rule_id} returned: {rule}")
    if not rule:
        logger.error(f"[PROMOTE-DEBUG] Rule not found: {rule_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Rule not found: {rule_id}. Did you approve the proposal first?",
        )
    data = await request.json()
    logger.debug(f"[PROMOTE-DEBUG] Incoming request data: {data}")
    scope_level = data.get("scope_level") or data.get("target_scope")
    scope_id = data.get("scope_id") or data.get("target_scope_id")
    team = data.get("team")
    project = data.get("project")
    if not scope_level:
        logger.error(f"[PROMOTE-DEBUG] scope_level missing for rule {rule_id}")
        raise HTTPException(
            status_code=400, detail="scope_level (or target_scope) is required"
        )
    logger.debug(f"[PROMOTE-DEBUG] scope_level validated: {scope_level}")
    levels = ["project", "team", "global"]
    current_idx = levels.index(rule.scope_level) if rule.scope_level in levels else -1
    target_idx = levels.index(scope_level) if scope_level in levels else -1
    if target_idx == -1:
        logger.error(f"[PROMOTE-DEBUG] Invalid scope_level: {scope_level}")
        raise HTTPException(status_code=400, detail="Invalid scope_level")
    logger.debug(f"[PROMOTE-DEBUG] target_idx={target_idx}, current_idx={current_idx}")
    if target_idx <= current_idx:
        logger.error(
            f"[PROMOTE-DEBUG] Cannot promote to same or lower scope: {scope_level}"
        )
        raise HTTPException(
            status_code=400, detail="Can only promote to a higher scope"
        )
    # Team scope promotion: resolve team name to scope_id
    if scope_level == "team":
        if project and not team and not scope_id:
            logger.error(
                f"[PROMOTE-DEBUG] project provided instead of team for team scope promotion"
            )
            raise HTTPException(
                status_code=422,
                detail="team is required for team scope promotion; got project instead",
            )
        if not scope_id:
            if team:
                try:
                    scope_id = resolve_team_id(db, team)
                except Exception as e:
                    logger.error(
                        f"[PROMOTE-DEBUG] Could not resolve team '{team}' to UUID: {e}"
                    )
                    raise HTTPException(
                        status_code=422,
                        detail=f"Could not resolve team '{team}' to UUID.",
                    )
            else:
                logger.error(
                    f"[PROMOTE-DEBUG] team is required for team scope promotion"
                )
                raise HTTPException(
                    status_code=422, detail="team is required for team scope promotion"
                )
    # Global scope: must not have scope_id, team, or project
    if scope_level == "global" and (scope_id or team or project):
        logger.error(
            f"[PROMOTE-DEBUG] scope_id, team, or project must not be set for global scope promotion"
        )
        raise HTTPException(
            status_code=400,
            detail="scope_id, team, or project must not be set for global scope",
        )
    logger.debug(f"[PROMOTE-DEBUG] All checks passed for rule {rule_id}")
    # All checks passed, perform promotion
    try:
        # Create a new promoted rule (clone with new scope)
        promoted_rule = Rule(
            id=str(uuid.uuid4()),
            rule_type=rule.rule_type,
            description=rule.description,
            diff=rule.diff,
            status="promoted",
            submitted_by=rule.submitted_by,
            added_by=rule.added_by,
            project=rule.project,
            timestamp=datetime.utcnow(),
            version=(rule.version or 1) + 1,
            categories=rule.categories,
            tags=rule.tags,
            examples=rule.examples,
            applies_to=rule.applies_to,
            applies_to_rationale=rule.applies_to_rationale,
            user_story=rule.user_story,
            scope_level=scope_level,
            scope_id=scope_id if scope_level != "global" else None,
            parent_rule_id=rule.parent_rule_id,
            superseded_by=None,
        )
        db.add(promoted_rule)
        db.flush()
        # Mark the old rule as superseded and point to the new rule
        rule.status = "superseded"
        rule.superseded_by = promoted_rule.id
        db.commit()
        db.refresh(promoted_rule)
        data = serialize_uuids(promoted_rule.__dict__.copy())
        data = normalize_rule_fields(data)
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        # Always return status as 'promoted' after promotion
        data["status"] = "promoted"
        logger.info(
            f"[PROMOTE-DEBUG] Promotion successful for rule {rule_id} to {scope_level}/{scope_id}"
        )
        return data
    except Exception as e:
        logger.error(f"[PROMOTE-DEBUG] Internal server error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    logger.error(
        f"[PROMOTE-DEBUG] Unexpected fall-through in promote_rule for rule {rule_id}"
    )
    raise HTTPException(status_code=500, detail="Unexpected error in promote_rule")


@router.get("/rules-mdc")
def rules_mdc(
    project: Optional[str] = None,
    db: Session = Depends(get_db),
    token: dict = Depends(require_api_token),
):
    """
    Return all approved rules as a single Markdown (MDC) document.
    Optionally filter by project.
    """
    query = db.query(Rule).filter(Rule.status == "approved")
    if project:
        query = query.filter(Rule.project == project)
    rules = query.order_by(Rule.timestamp.asc()).all()
    mdc = "\n\n".join(r.diff for r in rules if r.diff)
    return Response(content=mdc, media_type="text/markdown")


# Add 'superseded_by' to Rule model if not present
if not hasattr(Rule, "superseded_by"):
    Rule.superseded_by = Column(String, nullable=True)
