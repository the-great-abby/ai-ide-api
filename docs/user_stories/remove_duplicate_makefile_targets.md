# User Story: Removing Duplicate Makefile Targets

## Motivation
As a maintainer, I want to easily remove duplicate targets from the main Makefile.ai when targets are moved to modular sub-makefiles, so that the build system remains clean, maintainable, and avoids confusion.

## Actors
- Project maintainers
- Developers refactoring Makefile targets

## Preconditions
- Modular sub-makefiles (e.g., Makefile.ai-misc) exist and contain the canonical versions of certain targets
- The list of targets to remove is maintained in `makefile_targets_to_remove.txt`
- The AWK script `scripts/remove_makefile_targets.awk` exists
- The Makefile target `ai-remove-duplicate-makefile-targets` is available in `Makefile.ai-misc`

## Step-by-Step Actions
1. **Update the Target List**
   - Edit `makefile_targets_to_remove.txt` and add/remove target names (one per line) that should be removed from `Makefile.ai`.
2. **Run the Cleanup**
   - Execute:
     ```sh
     make -f Makefile.ai-misc ai-remove-duplicate-makefile-targets
     ```
   - This will:
     - Use the AWK script to remove all recipes and `.PHONY` lines for the listed targets from `Makefile.ai`.
     - Overwrite `Makefile.ai` with the cleaned version.
3. **Review the Result**
   - Inspect `Makefile.ai` to ensure only the intended targets were removed.
   - Commit the changes to version control.

## Expected Outcomes
- All duplicate targets listed in `makefile_targets_to_remove.txt` are removed from `Makefile.ai`.
- The main Makefile.ai only contains targets not managed by sub-makefiles.
- The process is repeatable and easy for future maintainers.

## Best Practices
- Always review the list in `makefile_targets_to_remove.txt` before running the script.
- Commit your changes before and after running the cleanup for easy rollback.
- Keep the AWK script and this user story up to date if the process changes.
- Reference this user story in onboarding and code review documentation when refactoring Makefile targets. 