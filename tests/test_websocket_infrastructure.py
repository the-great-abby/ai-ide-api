"""
Test WebSocket infrastructure for Phase 1 foundation.
"""

import pytest
import asyncio
import json
from datetime import datetime
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
from unittest.mock import AsyncMock, patch

from rule_api_server import app

def test_websocket_endpoints_exist(client):
    """Test that WebSocket endpoints are properly registered."""
    # Get all routes
    response = client.get("/routes")
    assert response.status_code == 200
    
    routes = response.json()
    websocket_routes = [route for route in routes if "/ws" in route["path"]]
    
    # Check that our WebSocket endpoints exist
    ws_paths = [route["path"] for route in websocket_routes]
    
    assert "/ws/ide" in ws_paths, "IDE WebSocket endpoint not found"
    assert "/ws/graph" in ws_paths, "Graph WebSocket endpoint not found"
    assert "/ws/predictions" in ws_paths, "Predictions WebSocket endpoint not found"

def test_websocket_ide_connection(client):
    """Test IDE WebSocket connection."""
    with client.websocket_connect("/ws/ide?token=test_token") as websocket:
        # Send a ping message
        websocket.send_json({"type": "ping"})
        
        # Receive pong response
        response = websocket.receive_json()
        assert response["type"] == "pong"
        assert "timestamp" in response

def test_websocket_graph_connection(client):
    """Test Graph WebSocket connection."""
    with client.websocket_connect("/ws/graph?token=test_token") as websocket:
        # Receive initial graph update
        response = websocket.receive_json()
        assert response["type"] == "graph_update"
        assert "updates" in response
        assert "timestamp" in response

def test_websocket_predictions_connection(client):
    """Test Predictions WebSocket connection."""
    with client.websocket_connect("/ws/predictions?token=test_token") as websocket:
        # Receive initial prediction update
        response = websocket.receive_json()
        assert response["type"] == "prediction_update"
        assert "predictions" in response
        assert "timestamp" in response

def test_websocket_code_analysis(client):
    """Test code analysis through WebSocket."""
    with client.websocket_connect("/ws/ide?token=test_token") as websocket:
        # Send code analysis request
        code_analysis_request = {
            "type": "code_analysis",
            "code": "print('Hello, World!')",
            "context": {
                "language": "python",
                "file_path": "test.py",
                "line_number": 1
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        websocket.send_json(code_analysis_request)
        
        # Receive analysis response
        response = websocket.receive_json()
        assert response["type"] == "code_analysis_response"
        assert "suggestions" in response
        assert "predictions" in response
        assert "alerts" in response
        assert "timestamp" in response

def test_websocket_invalid_token(client):
    """Test WebSocket connection with invalid token."""
    with pytest.raises(Exception):  # Should raise an exception for invalid token
        with client.websocket_connect("/ws/ide?token=invalid") as websocket:
            pass

def test_websocket_unknown_message_type(client):
    """Test WebSocket with unknown message type."""
    with client.websocket_connect("/ws/ide?token=test_token") as websocket:
        # Send unknown message type
        websocket.send_json({"type": "unknown_message_type"})
        
        # Receive error response
        response = websocket.receive_json()
        assert response["type"] == "error"
        assert "Unknown message type" in response["message"]
        assert "timestamp" in response

def test_websocket_connection_manager():
    """Test the connection manager functionality."""
    from api.websocket_endpoints import manager
    
    # Test initial state
    assert len(manager.ide_connections) == 0
    assert len(manager.graph_connections) == 0
    assert len(manager.prediction_connections) == 0

def test_memory_event_creation():
    """Test MemoryEvent creation and serialization."""
    from api.enhanced_memory import MemoryEvent
    
    event = MemoryEvent(
        event_type="test_event",
        content="Test content",
        meta={"test": "data"},
        namespace="test_namespace"
    )
    
    # Test event properties
    assert event.event_type == "test_event"
    assert event.content == "Test content"
    assert event.meta == {"test": "data"}
    assert event.namespace == "test_namespace"
    assert event.timestamp is not None
    assert event.id is None  # Should be None until stored
    
    # Test serialization
    event_dict = event.to_dict()
    assert event_dict["event_type"] == "test_event"
    assert event_dict["content"] == "Test content"
    assert event_dict["meta"] == {"test": "data"}
    assert event_dict["namespace"] == "test_namespace"
    assert "timestamp" in event_dict

def test_enhanced_data_collector():
    """Test the enhanced data collector."""
    from api.data_collection import EnhancedDataCollector
    
    collector = EnhancedDataCollector()
    
    # Test data collection
    data = asyncio.run(collector.collect_all_data())
    
    assert "ide_activity" in data
    assert "graph_changes" in data
    assert "development_metrics" in data
    assert "system_health" in data
    assert "collection_timestamp" in data
    
    # Test data summary
    summary = asyncio.run(collector.get_data_summary(hours=1))
    assert "total_collections" in summary
    assert "time_period_hours" in summary
    assert "timestamp" in summary

def test_enhanced_memory_system():
    """Test the enhanced memory system."""
    from api.enhanced_memory import EnhancedMemorySystem, MemoryEvent
    
    system = EnhancedMemorySystem()
    
    # Test event processing
    event = MemoryEvent(
        event_type="test_event",
        content="Test memory content",
        meta={"source": "test"},
        namespace="test"
    )
    
    result = asyncio.run(system.process_real_time_event(event))
    
    assert "memory_node" in result
    assert "vector_embedding" in result
    assert "graph_relationships" in result
    assert "timestamp" in result
    
    # Test system status
    status = asyncio.run(system.get_system_status())
    
    assert "memory_store" in status
    assert "vector_store" in status
    assert "graph_store" in status
    assert "real_time_processor" in status
    assert "timestamp" in status

class TestWebSocketInfrastructure:
    """Test WebSocket infrastructure and real-time communication endpoints."""

    def test_websocket_router_registration(self, client):
        """Test that WebSocket endpoints are properly registered."""
        # WebSocket routes don't appear in /routes endpoint, so we test connectivity directly
        # Test IDE WebSocket connection
        try:
            with client.websocket_connect("/ws/ide?token=test_token") as websocket:
                assert websocket is not None
                # Send a ping to test basic functionality
                websocket.send_json({"type": "ping"})
                response = websocket.receive_json()
                assert response["type"] == "pong"
        except Exception as e:
            pytest.fail(f"IDE WebSocket connection failed: {e}")

        # Test Graph WebSocket connection
        try:
            with client.websocket_connect("/ws/graph?token=test_token") as websocket:
                assert websocket is not None
                # Send a basic request
                websocket.send_json({"type": "get_graph", "scope": "test"})
                response = websocket.receive_json()
                assert "type" in response
        except Exception as e:
            pytest.fail(f"Graph WebSocket connection failed: {e}")

        # Test Predictions WebSocket connection
        try:
            with client.websocket_connect("/ws/predictions?token=test_token") as websocket:
                assert websocket is not None
                # Send a basic request
                websocket.send_json({"type": "get_predictions", "context": "test"})
                response = websocket.receive_json()
                assert "type" in response
        except Exception as e:
            pytest.fail(f"Predictions WebSocket connection failed: {e}")

    def test_ide_websocket_connection(self, client):
        """Test IDE WebSocket connection and basic communication."""
        with client.websocket_connect("/ws/ide?token=test_token") as websocket:
            # Test connection establishment
            assert websocket is not None
            
            # Test sending a message
            test_message = {
                "type": "file_change",
                "file_path": "test.py",
                "content": "print('hello world')"
            }
            websocket.send_text(json.dumps(test_message))
            
            # Test receiving a response
            response = websocket.receive_text()
            response_data = json.loads(response)
            
            assert response_data["type"] == "file_change_processed"
            assert "file_path" in response_data
            assert "analysis" in response_data

    def test_graph_websocket_connection(self, client):
        """Test knowledge graph WebSocket connection."""
        with client.websocket_connect("/ws/graph?token=test_token") as websocket:
            # Test connection establishment
            assert websocket is not None
            
            # Test requesting graph data
            request = {
                "type": "get_graph",
                "scope": "project",
                "project_id": "test-project"
            }
            websocket.send_text(json.dumps(request))
            
            # Test receiving graph data
            response = websocket.receive_text()
            response_data = json.loads(response)
            
            assert response_data["type"] == "graph_data"
            assert "nodes" in response_data
            assert "edges" in response_data

    def test_predictions_websocket_connection(self, client):
        """Test predictions WebSocket connection."""
        with client.websocket_connect("/ws/predictions?token=test_token") as websocket:
            # Test connection establishment
            assert websocket is not None
            
            # Test requesting predictions
            request = {
                "type": "get_predictions",
                "context": "user is working on authentication system"
            }
            websocket.send_text(json.dumps(request))
            
            # Test receiving predictions
            response = websocket.receive_text()
            response_data = json.loads(response)
            
            assert response_data["type"] == "predictions"
            assert "suggestions" in response_data
            assert "confidence" in response_data

    def test_data_collection_endpoints(self, client):
        """Test data collection endpoints for real-time IDE integration."""
        # Test file change endpoint
        file_change_data = {
            "file_path": "src/main.py",
            "content": "def hello(): print('world')",
            "timestamp": "2024-01-01T12:00:00Z"
        }
        response = client.post("/api/v1/ide/file-change", json=file_change_data)
        assert response.status_code == 200
        assert response.json()["status"] == "processed"

        # Test cursor position endpoint
        cursor_data = {
            "file_path": "src/main.py",
            "line": 10,
            "column": 5,
            "timestamp": "2024-01-01T12:00:00Z"
        }
        response = client.post("/api/v1/ide/cursor-position", json=cursor_data)
        assert response.status_code == 200
        assert response.json()["status"] == "tracked"

        # Test command execution endpoint
        command_data = {
            "command": "git commit -m 'feat: add authentication'",
            "timestamp": "2024-01-01T12:00:00Z",
            "success": True
        }
        response = client.post("/api/v1/ide/command-execution", json=command_data)
        assert response.status_code == 200
        assert response.json()["status"] == "logged"

    def test_memory_system_endpoints(self, client):
        """Test enhanced memory system endpoints."""
        # Test memory creation with real-time context
        memory_data = {
            "content": "User implemented OAuth2 authentication",
            "context": {
                "file_path": "src/auth.py",
                "cursor_position": {"line": 25, "column": 10},
                "recent_commands": ["git add .", "git commit -m 'feat: auth'"]
            },
            "tags": ["authentication", "oauth2"],
            "confidence": 0.85
        }
        response = client.post("/api/v1/memory/create", json=memory_data)
        assert response.status_code == 200
        assert "memory_id" in response.json()

        # Test memory retrieval with context
        retrieval_data = {
            "query": "authentication implementation",
            "context": {
                "current_file": "src/auth.py",
                "recent_activity": ["oauth2", "jwt"]
            }
        }
        response = client.post("/api/v1/memory/retrieve", json=retrieval_data)
        assert response.status_code == 200
        assert "memories" in response.json()

        # Test memory similarity with real-time updates
        similarity_data = {
            "memory_id": "test-memory-id",
            "threshold": 0.7
        }
        response = client.post("/api/v1/memory/similarity", json=similarity_data)
        assert response.status_code == 200
        assert "similar_memories" in response.json()

    def test_websocket_error_handling(self, client):
        """Test WebSocket error handling and graceful degradation."""
        # Test invalid JSON handling
        with client.websocket_connect("/ws/ide?token=test_token") as websocket:
            # Send invalid JSON
            websocket.send_text("invalid json")
            
            # Should receive error response
            response = websocket.receive_text()
            response_data = json.loads(response)
            assert response_data["type"] == "error"
            assert "Invalid JSON" in response_data["message"]

        # Test unsupported message type
        with client.websocket_connect("/ws/ide?token=test_token") as websocket:
            # Send unsupported message type
            message = {"type": "unsupported_type", "data": "test"}
            websocket.send_text(json.dumps(message))
            
            # Should receive error response
            response = websocket.receive_text()
            response_data = json.loads(response)
            assert response_data["type"] == "error"
            assert "Unsupported message type" in response_data["message"]

    def test_websocket_connection_limits(self, client):
        """Test WebSocket connection limits and resource management."""
        # Test multiple connections (should be allowed)
        connections = []
        try:
            for i in range(3):
                websocket = client.websocket_connect("/ws/ide?token=test_token")
                connections.append(websocket)
                assert websocket is not None
        finally:
            # Clean up connections
            for conn in connections:
                conn.close()

    def test_real_time_data_flow(self, client):
        """Test end-to-end real-time data flow from IDE to memory system."""
        # 1. Send file change through data collection
        file_change = {
            "file_path": "src/auth.py",
            "content": "def authenticate_user(token): return verify_token(token)",
            "timestamp": "2024-01-01T12:00:00Z"
        }
        response = client.post("/api/v1/ide/file-change", json=file_change)
        assert response.status_code == 200

        # 2. Create memory with the context
        memory_data = {
            "content": "User implemented token-based authentication",
            "context": {
                "file_path": "src/auth.py",
                "recent_changes": [file_change]
            },
            "tags": ["authentication", "tokens"],
            "confidence": 0.9
        }
        response = client.post("/api/v1/memory/create", json=memory_data)
        assert response.status_code == 200
        memory_id = response.json()["memory_id"]

        # 3. Retrieve memory through WebSocket
        with client.websocket_connect("/ws/graph?token=test_token") as websocket:
            request = {
                "type": "get_graph",
                "scope": "file",
                "file_path": "src/auth.py"
            }
            websocket.send_text(json.dumps(request))
            
            response = websocket.receive_text()
            response_data = json.loads(response)
            
            assert response_data["type"] == "graph_data"
            # Should include the memory we just created
            assert any(node.get("id") == memory_id for node in response_data["nodes"])

if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"]) 