# reasoner.py
import logging
import json
import re
import time
from typing import List, Dict, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio  # Add at top with other imports

# Core dependencies
import ollama
from langchain_community.llms import Ollama
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_community.embeddings import OllamaEmbeddings
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate

# Project components
from retriever import EnhancedRetriever
from cache_system import cache_manager as cache  # Use global instance
from enhanced_logging import get_enhanced_logger, performance_logging
from error_handling import handle_errors, CircuitBreakerConfig, RetryConfig
from health_checks import HealthCheckManager  # Correct import
from config_validation import load_and_validate_config
from performance_monitor import PerformanceReporter as PerformanceMonitor  # Alias to match usage

# Load configuration
try:
    config = load_and_validate_config('config')
    RAG_CONFIG = config.get('rag', {})
except Exception as e:
    logging.warning(f"Failed to load RAG configuration: {e}. Using defaults.")
    RAG_CONFIG = {
        'model_name': 'llama3',
        'cache_ttl': 3600,
        'max_context_length': 2048,
        'temperature': 0.7,
        'top_p': 0.9
    }

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageType(Enum):
    GREETING = "greeting"
    TROUBLESHOOTING = "troubleshooting"
    CHAT = "chat"
    BROWSER = "browser"
    ERROR = "error"

class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Confidence(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

@dataclass
class ChatResponse:
    type: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TroubleshootingStep:
    step_number: int
    action: str
    description: str
    expected_result: str
    tools_needed: List[str] = None
    estimated_time: str = "2-5 minutes"
    difficulty: str = "easy"

@dataclass
class TroubleshootingPlan:
    query: str
    confidence_score: float
    confidence_level: Confidence
    severity: Severity
    primary_cause: str
    steps: List[TroubleshootingStep]
    alternative_solutions: List[str] = None
    escalation_criteria: List[str] = None
    related_error_codes: List[str] = None
    estimated_total_time: str = "10-20 minutes"

class EnhancedReasoner(HealthCheckManager):  # Inherit from correct class
    def __init__(self, retriever, model_name=RAG_CONFIG.get('model_name', 'llama3')):
        super().__init__()
        self.model = ollama.Client()
        self.retriever = retriever
        self.model_name = model_name
        self.llm = OllamaLLM(model=self.model_name)
        self.cache = cache  # Use the global cache_manager
        self.perf_monitor = PerformanceMonitor()
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        
        # Register health checks
        self.register_health_check('model_availability', self._check_model_health)
        self.register_health_check('retriever_status', self._check_retriever_health)
        
        # Greeting patterns with more variations
        self.greeting_patterns = [
            r'^hi$', r'^hello$', r'^hey$', r'^greetings$', r'^howdy$',
            r'^good\s*(morning|afternoon|evening)$', r'^hi\s+there$',
            r'^hello\s+there$', r'^hey\s+there$', r'^what\'s\s+up$',
            r'^how\s+are\s+you$', r'^how\'s\s+it\s+going$'
        ]
        
        # Office-related keywords to identify troubleshooting queries
        self.office_keywords = [
            'word', 'excel', 'powerpoint', 'outlook', 'office', 'microsoft',
            'document', 'spreadsheet', 'presentation', 'email', 'calendar',
            'onedrive', 'sharepoint', 'teams', 'onenote', 'access'
        ]
        
        # Troubleshooting patterns
        self.troubleshooting_patterns = [
            r'error\s+(?:code\s+)?([0-9A-Fx]+)',
            r"(can't|cannot|won't|doesn't)\s+\w+",
            r'(not|isn\'t)\s+working',
            r'(problem|issue|error|broken|help|fix|trouble)',
            r'(fail|bug|crash|stuck|freeze|slow)'
        ]
        
        # Browser agent keywords
        self.browser_keywords = [
            'search', 'find', 'look up', 'browse', 'shop', 'purchase', 'buy',
            'compare', 'prices', 'amazon', 'shopping', 'product', 'website',
            'online', 'internet', 'web', 'google', 'bing'
        ]
        
        logger.info(f"Enhanced reasoner initialized with model: {model_name}")
    
    def is_greeting(self, message: str) -> bool:
        """Check if a message is a greeting using regex patterns"""
        message = message.strip().lower()
        
        # Check against greeting patterns
        for pattern in self.greeting_patterns:
            if re.match(pattern, message):
                logger.info(f"Message '{message}' identified as greeting")
                return True
                
        # Check for very short messages that might be greetings
        if len(message.split()) <= 2 and len(message) < 15:
            simple_greetings = ["hi", "hello", "hey", "greetings", "howdy"]
            for greeting in simple_greetings:
                if greeting in message:
                    logger.info(f"Short message '{message}' identified as greeting")
                    return True
        
        return False
    
    def is_browser_query(self, message: str) -> bool:
        """Check if a message is a browser agent query"""
        message = message.lower()
        
        # Check for browser keywords
        for keyword in self.browser_keywords:
            if keyword in message:
                return True
                
        # Check for shopping intent patterns
        shopping_patterns = [
            r'(find|search for|look for|where can i buy)\s+.+',
            r'(buy|purchase|order|shop for)\s+.+',
            r'(compare|best|price of|cheapest)\s+.+',
            r'(amazon|ebay|online store|website)\s+.+'
        ]
        
        for pattern in shopping_patterns:
            if re.search(pattern, message):
                return True
                
        return False
    
    def is_troubleshooting_query(self, message: str) -> bool:
        """Check if a message is a troubleshooting query"""
        # Skip greeting messages
        if self.is_greeting(message):
            return False
            
        # Skip browser queries
        if self.is_browser_query(message):
            return False
            
        message = message.lower()
        
        # Check for Office keywords
        for keyword in self.office_keywords:
            if keyword in message:
                return True
                
        # Check for troubleshooting patterns
        for pattern in self.troubleshooting_patterns:
            if re.search(pattern, message):
                return True
                
        # If message is longer than 15 words, it might be a troubleshooting query
        if len(message.split()) > 15:
            return True
            
        return False
    
    def classify_query(self, message: str) -> Tuple[str, Dict]:
        prompt = f"""Classify the following message into one category and provide relevant metadata:

Categories:

- greeting: simple hellos or greetings

- troubleshooting: issues with software, errors, problems

- chat: general conversation, questions not about troubleshooting or browsing

- browser_search: requests to search the web for information

- browser_shopping: requests to shop or buy products online

- browser_open: requests to open or visit a specific website or URL

Output in JSON format:

{{"classification": "category_name", "query": "extracted query if applicable", "url": "extracted URL if browser_open, infer if necessary"}}

Message: {message}

"""

        response = self.model.generate(

            model=self.model_name,

            prompt=prompt,

            options={"temperature": 0.3}

        )

        try:

            response_json = json.loads(response.get('response', '{}'))

        except json.JSONDecodeError:

            response_json = {}

        classification = response_json.get('classification', 'chat').strip().lower()

        metadata = {

            'query': response_json.get('query', message),

            'url': response_json.get('url', None)

        }

        if 'greeting' in classification:

            return 'greeting', metadata

        elif 'troubleshooting' in classification:

            return 'troubleshooting', metadata

        elif 'browser_shopping' in classification:

            return 'browser_shopping', metadata

        elif 'browser_search' in classification:

            return 'browser_search', metadata

        elif 'browser_open' in classification:

            return 'browser_open', metadata

        else:

            return 'chat', metadata
    
    async def process_message(self, message: str, context: List[Dict] = None) -> Dict:
        """Process incoming message and return appropriate response"""
        start_time = time.time()
        perf_monitor = PerformanceMonitor()
        
        try:
            # Generate cache key
            cache_key = f"message_{hash(message)}"
            
            # Check cache first
            cached_response = self.cache.get(cache_key)
            if cached_response:
                logger.info("Returning cached response")
                return cached_response
            
            with perf_monitor.measure('query_classification'):
                query_type, class_metadata = self.classify_query(message)
            
            # Track performance metrics
            perf_monitor.record_metric('message_length', len(message))
            perf_monitor.record_metric('query_type', query_type)
        
        
            if query_type == 'greeting':
                logger.info(f"Processing greeting: {message}")
                return ChatResponse(
                    type="greeting",
                    content="Hello! I'm your Super Troubleshooting Assistant. I can help you diagnose and fix Microsoft Office issues, chat about general topics, or help you search the web or shop online. How can I assist you today?",
                    metadata={"detected_intent": "greeting"}
                ).__dict__
        
        
            elif query_type == 'browser_search':
                with self.perf_monitor.measure('browser_search_processing'):
                    logger.info(
                        "Processing browser search query",
                        extra={"query": class_metadata['query']}
                    )
                    response = ChatResponse(
                        type="browser",
                        content=f"I'll help you search for '{class_metadata['query']}' on the web.",
                        metadata={
                            "query": class_metadata['query'],
                            "mode": "search",
                            "timestamp": datetime.now().isoformat(),
                            "performance": self.perf_monitor.get_operation_stats('browser_search_processing')
                        }
                    ).__dict__
                    
                    # Cache the response
                    self.cache.set(cache_key, response)
                    return response
        
        
            elif query_type == 'browser_shopping':
                logger.info(f"Processing browser shopping query: {message}")
                return ChatResponse(
                    type="browser",
                    content=f"I'll help you shop for '{class_metadata['query']}' online.",
                    metadata={
                        "query": class_metadata['query'],
                        "mode": "shopping"
                    }
                ).__dict__
        
        
            elif query_type == 'browser_open':
                logger.info(f"Processing browser open query: {message}")
                url = class_metadata['url'] if class_metadata['url'] else class_metadata['query']
                return ChatResponse(
                    type="browser",
                    content=f"I'll open {url} in the browser.",
                    metadata={
                        "query": url,
                        "mode": "open"
                    }
                ).__dict__
        
        
            elif query_type == 'troubleshooting':
                with self.perf_monitor.measure('troubleshooting_processing'):
                    logger.info(
                        "Processing troubleshooting query",
                        extra={"message": message}
                    )
                    
                    # Retrieve relevant information with monitoring
                    with self.perf_monitor.measure('retrieval'):
                        results = self.retriever.retrieve(message)
                    
                    self.perf_monitor.record_metric('results_count', len(results) if results else 0)
                    
                    if results and len(results) > 0:
                        # Format context from results
                        context = "\n\n".join([
                            f"Title: {r['title']}\nContent: {r.get('content', '')}\nSteps: {', '.join(r.get('steps', []))}\nRelevance: {r['relevance_score']}"
                            for r in results
                        ])
                        
                        # Define prompt
                        prompt_template = """
                        Based on the following retrieved information, provide a clear, step-by-step troubleshooting guide for the user's query.
                        Be helpful, concise, and professional. If multiple solutions exist, prioritize the most relevant one.
                        Query: {query}
                        Retrieved Information:
                        {context}
                        Response:
                        """
                        prompt = PromptTemplate(template=prompt_template, input_variables=["query", "context"])
                        
                        # Create chain
                        chain = prompt | self.llm
                        
                        # Generate response
                        response_content = chain.invoke({"query": message, "context": context})
                        
                        response = ChatResponse(
                            type="troubleshooting",
                            content=response_content,
                            metadata={
                                "results": results,
                                "query": message,
                                "used_rag": True,
                                "performance": self.perf_monitor.get_operation_stats('troubleshooting_processing')
                            }
                        ).__dict__
                        
                        # Cache the response
                        self.cache.set(cache_key, response)
                        return response
                    
                    logger.info("No troubleshooting results found, falling back to chat")
                    return await self._generate_chat_response(message, context)
            
            else:
                logger.info(f"Processing chat message: {message}")
                return await self._generate_chat_response(message, context)
        
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return ChatResponse(
                type="error",
                content="I'm sorry, I encountered an error processing your request. Please try again.",
                metadata={"error": str(e)}
            ).__dict__
    
    async def _generate_chat_response(self, message: str, context: List[Dict] = None) -> Dict:
        """Generate a chat response using the LLM with conversation memory"""
        try:
            # Save message to memory
            self.memory.save_context({"input": message}, {"output": ""})
            
            # Prepare prompt with memory
            history = self.memory.load_memory_variables({})
            prompt = self._prepare_prompt(message, history.get("chat_history", []))
            
            # Generate response from model
            response = self.model.generate(
                model=self.model_name,
                prompt=prompt,
                stream=False,
                options={"temperature": 0.7, "top_p": 0.9}
            )
            
            content = response.get('response', "I'm sorry, I couldn't generate a response.")
            
            # Save response to memory
            self.memory.save_context({"input": message}, {"output": content})
            
            return ChatResponse(
                type="chat",
                content=content,
                metadata={"model": self.model_name}
            ).__dict__
            
        except Exception as e:
            logger.error(f"Error generating chat response: {str(e)}")
            return ChatResponse(
                type="error",
                content="I'm sorry, I encountered an error generating a response. Please try again.",
                metadata={"error": str(e)}
            ).__dict__
    
    def _prepare_prompt(self, message: str, context: List[Dict] = None) -> str:
        """Prepare a prompt for the LLM based on message and context"""
        if not context:
            context = []
            
        # Build conversation history
        conversation = ""
        for item in context[-5:]:  # Use last 5 messages for context
            role = item.get("role", "")
            content = item.get("content", "")
            if role and content:
                conversation += f"{role.capitalize()}: {content}\n"
        
        # Add current message
        conversation += f"User: {message}\nAssistant:"
        
        return conversation

    async def _check_model_health(self) -> Dict[str, Any]:
        """Check if the LLM model is responding"""
        try:
            response = self.model.generate(
                model=self.model_name,
                prompt="test",
                options={"temperature": 0.1}
            )
            return {
                'status': 'healthy' if response else 'unhealthy',
                'message': 'Model is responsive',
                'latency': self.perf_monitor.get_average_latency('model_response')
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Model health check failed: {str(e)}'
            }
    
    async def _check_retriever_health(self) -> Dict[str, Any]:
        """Check if the retriever is functioning"""
        try:
            test_query = "test query"
            results = self.retriever.retrieve(test_query)
            return {
                'status': 'healthy',
                'message': 'Retriever is functioning',
                'result_count': len(results) if results else 0
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Retriever health check failed: {str(e)}'
            }
    
    async def get_diagnostics(self) -> Dict[str, Any]:
        """Get diagnostic information about the reasoner"""
        return {
            'model_name': self.model_name,
            'cache_stats': self.cache.get_stats(),
            'performance_metrics': self.perf_monitor.get_metrics(),
            'health_status': await self.get_health_status()
        }

    def test_process_message(self, test_message: str = "Hello, my Excel is crashing"):
        """Test method to verify message processing (for diagnostics)"""
        try:
            # Initialize a dummy retriever if needed (or use existing)
            from retriever import EnhancedRetriever  # Ensure import if not already
            dummy_retriever = EnhancedRetriever()  # Assuming it has a no-arg constructor or adjust
            reasoner = EnhancedReasoner(dummy_retriever)
            
            response = asyncio.run(reasoner.process_message(test_message))
            logger.info(f"Test response: {response['type']} - {response['content'][:50]}...")
            return response
        except Exception as e:
            logger.error(f"Test failed: {e}")
            return None

def get_reasoner():
    """Factory function to create a new reasoner instance"""
    return EnhancedReasoner()