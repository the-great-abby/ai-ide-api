#!/usr/bin/env python3
import sys
import os

if len(sys.argv) < 2:
    print("Usage: python search_user_stories.py <keyword>")
    sys.exit(1)

keyword = sys.argv[1].lower()
stories_dir = os.path.join(os.path.dirname(__file__), '../docs/user_stories')

for fname in os.listdir(stories_dir):
    if not fname.endswith('.md'):
        continue
    path = os.path.join(stories_dir, fname)
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    found = False
    # Search filename
    if keyword in fname.lower():
        print(f"[FILENAME MATCH] {fname}")
        found = True
    # Search content
    for line in lines:
        if keyword in line.lower():
            print(f"[CONTENT MATCH] {fname}: {line.strip()}")
            found = True
            break
    if found:
        print('-' * 60) 