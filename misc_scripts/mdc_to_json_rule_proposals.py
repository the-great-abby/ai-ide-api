import os
import sys
import json
import re
from pathlib import Path
import yaml

# Use absolute paths for Docker container
MDC_DIR = Path("/app/.cursor/rules")
OUTPUT_DIR = Path("/app/ai_ide_rules")
OUTPUT_DIR.mkdir(exist_ok=True)

print(f"MDC_DIR: {MDC_DIR}")
print(f"OUTPUT_DIR: {OUTPUT_DIR}")

# Helper to extract YAML frontmatter and body
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)

def parse_mdc_file(path):
    text = path.read_text()
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    frontmatter = yaml.safe_load(m.group(1))
    body = m.group(2).strip()
    return frontmatter, body

def mdc_to_json(mdc_path):
    front, body = parse_mdc_file(mdc_path)
    # Sensible defaults
    rule_type = front.get('categories', ['general'])[0] if 'categories' in front else 'general'
    description = front.get('description', '')
    diff = f"---\n{yaml.dump(front)}---\n\n{body}"
    out = {
        "rule_type": rule_type,
        "description": description,
        "diff": diff,
        "submitted_by": "portable-rules-bot",
        "categories": front.get('categories', []),
        "tags": front.get('tags', []),
        "project": "shared-rules",
        "applies_to": [],
        "applies_to_rationale": "",
        "examples": ""
    }
    return out

def main():
    mdc_files = list(MDC_DIR.glob("*.mdc"))
    print(f"Found {len(mdc_files)} .mdc files:")
    for mdc_path in mdc_files:
        print(f"  - {mdc_path}")
    for mdc_path in mdc_files:
        front, _ = parse_mdc_file(mdc_path)
        # Skip templates or meta rules if desired
        if mdc_path.name in {"rule_template.mdc", "meta.mdc"}:
            continue
        json_obj = mdc_to_json(mdc_path)
        out_path = OUTPUT_DIR / (mdc_path.stem + ".json")
        with out_path.open("w") as f:
            json.dump(json_obj, f, indent=2)
        print(f"Wrote: {out_path}")

if __name__ == "__main__":
    main() 