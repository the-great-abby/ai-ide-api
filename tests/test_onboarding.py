import os

def test_onboarding_md_exists():
    assert os.path.exists('ONBOARDING.md')

def test_onboarding_md_has_quick_start():
    with open('ONBOARDING.md') as f:
        content = f.read()
    assert 'Quick Start' in content or 'quick start' in content 