# test_smart_routing.py
"""Quick test to demonstrate smart routing functionality"""

from smart_router import SmartRouter

# Create router
router = SmartRouter()

# Test queries
test_queries = [
    "My Outlook email is not syncing properly",
    "I want to buy a laptop under $1000",
    "What is the capital of France?",
    "Find cheap flights to Paris",
    "Can't send emails from Outlook",
    "Compare prices for iPhone 15"
]

print("=" * 60)
print("SMART ROUTING TEST")
print("=" * 60)
print()

for query in test_queries:
    decision = router.route_query(query)
    destination = decision['destination']
    confidence = decision['confidence']
    
    icons = {
        'mistral': '🤖',
        'rag_outlook': '📧',
        'browser_use': '🌐'
    }
    
    icon = icons.get(destination, '❓')
    
    print(f"Query: {query}")
    print(f"  → {icon} {destination.upper()} (confidence: {confidence:.0%})")
    print()

print("=" * 60)
print("ROUTING STATISTICS")
print("=" * 60)

stats = router.get_statistics()
print(f"Total routes: {stats['total_routes']}")
print(f"By destination:")
for dest, count in stats['by_destination'].items():
    print(f"  - {dest}: {count}")
print(f"Average confidence: {stats['average_confidence']:.0%}")
