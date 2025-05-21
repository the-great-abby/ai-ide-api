import os
import yaml

def find_files_by_pattern(root, patterns):
    matches = []
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            for pattern in patterns:
                if filename.endswith(pattern):
                    matches.append(os.path.relpath(os.path.join(dirpath, filename), root))
    return matches

def main():
    root = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(root, '..'))
    project_map = {
        'models': {
            'sqlalchemy': 'db.py' if os.path.exists(os.path.join(repo_root, 'db.py')) else None,
            'pydantic': 'rule_api_server.py' if os.path.exists(os.path.join(repo_root, 'rule_api_server.py')) else None,
            'mocks': 'tests/mocks/mock_db_models.py' if os.path.exists(os.path.join(repo_root, 'tests/mocks/mock_db_models.py')) else None,
        },
        'tests': {
            'unit': 'tests/unit/' if os.path.exists(os.path.join(repo_root, 'tests/unit')) else None,
            'integration': 'tests/integration/' if os.path.exists(os.path.join(repo_root, 'tests/integration')) else None,
        },
        'fixtures': 'tests/conftest.py' if os.path.exists(os.path.join(repo_root, 'tests/conftest.py')) else None,
        'mocks': 'tests/mocks/' if os.path.exists(os.path.join(repo_root, 'tests/mocks')) else None,
        'scripts': 'scripts/' if os.path.exists(os.path.join(repo_root, 'scripts')) else None,
    }
    with open(os.path.join(repo_root, 'project_map.yaml'), 'w') as f:
        yaml.dump(project_map, f, default_flow_style=False)
    print("project_map.yaml updated.")

if __name__ == '__main__':
    main() 