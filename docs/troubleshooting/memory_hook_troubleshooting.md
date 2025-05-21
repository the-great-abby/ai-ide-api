# Memory Scanning Git Hook Troubleshooting Guide

This guide helps you resolve common issues with the memory scanning git hook.

## Common Issues and Solutions

### Hook Not Running

If the memory scanning hook is not running during commits:

1. Check if the hook is installed:
   ```bash
   ls -l .git/hooks/pre-commit
   ```

2. If the hook doesn't exist or isn't executable, run:
   ```bash
   make setup-memory-hook
   ```

3. Verify the hook content:
   ```bash
   cat .git/hooks/pre-commit
   ```
   The file should contain the docker-compose exec command for running the memory scanning script.

### Docker Container Issues

If you see errors related to Docker:

1. Verify the containers are running:
   ```bash
   docker compose ps
   ```
   Ensure `misc-scripts`, `api`, and `ollama-functions` containers are up.

2. Check container logs:
   ```bash
   docker compose logs misc-scripts
   ```

3. Ensure you're in the correct directory when running git commands.

### Permission Issues

If you encounter permission errors:

1. Make the hook executable:
   ```bash
   chmod +x .git/hooks/pre-commit
   ```

2. Check Docker permissions:
   ```bash
   docker compose exec misc-scripts ls -l /code/scripts/scan_for_memory_node_opportunities.py
   ```

### Hook Conflicts

If you have multiple pre-commit hooks:

1. Check existing hooks:
   ```bash
   ls -l .git/hooks/pre-commit*
   ```

2. If you have multiple hooks, you may need to combine them into a single pre-commit file.

## Getting Help

If you're still experiencing issues:

1. Check the git commit output for specific error messages
2. Review the Docker container logs
3. Open an issue in the project repository with:
   - The error message
   - Your git version
   - Docker version
   - The contents of your pre-commit hook
   - Docker container status 