"""
MCP Server Configuration

This module contains the configuration for the MCP server implementation.
Currently serves as a scaffold for future Claude integration while maintaining
compatibility with existing Ollama-based vector store.
"""

from typing import Dict, Any, Optional
import os


class MCPServerConfig:
    """Configuration for MCP server and vector stores"""

    def __init__(self):
        self.name = "ai-ide-api"
        self.version = "1.0.0"
        self.description = (
            "AI IDE API with integrated RAG, memory, and code analysis capabilities"
        )

        # Vector store configuration
        self.vector_stores = {
            "ollama": {
                "active": True,
                "dimension": int(os.getenv("OLLAMA_VECTOR_DIM", "1536")),
                "table": "memory_vectors_ollama",
                "model": os.getenv("OLLAMA_MODEL", "ollama/current"),
            },
            "claude": {
                "active": False,  # Will be enabled during migration
                "dimension": 1536,  # Claude's standard dimension
                "table": "memory_vectors_claude",
                "model": "claude/embedding-model",  # Will be updated with actual model
            },
        }

        # MCP-specific settings
        self.mcp_settings = {
            "max_batch_size": 100,
            "timeout_seconds": 30,
            "retry_attempts": 3,
        }

    def get_active_store(self) -> Dict[str, Any]:
        """Get the currently active vector store configuration"""
        return next(
            (config for name, config in self.vector_stores.items() if config["active"]),
            self.vector_stores["ollama"],  # Default to ollama if none active
        )

    def switch_vector_store(self, provider: str) -> None:
        """Switch the active vector store provider"""
        if provider not in self.vector_stores:
            raise ValueError(f"Unknown vector store provider: {provider}")

        # Deactivate all stores
        for store in self.vector_stores.values():
            store["active"] = False

        # Activate requested store
        self.vector_stores[provider]["active"] = True

    @property
    def is_mcp_enabled(self) -> bool:
        """Check if MCP mode is enabled"""
        return os.getenv("ENABLE_MCP", "false").lower() == "true"
