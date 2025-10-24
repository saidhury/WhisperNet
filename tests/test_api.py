"""
Unit tests for WhisperNet FastAPI backend.

These tests verify API endpoints in isolation using mocks to prevent
actual network calls or C++ library interactions.
"""
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, Mock
import sys
import os

# Add backend directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Mock the C++ bindings BEFORE importing anything that uses them
# This prevents the test from trying to load the actual .so/.dll/.dylib file
mock_core_lib = MagicMock()
mock_core_lib.send_udp_message = MagicMock()
mock_core_lib.start_udp_listener = MagicMock()

sys.modules['bindings'] = MagicMock(
    core_lib=mock_core_lib,
    ON_MESSAGE_RECEIVED_FUNC=MagicMock()
)

# Now we can safely import the app
from main import app

client = TestClient(app)


def test_get_peers_returns_ok_and_list():
    """
    Test that GET /api/peers returns a 200 status code
    and a list data structure.
    """
    response = client.get("/api/peers")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_send_message_calls_core_lib():
    """
    Test that POST /api/send correctly calls the C++ library
    with the appropriate parameters.
    """
    # Reset the mock call count
    mock_core_lib.send_udp_message.reset_mock()
    
    payload = {"recipient_ip": "192.168.1.100", "content": "test message"}
    
    response = client.post("/api/send", json=payload)

    assert response.status_code == 200
    assert response.json() == {"status": "message sent"}

    # Verify the C++ library function was called exactly once
    mock_core_lib.send_udp_message.assert_called_once()
    
    # Verify it was called with the correct arguments
    call_args = mock_core_lib.send_udp_message.call_args[0]
    # First arg should be the message as bytes
    assert b'"type": "MESSAGE"' in call_args[0]
    assert b'"content": "test message"' in call_args[0]
    # Second arg should be recipient IP as bytes
    assert call_args[1] == b'192.168.1.100'
    # Third arg should be the UDP port
    assert call_args[2] == 8888


def test_send_message_with_missing_recipient():
    """
    Test that POST /api/send returns an error when recipient_ip is missing.
    """
    # Reset the mock call count
    mock_core_lib.send_udp_message.reset_mock()
    
    payload = {"content": "test message"}
    
    response = client.post("/api/send", json=payload)

    assert response.status_code == 200
    assert response.json()["status"] == "error"
    assert "recipient_ip" in response.json()["detail"]
    
    # Should not call C++ library if validation fails
    mock_core_lib.send_udp_message.assert_not_called()


def test_send_message_with_missing_content():
    """
    Test that POST /api/send returns an error when content is missing.
    """
    # Reset the mock call count
    mock_core_lib.send_udp_message.reset_mock()
    
    payload = {"recipient_ip": "192.168.1.100"}
    
    response = client.post("/api/send", json=payload)

    assert response.status_code == 200
    assert response.json()["status"] == "error"
    assert "content" in response.json()["detail"]
    
    # Should not call C++ library if validation fails
    mock_core_lib.send_udp_message.assert_not_called()


def test_health_check_endpoint():
    """
    Test that GET /api/health returns the expected response.
    """
    response = client.get("/api/health")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["content-type"].startswith("application/json")
