import os
import requests
from tqdm import tqdm

RULE_API_URL = os.environ.get("RULE_API_URL", "http://api:8000/rules")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://host.docker.internal:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b-instruct-q6_K")


def fetch_rules():
    resp = requests.get(RULE_API_URL)
    resp.raise_for_status()
    return resp.json()


def generate_user_story(rule):
    prompt = f"""
Given the following rule description and diff, generate a concise user story explaining the purpose and context of the rule for developers and maintainers. Use the format: 'As a developer, ...'

Description: {rule.get('description', '')}
Diff: {rule.get('diff', '')}
"""
    data = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    resp = requests.post(OLLAMA_URL, json=data)
    resp.raise_for_status()
    result = resp.json()
    # Ollama returns {'response': '...'}
    return result.get("response", "").strip()


def update_user_story(rule_id, user_story):
    patch_url = f"{RULE_API_URL}/{rule_id}"
    resp = requests.patch(patch_url, json={"user_story": user_story})
    if resp.status_code == 200:
        print(f"Updated rule {rule_id} with user story.")
    else:
        print(f"Failed to update rule {rule_id}: {resp.status_code} {resp.text}")


def main():
    rules = fetch_rules()
    missing = [r for r in rules if not r.get("user_story")]
    print(f"Found {len(missing)} rules missing user stories.")
    for rule in tqdm(missing, desc="Updating rules"):
        try:
            user_story = generate_user_story(rule)
            if user_story:
                update_user_story(rule["id"], user_story)
            else:
                print(f"No user story generated for rule {rule['id']}.")
        except Exception as e:
            print(f"Error processing rule {rule['id']}: {e}")

if __name__ == "__main__":
    main() 