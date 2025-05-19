import os
import requests
from tqdm import tqdm

RULE_API_URL = os.environ.get("RULE_API_URL", "http://api:8000/rules")
ENHANCEMENT_API_URL = os.environ.get("ENHANCEMENT_API_URL", "http://api:8000/enhancements")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://host.docker.internal:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b-instruct-q6_K")


def fetch_rules():
    resp = requests.get(RULE_API_URL)
    resp.raise_for_status()
    return resp.json()

def fetch_enhancements():
    resp = requests.get(ENHANCEMENT_API_URL)
    resp.raise_for_status()
    return resp.json()


def generate_user_story(item):
    prompt = f"""
Given the following description and diff (if present), generate a concise user story explaining the purpose and context for developers and maintainers. Use the format: 'As a developer, ...'

Description: {item.get('description', '')}
Diff: {item.get('diff', '')}
"""
    data = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    resp = requests.post(OLLAMA_URL, json=data)
    resp.raise_for_status()
    result = resp.json()
    return result.get("response", "").strip()


def update_user_story_rule(rule_id, user_story):
    patch_url = f"{RULE_API_URL}/{rule_id}"
    resp = requests.patch(patch_url, json={"user_story": user_story})
    if resp.status_code == 200:
        print(f"Updated rule {rule_id} with user story.")
    else:
        print(f"Failed to update rule {rule_id}: {resp.status_code} {resp.text}")

def update_user_story_enhancement(enh_id, user_story):
    patch_url = f"{ENHANCEMENT_API_URL}/{enh_id}"
    resp = requests.patch(patch_url, json={"user_story": user_story})
    if resp.status_code == 200:
        print(f"Updated enhancement {enh_id} with user story.")
    else:
        print(f"Failed to update enhancement {enh_id}: {resp.status_code} {resp.text}")


def main():
    # Rules
    rules = fetch_rules()
    missing_rules = [r for r in rules if not r.get("user_story")]
    print(f"Found {len(missing_rules)} rules missing user stories.")
    for rule in tqdm(missing_rules, desc="Updating rules"):
        try:
            user_story = generate_user_story(rule)
            if user_story:
                update_user_story_rule(rule["id"], user_story)
            else:
                print(f"No user story generated for rule {rule['id']}.")
        except Exception as e:
            print(f"Error processing rule {rule['id']}: {e}")
    # Enhancements
    enhancements = fetch_enhancements()
    missing_enh = [e for e in enhancements if not e.get("user_story")]
    print(f"Found {len(missing_enh)} enhancements missing user stories.")
    for enh in tqdm(missing_enh, desc="Updating enhancements"):
        try:
            user_story = generate_user_story(enh)
            if user_story:
                update_user_story_enhancement(enh["id"], user_story)
            else:
                print(f"No user story generated for enhancement {enh['id']}.")
        except Exception as e:
            print(f"Error processing enhancement {enh['id']}: {e}")

if __name__ == "__main__":
    main() 