"""
Minimal test server to demonstrate smart routing
"""
from flask import Flask, request, jsonify
from smart_router import SmartRouter, RouteDestination

app = Flask(__name__)
router = SmartRouter()

@app.route('/chat', methods=['POST'])
def chat():
    """Simple chat endpoint with smart routing"""
    data = request.get_json()
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'error': 'No message provided'}), 400
    
    # Route the query
    routing_decision = router.route_query(message)
    destination = routing_decision['destination']
    confidence = routing_decision['confidence']
    
    # Simulate responses based on destination
    responses = {
        'mistral': f"🤖 [Mistral AI] I'll help with: {message}",
        'rag_outlook': f"📧 [RAG + Reasoner] I'll check Outlook documentation for: {message}",
        'browser_use': f"🌐 [Browser Automation] I'll search the web for: {message}"
    }
    
    response_text = responses.get(destination, f"Processing: {message}")
    explanation = router.get_routing_explanation(routing_decision)
    
    return jsonify({
        'content': response_text,
        'route': destination,
        'confidence': confidence,
        'explanation': explanation,
        'metadata': routing_decision['metadata']
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    stats = router.get_statistics()
    return jsonify({
        'status': 'healthy',
        'routing_stats': stats
    })

@app.route('/')
def index():
    """Root endpoint"""
    return """
    <html>
    <head><title>Smart Routing Test Server</title></head>
    <body>
        <h1>Smart Routing Test Server</h1>
        <p>Server is running! Try these endpoints:</p>
        <ul>
            <li><code>POST /chat</code> - Send messages with smart routing</li>
            <li><code>GET /health</code> - Check routing statistics</li>
        </ul>
        
        <h2>Test with curl:</h2>
        <pre>
# Test Outlook query
curl -X POST http://localhost:5000/chat -H "Content-Type: application/json" -d "{\\"message\\": \\"My Outlook is not syncing\\"}"

# Test shopping query
curl -X POST http://localhost:5000/chat -H "Content-Type: application/json" -d "{\\"message\\": \\"Find cheap laptops\\"}"

# Test general query
curl -X POST http://localhost:5000/chat -H "Content-Type: application/json" -d "{\\"message\\": \\"What is 2+2?\\"}"
        </pre>
    </body>
    </html>
    """

if __name__ == '__main__':
    print("=" * 60)
    print("SMART ROUTING TEST SERVER")
    print("=" * 60)
    print("\nServer starting on http://localhost:5000")
    print("\nFeatures:")
    print("  🤖 Mistral AI - General queries")
    print("  📧 RAG + Reasoner - Outlook/email queries")
    print("  🌐 Browser Automation - Shopping/search queries")
    print("\n" + "=" * 60)
    app.run(debug=True, port=5000, use_reloader=False)
