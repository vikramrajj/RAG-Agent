# reasoner.py
import logging
import json
import re
import time
import asyncio
from typing import List, Dict, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

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
from cache_system import cache_manager as cache
from enhanced_logging import get_enhanced_logger, performance_logging
from error_handling import handle_errors, CircuitBreakerConfig, RetryConfig
from health_checks import HealthCheckManager
from config_validation import load_and_validate_config
from performance_monitor import get_metrics_collector, get_app_monitor

# Performance Monitor Adapter
class PerformanceMonitorAdapter:
    """Adapter to provide simplified interface for reasoner"""
    def __init__(self):
        self.metrics = get_metrics_collector()
        self.app_monitor = get_app_monitor()
    
    def record_metric(self, name, value, tags=None):
        self.metrics.record_metric(name, value, tags)
    
    def measure(self, operation_name):
        """Context manager for timing operations"""
        return OperationTimer(self.app_monitor, operation_name)
    
    def get_operation_stats(self, operation_name):
        return self.metrics.get_metric_summary(operation_name)
    
    def get_metrics(self):
        return {"metrics_available": True}
    
    def get_average_latency(self, operation_name):
        summary = self.metrics.get_metric_summary(operation_name)
        return summary.get('avg', 0)

class OperationTimer:
    """Context manager for timing operations"""
    def __init__(self, app_monitor, operation_name):
        self.app_monitor = app_monitor
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.app_monitor.record_rag_operation(
            self.operation_name,
            duration * 1000,
            exc_type is None
        )

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

class EnhancedReasoner(HealthCheckManager):
    def __init__(self, retriever=None, model_name=RAG_CONFIG.get('model_name', 'llama3')):
        super().__init__()
        self.model = ollama.Client()
        self._retriever = retriever  # Store as private, lazy-load when needed
        self.model_name = model_name
        self.llm = OllamaLLM(model=self.model_name)
        self.cache = cache
        self.perf_monitor = PerformanceMonitorAdapter()
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        
        # Greeting patterns with more variations
        self.greeting_patterns = [
            r'^hi$', r'^hello$', r'^hey$', r'^greetings$', r'^howdy$',
            r'^good\s*(morning|afternoon|evening)$', r'^hi\s+there$',
            r'^hello\s+there$', r'^hey\s+there$', r'^what\'s\s+up$',
            r'^how\s+are\s+you$', r'^how\'s\s+it\s+going$'
        ]
        
        # Office-related keywords
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
    
    @property
    def retriever(self):
        """Lazy-load retriever only when needed for RAG queries"""
        if self._retriever is None:
            from retriever import get_retriever
            logger.info("Lazy-loading retriever for RAG query")
            self._retriever = get_retriever()
        return self._retriever
    
    def classify_query(self, message: str) -> Tuple[str, Dict]:
        prompt = f"""Classify the following message into one category and provide relevant metadata:

Categories:
- greeting: simple hellos or greetings
- troubleshooting: issues with software, errors, problems
- chat: general conversation
- browser_search: requests to search the web
- browser_shopping: requests to shop or buy products
- browser_open: requests to open a website

Output in JSON format:
{{"classification": "category_name", "query": "extracted query", "url": "extracted URL if applicable"}}

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
        
        try:
            # Generate cache key
            cache_key = f"message_{hash(message)}"
            
            # Skip cache for Outlook queries to ensure fresh responses with updated prompts
            skip_cache = any(keyword in message.lower() for keyword in ['outlook', 'owa', 'email not working', 'cant send', 'cant receive'])
            
            # Check cache first (unless skipped)
            if not skip_cache:
                cached_response = self.cache.get(cache_key)
                if cached_response:
                    logger.info("Returning cached response")
                    return cached_response
            else:
                logger.info("Skipping cache for Outlook query to ensure fresh response")
            
            # Classify query
            query_type, class_metadata = self.classify_query(message)
            
            # Track metrics
            self.perf_monitor.record_metric('message_length', len(message))
            self.perf_monitor.record_metric('query_type', query_type)
            
            # Process based on type
            if query_type == 'greeting':
                response = ChatResponse(
                    type="greeting",
                    content="Hello! I'm your Super Troubleshooting Assistant. I can help you diagnose and fix Microsoft Office issues, chat about general topics, or help you search the web or shop online. How can I assist you today?",
                    metadata={"detected_intent": "greeting"}
                ).__dict__
                self.cache.set(cache_key, response)
                return response
            
            elif query_type in ['browser_search', 'browser_shopping', 'browser_open']:
                mode = 'search' if query_type == 'browser_search' else ('shopping' if query_type == 'browser_shopping' else 'open')
                response = ChatResponse(
                    type="browser",
                    content=f"I'll help you {mode} for '{class_metadata['query']}'.",
                    metadata={
                        "query": class_metadata['query'],
                        "mode": mode,
                        "timestamp": datetime.now().isoformat()
                    }
                ).__dict__
                self.cache.set(cache_key, response)
                return response
            
            elif query_type == 'troubleshooting':
                with self.perf_monitor.measure('troubleshooting_processing'):
                    results = self.retriever.retrieve(message)
                    
                    if results and len(results) > 0:
                        context_text = "\n\n".join([
                            f"Title: {r['title']}\nContent: {r.get('content', '')}\nSteps: {', '.join(r.get('steps', []))}\nRelevance: {r['relevance_score']}"
                            for r in results
                        ])
                        
                        prompt_template = """
You are an expert Microsoft Outlook troubleshooting assistant. Based on the retrieved information, provide a comprehensive troubleshooting guide.

CRITICAL FIRST STEPS for Outlook "not working" issues - ALWAYS include these FIRST:

🌐 IMMEDIATE ACTION - Try Outlook Web Access (OWA):
   👉 Click here to open OWA: https://outlook.office.com
   This will help determine if the issue is with your desktop Outlook app or your account itself.
   
   IF OWA WORKS:
   ✅ Your account is fine → Issue is with the desktop Outlook application
   ✅ You can access your emails immediately via browser while we fix the app
   
   IF OWA DOESN'T WORK:
   ❌ Account/server issue → Need to check account credentials, server status, or network

🔧 DIAGNOSTIC TOOL:
   Run Microsoft Support and Recovery Assistant (SaRA):
   👉 Download: https://aka.ms/SaRA-OutlookSetupIssues
   This official Microsoft tool automatically diagnoses and fixes common Outlook problems including:
   - Connectivity issues
   - Profile corruption
   - Add-in conflicts
   - Configuration errors

🛡️ SAFE MODE TEST (if desktop app issue):
   Start Outlook in Safe Mode to bypass add-ins:
   - Hold Ctrl key while clicking Outlook icon
   - Select 'Safe Mode' when prompted
   - If it works in Safe Mode → An add-in is causing the problem

Then provide specific troubleshooting steps from the knowledge base below.

Query: {query}
Retrieved Information:
{context}

Response Format:
1. Start with OWA link and explanation (make it clickable/actionable)
2. Suggest SaRA diagnostic tool with download link
3. If relevant, mention Safe Mode test
4. Provide specific troubleshooting from knowledge base
5. End with clear next steps

Response:
"""
                        prompt = PromptTemplate(template=prompt_template, input_variables=["query", "context"])
                        chain = prompt | self.llm
                        response_content = chain.invoke({"query": message, "context": context_text})
                        
                        response = ChatResponse(
                            type="troubleshooting",
                            content=response_content,
                            metadata={
                                "results": results,
                                "query": message,
                                "used_rag": True
                            }
                        ).__dict__
                        
                        # Only cache if not an Outlook query (to ensure fresh responses with updated prompts)
                        if not skip_cache:
                            self.cache.set(cache_key, response)
                        return response
                    
                    logger.info("No troubleshooting results found, falling back to chat")
                    return await self._generate_chat_response(message, context)
            
            else:
                return await self._generate_chat_response(message, context)
        
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return ChatResponse(
                type="error",
                content="I'm sorry, I encountered an error processing your request. Please try again.",
                metadata={"error": str(e)}
            ).__dict__
    
    async def _generate_chat_response(self, message: str, context: List[Dict] = None) -> Dict:
        """Generate a chat response using the LLM"""
        try:
            # Save message to memory
            self.memory.save_context({"input": message}, {"output": ""})
            
            # Prepare prompt
            prompt = self._prepare_prompt(message, context)
            
            # Generate response
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
                content="I'm sorry, I encountered an error generating a response.",
                metadata={"error": str(e)}
            ).__dict__
    
    def _prepare_prompt(self, message: str, context: List[Dict] = None) -> str:
        """Prepare a prompt for the LLM"""
        if not context:
            context = []
        
        conversation = ""
        for item in context[-5:]:
            role = item.get("role", "")
            content = item.get("content", "")
            if role and content:
                conversation += f"{role.capitalize()}: {content}\n"
        
        conversation += f"User: {message}\nAssistant:"
        return conversation
    
    async def _check_model_health(self) -> Dict[str, Any]:
        """Health check for LLM model"""
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
        """Health check for retriever"""
        try:
            results = self.retriever.retrieve("test query")
            return {
                'status': 'healthy',
                'message': 'Retriever is functioning',
                'result_count': len(results) if results else 0,
                'latency': self.perf_monitor.get_average_latency('retrieval')
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Retriever health check failed: {str(e)}'
            }
    
    async def get_diagnostics(self) -> Dict[str, Any]:
        """Get diagnostic information"""
        return {
            'model_name': self.model_name,
            'cache_stats': self.cache.stats(),
            'performance_metrics': self.perf_monitor.get_metrics(),
            'health_status': await self.get_health_status(),
            'configuration': {
                'max_context_length': RAG_CONFIG.get('max_context_length'),
                'temperature': RAG_CONFIG.get('temperature'),
                'top_p': RAG_CONFIG.get('top_p')
            }
        }

def get_reasoner():
    """Factory function to create a new reasoner instance"""
    from retriever import EnhancedRetriever
    retriever = EnhancedRetriever()
    return EnhancedReasoner(retriever)
