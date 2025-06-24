# AI-IDE-API External Project Setup

## Quick Start

1. **Test your connection:**
   ```bash
   make -f Makefile.external test-connection
   ```

2. **Check LLM access:**
   ```bash
   make -f Makefile.external check-llm-access
   ```

3. **Request LLM access if needed:**
   ```bash
   make -f Makefile.external request-llm-access
   ```

4. **Start using the API:**
   ```bash
   make -f Makefile.external help
   ```

## Configuration

- API Base: http://localhost:9103
- Project: ai-ide-api_internal
- Token: Stored in `.apitoken` file

## Available Commands

- `test-connection` - Test API connection and authentication
- `check-llm-access` - Check if project has LLM access enabled  
- `request-llm-access` - Show instructions for requesting LLM access
- `health` - Check API health status
- `help` - Show all available commands

## Support

For additional operations, use the API directly or contact the administrator.
