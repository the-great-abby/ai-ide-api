#!/usr/bin/env python3
import os
import re
from collections import defaultdict

def extract_targets(makefile_path):
    """Extract target names from a makefile."""
    targets = set()
    if not os.path.exists(makefile_path):
        return targets
    
    with open(makefile_path) as f:
        content = f.read()
    
    # Find all target definitions (lines ending with :)
    target_pattern = r'^([a-zA-Z0-9_-]+):'
    for line in content.split('\n'):
        match = re.match(target_pattern, line.strip())
        if match:
            targets.add(match.group(1))
    
    return targets

def main():
    # Use /code directory where the files are mounted
    base_dir = '/code'
    
    # Get all Makefile.ai* files
    makefiles = [f for f in os.listdir(base_dir) if f.startswith('Makefile.ai')]
    print(f"Found makefiles: {makefiles}")  # Debug output
    
    # Extract targets from each makefile
    all_targets = defaultdict(list)
    for makefile in makefiles:
        makefile_path = os.path.join(base_dir, makefile)
        targets = extract_targets(makefile_path)
        print(f"\nTargets in {makefile}:")  # Debug output
        for target in sorted(targets):
            print(f"  {target}")
        for target in targets:
            all_targets[target].append(makefile)
    
    # Find duplicates (targets that appear in multiple makefiles)
    duplicates = {target: files for target, files in all_targets.items() if len(files) > 1}
    
    if duplicates:
        print("\n=== Duplicate Makefile Targets ===")
        print("The following targets appear in multiple makefiles:")
        for target, files in sorted(duplicates.items()):
            print(f"\n{target}:")
            for file in files:
                print(f"  - {file}")
        
        print("\nSuggested targets to remove from Makefile.ai:")
        for target, files in sorted(duplicates.items()):
            if 'Makefile.ai' in files and len(files) > 1:
                print(f"  {target}")
    else:
        print("\nNo duplicate targets found!")

if __name__ == "__main__":
    main() 