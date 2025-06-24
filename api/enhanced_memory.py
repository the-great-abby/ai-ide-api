"""
Enhanced memory system with real-time capabilities.
Part of Phase 1: Foundation & Infrastructure implementation.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from db import get_db, Session, MemoryNode, MemoryEdge
from memory_endpoints import get_memory_nodes

logger = logging.getLogger(__name__)

class MemoryEvent:
    """Represents a memory event that can be processed in real-time."""
    
    def __init__(self, event_type: str, content: str, meta: Dict[str, Any] = None, namespace: str = "default"):
        self.event_type = event_type
        self.content = content
        self.meta = meta or {}
        self.namespace = namespace
        self.timestamp = datetime.utcnow().isoformat()
        self.id = None  # Will be set when stored
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_type": self.event_type,
            "content": self.content,
            "meta": self.meta,
            "namespace": self.namespace,
            "timestamp": self.timestamp,
            "id": self.id
        }

class MemoryStore:
    """Enhanced memory store with real-time capabilities."""
    
    def __init__(self):
        self.subscribers: List[Any] = []
        self.event_history: List[MemoryEvent] = []
        self.max_history_size = 1000
    
    async def add_node(self, event: MemoryEvent) -> Dict[str, Any]:
        """Add a memory node from an event."""
        try:
            # TODO: Implement actual database storage
            # For now, simulate storage
            event.id = f"node_{len(self.event_history) + 1}"
            self.event_history.append(event)
            
            # Trim history if needed
            if len(self.event_history) > self.max_history_size:
                self.event_history.pop(0)
            
            # Notify subscribers
            await self._notify_subscribers(event)
            
            logger.info(f"Added memory node: {event.id}")
            return {
                "id": event.id,
                "status": "created",
                "timestamp": event.timestamp
            }
            
        except Exception as e:
            logger.error(f"Error adding memory node: {e}")
            return {"error": str(e)}
    
    async def get_node(self, node_id: str) -> Optional[MemoryEvent]:
        """Get a memory node by ID."""
        try:
            for event in self.event_history:
                if event.id == node_id:
                    return event
            return None
        except Exception as e:
            logger.error(f"Error getting memory node: {e}")
            return None
    
    async def search_nodes(self, query: str, namespace: str = None, limit: int = 10) -> List[MemoryEvent]:
        """Search memory nodes by content."""
        try:
            results = []
            for event in reversed(self.event_history):  # Search most recent first
                if namespace and event.namespace != namespace:
                    continue
                
                if query.lower() in event.content.lower():
                    results.append(event)
                    if len(results) >= limit:
                        break
            
            return results
        except Exception as e:
            logger.error(f"Error searching memory nodes: {e}")
            return []
    
    def subscribe(self, subscriber: Any):
        """Subscribe to memory events."""
        if subscriber not in self.subscribers:
            self.subscribers.append(subscriber)
            logger.info(f"New memory subscriber added. Total subscribers: {len(self.subscribers)}")
    
    def unsubscribe(self, subscriber: Any):
        """Unsubscribe from memory events."""
        if subscriber in self.subscribers:
            self.subscribers.remove(subscriber)
            logger.info(f"Memory subscriber removed. Total subscribers: {len(self.subscribers)}")
    
    async def _notify_subscribers(self, event: MemoryEvent):
        """Notify all subscribers of a new memory event."""
        if not self.subscribers:
            return
        
        notification = {
            "type": "memory_event",
            "event": event.to_dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Notify subscribers asynchronously
        for subscriber in self.subscribers:
            try:
                if hasattr(subscriber, 'notify'):
                    await subscriber.notify(notification)
                elif hasattr(subscriber, 'send_json'):
                    await subscriber.send_json(notification)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")

class VectorStore:
    """Enhanced vector store for embeddings."""
    
    def __init__(self):
        self.embeddings: Dict[str, List[float]] = {}
        self.subscribers: List[Any] = []
    
    async def add_embedding(self, event: MemoryEvent) -> Dict[str, Any]:
        """Add an embedding for a memory event."""
        try:
            # TODO: Implement actual embedding generation
            # For now, create a mock embedding
            import random
            embedding = [random.random() for _ in range(384)]  # Mock 384-dimensional embedding
            
            self.embeddings[event.id] = embedding
            
            # Notify subscribers
            await self._notify_subscribers(event, embedding)
            
            logger.info(f"Added embedding for node: {event.id}")
            return {
                "node_id": event.id,
                "embedding_dimensions": len(embedding),
                "status": "created"
            }
            
        except Exception as e:
            logger.error(f"Error adding embedding: {e}")
            return {"error": str(e)}
    
    async def get_embedding(self, node_id: str) -> Optional[List[float]]:
        """Get embedding for a node."""
        return self.embeddings.get(node_id)
    
    async def find_similar(self, embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """Find similar embeddings using cosine similarity."""
        try:
            # TODO: Implement actual similarity search
            # For now, return mock results
            results = []
            for node_id, stored_embedding in self.embeddings.items():
                # Mock similarity calculation
                similarity = 0.8  # Mock value
                results.append({
                    "node_id": node_id,
                    "similarity": similarity
                })
            
            # Sort by similarity and limit results
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error finding similar embeddings: {e}")
            return []
    
    def subscribe(self, subscriber: Any):
        """Subscribe to embedding events."""
        if subscriber not in self.subscribers:
            self.subscribers.append(subscriber)
    
    def unsubscribe(self, subscriber: Any):
        """Unsubscribe from embedding events."""
        if subscriber in self.subscribers:
            self.subscribers.remove(subscriber)
    
    async def _notify_subscribers(self, event: MemoryEvent, embedding: List[float]):
        """Notify subscribers of new embedding."""
        if not self.subscribers:
            return
        
        notification = {
            "type": "embedding_created",
            "node_id": event.id,
            "embedding_dimensions": len(embedding),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for subscriber in self.subscribers:
            try:
                if hasattr(subscriber, 'notify'):
                    await subscriber.notify(notification)
                elif hasattr(subscriber, 'send_json'):
                    await subscriber.send_json(notification)
            except Exception as e:
                logger.error(f"Error notifying embedding subscriber: {e}")

class GraphStore:
    """Enhanced graph store for relationships."""
    
    def __init__(self):
        self.relationships: Dict[str, List[Dict[str, Any]]] = {}
        self.subscribers: List[Any] = []
    
    async def add_relationships(self, event: MemoryEvent) -> Dict[str, Any]:
        """Add relationships for a memory event."""
        try:
            # TODO: Implement actual relationship detection
            # For now, create mock relationships
            relationships = []
            
            # Find potential relationships with existing nodes
            for existing_event in self._get_all_events():
                if existing_event.id != event.id:
                    # Mock relationship detection
                    if self._should_create_relationship(event, existing_event):
                        relationship = {
                            "from_id": event.id,
                            "to_id": existing_event.id,
                            "relation_type": "related",
                            "strength": 0.7,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        relationships.append(relationship)
            
            # Store relationships
            if event.id not in self.relationships:
                self.relationships[event.id] = []
            self.relationships[event.id].extend(relationships)
            
            # Notify subscribers
            await self._notify_subscribers(event, relationships)
            
            logger.info(f"Added {len(relationships)} relationships for node: {event.id}")
            return {
                "node_id": event.id,
                "relationships_created": len(relationships),
                "relationships": relationships
            }
            
        except Exception as e:
            logger.error(f"Error adding relationships: {e}")
            return {"error": str(e)}
    
    def _get_all_events(self) -> List[MemoryEvent]:
        """Get all events from memory store."""
        # TODO: Get from actual memory store
        return []
    
    def _should_create_relationship(self, event1: MemoryEvent, event2: MemoryEvent) -> bool:
        """Determine if two events should have a relationship."""
        # TODO: Implement actual relationship detection logic
        # For now, return True for demonstration
        return True
    
    async def get_relationships(self, node_id: str) -> List[Dict[str, Any]]:
        """Get relationships for a node."""
        return self.relationships.get(node_id, [])
    
    async def get_graph_data(self) -> Dict[str, Any]:
        """Get complete graph data for visualization."""
        try:
            nodes = []
            edges = []
            
            # Collect all nodes
            for event in self._get_all_events():
                nodes.append({
                    "id": event.id,
                    "content": event.content[:100],  # Truncate for display
                    "namespace": event.namespace,
                    "timestamp": event.timestamp
                })
            
            # Collect all edges
            for node_id, relationships in self.relationships.items():
                for rel in relationships:
                    edges.append({
                        "from": rel["from_id"],
                        "to": rel["to_id"],
                        "type": rel["relation_type"],
                        "strength": rel["strength"]
                    })
            
            return {
                "nodes": nodes,
                "edges": edges,
                "total_nodes": len(nodes),
                "total_edges": len(edges)
            }
            
        except Exception as e:
            logger.error(f"Error getting graph data: {e}")
            return {"error": str(e)}
    
    def subscribe(self, subscriber: Any):
        """Subscribe to graph events."""
        if subscriber not in self.subscribers:
            self.subscribers.append(subscriber)
    
    def unsubscribe(self, subscriber: Any):
        """Unsubscribe from graph events."""
        if subscriber in self.subscribers:
            self.subscribers.remove(subscriber)
    
    async def _notify_subscribers(self, event: MemoryEvent, relationships: List[Dict[str, Any]]):
        """Notify subscribers of new relationships."""
        if not self.subscribers:
            return
        
        notification = {
            "type": "relationships_created",
            "node_id": event.id,
            "relationships_count": len(relationships),
            "relationships": relationships,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for subscriber in self.subscribers:
            try:
                if hasattr(subscriber, 'notify'):
                    await subscriber.notify(notification)
                elif hasattr(subscriber, 'send_json'):
                    await subscriber.send_json(notification)
            except Exception as e:
                logger.error(f"Error notifying graph subscriber: {e}")

class RealTimeProcessor:
    """Real-time processor for memory events."""
    
    def __init__(self):
        self.subscribers: List[Any] = []
        self.processing_queue: asyncio.Queue = asyncio.Queue()
        self.is_processing = False
    
    async def start_processing(self):
        """Start the real-time processing loop."""
        if self.is_processing:
            return
        
        self.is_processing = True
        logger.info("Starting real-time processing loop")
        
        while self.is_processing:
            try:
                # Process events from queue
                event = await asyncio.wait_for(self.processing_queue.get(), timeout=1.0)
                await self._process_event(event)
                self.processing_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in real-time processing: {e}")
    
    async def stop_processing(self):
        """Stop the real-time processing loop."""
        self.is_processing = False
        logger.info("Stopping real-time processing loop")
    
    async def add_event(self, event: MemoryEvent):
        """Add an event to the processing queue."""
        await self.processing_queue.put(event)
    
    async def _process_event(self, event: MemoryEvent):
        """Process a single memory event."""
        try:
            # Notify all subscribers
            await self.notify_subscribers(event)
            
            logger.info(f"Processed real-time event: {event.id}")
            
        except Exception as e:
            logger.error(f"Error processing event: {e}")
    
    def subscribe(self, subscriber: Any):
        """Subscribe to real-time events."""
        if subscriber not in self.subscribers:
            self.subscribers.append(subscriber)
            logger.info(f"New real-time subscriber added. Total subscribers: {len(self.subscribers)}")
    
    def unsubscribe(self, subscriber: Any):
        """Unsubscribe from real-time events."""
        if subscriber in self.subscribers:
            self.subscribers.remove(subscriber)
            logger.info(f"Real-time subscriber removed. Total subscribers: {len(self.subscribers)}")
    
    async def notify_subscribers(self, event: MemoryEvent):
        """Notify all subscribers of a real-time event."""
        if not self.subscribers:
            return
        
        notification = {
            "type": "real_time_event",
            "event": event.to_dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for subscriber in self.subscribers:
            try:
                if hasattr(subscriber, 'notify'):
                    await subscriber.notify(notification)
                elif hasattr(subscriber, 'send_json'):
                    await subscriber.send_json(notification)
            except Exception as e:
                logger.error(f"Error notifying real-time subscriber: {e}")

class EnhancedMemorySystem:
    """Enhanced memory system with real-time capabilities."""
    
    def __init__(self):
        self.memory_store = MemoryStore()
        self.vector_store = VectorStore()
        self.graph_store = GraphStore()
        self.real_time_processor = RealTimeProcessor()
        
        # Start real-time processing
        asyncio.create_task(self.real_time_processor.start_processing())
    
    async def process_real_time_event(self, event: MemoryEvent) -> Dict[str, Any]:
        """Process real-time events and update all stores."""
        try:
            # Add event to processing queue
            await self.real_time_processor.add_event(event)
            
            # Update memory store
            memory_result = await self.memory_store.add_node(event)
            
            # Update vector store
            vector_result = await self.vector_store.add_embedding(event)
            
            # Update graph store
            graph_result = await self.graph_store.add_relationships(event)
            
            logger.info(f"Processed real-time event: {event.id}")
            
            return {
                'memory_node': memory_result,
                'vector_embedding': vector_result,
                'graph_relationships': graph_result,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing real-time event: {e}")
            return {"error": str(e)}
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get the status of all memory system components."""
        try:
            return {
                'memory_store': {
                    'total_nodes': len(self.memory_store.event_history),
                    'subscribers': len(self.memory_store.subscribers)
                },
                'vector_store': {
                    'total_embeddings': len(self.vector_store.embeddings),
                    'subscribers': len(self.vector_store.subscribers)
                },
                'graph_store': {
                    'total_relationships': sum(len(rels) for rels in self.graph_store.relationships.values()),
                    'subscribers': len(self.graph_store.subscribers)
                },
                'real_time_processor': {
                    'is_processing': self.real_time_processor.is_processing,
                    'queue_size': self.real_time_processor.processing_queue.qsize(),
                    'subscribers': len(self.real_time_processor.subscribers)
                },
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {"error": str(e)}
    
    def subscribe_to_events(self, subscriber: Any, event_types: List[str] = None):
        """Subscribe to memory system events."""
        if not event_types or 'memory' in event_types:
            self.memory_store.subscribe(subscriber)
        if not event_types or 'vector' in event_types:
            self.vector_store.subscribe(subscriber)
        if not event_types or 'graph' in event_types:
            self.graph_store.subscribe(subscriber)
        if not event_types or 'real_time' in event_types:
            self.real_time_processor.subscribe(subscriber)
    
    def unsubscribe_from_events(self, subscriber: Any):
        """Unsubscribe from all memory system events."""
        self.memory_store.unsubscribe(subscriber)
        self.vector_store.unsubscribe(subscriber)
        self.graph_store.unsubscribe(subscriber)
        self.real_time_processor.unsubscribe(subscriber)

# Global enhanced memory system instance
enhanced_memory_system = EnhancedMemorySystem()

# Utility functions for external access
async def process_memory_event(event_type: str, content: str, meta: Dict[str, Any] = None, namespace: str = "default") -> Dict[str, Any]:
    """Process a memory event through the enhanced memory system."""
    event = MemoryEvent(event_type, content, meta, namespace)
    return await enhanced_memory_system.process_real_time_event(event)

async def get_memory_system_status() -> Dict[str, Any]:
    """Get the status of the enhanced memory system."""
    return await enhanced_memory_system.get_system_status()

def subscribe_to_memory_events(subscriber: Any, event_types: List[str] = None):
    """Subscribe to memory system events."""
    enhanced_memory_system.subscribe_to_events(subscriber, event_types)

def unsubscribe_from_memory_events(subscriber: Any):
    """Unsubscribe from memory system events."""
    enhanced_memory_system.unsubscribe_from_events(subscriber) 