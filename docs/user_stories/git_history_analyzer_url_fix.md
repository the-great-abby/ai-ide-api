# Git History Analyzer URL Configuration Fix

## Overview
The git history analyzer was experiencing connection issues because it was using the generic `OLLAMA_URL` environment variable, which conflicted with other services. This fix introduces a dedicated `GIT_DIFF_SUMMARY_URL` environment variable to ensure proper connectivity to the Ollama functions service.

## Problem
- Git history analyzer was trying to connect to `http://host.docker.internal:11434/api/generate` instead of the correct Ollama functions service
- This caused 404 errors and prevented LLM analysis from working
- The generic `OLLAMA_URL` was being used by multiple services with different requirements

## Solution
- Added dedicated `GIT_DIFF_SUMMARY_URL` environment variable specifically for git diff summarization
- Updated the git history analyzer to use the new environment variable
- Configured the correct endpoint: `http://ollama-functions:8000/summarize-git-diff`
- Maintained backward compatibility by keeping the original `OLLAMA_URL` for other services

## Implementation

### Code Changes
1. **scripts/git_history_analyzer.py**:
   - Added `GIT_DIFF_SUMMARY_URL` environment variable
   - Updated `summarize_diff()` function to use the new URL
   - Kept original `OLLAMA_URL` for backward compatibility

2. **docker-compose.yml**:
   - Added `GIT_DIFF_SUMMARY_URL=http://ollama-functions:8000/summarize-git-diff` to misc-scripts service

3. **docker-compose.test.yml**:
   - Added `GIT_DIFF_SUMMARY_URL=http://test-ollama-functions:8000/summarize-git-diff` to test-misc-scripts service

## Usage

### Running Git History Analysis
```bash
# The git history analyzer now works automatically without custom URL overrides
docker compose exec misc-scripts bash -c 'cd /code && python3 scripts/git_history_analyzer.py --since "1 week ago" --max-commits 5 --output-format story'
```

### Environment Variables
- `GIT_DIFF_SUMMARY_URL`: Points to the Ollama functions service for git diff summarization
- `OLLAMA_URL`: Remains available for other services that need direct Ollama access

## Benefits
- **Reliability**: Git history analyzer now connects to the correct service consistently
- **Isolation**: Dedicated URL prevents conflicts with other services
- **Maintainability**: Clear separation of concerns for different LLM endpoints
- **LLM Analysis**: Full AI-powered commit analysis now works as intended

## Testing
The fix has been tested and verified:
- Git history analyzer successfully connects to Ollama functions service
- LLM analysis generates detailed summaries of commits
- No more 404 connection errors
- Works in both development and test environments

## Related Files
- `scripts/git_history_analyzer.py` - Main analyzer script
- `docker-compose.yml` - Development environment configuration
- `docker-compose.test.yml` - Test environment configuration
- `scripts/llm_rule_suggester_service.py` - Ollama functions service endpoint 