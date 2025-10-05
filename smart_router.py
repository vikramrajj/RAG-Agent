# smart_router.py
"""
Smart Routing System for RAG Agent
Routes queries to appropriate AI models/systems:
- Mistral: Primary AI agent for general queries
- RAG Loader + Reasoner: Outlook/email related queries
- Browser-use: Shopping/search/web automation tasks
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class RouteDestination(Enum):
    """Defines possible routing destinations"""
    MISTRAL = "mistral"  # General purpose AI
    RAG_OUTLOOK = "rag_outlook"  # Outlook/email queries with RAG
    BROWSER_USE = "browser_use"  # Web automation and shopping
    HYBRID = "hybrid"  # Combination of multiple systems


class SmartRouter:
    """
    Routes user queries to the appropriate AI system based on intent detection
    """
    
    # Outlook/Email related keywords
    OUTLOOK_KEYWORDS = [
        "outlook", "email", "mail", "inbox", "sent items", "calendar", 
        "meeting", "appointment", "contact", "exchange", "owa", "office 365",
        "email not working", "can't send email", "email error", 
        "outlook crash", "outlook frozen", "sync issue", "calendar sync",
        "email delivery", "spam folder", "junk mail", "email rules",
        "out of office", "auto reply", "signature", "attachment issue"
    ]
    
    # Shopping/Search/Web automation keywords
    SHOPPING_KEYWORDS = [
        "shop", "shopping", "buy", "purchase", "order", "cart", "checkout",
        "price", "compare prices", "deal", "discount", "coupon", "sale",
        "search for", "find on", "find", "google", "amazon", "ebay", "website",
        "browse", "web search", "online search", "product", "review",
        "laptop", "computer", "phone", "tablet", "device", "electronics",
        "headphones", "tv", "monitor", "keyboard", "mouse",
        "book flight", "flights", "hotel", "reservation", "ticket", "travel",
        "cheap", "cheaper", "best price", "available", "stock", "inventory",
        "open amazon", "go to amazon", "on amazon"
    ]
    
    # Web automation specific keywords
    WEB_AUTOMATION_KEYWORDS = [
        "automate", "fill form", "click button", "navigate to",
        "login to", "sign in", "submit form", "download from",
        "extract data", "scrape", "monitor website"
    ]
    
    def __init__(self):
        """Initialize the smart router"""
        self.route_history: List[Dict[str, Any]] = []
        logger.info("SmartRouter initialized")
    
    def detect_intent(self, message: str) -> Tuple[RouteDestination, float]:
        """
        Detect the intent of the user message and return routing destination
        
        Args:
            message: User's message
            
        Returns:
            Tuple of (RouteDestination, confidence_score)
        """
        message_lower = message.lower()
        
        # Check for Outlook/Email intent
        outlook_score = self._calculate_keyword_score(message_lower, self.OUTLOOK_KEYWORDS)
        
        # Check for Shopping/Web intent
        shopping_score = self._calculate_keyword_score(message_lower, self.SHOPPING_KEYWORDS)
        web_automation_score = self._calculate_keyword_score(message_lower, self.WEB_AUTOMATION_KEYWORDS)
        
        # Combine shopping and web automation scores
        browser_use_score = max(shopping_score, web_automation_score)
        
        # Determine destination based on scores
        scores = {
            RouteDestination.RAG_OUTLOOK: outlook_score,
            RouteDestination.BROWSER_USE: browser_use_score,
            RouteDestination.MISTRAL: 0.5  # Default baseline
        }
        
        # Get the highest scoring destination
        destination = max(scores, key=scores.get)
        confidence = scores[destination]
        
        # Log the routing decision
        logger.info(f"Intent detected: {destination.value} (confidence: {confidence:.2f})")
        logger.debug(f"Scores: Outlook={outlook_score:.2f}, Browser={browser_use_score:.2f}")
        
        return destination, confidence
    
    def _calculate_keyword_score(self, message: str, keywords: List[str]) -> float:
        """
        Calculate a score based on keyword matches
        
        Args:
            message: Message to analyze
            keywords: List of keywords to match
            
        Returns:
            Score between 0 and 1
        """
        if not keywords:
            return 0.0
            
        matches = 0
        message_lower = message.lower()
        
        for keyword in keywords:
            # Use word boundaries for better matching
            keyword_lower = keyword.lower()
            
            # Check if keyword appears in message
            if keyword_lower in message_lower:
                # Give higher weight for exact word boundary matches
                pattern = r'\b' + re.escape(keyword_lower) + r'\b'
                if re.search(pattern, message_lower):
                    matches += 2  # Full word match
                else:
                    matches += 1  # Partial match
        
        if matches == 0:
            return 0.0
        
        # Return a score that increases with more matches
        # Each match adds 0.3, capped at 1.0
        score = min(matches * 0.3, 1.0)
        
        return score
    
    def route_query(
        self, 
        message: str, 
        context: Optional[List[Dict]] = None,
        user_preferences: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Route a query to the appropriate destination with full context
        
        Args:
            message: User's message
            context: Conversation context
            user_preferences: User's routing preferences
            
        Returns:
            Routing decision with metadata
        """
        # Detect intent
        destination, confidence = self.detect_intent(message)
        
        # Apply user preferences if provided
        if user_preferences:
            force_destination = user_preferences.get('force_destination')
            if force_destination:
                destination = RouteDestination(force_destination)
                confidence = 1.0
                logger.info(f"User preference override: {destination.value}")
        
        # Create routing decision
        routing_decision = {
            'destination': destination.value,
            'confidence': confidence,
            'message': message,
            'context': context or [],
            'requires_rag': destination == RouteDestination.RAG_OUTLOOK,
            'requires_browser': destination == RouteDestination.BROWSER_USE,
            'use_mistral': destination in [RouteDestination.MISTRAL, RouteDestination.RAG_OUTLOOK],
            'metadata': {
                'timestamp': self._get_timestamp(),
                'message_length': len(message)
            }
        }
        
        # Store in history
        self.route_history.append(routing_decision)
        
        # Keep only last 100 routing decisions
        if len(self.route_history) > 100:
            self.route_history = self.route_history[-100:]
        
        return routing_decision
    
    def get_routing_explanation(self, decision: Dict[str, Any]) -> str:
        """
        Generate a human-readable explanation of the routing decision
        
        Args:
            decision: Routing decision dict
            
        Returns:
            Explanation string
        """
        destination = decision['destination']
        confidence = decision['confidence']
        
        explanations = {
            'mistral': f"🤖 Using Mistral AI for general conversation (confidence: {confidence:.0%})",
            'rag_outlook': f"📧 Using RAG + Reasoner for Outlook-related query (confidence: {confidence:.0%})",
            'browser_use': f"🌐 Using Browser automation for web task (confidence: {confidence:.0%})"
        }
        
        return explanations.get(destination, f"Using {destination}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get routing statistics
        
        Returns:
            Statistics dict
        """
        if not self.route_history:
            return {
                'total_routes': 0,
                'by_destination': {},
                'average_confidence': 0.0
            }
        
        total = len(self.route_history)
        by_destination = {}
        total_confidence = 0.0
        
        for decision in self.route_history:
            dest = decision['destination']
            by_destination[dest] = by_destination.get(dest, 0) + 1
            total_confidence += decision['confidence']
        
        return {
            'total_routes': total,
            'by_destination': by_destination,
            'average_confidence': total_confidence / total if total > 0 else 0.0,
            'recent_routes': self.route_history[-10:]  # Last 10 routes
        }


# Singleton instance
_router_instance = None


def get_smart_router() -> SmartRouter:
    """Get or create the singleton SmartRouter instance"""
    global _router_instance
    if _router_instance is None:
        _router_instance = SmartRouter()
    return _router_instance


def detect_query_type(message: str) -> str:
    """
    Simple helper to detect query type
    
    Args:
        message: User message
        
    Returns:
        Query type: 'outlook', 'shopping', 'web', or 'general'
    """
    router = get_smart_router()
    destination, _ = router.detect_intent(message)
    
    type_mapping = {
        RouteDestination.RAG_OUTLOOK: 'outlook',
        RouteDestination.BROWSER_USE: 'shopping',
        RouteDestination.MISTRAL: 'general'
    }
    
    return type_mapping.get(destination, 'general')


if __name__ == "__main__":
    # Test the router
    logging.basicConfig(level=logging.INFO)
    
    router = SmartRouter()
    
    test_messages = [
        "My Outlook email is not syncing properly",
        "I want to buy a new laptop on Amazon",
        "What's the weather like today?",
        "Search for cheap flights to Paris",
        "Can you help me with my calendar appointments?",
        "Find the best deal on iPhone 15",
        "My inbox is full, how do I archive emails?"
    ]
    
    print("\n=== Smart Router Test ===\n")
    for msg in test_messages:
        decision = router.route_query(msg)
        explanation = router.get_routing_explanation(decision)
        print(f"Message: {msg}")
        print(f"  → {explanation}\n")
    
    print("\n=== Routing Statistics ===")
    stats = router.get_statistics()
    print(f"Total routes: {stats['total_routes']}")
    print(f"By destination: {stats['by_destination']}")
    print(f"Average confidence: {stats['average_confidence']:.0%}")
