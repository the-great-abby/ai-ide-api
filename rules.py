import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import or_
from sqlalchemy.orm import Session

from auth import require_api_token, require_role
from db import Rule, RuleVersion, get_db, resolve_project_id, resolve_team_id, project_defaults_from_name

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
        if ',' in val:
            return [v.strip() for v in val.split(',') if v.strip()]
        if val.strip():
            return [val.strip()]
        return []
    return [val]


def normalize_rule_fields(data):
    if hasattr(data, '__dict__'):
        data = data.__dict__.copy()
    for field in ['categories', 'tags', 'examples', 'applies_to']:
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
        # Match if any category is present in the comma-separated string
        category_filters = []
        for cat in categories:
            # Match at start, middle, or end
            category_filters.append(Rule.categories.ilike(f"{cat}"))
            category_filters.append(Rule.categories.ilike(f"{cat},%"))
            category_filters.append(Rule.categories.ilike(f"%,{cat}"))
            category_filters.append(Rule.categories.ilike(f"%,{cat},%"))
        query = query.filter(or_(*category_filters))

    if tag:
        tags = [t.strip() for t in tag.split(",")]
        # Match if any tag is present in the comma-separated string
        tag_filters = []
        for t in tags:
            tag_filters.append(Rule.tags.ilike(f"{t}"))
            tag_filters.append(Rule.tags.ilike(f"{t},%"))
            tag_filters.append(Rule.tags.ilike(f"%,{t}"))
            tag_filters.append(Rule.tags.ilike(f"%,{t},%"))
        query = query.filter(or_(*tag_filters))

    if scope_level:
        query = query.filter(Rule.scope_level == scope_level)

    if scope_id:
        # Accept both UUID and string for scope_id
        # If scope_level is project or team, resolve to UUID
        if scope_level == "project":
            try:
                uuid.UUID(scope_id)
                scope_id = resolve_project_id(db, scope_id)
            except Exception:
                scope_id = resolve_project_id(db, scope_id, **project_defaults_from_name(scope_id))
        elif scope_level == "team":
            scope_id = resolve_team_id(db, scope_id)
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
        query = query.filter(
            or_(
                Rule.description.ilike(search_term),
                Rule.diff.ilike(search_term),
                Rule.tags.ilike(search_term),
                Rule.applies_to.ilike(search_term),
            )
        )

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
def update_rule(
    rule_id: str,
    update: RuleUpdateModel = Body(...),
    request: Request = None,
    db: Session = Depends(get_db),
    token: dict = Depends(require_role("admin")),
):
    logger.debug(f"[UPDATE-DEBUG] Called with rule_id={rule_id}, update={update.dict()}, token={token}")
    # Validate UUID format
    if not validate_uuid(rule_id):
        logger.error(f"[UPDATE-DEBUG] Invalid UUID: {rule_id}")
        raise HTTPException(status_code=422, detail="Invalid UUID format for rule_id.")
    logger.debug(f"[UPDATE-DEBUG] UUID validated: {rule_id}")
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    logger.debug(f"[UPDATE-DEBUG] DB query for rule_id={rule_id} returned: {rule}")
    if not rule:
        logger.error(f"[UPDATE-DEBUG] Rule not found: {rule_id}")
        raise HTTPException(status_code=404, detail="Rule not found")
    # Prevent updates to immutable fields
    immutable_fields = ["rule_type", "submitted_by", "version", "id"]
    for field in immutable_fields:
        if field in update.__fields_set__:
            logger.error(f"[UPDATE-DEBUG] Attempt to update immutable field: {field}")
            raise HTTPException(
                status_code=400,
                detail=f"Field '{field}' is immutable and cannot be updated.",
            )
    logger.debug(f"[UPDATE-DEBUG] All checks passed for rule {rule_id}")
    # All checks passed, perform update
    try:
        # ARR! Apply all updates from the request, or walk the plank!
        for field in update.__fields_set__:
            value = getattr(update, field)
            # Normalize list fields
            if field in ['categories', 'tags', 'examples', 'applies_to'] and value is not None:
                value = ensure_list(value)
            setattr(rule, field, value)
        logger.warning(f"[PIRATE-PATCH] Rule {rule_id} updated with fields: {list(update.__fields_set__)}")
        for field in ['categories', 'tags', 'examples', 'applies_to']:
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
    logger.error(f"[UPDATE-DEBUG] Unexpected fall-through in update_rule for rule {rule_id}")
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
        raise HTTPException(status_code=404, detail="Rule not found")
    data = await request.json()
    logger.debug(f"[PROMOTE-DEBUG] Incoming request data: {data}")
    scope_level = data.get("scope_level") or data.get("target_scope")
    scope_id = data.get("scope_id") or data.get("target_scope_id")
    if not scope_level:
        logger.error(f"[PROMOTE-DEBUG] scope_level missing for rule {rule_id}")
        raise HTTPException(status_code=400, detail="scope_level (or target_scope) is required")
    logger.debug(f"[PROMOTE-DEBUG] scope_level validated: {scope_level}")
    levels = ["project", "team", "global"]
    current_idx = levels.index(rule.scope_level) if rule.scope_level in levels else -1
    target_idx = levels.index(scope_level) if scope_level in levels else -1
    if target_idx == -1:
        logger.error(f"[PROMOTE-DEBUG] Invalid scope_level: {scope_level}")
        raise HTTPException(status_code=400, detail="Invalid scope_level")
    logger.debug(f"[PROMOTE-DEBUG] target_idx={target_idx}, current_idx={current_idx}")
    if target_idx <= current_idx:
        logger.error(f"[PROMOTE-DEBUG] Cannot promote to same or lower scope: {scope_level}")
        raise HTTPException(status_code=400, detail="Can only promote to a higher scope")
    if scope_level == "team" and not scope_id:
        logger.error(f"[PROMOTE-DEBUG] scope_id missing for team scope promotion")
        raise HTTPException(status_code=422, detail="scope_id (or target_scope_id) is required for team scope")
    if scope_level == "global" and scope_id:
        logger.error(f"[PROMOTE-DEBUG] scope_id must not be set for global scope promotion")
        raise HTTPException(status_code=400, detail="scope_id (or target_scope_id) must not be set for global scope")
    logger.debug(f"[PROMOTE-DEBUG] All checks passed for rule {rule_id}")
    # All checks passed, perform promotion
    try:
        # ... existing promotion logic ...
        for field in ['categories', 'tags', 'examples', 'applies_to']:
            if hasattr(rule, field):
                setattr(rule, field, ensure_list(getattr(rule, field)))
        db.commit()
        db.refresh(rule)
        data = serialize_uuids(rule.__dict__.copy())
        data = normalize_rule_fields(data)
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        logger.info(f"[PROMOTE-DEBUG] Promotion successful for rule {rule_id}")
        return data
    except Exception as e:
        logger.error(f"[PROMOTE-DEBUG] Internal server error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    logger.error(f"[PROMOTE-DEBUG] Unexpected fall-through in promote_rule for rule {rule_id}")
    raise HTTPException(status_code=500, detail="Unexpected error in promote_rule")
