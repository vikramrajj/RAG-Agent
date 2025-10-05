import pytest
import pytest_asyncio
import json
import asyncio
import httpx
from flask import Flask, current_app
from unittest.mock import patch, AsyncMock
from contextlib import contextmanager
from asgiref.wsgi import WsgiToAsgi

# Import the Flask app and components
from agent_bridge import app

# Configure Flask test client
app.config['TESTING'] = True
app.config['SERVER_NAME'] = 'localhost'

@pytest_asyncio.fixture
async def async_client():
    """Fixture for async test client using httpx"""
    asgi_app = WsgiToAsgi(app)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=asgi_app), base_url="http://test") as client:
        yield client

@pytest.fixture
def mock_reasoner():
    """Mock the reasoner component with async support"""
    with patch('agent_bridge.EnhancedReasoner') as mock:
        instance = mock.return_value
        instance.process_message = AsyncMock()
        yield mock

@pytest.fixture
def mock_web_agent():
    """Mock the WebAgent component with async support"""
    with patch('agent_bridge.WebAgent') as mock:
        instance = mock.return_value
        instance.execute = AsyncMock()
        yield mock

@pytest.fixture
def mock_outlook_login():
    """Mock the OutlookLogin component with async support"""
    with patch('agent_bridge.OutlookLogin') as mock:
        instance = mock.return_value
        instance.handle_request = AsyncMock()
        yield mock

@pytest.mark.asyncio
async def test_outlook_fallback_endpoint(async_client):
    """Test the outlook fallback endpoint that integrates with agent_orchestrator"""
    with patch('agent_bridge.run_outlook_agent', new_callable=AsyncMock) as mock_run_outlook:
        mock_run_outlook.return_value = {
            'status': 'success',
            'request_id': '123',
            'result': 'Test result'
        }
        
        response = await async_client.post("/fallback/outlook")
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = response.json()
            assert 'status' in data
            assert 'request_id' in data

@pytest.mark.asyncio
async def test_chat_endpoint_text_response(async_client):
    """Test chat endpoint with text response"""
    with patch('agent_bridge.EnhancedReasoner') as mock_reasoner:
        # Setup mock response
        mock_response = {
            'type': 'text',
            'content': 'Test response',
            'metadata': {}
        }
        mock_reasoner.return_value.process_message = AsyncMock(return_value=mock_response)

        # Test request
        response = await async_client.post(
            "/chat",
            json={"message": "test message", "context": []}
        )
        assert response.status_code == 200
        data = response.json()
        assert data['type'] == 'text'
        assert data['content'] == 'Test response'
        assert 'request_id' in data['metadata']
        assert 'timestamp' in data['metadata']

@pytest.mark.asyncio
async def test_chat_endpoint_browser_response(async_client):
    """Test chat endpoint with browser response"""
    with patch('agent_bridge.EnhancedReasoner') as mock_reasoner, \
         patch('agent_bridge.WebAgent') as mock_web_agent:
        # Setup mock responses
        mock_reasoner.return_value.process_message = AsyncMock(return_value={
            'type': 'browser',
            'metadata': {'query': 'test search', 'mode': 'search'}
        })
        mock_web_agent.return_value.execute = AsyncMock(return_value="Search results")

        # Test request
        response = await async_client.post(
            "/chat",
            json={"message": "search for test", "context": [], "browser_mode": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data['type'] == 'browser_search'
        assert data['content'] == 'Search results'
        assert 'request_id' in data['metadata']

@pytest.mark.asyncio
async def test_chat_endpoint_validation(async_client):
    """Test chat endpoint input validation"""
    # Test empty message
    response = await async_client.post(
        "/chat",
        json={"message": "", "context": []}
    )
    assert response.status_code == 400
    data = response.json()
    assert "Invalid message length" in data['error']

    # Test too long message
    response = await async_client.post(
        "/chat",
        json={"message": "x" * 3000, "context": []}
    )
    assert response.status_code == 400
    data = response.json()
    assert "Invalid message length" in data['error']

@pytest.mark.asyncio
async def test_chat_endpoint_error_handling(async_client):
    """Test chat endpoint error handling"""
    # Force re-initialization to ensure mock applies
    if 'reasoner' in app.config:
        del app.config['reasoner']
    
    with patch('agent_bridge.EnhancedReasoner') as mock_reasoner:
        # Setup mock to raise exception
        mock_reasoner.return_value.process_message = AsyncMock(side_effect=Exception("Test error"))

        # Test request
        response = await async_client.post(
            "/chat",
            json={"message": "test message", "context": []}
        )
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Test error' in data['error']['message']  # Matches the raised exception
        assert data['error']['category'] == 'internal'
        assert data['error']['severity'] == 'medium'

@pytest.mark.asyncio
async def test_search_endpoint(async_client, mock_web_agent):
    """Test search endpoint"""
    # Setup mock response
    mock_web_agent.return_value.execute = AsyncMock(return_value="Search results")

    # Test request
    response = await async_client.post(
        "/search",
        json={"query": "test search"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data['type'] == 'browser_search'
    assert data['content'] == 'Search results'

@pytest.mark.asyncio
async def test_shop_endpoint(async_client, mock_web_agent):
    """Test shop endpoint"""
    # Setup mock response
    mock_web_agent.return_value.execute = AsyncMock(return_value="Shopping results")

    # Test request
    response = await async_client.post(
        "/shop",
        json={"query": "test product"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data['type'] == 'browser_shopping'
    assert data['content'] == 'Shopping results'

@pytest.mark.asyncio
async def test_open_endpoint(async_client):
    """Test open endpoint"""
    with patch('agent_bridge.WebAgent') as mock_web_agent:
        # Setup mock response
        mock_web_agent.return_value.execute = AsyncMock(return_value="Opened URL")

        # Test valid URL
        response = await async_client.post(
            "/open",
            json={"url": "https://example.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data['type'] == 'browser_open'
        assert data['content'] == 'Opened URL'
        assert data['metadata']['url'] == 'https://example.com'

        # Test invalid URL
        response = await async_client.post(
            "/open",
            json={"url": "not-a-url"}
        )
        assert response.status_code == 400

@pytest.mark.asyncio
async def test_health_endpoints(async_client):
    """Test all health check endpoints"""
    # Basic health check
    response = await async_client.get("/health")
    assert response.status_code in [200, 503]
    data = response.json()
    assert 'status' in data
    assert 'timestamp' in data

    # Detailed health check
    response = await async_client.get("/health/detailed")
    assert response.status_code in [200, 503]
    data = response.json()
    assert 'status' in data
    assert 'checks' in data
    
    # Readiness check
    response = await async_client.get("/health/ready")
    assert response.status_code in [200, 503]
    data = response.json()
    assert 'status' in data

    # Liveness check
    response = await async_client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'alive'
    assert 'uptime' in data

@pytest.mark.asyncio
async def test_websocket_connection(async_client, mock_reasoner, mock_outlook_login):
    """Test WebSocket connection and message handling"""
    # This test is a placeholder because httpx does not directly support WebSockets.
    # A library like 'pytest-asyncio-cooperative' or 'async-asgi-testclient' would be needed.
    pass

if __name__ == '__main__':
    pytest.main([__file__])