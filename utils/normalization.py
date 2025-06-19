import uuid
import json
import re
import logging


def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except Exception:
        return False


def str_to_list(s):
    if not s:
        return []
    if isinstance(s, list):
        return [str(e) for e in s if e]
    if isinstance(s, str):
        s = s.strip()
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
    return [str(s)]


def clean_list_field(lst):
    # Remove curly braces, extra quotes, and whitespace from each item
    cleaned = []
    for item in lst:
        if isinstance(item, str):
            # Remove curly braces and quotes
            s = item.strip().strip("{}").strip('"').strip("'")
            # Remove leading/trailing whitespace and stray commas
            s = s.strip().strip(",")
            cleaned.append(s)
        else:
            cleaned.append(item)
    return cleaned


def clean_examples_field(lst):
    logger = logging.getLogger("examples_normalization")
    logger.debug(f"clean_examples_field input: {repr(lst)}")
    # Accepts a list, a JSON string, a Postgres array string, a comma-separated string, or a single string
    if lst is None:
        logger.debug("clean_examples_field output: [] (input was None)")
        return []
    if isinstance(lst, str):
        s = lst.strip()
        # Try to parse as JSON array
        if s.startswith("[") and s.endswith("]"):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    out = [str(x).strip("\"'{}[] ") for x in parsed]
                    logger.debug(
                        f"clean_examples_field output: {out} (parsed JSON array)"
                    )
                    return out
                else:
                    out = [str(parsed)]
                    logger.debug(
                        f"clean_examples_field output: {out} (parsed JSON non-list)"
                    )
                    return out
            except Exception as e:
                logger.debug(f"clean_examples_field JSON parse error: {e}")
        # Try to parse as Postgres array string: {"Example 1","Example 2"}
        if s.startswith("{") and s.endswith("}"):
            inner = s[1:-1]
            # Split on commas not inside quotes
            items = re.findall(r'"(.*?)"|([^,]+)', inner)
            result = []
            for match in items:
                val = match[0] if match[0] else match[1]
                if val is not None:
                    val = val.strip("\"'{}[] ")
                    if val:
                        result.append(val)
            logger.debug(
                f"clean_examples_field output: {result} (parsed Postgres array)"
            )
            return result
        # Fallback: comma-separated
        if "," in s:
            out = [item.strip("\"'{}[] ") for item in s.split(",") if item.strip()]
            logger.debug(f"clean_examples_field output: {out} (comma-separated)")
            return out
        # Single value
        out = [s.strip("\"'{}[] ")] if s else []
        logger.debug(f"clean_examples_field output: {out} (single value)")
        return out
    # If it's a list, flatten and clean each item
    if isinstance(lst, list):
        result = []
        for item in lst:
            if isinstance(item, str):
                s = item.strip()
                if s.startswith("{") and s.endswith("}"):
                    # Parse as Postgres array and extend
                    result.extend(clean_examples_field(s))
                else:
                    # Treat as a single example
                    result.append(s.strip("\"'{}[] "))
            elif isinstance(item, (dict, list)):
                result.extend(clean_examples_field(json.dumps(item)))
            else:
                result.append(str(item))
        out = [x for x in result if x]
        logger.debug(f"clean_examples_field output: {out} (flattened list)")
        return out
    # Fallback: treat as string
    out = [str(lst)]
    logger.debug(f"clean_examples_field output: {out} (fallback)")
    return out


def normalize_rule_dict(data):
    # For API output: ensure all required fields are present and list fields are always lists
    required_fields = [
        "rule_type",
        "description",
        "diff",
        "added_by",
        "project",
        "timestamp",
        "categories",
        "tags",
        "examples",
        "applies_to",
        "applies_to_rationale",
        "user_story",
        "scope_level",
        "scope_id",
        "version",
        "status",
        "submitted_by",
    ]
    uuid_fields = ["id", "parent_rule_id", "rule_id", "scope_id", "project"]
    # Normalize list fields: always output as lists for API
    for field in ["categories", "tags", "applies_to"]:
        if field in data:
            if isinstance(data[field], str):
                data[field] = str_to_list(data[field])
            elif not isinstance(data[field], list):
                data[field] = [data[field]] if data[field] else []
            data[field] = clean_list_field(data[field])
        else:
            data[field] = []
    # Examples field special cleaning
    if "examples" in data:
        data["examples"] = clean_examples_field(data["examples"])
    else:
        data["examples"] = []
    # Convert any UUIDs in lists to strings
    for field in ["categories", "tags", "examples", "applies_to"]:
        data[field] = [str(x) if isinstance(x, uuid.UUID) else x for x in data[field]]
    # Convert UUID fields to strings (handle None and lists)
    for field in uuid_fields:
        if field in data:
            if isinstance(data[field], uuid.UUID):
                data[field] = str(data[field])
            elif isinstance(data[field], list):
                data[field] = [
                    str(x) if isinstance(x, uuid.UUID) else x for x in data[field]
                ]
            elif data[field] is None:
                data[field] = None
    # Ensure all required fields are present and not None
    for field in required_fields:
        if field not in data or data[field] is None:
            if field in ["categories", "tags", "examples", "applies_to"]:
                data[field] = []
            elif field == "version":
                data[field] = 1
            else:
                data[field] = ""
    # Extra defensiveness for submitted_by
    if "submitted_by" not in data or data["submitted_by"] is None:
        data["submitted_by"] = ""
    logging.getLogger("examples_normalization").debug(
        f"[normalize_rule_dict] output: {data}"
    )
    return data
