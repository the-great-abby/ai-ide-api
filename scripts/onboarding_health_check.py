import os
import sys
import re
yaml_pattern = re.compile(r'^---\s*([\s\S]+?)---', re.MULTILINE)

REQUIRED_FILES = [
    'ONBOARDING.md',
    'ONBOARDING_OTHER_AI_IDE.md',
    'INTEGRATING_AI_IDE.md',
]
REQUIRED_ENV_VARS = [
    'ENVIRONMENT', 'POSTGRES_HOST', 'POSTGRES_PORT', 'REDIS_HOST', 'REDIS_PORT'
]
REQUIRED_MAKE_TARGETS = [
    'ai-test', 'ai-test-one', 'ai-test-json', 'ai-accept-enhancement', 'ai-complete-enhancement',
    'ai-list-enhancements', 'ai-proposal-to-enhancement', 'ai-db-autorevision', 'ai-db-migrate',
    'ai-bug-report', 'ai-suggest-enhancement', 'ai-onboarding-health'
]

ok = True

def check_file_exists(path):
    global ok
    if os.path.exists(path):
        print(f"[OK] {path} found")
    else:
        print(f"[ERROR] {path} not found")
        ok = False

def check_rules_dir():
    global ok
    if not os.path.isdir('.cursor/rules'):
        print("[ERROR] .cursor/rules/ directory not found")
        ok = False
        return
    print("[OK] .cursor/rules/ directory exists")
    for fname in os.listdir('.cursor/rules'):
        path = os.path.join('.cursor/rules', fname)
        if fname.endswith('.txt'):
            print(f"[ERROR] .txt file found: {fname} (should be .mdc)")
            ok = False
        if fname.endswith('.mdc'):
            with open(path) as f:
                content = f.read()
            m = yaml_pattern.search(content)
            if not m:
                print(f"[ERROR] {fname} missing YAML frontmatter")
                ok = False
                continue
            yaml_block = m.group(1)
            if 'description:' not in yaml_block or 'globs:' not in yaml_block:
                print(f"[ERROR] {fname} missing required frontmatter fields (description, globs)")
                ok = False
            else:
                print(f"[OK] {fname} has valid frontmatter")

def check_env():
    global ok
    if not os.path.exists('.env'):
        print("[ERROR] .env file not found")
        ok = False
        return
    print("[OK] .env file found")
    with open('.env') as f:
        env = f.read()
    for var in REQUIRED_ENV_VARS:
        if f'{var}=' not in env:
            print(f"[ERROR] .env missing required variable: {var}")
            ok = False
        else:
            print(f"[OK] .env has {var}")

def check_makefile():
    global ok
    if not os.path.exists('Makefile.ai'):
        print("[ERROR] Makefile.ai not found")
        ok = False
        return
    print("[OK] Makefile.ai found")
    with open('Makefile.ai') as f:
        make = f.read()
    for target in REQUIRED_MAKE_TARGETS:
        if f'{target}:' not in make:
            print(f"[ERROR] Makefile.ai missing target: {target}")
            ok = False
        else:
            print(f"[OK] Makefile.ai has target: {target}")

def check_whats_new():
    global ok
    path = 'ONBOARDING.md'
    if not os.path.exists(path):
        return
    with open(path) as f:
        content = f.read()
    m = re.search(r"## 🚨 What's New.*?\n(- .+\n)+", content, re.DOTALL)
    if m and len(m.group(0).strip().splitlines()) > 2:
        print("[OK] 'What's New' section present in ONBOARDING.md")
    else:
        print("[ERROR] 'What's New' section missing or empty in ONBOARDING.md")
        ok = False

def main():
    for f in REQUIRED_FILES:
        check_file_exists(f)
    check_rules_dir()
    check_env()
    check_makefile()
    check_whats_new()
    if ok:
        print("[PASS] Onboarding health check passed!")
        sys.exit(0)
    else:
        print("[FAIL] Onboarding health check failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 