import json
import os

CONFIG_PATH = os.path.join('config', 'theme.json')
THEMES_DIR = 'themes'


def load_theme():
    with open(CONFIG_PATH) as f:
        theme = json.load(f)['current_theme']
    theme_file = os.path.join(THEMES_DIR, f'{theme}.json')
    with open(theme_file) as f:
        messages = json.load(f)
    return messages


def get_message(key):
    messages = load_theme()
    return messages.get(key, f"[Missing message for '{key}']")

# Example usage:
if __name__ == "__main__":
    print(get_message('welcome'))
    print(get_message('onboarding_intro'))
    print(get_message('error'))
    print(get_message('achievement_first_test'))
    print(get_message('mission_brief')) 