"""
Vector Store Abstraction Layer

This module provides a clean abstraction for different vector store implementations,
allowing seamless switching between Ollama and Claude embeddings while maintaining
backward compatibility during migration.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import numpy as np

class VectorStore(ABC):
    """Abstract base class for vector store implementations"""
    
    @abstractmethod
    async def store_vector(
        self, 
        vector: np.ndarray, 
        metadata: Dict[str, Any],
        node_id: Optional[str] = None
    ) -> str:
        """Store a vector with associated metadata"""
        pass
    
    @abstractmethod
    async def search_vectors(
        self, 
        query_vector: np.ndarray,
        top_k: int = 5,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors"""
        pass
    
    @abstractmethod
    async def delete_vector(self, vector_id: str) -> bool:
        """Delete a vector by ID"""
        pass

class OllamaVectorStore(VectorStore):
    """Ollama-based vector store implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.dimension = config["dimension"]
        self.table = config["table"]
        self.model = config["model"]
    
    async def store_vector(
        self, 
        vector: np.ndarray, 
        metadata: Dict[str, Any],
        node_id: Optional[str] = None
    ) -> str:
        # Implementation remains unchanged for now
        # Will be updated during MCP integration
        pass
    
    async def search_vectors(
        self, 
        query_vector: np.ndarray,
        top_k: int = 5,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        # Implementation remains unchanged for now
        # Will be updated during MCP integration
        pass
    
    async def delete_vector(self, vector_id: str) -> bool:
        # Implementation remains unchanged for now
        # Will be updated during MCP integration
        pass

class ClaudeVectorStore(VectorStore):
    """Claude-based vector store implementation (Future)"""
    
    def __init__(self, config: Dict[str, Any]):
        self.dimension = config["dimension"]
        self.table = config["table"]
        self.model = config["model"]
    
    async def store_vector(
        self, 
        vector: np.ndarray, 
        metadata: Dict[str, Any],
        node_id: Optional[str] = None
    ) -> str:
        """
        Store a vector using Claude's embedding model
        
        Note: This is a placeholder implementation that will be completed
        during the MCP integration phase.
        """
        raise NotImplementedError(
            "Claude vector store implementation pending MCP integration"
        )
    
    async def search_vectors(
        self, 
        query_vector: np.ndarray,
        top_k: int = 5,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search vectors using Claude's embedding model
        
        Note: This is a placeholder implementation that will be completed
        during the MCP integration phase.
        """
        raise NotImplementedError(
            "Claude vector store implementation pending MCP integration"
        )
    
    async def delete_vector(self, vector_id: str) -> bool:
        """
        Delete a vector using Claude's API
        
        Note: This is a placeholder implementation that will be completed
        during the MCP integration phase.
        """
        raise NotImplementedError(
            "Claude vector store implementation pending MCP integration"
        )

def create_vector_store(config: Dict[str, Any]) -> VectorStore:
    """Factory function to create the appropriate vector store"""
    provider = next(
        (name for name, cfg in config.items() if cfg["active"]),
        "ollama"
    )
    
    if provider == "claude":
        return ClaudeVectorStore(config[provider])
    return OllamaVectorStore(config[provider]) 