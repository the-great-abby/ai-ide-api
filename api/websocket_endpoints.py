"""
WebSocket endpoints for real-time communication.
Part of Phase 1: Foundation & Infrastructure implementation.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel

from auth import require_api_token, ApiAccessToken
from db import get_db, Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])

# Connection management
class ConnectionManager:
    """Manages WebSocket connections for different types of clients."""
    
    def __init__(self):
        self.ide_connections: List[WebSocket] = []
        self.graph_connections: List[WebSocket] = []
        self.prediction_connections: List[WebSocket] = []
    
    async def connect_ide(self, websocket: WebSocket):
        """Connect an IDE client."""
        await websocket.accept()
        self.ide_connections.append(websocket)
        logger.info(f"IDE client connected. Total IDE connections: {len(self.ide_connections)}")
    
    async def connect_graph(self, websocket: WebSocket):
        """Connect a graph visualization client."""
        await websocket.accept()
        self.graph_connections.append(websocket)
        logger.info(f"Graph client connected. Total graph connections: {len(self.graph_connections)}")
    
    async def connect_prediction(self, websocket: WebSocket):
        """Connect a prediction client."""
        await websocket.accept()
        self.prediction_connections.append(websocket)
        logger.info(f"Prediction client connected. Total prediction connections: {len(self.prediction_connections)}")
    
    def disconnect_ide(self, websocket: WebSocket):
        """Disconnect an IDE client."""
        if websocket in self.ide_connections:
            self.ide_connections.remove(websocket)
            logger.info(f"IDE client disconnected. Total IDE connections: {len(self.ide_connections)}")
    
    def disconnect_graph(self, websocket: WebSocket):
        """Disconnect a graph client."""
        if websocket in self.graph_connections:
            self.graph_connections.remove(websocket)
            logger.info(f"Graph client disconnected. Total graph connections: {len(self.graph_connections)}")
    
    def disconnect_prediction(self, websocket: WebSocket):
        """Disconnect a prediction client."""
        if websocket in self.prediction_connections:
            self.prediction_connections.remove(websocket)
            logger.info(f"Prediction client disconnected. Total prediction connections: {len(self.prediction_connections)}")
    
    async def broadcast_to_ide(self, message: Dict[str, Any]):
        """Broadcast message to all IDE clients."""
        if not self.ide_connections:
            return
        
        disconnected = []
        for connection in self.ide_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to IDE client: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect_ide(connection)
    
    async def broadcast_to_graph(self, message: Dict[str, Any]):
        """Broadcast message to all graph clients."""
        if not self.graph_connections:
            return
        
        disconnected = []
        for connection in self.graph_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to graph client: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect_graph(connection)
    
    async def broadcast_to_prediction(self, message: Dict[str, Any]):
        """Broadcast message to all prediction clients."""
        if not self.prediction_connections:
            return
        
        disconnected = []
        for connection in self.prediction_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to prediction client: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect_prediction(connection)

# Global connection manager
manager = ConnectionManager()

# Pydantic models for WebSocket messages
class CodeAnalysisRequest:
    """Request model for code analysis."""
    def __init__(self, type: str = "code_analysis", code: str = "", context: Dict[str, Any] = None, timestamp: Optional[str] = None):
        self.type = type
        self.code = code
        self.context = context or {}
        self.timestamp = timestamp

class CodeAnalysisResponse:
    """Response model for code analysis."""
    def __init__(self, suggestions: List[Dict[str, Any]] = None, predictions: List[Dict[str, Any]] = None, alerts: List[Dict[str, Any]] = None, timestamp: str = None):
        self.type = "code_analysis_response"
        self.suggestions = suggestions or []
        self.predictions = predictions or []
        self.alerts = alerts or []
        self.timestamp = timestamp or datetime.utcnow().isoformat()
    
    def dict(self):
        return {
            "type": self.type,
            "suggestions": self.suggestions,
            "predictions": self.predictions,
            "alerts": self.alerts,
            "timestamp": self.timestamp
        }

class GraphUpdateRequest:
    """Request model for graph updates."""
    def __init__(self, type: str = "graph_update_request", filters: Optional[Dict[str, Any]] = None, timestamp: Optional[str] = None):
        self.type = type
        self.filters = filters or {}
        self.timestamp = timestamp

class GraphUpdateResponse:
    """Response model for graph updates."""
    def __init__(self, nodes: List[Dict[str, Any]] = None, edges: List[Dict[str, Any]] = None, timestamp: str = None):
        self.type = "graph_update"
        self.nodes = nodes or []
        self.edges = edges or []
        self.timestamp = timestamp or datetime.utcnow().isoformat()

class PredictionRequest:
    """Request model for predictions."""
    def __init__(self, type: str = "prediction_request", data: Dict[str, Any] = None, timestamp: Optional[str] = None):
        self.type = type
        self.data = data or {}
        self.timestamp = timestamp

class PredictionResponse:
    """Response model for predictions."""
    def __init__(self, predictions: List[Dict[str, Any]] = None, insights: List[Dict[str, Any]] = None, recommendations: List[Dict[str, Any]] = None, timestamp: str = None):
        self.type = "prediction_response"
        self.predictions = predictions or []
        self.insights = insights or []
        self.recommendations = recommendations or []
        self.timestamp = timestamp or datetime.utcnow().isoformat()

# WebSocket endpoints
@router.websocket("/ide")
async def ide_websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    """Real-time IDE integration endpoint."""
    try:
        # Validate token (simplified for now - will be enhanced)
        if not token or token == "invalid":
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        await manager.connect_ide(websocket)
        
        try:
            while True:
                # Receive message from IDE
                data = await websocket.receive_json()
                
                # Process the message
                if data.get("type") == "code_analysis":
                    response = await process_code_analysis(data)
                    await websocket.send_json(response.dict())
                elif data.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {data.get('type')}",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
        except WebSocketDisconnect:
            logger.info("IDE client disconnected")
        except Exception as e:
            logger.error(f"Error in IDE WebSocket: {e}")
            await websocket.send_json({
                "type": "error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
    finally:
        manager.disconnect_ide(websocket)

@router.websocket("/ws/graph")
async def websocket_graph(websocket: WebSocket, token: str = Query(None)):
    """WebSocket endpoint for real-time knowledge graph updates."""
    await manager.connect_graph(websocket)
    try:
        # Send initial graph data
        initial_data = await get_memory_graph_data()
        await websocket.send_json({
            "type": "graph_update",
            "updates": initial_data,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                await handle_graph_message(websocket, message)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON",
                    "timestamp": datetime.utcnow().isoformat()
                })
    except WebSocketDisconnect:
        manager.disconnect_graph(websocket)

@router.websocket("/predictions")
async def predictions_websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    """Real-time prediction updates."""
    try:
        # Validate token (simplified for now - will be enhanced)
        if not token or token == "invalid":
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        await manager.connect_prediction(websocket)
        
        try:
            while True:
                # Send prediction updates in real-time
                predictions = await get_prediction_updates()
                await websocket.send_json({
                    "type": "prediction_update",
                    "predictions": predictions,
                    "timestamp": datetime.utcnow().isoformat()
                })
                await asyncio.sleep(10)  # Update every 10 seconds
                
        except WebSocketDisconnect:
            logger.info("Prediction client disconnected")
        except Exception as e:
            logger.error(f"Error in Prediction WebSocket: {e}")
            await websocket.send_json({
                "type": "error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
    finally:
        manager.disconnect_prediction(websocket)

# Processing functions
async def process_code_analysis(data: Dict[str, Any]) -> CodeAnalysisResponse:
    """Process code analysis request and return suggestions."""
    try:
        from ide_analysis import analyze_code_for_ide
        
        # Extract code and context from the request
        code = data.get("code", "")
        context = data.get("context", {})
        
        # Perform real-time analysis
        analysis_result = await analyze_code_for_ide(code, context)
        
        return CodeAnalysisResponse(
            suggestions=analysis_result["suggestions"],
            predictions=analysis_result["predictions"],
            alerts=analysis_result["alerts"],
            timestamp=analysis_result["timestamp"]
        )
        
    except ImportError:
        # Fallback to mock data if analysis engine is not available
        logger.warning("IDE analysis engine not available, using mock data")
        suggestions = [
            {
                "type": "rule_violation",
                "message": "Consider using logger instead of print statements",
                "severity": "warning",
                "line": 1,
                "column": 1,
                "fix": "Replace print() with logger.debug()"
            }
        ]
        
        predictions = [
            {
                "type": "bug_prediction",
                "message": "Potential null pointer exception",
                "confidence": 0.85,
                "line": 5,
                "column": 10
            }
        ]
        
        alerts = [
            {
                "type": "security",
                "message": "Hardcoded credentials detected",
                "severity": "high",
                "line": 10,
                "column": 5
            }
        ]
        
        return CodeAnalysisResponse(
            suggestions=suggestions,
            predictions=predictions,
            alerts=alerts,
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        logger.error(f"Error in code analysis: {e}")
        return CodeAnalysisResponse(
            suggestions=[{
                "type": "analysis_error",
                "message": f"Analysis failed: {str(e)}",
                "severity": "error"
            }],
            predictions=[],
            alerts=[],
            timestamp=datetime.utcnow().isoformat()
        )

async def get_memory_graph_data():
    """Get current memory graph data for WebSocket updates."""
    try:
        from db import MemorySessionLocal, MemoryVector, MemoryEdge
        
        session = MemorySessionLocal()
        
        # Get nodes (memory vectors)
        nodes = session.query(MemoryVector).all()
        node_data = []
        for node in nodes:
            node_data.append({
                "id": str(node.id),
                "label": node.content[:50] + "..." if len(node.content) > 50 else node.content,
                "type": node.namespace,
                "meta": node.meta,
                "created_at": node.created_at.isoformat() if node.created_at else None,
                "categories": node.categories or [],
                "tags": node.tags or []
            })
        
        # Get edges (memory edges)
        edges = session.query(MemoryEdge).all()
        edge_data = []
        for edge in edges:
            edge_data.append({
                "id": str(edge.id),
                "source_id": str(edge.from_id),
                "target_id": str(edge.to_id),
                "label": edge.relation_type,
                "meta": edge.meta,
                "created_at": edge.created_at.isoformat() if edge.created_at else None
            })
        
        session.close()
        
        return {
            "nodes": node_data,
            "edges": edge_data
        }
    except Exception as e:
        logger.error(f"Error getting memory graph data: {e}")
        return {"nodes": [], "edges": []}

async def handle_graph_message(websocket: WebSocket, message: dict):
    """Handle incoming graph messages from WebSocket."""
    message_type = message.get("type")
    
    if message_type == "get_graph":
        # Return full graph data
        graph_data = await get_memory_graph_data()
        await websocket.send_json({
            "type": "graph_data",
            "nodes": graph_data["nodes"],
            "edges": graph_data["edges"],
            "timestamp": datetime.utcnow().isoformat()
        })
    
    elif message_type == "get_node":
        # Get specific node data
        node_id = message.get("node_id")
        if node_id:
            node_data = await get_memory_node_data(node_id)
            await websocket.send_json({
                "type": "node_data",
                "node": node_data,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    elif message_type == "get_connected":
        # Get connected nodes
        node_id = message.get("node_id")
        if node_id:
            connected_data = await get_connected_memory_nodes(node_id)
            await websocket.send_json({
                "type": "connected_nodes",
                "nodes": connected_data,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    else:
        await websocket.send_json({
            "type": "error",
            "message": f"Unsupported message type: {message_type}",
            "timestamp": datetime.utcnow().isoformat()
        })

async def get_memory_node_data(node_id: str):
    """Get specific memory node data."""
    try:
        from db import MemorySessionLocal, MemoryVector
        
        session = MemorySessionLocal()
        node = session.query(MemoryVector).filter(MemoryVector.id == node_id).first()
        session.close()
        
        if node:
            return {
                "id": str(node.id),
                "label": node.content,
                "type": node.namespace,
                "meta": node.meta,
                "created_at": node.created_at.isoformat() if node.created_at else None,
                "categories": node.categories or [],
                "tags": node.tags or []
            }
        return None
    except Exception as e:
        logger.error(f"Error getting memory node data: {e}")
        return None

async def get_connected_memory_nodes(node_id: str):
    """Get nodes connected to the specified node."""
    try:
        from db import MemorySessionLocal, MemoryEdge, MemoryVector
        
        session = MemorySessionLocal()
        
        # Find edges where this node is involved
        edges = session.query(MemoryEdge).filter(
            (MemoryEdge.from_id == node_id) | (MemoryEdge.to_id == node_id)
        ).all()
        
        # Get connected node IDs
        connected_ids = set()
        for edge in edges:
            if str(edge.from_id) != node_id:
                connected_ids.add(str(edge.from_id))
            if str(edge.to_id) != node_id:
                connected_ids.add(str(edge.to_id))
        
        # Get the actual nodes
        nodes = []
        if connected_ids:
            memory_nodes = session.query(MemoryVector).filter(
                MemoryVector.id.in_(connected_ids)
            ).all()
            
            for node in memory_nodes:
                nodes.append({
                    "id": str(node.id),
                    "label": node.content[:50] + "..." if len(node.content) > 50 else node.content,
                    "type": node.namespace,
                    "meta": node.meta,
                    "created_at": node.created_at.isoformat() if node.created_at else None,
                    "categories": node.categories or [],
                    "tags": node.tags or []
                })
        
        session.close()
        return nodes
    except Exception as e:
        logger.error(f"Error getting connected memory nodes: {e}")
        return []

async def get_prediction_updates() -> Dict[str, Any]:
    """Get prediction updates for real-time broadcasting."""
    # TODO: Implement actual prediction update logic
    # For now, return mock data
    return {
        "new_predictions": 0,
        "updated_predictions": 0,
        "alerts": 0,
        "model_accuracy": 0.92
    }

# Utility functions for broadcasting
async def broadcast_code_analysis_update(analysis_result: Dict[str, Any]):
    """Broadcast code analysis results to all IDE clients."""
    await manager.broadcast_to_ide({
        "type": "code_analysis_update",
        "result": analysis_result,
        "timestamp": datetime.utcnow().isoformat()
    })

async def broadcast_graph_update(graph_data: Dict[str, Any]):
    """Broadcast graph updates to all graph clients."""
    await manager.broadcast_to_graph({
        "type": "graph_update",
        "data": graph_data,
        "timestamp": datetime.utcnow().isoformat()
    })

async def broadcast_prediction_update(prediction_data: Dict[str, Any]):
    """Broadcast prediction updates to all prediction clients."""
    await manager.broadcast_to_prediction({
        "type": "prediction_update",
        "data": prediction_data,
        "timestamp": datetime.utcnow().isoformat()
    }) 