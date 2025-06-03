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
from db import Rule, RuleVersion, get_db

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


@router.get("/rules", response_model=List[RuleOut])
def list_rules(
    category: Optional[str] = None,
    tag: Optional[str] = None,
    scope_level: Optional[str] = None,
    scope_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all approved rules with optional filtering."""
    query = db.query(Rule).filter(Rule.status == "approved")

    if category:
        categories = [c.strip() for c in category.split(",")]
        query = query.filter(Rule.categories.in_(categories))

    if tag:
        tags = [t.strip() for t in tag.split(",")]
        query = query.filter(Rule.tags.in_(tags))

    if scope_level:
        query = query.filter(Rule.scope_level == scope_level)

    if scope_id:
        # Accept both UUID and string for scope_id
        # Try to match as string or UUID (for project/team scopes)
        try:
            import uuid as uuidlib

            uuid_val = str(uuidlib.UUID(scope_id))
            query = query.filter(
                or_(Rule.scope_id == scope_id, Rule.scope_id == uuid_val)
            )
        except Exception:
            query = query.filter(Rule.scope_id == scope_id)

    rules = query.order_by(Rule.timestamp.desc()).all()
    result = []
    for rule in rules:
        data = rule.__dict__.copy()
        data.pop("_sa_instance_state", None)
        data = serialize_uuids(data)
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        # Always return categories as a list
        categories_val = data.get("categories")
        if not categories_val:
            data["categories"] = []
        elif isinstance(categories_val, str):
            data["categories"] = [
                c.strip() for c in categories_val.split(",") if c.strip()
            ]
        # Always return tags as a list
        tags_val = data.get("tags")
        if not tags_val:
            data["tags"] = []
        elif isinstance(tags_val, str):
            data["tags"] = [t.strip() for t in tags_val.split(",") if t.strip()]
        applies_to_val = data.get("applies_to")
        if not applies_to_val:
            data["applies_to"] = []
        elif isinstance(applies_to_val, str):
            data["applies_to"] = [
                a.strip() for a in applies_to_val.split(",") if a.strip()
            ]
        data["examples"] = parse_list_field(data.get("examples"))
        data["applies_to"] = parse_list_field(data.get("applies_to"))
        data["categories"] = parse_list_field(data.get("categories"))
        data["tags"] = parse_list_field(data.get("tags"))
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

    data = rule.__dict__.copy()
    data.pop("_sa_instance_state", None)
    data = serialize_uuids(data)
    if isinstance(data.get("timestamp"), datetime):
        data["timestamp"] = data["timestamp"].isoformat()
    # Always return categories as a list
    categories_val = data.get("categories")
    if not categories_val:
        data["categories"] = []
    elif isinstance(categories_val, str):
        data["categories"] = [c.strip() for c in categories_val.split(",") if c.strip()]
    # Always return tags as a list
    tags_val = data.get("tags")
    if not tags_val:
        data["tags"] = []
    elif isinstance(tags_val, str):
        data["tags"] = [t.strip() for t in tags_val.split(",") if t.strip()]
    applies_to_val = data.get("applies_to")
    if not applies_to_val:
        data["applies_to"] = []
    elif isinstance(applies_to_val, str):
        data["applies_to"] = [a.strip() for a in applies_to_val.split(",") if a.strip()]
    data["examples"] = parse_list_field(data.get("examples"))
    data["applies_to"] = parse_list_field(data.get("applies_to"))
    data["categories"] = parse_list_field(data.get("categories"))
    data["tags"] = parse_list_field(data.get("tags"))
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

    versions = (
        db.query(RuleVersion)
        .filter(RuleVersion.rule_id == rule_id)
        .order_by(RuleVersion.version.desc())
        .all()
    )
    if not versions:
        raise HTTPException(status_code=404, detail="Rule history not found")

    result = []
    for version in versions:
        data = version.__dict__.copy()
        data.pop("_sa_instance_state", None)
        data = serialize_uuids(data)
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        # Always return categories as a list
        categories_val = data.get("categories")
        if not categories_val:
            data["categories"] = []
        elif isinstance(categories_val, str):
            data["categories"] = [
                c.strip() for c in categories_val.split(",") if c.strip()
            ]
        # Always return tags as a list
        tags_val = data.get("tags")
        if not tags_val:
            data["tags"] = []
        elif isinstance(tags_val, str):
            data["tags"] = [t.strip() for t in tags_val.split(",") if t.strip()]
        applies_to_val = data.get("applies_to")
        if not applies_to_val:
            data["applies_to"] = []
        elif isinstance(applies_to_val, str):
            data["applies_to"] = [
                a.strip() for a in applies_to_val.split(",") if a.strip()
            ]
        # Ensure submitted_by and status are always strings
        data["submitted_by"] = data.get("submitted_by") or ""
        data["status"] = data.get("status") or ""
        data["examples"] = parse_list_field(data.get("examples"))
        data["applies_to"] = parse_list_field(data.get("applies_to"))
        data["categories"] = parse_list_field(data.get("categories"))
        data["tags"] = parse_list_field(data.get("tags"))
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
    import logging

    logging.warning(f"[DEBUG] PATCH /rules/{{rule_id}} payload: {update.dict()}")
    logging.warning(
        f"[DEBUG] PATCH /rules/{{rule_id}} __fields_set__: {update.__fields_set__}"
    )
    # Validate UUID format
    if not validate_uuid(rule_id):
        raise HTTPException(status_code=422, detail="Invalid UUID format for rule_id.")
    # Validate required fields for PATCH
    required_fields = ["description", "diff"]
    for field in required_fields:
        if field in update.__fields_set__:
            value = getattr(update, field)
            if value is None or (isinstance(value, str) and not value.strip()):
                raise HTTPException(
                    status_code=422,
                    detail=f"Field '{field}' is required and cannot be empty.",
                )
    # Inspect raw request body for immutable fields
    if request is not None:
        try:
            raw_payload = (
                asyncio.run(request.json())
                if asyncio.iscoroutinefunction(request.json)
                else request.json()
            )
        except Exception:
            raw_payload = None
        if not raw_payload:
            try:
                raw_payload = update.dict(exclude_unset=False)
            except Exception:
                raw_payload = {}
        logging.warning(f"[DEBUG] PATCH /rules/{{rule_id}} raw payload: {raw_payload}")
        immutable_fields = ["rule_type", "submitted_by", "version", "id"]
        for field in immutable_fields:
            if field in raw_payload:
                logging.error(
                    f"[DEBUG] PATCH /rules/{{rule_id}} immutable field present in raw payload: {field} (value: {raw_payload.get(field)})"
                )
                raise HTTPException(
                    status_code=422,
                    detail=f"Field '{field}' is immutable and cannot be updated.",
                )
    try:
        rule = db.query(Rule).filter(Rule.id == rule_id).first()
        logging.warning(
            f"[DEBUG] Rule before update: {rule.__dict__ if rule else None}"
        )
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        # Prevent updates to immutable fields (fallback for direct model usage)
        immutable_fields = ["rule_type", "submitted_by", "version", "id"]
        for field in immutable_fields:
            if field in update.__fields_set__:
                logging.error(
                    f"[DEBUG] PATCH /rules/{{rule_id}} immutable field present: {field} (value: {getattr(update, field, None)})"
                )
                raise HTTPException(
                    status_code=422,
                    detail=f"Field '{field}' is immutable and cannot be updated.",
                )
        # Validate description if present
        if update.description is not None and (
            isinstance(update.description, str) and not update.description.strip()
        ):
            raise HTTPException(
                status_code=400, detail="Field 'description' cannot be empty."
            )
        # Conflict check: approved rules (excluding self)
        new_diff = update.diff if update.diff is not None else rule.diff
        new_scope_level = (
            update.scope_level if update.scope_level is not None else rule.scope_level
        )
        new_scope_id = update.scope_id if update.scope_id is not None else rule.scope_id
        existing_rule = (
            db.query(Rule)
            .filter(
                Rule.id != rule_id,
                Rule.rule_type == rule.rule_type,
                Rule.diff == new_diff,
                Rule.scope_level == new_scope_level,
                Rule.scope_id == new_scope_id,
                Rule.status == "approved",
            )
            .first()
        )
        # Only raise conflict if the update would actually create a duplicate (i.e., another rule matches)
        if existing_rule and (
            new_diff != rule.diff
            or new_scope_level != rule.scope_level
            or new_scope_id != rule.scope_id
        ):
            raise HTTPException(
                status_code=422,
                detail="A rule with the same type, diff, and scope already exists (conflict). Please modify your update.",
            )
        # Only allow updates to mutable fields
        mutable_fields = [
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
        ]
        updated = False
        for field in mutable_fields:
            value = getattr(update, field)
            if value is not None:
                if field == "tags" and isinstance(value, list):
                    # Merge tags with existing tags, ensure uniqueness
                    existing_tags = (
                        set(parse_list_field(rule.tags)) if rule.tags else set()
                    )
                    new_tags = set(value)
                    merged_tags = list(existing_tags.union(new_tags))
                    setattr(rule, field, ",".join(merged_tags))
                elif field in ["categories", "applies_to"] and isinstance(value, list):
                    setattr(rule, field, ",".join(value))
                else:
                    setattr(rule, field, value)
                updated = True
        if updated:
            rule.version += 1
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
        db.commit()
        db.refresh(rule)
        logging.warning(f"[DEBUG] Rule after update: {rule.__dict__}")
    except ValidationError as ve:
        logging.error(f"[DEBUG] ValidationError: {ve.errors()}")
        raise HTTPException(status_code=422, detail=f"Validation error: {ve.errors()}")
    except HTTPException as he:
        logging.error(f"[DEBUG] HTTPException: {he.detail}")
        raise
    except Exception as e:
        logging.error(f"[DEBUG] Exception: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    # Return updated rule in the same format as get_rule
    data = rule.__dict__.copy()
    data.pop("_sa_instance_state", None)
    data = serialize_uuids(data)
    if isinstance(data.get("timestamp"), datetime):
        data["timestamp"] = data["timestamp"].isoformat()
    # Always return categories as a list
    categories_val = data.get("categories")
    if not categories_val:
        data["categories"] = []
    elif isinstance(categories_val, str):
        data["categories"] = [c.strip() for c in categories_val.split(",") if c.strip()]
    # Always return tags as a list
    tags_val = data.get("tags")
    if not tags_val:
        data["tags"] = []
    elif isinstance(tags_val, str):
        data["tags"] = [t.strip() for t in tags_val.split(",") if t.strip()]
    applies_to_val = data.get("applies_to")
    if not applies_to_val:
        data["applies_to"] = []
    elif isinstance(applies_to_val, str):
        data["applies_to"] = [a.strip() for a in applies_to_val.split(",") if a.strip()]
    data["examples"] = parse_list_field(data.get("examples"))
    data["applies_to"] = parse_list_field(data.get("applies_to"))
    data["categories"] = parse_list_field(data.get("categories"))
    data["tags"] = parse_list_field(data.get("tags"))
    return data


@router.post("/rules/{rule_id}/promote", response_model=RuleOut)
async def promote_rule(
    rule_id: str,
    request: Request,
    db: Session = Depends(get_db),
    token: dict = Depends(require_role("admin")),
):
    if not rule_id or rule_id.strip() == "":
        raise HTTPException(status_code=404, detail="Rule ID is required")
    data = await request.json()
    logging.warning(f"[DEBUG] Incoming /rules/{{rule_id}}/promote payload: {data}")
    scope_level = data.get("scope_level")
    scope_id = data.get("scope_id")
    if not scope_level:
        raise HTTPException(status_code=400, detail="scope_level is required")
    # Fetch rule
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    logging.warning(f"[DEBUG] Rule before promotion: {rule.__dict__ if rule else None}")
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    # Only allow promotion to a higher scope
    levels = ["project", "team", "global"]
    current_idx = levels.index(rule.scope_level) if rule.scope_level in levels else -1
    target_idx = levels.index(scope_level) if scope_level in levels else -1
    if target_idx == -1:
        raise HTTPException(status_code=400, detail="Invalid scope_level")
    if target_idx <= current_idx:
        raise HTTPException(
            status_code=400, detail="Can only promote to a higher scope"
        )
    if scope_level == "team" and not scope_id:
        raise HTTPException(
            status_code=400, detail="scope_id is required for team scope"
        )
    if scope_level == "global" and scope_id:
        raise HTTPException(
            status_code=400, detail="scope_id must not be set for global scope"
        )
    # Update rule
    rule.scope_level = scope_level
    rule.scope_id = scope_id if scope_level == "team" else None
    rule.version += 1
    rule.timestamp = datetime.utcnow()
    logging.warning(f"[DEBUG] Rule after promotion: {rule.__dict__}")
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
    db.commit()
    db.refresh(rule)
    # Return updated rule in the same format as get_rule
    result = rule.__dict__.copy()
    result.pop("_sa_instance_state", None)
    result = serialize_uuids(result)
    if isinstance(result.get("timestamp"), datetime):
        result["timestamp"] = result["timestamp"].isoformat()
    result["examples"] = parse_list_field(result.get("examples"))
    result["applies_to"] = parse_list_field(result.get("applies_to"))
    result["categories"] = parse_list_field(result.get("categories"))
    result["tags"] = parse_list_field(result.get("tags"))
    return result
