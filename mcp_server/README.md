# MCP Server Integration for AI-IDE-API

## Overview
This directory contains the Model Context Protocol (MCP) server implementation for the AI-IDE-API. Currently, it serves as a scaffold for future MCP integration while maintaining compatibility with our existing vector store and memory system.

## Current Status
- Scaffold implementation with dual vector store support
- Preparation for Claude integration
- Maintains backward compatibility with Ollama

## Future Upgrade Path
1. **Vector Store Migration**
   - Current: Using Ollama embeddings
   - Future: Will support Claude embeddings
   - Both stores can run in parallel during transition

2. **MCP Tools**
   - Memory operations (create/read/update/delete)
   - Code analysis tools
   - Vector search capabilities

3. **Integration Timeline**
   - Phase 1: Scaffold and dual store support (Current)
   - Phase 2: Claude embedding integration
   - Phase 3: Full MCP tool implementation
   - Phase 4: Production deployment

## Directory Structure
```
mcp_server/
├── tools/           # MCP tool definitions
├── utils/           # Shared utilities
├── config.py        # MCP server configuration
├── server.py        # Main MCP server implementation
└── vector_store.py  # Vector store abstraction layer
```

## Vector Store Strategy
The implementation supports multiple vector stores to facilitate a smooth transition:
- Ollama store (current)
- Claude store (future)
- Ability to run both simultaneously during migration

## Usage
Currently in scaffold phase. Do not use in production until full MCP integration is complete.

## References
- [MCP Documentation](https://docs.anthropic.com/claude/docs/model-context-protocol)
- [Vector Store Migration Guide](https://docs.anthropic.com/claude/docs/vector-store-integration) 