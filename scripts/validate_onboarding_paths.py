import json
import os
import sys

BUDDY_NAMES = {
    "Patch McDebug",
    "Captain Abby",
    "Doc Testwell",
    "Dave the Database Deckhand",
    "Maple Cartwright",
    "Bosun Riggs",
}


def main():
    # Allow path override
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = os.path.join(os.path.dirname(__file__), "..", "onboarding_paths.json")
    errors = []
    try:
        with open(path, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"ERROR: Could not load JSON: {e}")
        sys.exit(1)
    if not isinstance(data, dict) or "paths" not in data:
        print("ERROR: onboarding_paths.json must be a dict with a 'paths' key.")
        sys.exit(1)
    for i, path_entry in enumerate(data["paths"]):
        prefix = f"Path[{i}] ({path_entry.get('name', '<no name>')})"
        # Check display_name
        if "display_name" not in path_entry:
            errors.append(f"{prefix}: Missing 'display_name'.")
        # Check buddy
        buddy = path_entry.get("buddy")
        if buddy not in BUDDY_NAMES:
            errors.append(
                f"{prefix}: Buddy '{buddy}' not in allowed buddy names: {sorted(BUDDY_NAMES)}."
            )
        # Check steps
        steps = path_entry.get("steps")
        if not isinstance(steps, list):
            errors.append(f"{prefix}: 'steps' must be a list.")
            continue
        for j, step in enumerate(steps):
            sprefix = f"{prefix} Step[{j}]"
            if not isinstance(step, dict):
                errors.append(
                    f"{sprefix}: Step is not a dict (found {type(step)}). All steps must be dicts with 'instruction'."
                )
                continue
            if "instruction" not in step:
                errors.append(f"{sprefix}: Missing 'instruction' field.")
            # doc_link can be missing, but if present must be str or None
            if "doc_link" in step:
                doc_link = step["doc_link"]
                if doc_link is not None and not isinstance(doc_link, str):
                    errors.append(f"{sprefix}: 'doc_link' must be a string or null.")
    if errors:
        print("Validation failed with the following issues:")
        for err in errors:
            print(" -", err)
        sys.exit(1)
    print("Validation passed!")


if __name__ == "__main__":
    main()
