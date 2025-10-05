"""
Complete Smart Routing Demo
Shows all features working together
"""
import sys
from smart_router import SmartRouter

def print_banner(text):
    """Print a nice banner"""
    width = 70
    print("\n" + "=" * width)
    print(text.center(width))
    print("=" * width + "\n")

def print_section(text):
    """Print a section header"""
    print(f"\n{'─' * 70}")
    print(f"  {text}")
    print('─' * 70)

def print_route_result(query, decision):
    """Print routing result in a nice format"""
    destination = decision['destination']
    confidence = decision['confidence']
    
    icons = {
        'mistral': '🤖',
        'rag_outlook': '📧',
        'browser_use': '🌐'
    }
    
    colors = {
        'mistral': '\033[94m',      # Blue
        'rag_outlook': '\033[92m',  # Green
        'browser_use': '\033[96m'   # Cyan
    }
    
    reset = '\033[0m'
    bold = '\033[1m'
    
    icon = icons.get(destination, '❓')
    color = colors.get(destination, '')
    
    print(f"\n  Query: {bold}{query}{reset}")
    print(f"  Route: {color}{icon} {destination.upper()}{reset}")
    print(f"  Confidence: {confidence:.0%}")
    
    # Simulate what each system would do
    actions = {
        'mistral': "Processing with Mistral AI for general conversation...",
        'rag_outlook': "Searching Outlook documentation with RAG + Reasoner...",
        'browser_use': "Launching browser automation with Gemini Flash 2.0..."
    }
    
    print(f"  Action: {actions.get(destination, 'Processing...')}")

def demo_basic_routing():
    """Demo 1: Basic routing functionality"""
    print_section("DEMO 1: Basic Smart Routing")
    
    router = SmartRouter()
    
    test_queries = [
        "My Outlook email is not syncing properly",
        "Find cheap laptops under $500",
        "What is the capital of France?",
        "My calendar meetings aren't showing up in Outlook",
        "Search for best iPhone 15 deals",
        "Explain quantum computing"
    ]
    
    for query in test_queries:
        decision = router.route_query(query)
        print_route_result(query, decision)

def demo_intent_detection():
    """Demo 2: Intent detection with scores"""
    print_section("DEMO 2: Intent Detection Analysis")
    
    router = SmartRouter()
    
    test_cases = [
        ("Outlook not syncing emails", "Should detect Outlook keywords"),
        ("Buy cheap iPhone", "Should detect shopping intent"),
        ("What is 2+2?", "Should route to general AI"),
        ("Can't send calendar invites from Office 365", "Multiple Outlook keywords"),
        ("Compare prices for MacBook Pro", "Shopping with comparison intent")
    ]
    
    for query, explanation in test_cases:
        print(f"\n  Test: {explanation}")
        print(f"  Query: \"{query}\"")
        
        destination, confidence = router.detect_intent(query)
        print(f"  → Detected: {destination.value} ({confidence:.0%} confidence)")

def demo_routing_statistics():
    """Demo 3: Routing statistics"""
    print_section("DEMO 3: Routing Statistics")
    
    router = SmartRouter()
    
    # Run a bunch of queries
    queries = [
        "Outlook sync issue",
        "Buy laptop",
        "What is AI?",
        "Email not working",
        "Find cheap flights",
        "Calendar problem",
        "Shop for phones",
        "Explain Python",
        "Meeting not showing in Outlook",
        "Search for best deals"
    ]
    
    print("  Processing 10 diverse queries...")
    for query in queries:
        router.route_query(query)
    
    stats = router.get_statistics()
    
    print(f"\n  Total routes: {stats['total_routes']}")
    print(f"  Average confidence: {stats['average_confidence']:.0%}")
    print(f"\n  Distribution by destination:")
    
    for dest, count in stats['by_destination'].items():
        percentage = (count / stats['total_routes']) * 100
        bar = '█' * int(percentage / 5)  # Scale to fit
        print(f"    {dest:15} │ {bar} {count} ({percentage:.0f}%)")

def demo_user_preferences():
    """Demo 4: User preference overrides"""
    print_section("DEMO 4: User Preference Overrides")
    
    router = SmartRouter()
    query = "What is the weather?"
    
    # Normal routing
    print("\n  Normal routing:")
    decision = router.route_query(query)
    print(f"  Query: \"{query}\"")
    print(f"  → Route: {decision['destination']}")
    
    # Force RAG
    print("\n  With user preference (force RAG):")
    preferences = {'force_destination': 'rag_outlook'}
    decision = router.route_query(query, user_preferences=preferences)
    print(f"  Query: \"{query}\"")
    print(f"  → Route: {decision['destination']} (forced)")
    
    # Force browser
    print("\n  With user preference (force browser):")
    preferences = {'force_destination': 'browser_use'}
    decision = router.route_query(query, user_preferences=preferences)
    print(f"  Query: \"{query}\"")
    print(f"  → Route: {decision['destination']} (forced)")

def demo_api_integration():
    """Demo 5: How it integrates with API"""
    print_section("DEMO 5: API Integration Example")
    
    print("""
  In the actual Flask API (agent_bridge.py), routing works like this:

  1. User sends message to /chat endpoint
  2. Smart router analyzes the message
  3. Based on intent, the message is routed to:
  
     📧 RAG_OUTLOOK:
        → Retrieves relevant Outlook docs
        → Feeds to Reasoner with context
        → Returns documentation-based answer
     
     🌐 BROWSER_USE:
        → Initializes browser automation
        → Uses Gemini Flash 2.0 for web tasks
        → Returns search/shopping results
     
     🤖 MISTRAL (default):
        → Sends to Ollama Mistral model
        → Returns conversational response
  
  4. Response includes metadata:
     - route: Which system handled it
     - confidence: How confident the routing was
     - sources: If RAG was used, what docs were retrieved
    """)

def main():
    """Run all demos"""
    print_banner("🚀 SMART ROUTING SYSTEM - COMPLETE DEMO 🚀")
    
    print("""
  This demo shows the intelligent routing system that:
  
  ✓ Automatically detects user intent
  ✓ Routes Outlook queries to RAG + documentation
  ✓ Routes shopping/search to browser automation
  ✓ Routes general questions to Mistral AI
  ✓ Tracks statistics and confidence scores
  ✓ Supports user preference overrides
    """)
    
    try:
        demo_basic_routing()
        demo_intent_detection()
        demo_routing_statistics()
        demo_user_preferences()
        demo_api_integration()
        
        print_banner("✅ DEMO COMPLETE - ALL FEATURES WORKING ✅")
        
        print("""
  Next Steps:
  
  1. Set GEMINI_API_KEY for browser automation:
     $env:GEMINI_API_KEY = "your-api-key"
  
  2. Install browser-use dependencies:
     pip install browser-use langchain-google-genai playwright
     playwright install chromium
  
  3. Apply UI changes to sat_ui_improved.html:
     See: SAT_UI_MODEL_SELECTOR_PATCH.md
  
  4. Start full server:
     python agent_bridge.py
  
  5. Test with UI at http://localhost:8000
        """)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
