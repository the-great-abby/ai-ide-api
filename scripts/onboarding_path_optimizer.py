#!/usr/bin/env python3
"""
Onboarding Path Optimizer
Analyzes onboarding documentation and feedback, uses LLM to suggest improvements or new onboarding paths.
Follows the user story in docs/user_stories/onboarding_path_optimizer.md.
"""
import os
import glob
import logging
import argparse
import requests

# LLM config
OLLAMA_URL = os.environ.get(
    "OLLAMA_URL", "http://host.docker.internal:11434/api/generate"
)
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b-instruct-q6_K")

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("onboarding_path_optimizer")

ONBOARDING_DOCS = sorted(
    glob.glob("docs/onboarding/*.md") + ["ONBOARDING.md"]
)  # Add main onboarding doc
FEEDBACK_FILES = sorted(glob.glob("docs/onboarding/*feedback*.md"))

LLM_PROMPT = """
You are an expert onboarding designer. Given the following onboarding documentation and user feedback, suggest improvements, clarifications, or new onboarding paths. Respond with a numbered list of actionable suggestions.\n\nONBOARDING DOCS:\n{docs}\n\nUSER FEEDBACK:\n{feedback}\n"""


def read_files(file_list):
    contents = []
    for path in file_list:
        if os.path.exists(path):
            with open(path) as f:
                contents.append(f"# {os.path.basename(path)}\n" + f.read())
    return "\n\n".join(contents)


def call_ollama(prompt):
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "")
    except Exception as e:
        logger.error(f"[ERROR] Ollama call failed: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Onboarding Path Optimizer")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview suggestions only"
    )
    args = parser.parse_args()

    docs = read_files(ONBOARDING_DOCS)
    feedback = read_files(FEEDBACK_FILES)
    logger.info(
        f"Loaded {len(ONBOARDING_DOCS)} onboarding docs and {len(FEEDBACK_FILES)} feedback files."
    )

    prompt = LLM_PROMPT.format(
        docs=docs[:4000], feedback=feedback[:2000]
    )  # Truncate for prompt size
    logger.info("Calling LLM to analyze onboarding docs and feedback...")
    suggestions = call_ollama(prompt)
    if suggestions:
        logger.info("[LLM SUGGESTIONS]\n" + suggestions)
        if not args.dry_run:
            with open(
                "docs/onboarding/onboarding_optimization_suggestions.md", "w"
            ) as f:
                f.write("# Onboarding Optimization Suggestions\n\n")
                f.write(suggestions)
            logger.info(
                "[CREATED] docs/onboarding/onboarding_optimization_suggestions.md"
            )
    else:
        logger.info("No suggestions returned by LLM.")


if __name__ == "__main__":
    main()
