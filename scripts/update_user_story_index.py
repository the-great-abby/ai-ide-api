#!/usr/bin/env python3
import os
import re

USER_STORIES_DIR = os.path.join(os.path.dirname(__file__), '../docs/user_stories')
INDEX_FILE = os.path.join(USER_STORIES_DIR, 'INDEX.md')

# List of onboarding user stories to prioritize
ONBOARDING_FILES = [
    'external_project_onboarding.md',
    'internal_dev_onboarding.md',
    'ai_agent_onboarding.md',
]

def extract_title_and_desc(path):
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    title = None
    desc = None
    for i, line in enumerate(lines):
        if line.startswith('# '):
            title = line.strip('# ').strip()
            # Try to find the first non-empty line after the title
            for l in lines[i+1:]:
                if l.strip() and not l.startswith('#'):
                    desc = l.strip()
                    break
            break
    return title or os.path.basename(path), desc or ''

def main():
    files = [f for f in os.listdir(USER_STORIES_DIR) if f.endswith('.md') and f != 'INDEX.md']
    # Onboarding stories first
    onboarding = [f for f in ONBOARDING_FILES if f in files]
    rest = [f for f in files if f not in onboarding]
    rows = []
    for fname in onboarding + rest:
        path = os.path.join(USER_STORIES_DIR, fname)
        title, desc = extract_title_and_desc(path)
        rows.append(f'| {title} | {desc} | [{fname}]({fname}) |')
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        f.write('# User Story Index\n\n')
        f.write('A central index of all user stories for workflows, onboarding, automation, and best practices in this project.\n\n')
        f.write('| User Story | Description | Link |\n')
        f.write('|------------|-------------|------|\n')
        for row in rows:
            f.write(row + '\n')
        f.write('\n**Tip:** Reference this index when onboarding, reviewing code, or adding new workflows.\n')

if __name__ == '__main__':
    main() 