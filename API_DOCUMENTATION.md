# RAG Agent API Documentation

## Overview

The RAG Agent provides a comprehensive REST API for intelligent troubleshooting assistance, web automation, and Office application integration. This document describes all available endpoints, request/response formats, and usage examples.

## Base URL

```
http://localhost:5000
```

## Authentication

Currently, the API uses session-based authentication. All requests should include appropriate headers and follow security best practices.

## Common Headers

```http
Content-Type: application/json
X-Requested-With: XMLHttpRequest
```

## Rate Limiting

- **General endpoints**: 100 requests per hour, 20 per minute
- **Search endpoints**: 10 requests per minute
- **Health endpoints**: 30 requests per minute

## Response Format

All API responses follow a consistent structure:

```json
{
  "type": "response_type",
  "content": "Response content",
  "metadata": {
    "request_id": "uuid",
    "timestamp": "2024-01-01T00:00:00Z",
    "additional_info": {}
  }
}
```

## Endpoints

### 1. Chat Interface

#### POST /chat

Main chat endpoint for troubleshooting assistance.

**Request:**
```json
{
  "message": "Outlook won't open",
  "context": [
    {
      "role": "user",
      "content": "Previous message"
    }
  ],
  "browser_mode": false
}
```

**Response:**
```json
{
  "type": "troubleshooting",
  "content": "Here are the steps to resolve Outlook startup issues...",
  "metadata": {
    "request_id": "abc123",
    "timestamp": "2024-01-01T00:00:00Z",
    "confidence": 0.95,
    "sources": [
      {
        "title": "Outlook Startup Troubleshooting",
        "relevance_score": 0.92
      }
    ]
  }
}
```

**Error Response:**
```json
{
  "error": "Invalid message length",
  "type": "validation_error",
  "metadata": {
    "request_id": "abc123",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### 2. Web Search

#### POST /search

Perform web searches for troubleshooting information.

**Request:**
```json
{
  "query": "Outlook error 0x80042108"
}
```

**Response:**
```json
{
  "type": "browser_search",
  "content": {
    "status": "ok",
    "final_result": {
      "title": "Search Results",
      "summary": "Found 5 relevant articles about Outlook error 0x80042108"
    },
    "steps": [
      {
        "id": "step-1",
        "title": "Search Step",
        "status": "ok",
        "details": "Searched Microsoft support database"
      }
    ]
  }
}
```

### 3. Shopping/Product Search

#### POST /shop

Search for products and shopping information.

**Request:**
```json
{
  "query": "Microsoft Office 365"
}
```

**Response:**
```json
{
  "type": "browser_shopping",
  "content": {
    "status": "ok",
    "final_result": {
      "title": "Product Search Results",
      "summary": "Found 3 Microsoft Office 365 options with pricing"
    }
  }
}
```

### 4. Website Navigation

#### POST /open

Open specific websites or URLs.

**Request:**
```json
{
  "url": "https://outlook.office365.com"
}
```

**Response:**
```json
{
  "type": "browser_open",
  "content": {
    "status": "ok",
    "final_result": {
      "title": "Website Opened",
      "summary": "Successfully opened Outlook Web App"
    }
  },
  "metadata": {
    "url": "https://outlook.office365.com"
  }
}
```

### 5. Diagnostics

#### POST /diagnostics

Run system diagnostics for Office applications.

**Request:**
```json
{}
```

**Response:**
```json
{
  "status": "success",
  "message": "Diagnostics completed successfully"
}
```

## Health Monitoring Endpoints

### 1. Basic Health Check

#### GET /health

Quick health status check.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "checks_passed": 4,
  "checks_failed": 0,
  "total_checks": 4
}
```

### 2. Detailed Health Check

#### GET /health/detailed

Comprehensive health check with individual component status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "summary": {
    "checks_passed": 4,
    "checks_failed": 0,
    "total_checks": 4,
    "execution_time": 2.5
  },
  "checks": [
    {
      "name": "system_resources",
      "status": "healthy",
      "message": "System resources are healthy",
      "duration_ms": 1500,
      "timestamp": "2024-01-01T00:00:00Z",
      "details": {
        "cpu_percent": 45.2,
        "memory_percent": 67.8,
        "disk_percent": 23.1
      }
    }
  ]
}
```

### 3. Readiness Check

#### GET /health/ready

Kubernetes-style readiness check.

**Response:**
```json
{
  "status": "ready",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 4. Liveness Check

#### GET /health/live

Kubernetes-style liveness check.

**Response:**
```json
{
  "status": "alive",
  "timestamp": "2024-01-01T00:00:00Z",
  "uptime": 3600.5
}
```

## Static File Serving

### GET /

Serve the main web interface.

### GET /static/\<filename>

Serve static files (CSS, JS, images).

## Error Handling

### Standard Error Responses

All endpoints return consistent error responses:

```json
{
  "error": {
    "id": "error_id",
    "category": "validation|authentication|authorization|not_found|network|database|external_service|internal|timeout|rate_limit|configuration|unknown",
    "severity": "low|medium|high|critical",
    "message": "Human-readable error message",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### HTTP Status Codes

- `200` - Success
- `400` - Bad Request (validation errors)
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `408` - Request Timeout
- `413` - Payload Too Large
- `429` - Too Many Requests
- `500` - Internal Server Error
- `502` - Bad Gateway
- `503` - Service Unavailable

### Common Error Scenarios

#### Validation Errors (400)
```json
{
  "error": {
    "id": "val_001",
    "category": "validation",
    "severity": "low",
    "message": "Invalid message length",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

#### Rate Limiting (429)
```json
{
  "error": {
    "id": "rate_001",
    "category": "rate_limit",
    "severity": "medium",
    "message": "Rate limit exceeded. Please try again later.",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

#### Internal Server Error (500)
```json
{
  "error": {
    "id": "int_001",
    "category": "internal",
    "severity": "high",
    "message": "Internal server error",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

## Request Validation

### Input Sanitization

All text inputs are sanitized to prevent XSS attacks:
- HTML tags are stripped or escaped
- Script content is removed
- URLs are validated

### Size Limits

- **Message content**: 10KB maximum
- **Search queries**: 5KB maximum
- **URLs**: 1KB maximum
- **Diagnostic requests**: 1KB maximum

### Required Fields

Different endpoints have different required fields:

- `/chat`: `message` (required)
- `/search`: `query` (required)
- `/shop`: `query` (required)
- `/open`: `url` or `query` (required)
- `/diagnostics`: No required fields

## Usage Examples

### JavaScript/Node.js

```javascript
const axios = require('axios');

const apiClient = axios.create({
  baseURL: 'http://localhost:5000',
  timeout: 30000
});

// Chat example
async function chatWithAgent(message) {
  try {
    const response = await apiClient.post('/chat', {
      message: message,
      context: [],
      browser_mode: false
    });
    
    return response.data;
  } catch (error) {
    console.error('Chat error:', error.response?.data || error.message);
    throw error;
  }
}

// Search example
async function searchTroubleshooting(query) {
  try {
    const response = await apiClient.post('/search', {
      query: query
    });
    
    return response.data;
  } catch (error) {
    console.error('Search error:', error.response?.data || error.message);
    throw error;
  }
}
```

### Python

```python
import requests
import json

class RAGAgentClient:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def chat(self, message, context=None, browser_mode=False):
        """Send a chat message to the agent."""
        url = f"{self.base_url}/chat"
        data = {
            "message": message,
            "context": context or [],
            "browser_mode": browser_mode
        }
        
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def search(self, query):
        """Perform a web search."""
        url = f"{self.base_url}/search"
        data = {"query": query}
        
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def open_website(self, url):
        """Open a website."""
        url = f"{self.base_url}/open"
        data = {"url": url}
        
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def run_diagnostics(self):
        """Run system diagnostics."""
        url = f"{self.base_url}/diagnostics"
        
        response = self.session.post(url, json={})
        response.raise_for_status()
        return response.json()
    
    def health_check(self):
        """Check system health."""
        url = f"{self.base_url}/health"
        
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

# Usage example
client = RAGAgentClient()

# Chat with the agent
response = client.chat("Outlook won't open")
print(f"Response: {response['content']}")

# Search for troubleshooting info
search_response = client.search("Outlook error 0x80042108")
print(f"Search results: {search_response['content']}")

# Check system health
health = client.health_check()
print(f"System status: {health['status']}")
```

### cURL Examples

```bash
# Chat endpoint
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Outlook won't open",
    "context": [],
    "browser_mode": false
  }'

# Search endpoint
curl -X POST http://localhost:5000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Outlook error 0x80042108"
  }'

# Health check
curl -X GET http://localhost:5000/health

# Detailed health check
curl -X GET http://localhost:5000/health/detailed
```

## WebSocket Support (Future)

Planned WebSocket endpoints for real-time communication:

- `/ws/chat` - Real-time chat
- `/ws/status` - Live status updates
- `/ws/logs` - Live log streaming

## API Versioning

Current version: v1

Future versions will be available at:
- `/v2/chat`
- `/v2/search`
- etc.

## Rate Limiting Details

Rate limits are applied per IP address and include:

- **Chat requests**: 20 per minute
- **Search requests**: 10 per minute
- **Health checks**: 30 per minute
- **Total requests**: 100 per hour

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 20
X-RateLimit-Remaining: 19
X-RateLimit-Reset: 1640995200
```

## Security Considerations

1. **Input Validation**: All inputs are validated and sanitized
2. **CSRF Protection**: CSRF tokens are required for state-changing operations
3. **Rate Limiting**: Prevents abuse and DoS attacks
4. **Secure Headers**: Security headers are applied to all responses
5. **Credential Security**: Sensitive credentials are handled securely

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure the server is running
   - Check the port number
   - Verify firewall settings

2. **Rate Limit Exceeded**
   - Wait for the rate limit window to reset
   - Implement exponential backoff in your client

3. **Validation Errors**
   - Check request format and required fields
   - Verify input data types and lengths

4. **Timeout Errors**
   - Increase client timeout settings
   - Check server performance and load

### Debug Mode

Enable debug mode for detailed error information:

```bash
export FLASK_DEBUG=true
python agent_bridge.py
```

This will provide stack traces and additional debugging information in error responses.
