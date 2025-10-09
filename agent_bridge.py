# agent_bridge.py
import logging
import uuid
import json
import time
from datetime import datetime, timedelta, timezone
from flask import Flask, request, send_from_directory, jsonify, session
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
# from voice_handler import VoiceHandler  # Temporarily disabled due to heavy dependencies
from browser_automation import BrowserAutomation
from concurrent.futures import ThreadPoolExecutor
import asyncio
from functools import wraps, lru_cache
import traceback
import os
from pathlib import Path
from web_agent import WebAgent
from agent_orchestrator import run_outlook_agent

# Import security and error handling utilities
from security_utils import (
    SecurityValidator, CSRFProtection, SecurityHeaders, 
    validate_request_data, SECURITY_CONFIG
)
from error_handling import (
    circuit_breaker, retry, resilient,
    CircuitBreakerConfig, RetryConfig, error_tracker
)
from standardized_error_handler import (
    handle_errors, handle_async_errors, ErrorCategory, ErrorSeverity,
    error_handler, handle_validation_error, handle_network_error
)
from health_checks import HealthCheckManager, setup_default_health_checks
from structured_logging import (
    setup_structured_logging, CorrelationContext, get_logger, 
    get_performance_logger, get_security_logger, with_correlation_id,
    log_api_request, log_api_response
)
from enhanced_logging import get_enhanced_logger, log_context, performance_logging, log_user_action
from config_validation import (
    EnvironmentManager, load_and_validate_config, create_default_config_files,
    ConfigError
)
from typing import Optional, Dict, Any
from fastapi import WebSocket
from tool_invoker import ToolInvoker
from outlook_login import OutlookLogin

# Import the RAG components
try:
    from retriever import EnhancedRetriever
    from reasoner import EnhancedReasoner
    from browser_integration import get_browser_integration, is_browser_integration_available
except ImportError as e:
    logging.error(f"Could not import required modules: {e}")
    raise

# Import smart routing and browser-use wrapper
try:
    from smart_router import SmartRouter, get_smart_router, RouteDestination
    from browser_use_wrapper import BrowserUseWrapper, get_browser_use_wrapper, execute_web_task
    SMART_ROUTING_AVAILABLE = True
    logging.info("Smart routing and browser-use wrapper loaded")
except Exception as e:
    logging.warning(f"Smart routing/browser-use not available: {e}")
    SMART_ROUTING_AVAILABLE = False
    get_smart_router = None
    get_browser_use_wrapper = None
    RouteDestination = None
    execute_web_task = None

# Import lightweight model management
try:
    from model_manager import get_model_manager, load_model as load_lightweight_model
    from lightweight_models_config import LIGHTWEIGHT_MODELS, list_all_models
    MODELS_AVAILABLE = True
    logging.info("Lightweight models support enabled")
except ImportError as e:
    logging.warning(f"Lightweight models not available: {e}")
    MODELS_AVAILABLE = False
    get_model_manager = None
    list_all_models = None

# Initialize configuration management
config_dir = Path("config")
try:
    # Create default config files if they don't exist
    if not config_dir.exists():
        create_default_config_files(str(config_dir))
        print("Created default configuration files in config/ directory")
    
    # Load and validate configuration
    app_config = load_and_validate_config(str(config_dir))
    print(f"Configuration loaded successfully for environment: {os.getenv('APP_ENV', 'development')}")
    
except ConfigError as e:
    print(f"Configuration validation failed: {e}")
    print("Please check your configuration files in the config/ directory")
    raise
except Exception as e:
    print(f"Failed to load configuration: {e}")
    # Use default configuration for basic operation
    app_config = {
        "server": {"host": "127.0.0.1", "port": 5000, "debug": False},
        "logging": {"level": "INFO", "log_dir": "logs"},
        "security": {"secret_key": os.urandom(24).hex()}
    }

# Configure structured logging with config values
log_level = app_config.get("logging", {}).get("level", os.getenv('LOG_LEVEL', 'INFO'))
log_dir = app_config.get("logging", {}).get("log_dir", "logs")

loggers = setup_structured_logging(
    app_name="rag_agent",
    log_level=log_level,
    log_dir=log_dir,
    enable_console=True,
    enable_file=True
)
logger = get_logger('app')
performance_logger = get_performance_logger()
security_logger = get_security_logger()

# Log configuration status
logger.info("Configuration loaded successfully", extra={
    "environment": os.getenv('APP_ENV', 'development'),
    "config_dir": str(config_dir),
    "log_level": log_level
})

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.start_time = time.time()  # Track application start time

# Initialize components
# voice_handler = VoiceHandler()  # Disabled: causes slow startup due to model download
voice_handler = None  # Temporarily disabled for faster startup
browser_automation = BrowserAutomation()
# browser_integration = get_browser_integration()  # Disabled: gradio import issue
browser_integration = None  # Temporarily disabled
reasoner = None  # Will be initialized in init_components()

# Security configuration from loaded config
security_config = app_config.get("security", {})
app.secret_key = os.getenv('FLASK_SECRET_KEY', security_config.get("secret_key", os.urandom(24)))

# Update Flask config with security settings
app.config.update(SECURITY_CONFIG)
app.config.update(
    PERMANENT_SESSION_LIFETIME=timedelta(seconds=security_config.get("session_timeout", 3600))
)

# Apply security headers to all responses
@app.after_request
def apply_security_headers(response):
    return SecurityHeaders.apply_security_headers(response)

# Enable CORS with security settings
CORS(app, resources={r"/*": {"origins": ['http://localhost:3000', 'http://127.0.0.1:5000', 'http://localhost:8000', 'http://127.0.0.1:8000']}})

# Rate limiting with configuration-based settings
rate_limit_per_minute = security_config.get("rate_limit_per_minute", 20)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per hour", f"{rate_limit_per_minute} per minute"],
    storage_uri="memory://"  # In production, use Redis for distributed rate limiting
)

# Thread executor with limited workers
executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="agent-worker")

# Request tracking
active_requests = {}
request_history = []

class DiagnosticsError(Exception):
    """Custom exception for diagnostics failures"""
    pass

def generate_request_id():
    """Generate unique request ID and set as correlation ID"""
    request_id = str(uuid.uuid4())
    CorrelationContext.set_correlation_id(request_id)
    return request_id

def log_request_start(request_id, endpoint, user_ip):
    """Log request start with structured logging"""
    CorrelationContext.set_correlation_id(request_id)
    
    # Only log API request in non-debug mode to reduce overhead
    if log_level != 'DEBUG':
        log_api_request(
            endpoint=endpoint,
            method=request.method if request else 'UNKNOWN',
            ip_address=user_ip,
            request_id=request_id
        )
    
    # Use a more efficient approach with fewer dictionary operations
    active_requests[request_id] = {
        'request_id': request_id,
        'endpoint': endpoint,
        'user_ip': user_ip,
        'start_time': datetime.now(timezone.utc),
        'status': 'started'
    }

def log_request_end(request_id, status, message=None, error=None):
    """Log request completion with structured logging and timing"""
    CorrelationContext.set_correlation_id(request_id)
    
    # Fast path if request not found
    if request_id not in active_requests:
        return
        
    request_info = active_requests[request_id]
    end_time = datetime.now(timezone.utc)
    duration = (end_time - request_info['start_time']).total_seconds()
    
    # Update request info in-place to avoid creating new dictionaries
    request_info['end_time'] = end_time
    request_info['duration'] = duration
    request_info['status'] = status
    
    # Only set message and error if they exist to save memory
    if message:
        request_info['message'] = message
    if error:
        request_info['error'] = str(error)
    
    # Determine status code - use constant for better performance
    status_code = 200 if status == 'completed' else 500
    
    # Only log API response in non-debug mode to reduce overhead
    if log_level != 'DEBUG':
        log_api_response(
            endpoint=request_info['endpoint'],
            method=request.method if request else 'UNKNOWN',
            status_code=status_code,
            duration=duration,
            request_id=request_id,
            response_message=message,
            error=str(error) if error else None
        )
    
    # Use conditional logging to reduce overhead
    if error:
        logger.error(
            f"Request {request_id} failed",
            extra={
                'request_id': request_id,
                'endpoint': request_info['endpoint'],
                'duration_seconds': duration,
                'error': str(error)
            },
            exc_info=error
        )
    else:
        logger.info(
            f"Request {request_id} completed successfully",
                extra={
                    'request_id': request_id,
                    'endpoint': request_info['endpoint'],
                    'duration_seconds': request_info['duration'],
                    'status': status
                }
            )
        
        # Move to history
        request_history.append(request_info.copy())
        del active_requests[request_id]

# Initialize components
def initialize_components():
    """Initialize RAG components with error handling"""
    try:
        global retriever, reasoner, health_manager
        retriever = EnhancedRetriever()
        reasoner = EnhancedReasoner(retriever)
        
        # Initialize health check manager
        health_manager = HealthCheckManager()
        setup_default_health_checks(health_manager)
        
        logger.info("RAG components and health checks initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize RAG components: {str(e)}")
        logger.error(traceback.format_exc())
        return False

# Initialize components before first request
with app.app_context():
    initialize_components()

# Serve static files
@app.route('/')
def index():
    """Serve the main index.html page"""
    return send_from_directory('.', 'index.html')

@app.route('/sat')
@app.route('/sat_ui.html')
def sat_ui():
    """Serve the Student Assistance Tool interface - Improved Version"""
    return send_from_directory('.', 'sat_ui_improved.html')

@app.route('/sat_legacy')
@app.route('/sat_ui_legacy.html')
def sat_ui_legacy():
    """Serve the legacy Student Assistance Tool interface"""
    return send_from_directory('.', 'sat_ui.html')

@app.route('/api/models', methods=['GET'])
def get_models():
    """Get list of all available lightweight models"""
    try:
        model_manager = get_model_manager()
        all_models = list_all_models()
        downloaded = model_manager.list_downloaded_models()
        current = model_manager.get_model_info()
        
        return jsonify({
            'success': True,
            'all_models': all_models,
            'downloaded': downloaded,
            'current_model': current,
            'ollama_status': model_manager._check_ollama_status()
        })
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/models/current', methods=['GET'])
def get_current_model():
    """Get information about the currently loaded model"""
    try:
        model_manager = get_model_manager()
        info = model_manager.get_model_info()
        return jsonify({
            'success': True,
            'model': info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/models/load', methods=['POST'])
@validate_request_data(required_fields=['model'], max_content_length=1024)
def load_model_api():
    """Load a specific model"""
    try:
        data = request.get_json()
        model_name = data.get('model')
        auto_pull = data.get('auto_pull', True)
        
        model_manager = get_model_manager()
        success = model_manager.load_model(model_name, auto_pull=auto_pull)
        
        if success:
            info = model_manager.get_model_info()
            return jsonify({
                'success': True,
                'message': f'Model {model_name} loaded successfully',
                'model': info
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to load model {model_name}'
            }), 400
            
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/models/download', methods=['POST'])
@validate_request_data(required_fields=['model'], max_content_length=1024)
def download_model_api():
    """Download a model via Ollama"""
    try:
        data = request.get_json()
        model_name = data.get('model')
        
        model_manager = get_model_manager()
        success = model_manager.pull_model(model_name)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Model {model_name} downloaded successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to download model {model_name}'
            }), 400
            
    except Exception as e:
        logger.error(f"Error downloading model: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/models/recommend', methods=['POST'])
@validate_request_data(required_fields=['use_case'], max_content_length=1024)
def recommend_models_api():
    """Get model recommendations for a use case"""
    try:
        data = request.get_json()
        use_case = data.get('use_case')
        available_ram = data.get('available_ram_gb', 8)
        
        model_manager = get_model_manager()
        recommendations = model_manager.recommend_for_use_case(use_case, available_ram)
        
        return jsonify({
            'success': True,
            'use_case': use_case,
            'recommendations': recommendations
        })
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/static/<path:filename>')
def serve_static_file(filename):
    """Serve static files from the static directory"""
    return send_from_directory('static', filename)

# Chat endpoint for handling user messages
@app.route('/chat/ws')
async def chat_ws():
    """WebSocket endpoint for chat functionality"""
    websocket = request.environ.get('wsgi.websocket')
    if not websocket:
        return 'Expected WebSocket connection', 400

    agent = AgentBridge()
    try:
        await agent.register_websocket(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        return str(e), 500

@app.route('/chat', methods=['POST'])
@handle_async_errors(
    category=ErrorCategory.INTERNAL,
    severity=ErrorSeverity.MEDIUM,
    context={'endpoint': 'chat', 'component': 'agent_bridge'},
    return_error_response=True
)
@validate_request_data(required_fields=['message'], max_content_length=10*1024)  # 10KB limit
@resilient('chat_service', 
          cb_config=CircuitBreakerConfig(failure_threshold=3, recovery_timeout=30),
          retry_config=RetryConfig(max_attempts=2, base_delay=0.5))
async def chat():
    request_id = generate_request_id()
    log_request_start(request_id, 'chat', get_remote_address())
    
    try:
        # Parse and validate request data
        data = request.get_json()
        message = data.get('message', '').strip()
        context = data.get('context', [])
        browser_mode = data.get('browser_mode', False)
        model_name = data.get('model', 'mistral').strip()  # Default to Mistral
        use_smart_routing = data.get('smart_routing', True)  # Enable by default
        
        # Validate message content
        if not SecurityValidator.validate_string_length(message, min_length=1, max_length=2000):
            return jsonify({
                'error': 'Invalid message length',
                'type': 'validation_error'
            }), 400
        
        # Sanitize message content
        message = SecurityValidator.sanitize_html(message)
        
        # Initialize routing variables (may be overridden by smart routing)
        destination = 'mistral'  # Default
        confidence = 0.0  # Default
        
        # ==============================================
        # SMART ROUTING: Route to appropriate system
        # ==============================================
        if SMART_ROUTING_AVAILABLE and use_smart_routing:
            router = get_smart_router()
            routing_decision = router.route_query(message, context)
            destination = routing_decision['destination']
            confidence = routing_decision['confidence']
            
            logger.info(f"Smart routing → {destination} (confidence: {confidence:.2f})")
            
            # Route 1: Browser-use for shopping/web automation
            if destination == 'browser_use':
                browser_wrapper = get_browser_use_wrapper()
                if browser_wrapper.is_available():
                    try:
                        logger.info("Executing browser automation task...")
                        # Determine task type based on query content
                        if any(shop_word in message.lower() for shop_word in ['find', 'search for', 'buy', 'purchase', 'shop']):
                            result = await execute_web_task(message, task_type='shop')
                        else:
                            result = await execute_web_task(message, task_type='search')
                        
                        if result['success']:
                            return jsonify({
                                'response': result['content'],
                                'content': result['content'],
                                'type': 'browser_automation',
                                'route': 'browser_use',
                                'confidence': confidence,
                                'metadata': {
                                    'request_id': request_id,
                                    'timestamp': datetime.now(timezone.utc).isoformat(),
                                    **result.get('metadata', {})
                                }
                            })
                        else:
                            # Task failed, return error message
                            error_msg = result.get('error', 'Browser automation failed')
                            logger.error(f"Browser automation failed: {error_msg}")
                            return jsonify({
                                'response': f"Browser automation encountered an error: {error_msg}",
                                'content': f"Failed to execute browser task. Error: {error_msg}",
                                'type': 'browser_automation_error',
                                'route': 'browser_use',
                                'confidence': confidence,
                                'metadata': {
                                    'request_id': request_id,
                                    'timestamp': datetime.now(timezone.utc).isoformat(),
                                    'error': error_msg
                                }
                            })
                    except Exception as e:
                        logger.error(f"Browser automation error: {e}", exc_info=True)
                        return jsonify({
                            'response': f"Browser automation encountered an exception: {str(e)}",
                            'content': f"Failed to execute browser task. Exception: {str(e)}",
                            'type': 'browser_automation_error',
                            'route': 'browser_use',
                            'confidence': confidence,
                            'metadata': {
                                'request_id': request_id,
                                'timestamp': datetime.now(timezone.utc).isoformat(),
                                'error': str(e)
                            }
                        })
                
                # Browser-use not available - use Mistral but preserve route info
                logger.warning("Browser-use not available, falling back to Mistral (route preserved)")
                # Continue to Mistral path below, but keep destination and confidence for response
                
                        # Route 2: RAG + Reasoner for Outlook queries
            elif destination == 'rag_outlook':
                logger.info("Using RAG Loader + Reasoner for Outlook query")
                try:
                    # Retrieve relevant Outlook documentation
                    retrieved_docs = retriever.retrieve(message, k=5)
                    
                    # Process with reasoner
                    if 'reasoner' not in app.config:
                        app.config['reasoner'] = EnhancedReasoner(retriever)
                    
                    response = await app.config['reasoner'].process_message(message, context)
                    
                    return jsonify({
                        'response': response['content'],
                        'content': response['content'],
                        'type': 'rag_outlook',
                        'route': 'rag_outlook',
                        'confidence': confidence,
                        'sources': [doc.get('source', 'Unknown') for doc in retrieved_docs[:3]],
                        'metadata': {
                            'request_id': request_id,
                            'timestamp': datetime.now(timezone.utc).isoformat(),
                            **response.get('metadata', {})
                        }
                    })
                except Exception as e:
                    logger.error(f"RAG Outlook routing error: {e}")
                    # Fall through to Mistral
        
        # ================================================
        # Route 3 (DEFAULT): Use Mistral for general queries
        # ================================================
        if MODELS_AVAILABLE and model_name:
            try:
                manager = get_model_manager()
                
                # Load the model if not already loaded
                if not manager.current_model or manager.current_model.get('name') != model_name:
                    load_success = manager.load_model(model_name, auto_pull=False)
                    if not load_success:
                        logging.warning(f"Failed to load model {model_name}, falling back to default reasoner")
                        raise ValueError(f"Model {model_name} not available")
                
                # Use Mistral (or selected model) for chat
                import time
                from datetime import datetime
                start_time = time.time()
                
                # Get current date for system prompt
                current_date = datetime.now().strftime("%A, %B %d, %Y")
                current_time = datetime.now().strftime("%I:%M %p")
                
                system_prompt = f"You are SAT (Support Assistance Tool), a helpful technical support AI assistant powered by Mistral. Today's date is {current_date} and the current time is {current_time}. Provide clear, accurate, and helpful responses for technical troubleshooting, especially for Microsoft Office products (Outlook, Teams), network issues, and system diagnostics. When asked about the current date or time, always refer to {current_date} at {current_time}."
                response = manager.chat(
                    message=message,
                    conversation_history=context,
                    system_prompt=system_prompt
                )
                
                duration = time.time() - start_time
                
                # Handle both string and dict responses
                if isinstance(response, str):
                    response_content = response
                    response_dict = {'content': response}
                else:
                    response_content = response.get('content', str(response))
                    response_dict = response
                
                # Format response with model info
                return jsonify({
                    'response': response_content,
                    'content': response_content,
                    'type': 'text',
                    'route': destination if use_smart_routing and SMART_ROUTING_AVAILABLE else 'mistral',
                    'confidence': confidence if use_smart_routing and SMART_ROUTING_AVAILABLE else 0.0,
                    'model': manager.current_model.get('display_name', model_name) if hasattr(manager, 'current_model') and hasattr(manager.current_model, 'get') else model_name,
                    'tokens_per_second': response_dict.get('tokens_per_second', 0) if isinstance(response_dict, dict) else 0,
                    'duration': duration,
                    'metadata': {
                        'model': model_name,
                        'request_id': request_id,
                        'timestamp': response_dict.get('timestamp') if isinstance(response_dict, dict) else datetime.now(timezone.utc).isoformat(),
                        'smart_routing': use_smart_routing
                    }
                })
            except Exception as e:
                logging.error(f"Error using model {model_name}: {e}", exc_info=True)
                # Fall through to default reasoner
        
        # Initialize reasoner if not already done
        if 'reasoner' not in app.config:
            app.config['reasoner'] = EnhancedReasoner(retriever)
        
        # Process with reasoner
        response = await app.config['reasoner'].process_message(message, context)
        
        # If browser type or browser_mode is set, integrate web agent
        if browser_mode or response.get('type') == 'browser':
            agent = WebAgent()
            query = response.get('metadata', {}).get('query', '') or message
            mode = response.get('metadata', {}).get('mode', 'search')
            agent_result = await agent.execute(query, mode)
            structured = {
                'type': f"browser_{mode if mode in ['search','shopping','open'] else 'search'}",
                'content': agent_result,
                'metadata': {
                    'query': query,
                    'mode': mode,
                    'request_id': request_id,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            }
            log_request_end(request_id, 'completed', 'Chat request processed successfully')
            return jsonify(structured)
        
        # Check if this is an Outlook/OWA/Email request
        # Only trigger if it's a clear action request, not just mentioning outlook
        message_lower = message.lower().strip()
        outlook_action_keywords = [
            'open outlook', 'launch outlook', 'start outlook',
            'open owa', 'launch owa', 'open email app',
            'open outlook web', 'go to outlook'
        ]
        
        # Check if message starts with or is primarily about opening outlook
        if any(message_lower.startswith(keyword) or message_lower == keyword.replace('open ', '').replace('launch ', '').replace('start ', '') for keyword in outlook_action_keywords):
            # Return browser_open response with OWA URL
            structured = {
                'type': 'browser_open',
                'content': 'Opening Outlook Web Access (OWA) in your browser...',
                'url': 'https://outlook.office365.com/owa/',
                'metadata': {
                    'action': 'open_owa',
                    'request_id': request_id,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            }
            log_request_end(request_id, 'completed', 'OWA open request processed')
            return jsonify(structured)
        
        # Add request metadata to response
        response['metadata'] = response.get('metadata', {})
        response['metadata'].update({
            'request_id': request_id,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        # Add routing metadata to response (for when smart routing falls through to reasoner)
        if 'route' not in response:
            response['route'] = 'llama3'  # Default reasoner
        if 'confidence' not in response:
            response['confidence'] = 0.0  # No smart routing was used
        
        # Log successful completion
        log_request_end(request_id, 'completed', 'Chat request processed successfully')
        
        # Return typed response
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        log_request_end(request_id, 'error', error=str(e))
        # The decorator will handle the response
        raise

# Cleanup task for request history
@app.before_request
def cleanup_request_history():
    """Clean up old request history entries"""
    global request_history
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
    old_count = len(request_history)
    request_history = [r for r in request_history if r.get('start_time', datetime.now(timezone.utc)) > cutoff_time]
    if old_count > len(request_history):
        logger.info("Cleaned up old request history entries")

@app.route('/email', methods=['POST'])
@validate_request_data(required_fields=[], max_content_length=1*1024)
@handle_async_errors(
    category=ErrorCategory.EXTERNAL_SERVICE,
    severity=ErrorSeverity.LOW,
    context={'endpoint': 'email'},
    return_error_response=True
)
async def email():
    """Handle Outlook/OWA opening and email operations"""
    request_id = generate_request_id()
    log_request_start(request_id, 'email', get_remote_address())
    
    try:
        data = request.get_json() or {}
        action = data.get('action', 'open_owa')
        message = data.get('message', '')
        
        # For now, just open OWA (full Outlook login can be implemented later)
        if action == 'open_owa' or 'owa' in message.lower() or 'outlook' in message.lower():
            result = {
                'type': 'browser_open',
                'content': 'Opening Outlook Web Access (OWA)...',
                'url': 'https://outlook.office365.com/owa/',
                'metadata': {
                    'action': 'open_owa',
                    'request_id': request_id,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            }
            log_request_end(request_id, 'completed', 'Email request processed successfully')
            return jsonify(result)
        else:
            return jsonify({
                'error': 'Unknown email action',
                'available_actions': ['open_owa']
            }), 400
            
    except Exception as e:
        logger.error(f"Email endpoint error: {str(e)}")
        log_request_end(request_id, 'error', str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/diagnostics/outlook', methods=['POST'])
@validate_request_data(required_fields=[], max_content_length=1*1024)
@handle_async_errors(
    category=ErrorCategory.INTERNAL,
    severity=ErrorSeverity.LOW,
    context={'endpoint': 'diagnostics'},
    return_error_response=True
)
async def outlook_diagnostics():
    """Run Outlook diagnostics using tool_invoker and agent_orchestrator"""
    request_id = generate_request_id()
    log_request_start(request_id, 'outlook_diagnostics', get_remote_address())
    
    try:
        data = request.get_json() or {}
        action = data.get('action', 'run_diagnostics')
        
        # Import tool invoker
        from tool_invoker import get_tool_invoker
        from agent_orchestrator import try_open_desktop_outlook, run_sara_diagnostics
        
        if action == 'run_diagnostics':
            # Try to open Outlook desktop first
            outlook_result = try_open_desktop_outlook()
            
            # Run SaRA diagnostics
            try:
                run_sara_diagnostics()
                sara_launched = True
            except Exception as e:
                logger.warning(f"Failed to launch SaRA: {e}")
                sara_launched = False
            
            # Build response (without emojis to avoid encoding issues)
            details = []
            if outlook_result:
                details.append("[OK] Outlook desktop launched successfully")
            else:
                details.append("[WARNING] Outlook desktop failed to launch")
            
            if sara_launched:
                details.append("[OK] Microsoft Support and Recovery Assistant (SaRA) launched")
                details.append("[INFO] SaRA will help diagnose Outlook issues")
            else:
                details.append("[WARNING] SaRA not available - please install from Microsoft")
            
            result = {
                'success': True,
                'message': 'Outlook diagnostics initiated',
                'details': '\\n'.join(details),
                'outlook_status': 'running' if outlook_result else 'failed',
                'sara_status': 'running' if sara_launched else 'not_available',
                'metadata': {
                    'request_id': request_id,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            }
            
            log_request_end(request_id, 'completed', 'Diagnostics initiated')
            return jsonify(result)
        else:
            return jsonify({
                'error': 'Unknown diagnostics action',
                'available_actions': ['run_diagnostics']
            }), 400
            
    except Exception as e:
        logger.error(f"Diagnostics endpoint error: {str(e)}")
        log_request_end(request_id, 'error', str(e))
        return jsonify({
            'error': str(e),
            'message': 'Failed to run diagnostics'
        }), 500

@app.route('/search', methods=['POST'])
@validate_request_data(required_fields=['query'], max_content_length=5*1024)  # 5KB limit
@handle_async_errors(
    category=ErrorCategory.INTERNAL,
    severity=ErrorSeverity.MEDIUM,
    context={'endpoint': 'search', 'component': 'agent_bridge'},
    return_error_response=False
)
# @limiter.limit("10 per minute")  # Disabled for async route to avoid AsyncToSync issues
async def search():
    request_id = generate_request_id()
    log_request_start(request_id, 'search', get_remote_address())
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        use_browser_use = data.get('use_browser_use', False)  # NEW: Option to use browser-use
        
        # Validate query content
        if not SecurityValidator.validate_string_length(query, min_length=1, max_length=500):
            return jsonify({
                'error': 'Invalid query length',
                'type': 'validation_error'
            }), 400
        
        # Sanitize query content
        query = SecurityValidator.sanitize_html(query)
        
        # NEW: Use browser-use integration if available and requested
        if use_browser_use and is_browser_integration_available():
            logger.info(f"Using browser-use integration for search: {query}")
            browser_result = await browser_integration.search_web(query, max_results=5)
            
            if browser_result.get('success'):
                log_request_end(request_id, 'completed')
                return jsonify({
                    'type': 'browser_use_search',
                    'content': browser_result.get('result'),
                    'metadata': {
                        'request_id': request_id,
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'method': 'browser-use'
                    }
                })
        
        # Fallback to original WebAgent
        agent = WebAgent()
        result = await agent.execute(query, 'search')
        
        log_request_end(request_id, 'completed')
        return jsonify({
            'type': 'browser_search',
            'content': result
        })
    except Exception as e:
        log_request_end(request_id, 'error', str(e), e)
        return jsonify({'error': str(e)}), 400

@app.route('/shop', methods=['POST'])
@validate_request_data(required_fields=['query'], max_content_length=5*1024)  # 5KB limit
@handle_async_errors(
    category=ErrorCategory.INTERNAL,
    severity=ErrorSeverity.MEDIUM,
    context={'endpoint': 'shop', 'component': 'agent_bridge'},
    return_error_response=False
)
# @limiter.limit("10 per minute")  # Disabled for async route to avoid AsyncToSync issues
async def shop():
    request_id = generate_request_id()
    log_request_start(request_id, 'shop', get_remote_address())
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        # Validate query content
        if not SecurityValidator.validate_string_length(query, min_length=1, max_length=500):
            return jsonify({
                'error': 'Invalid query length',
                'type': 'validation_error'
            }), 400
        
        # Sanitize query content
        query = SecurityValidator.sanitize_html(query)
        
        agent = WebAgent()
        result = await agent.execute(query, 'shopping')
        
        log_request_end(request_id, 'completed')
        return jsonify({
            'type': 'browser_shopping',
            'content': result
        })
    except Exception as e:
        log_request_end(request_id, 'error', str(e), e)
        return jsonify({'error': str(e)}), 400

@app.route('/open', methods=['POST'])
@validate_request_data(required_fields=[], max_content_length=5*1024)  # 5KB limit, flexible required fields
@handle_async_errors(
    category=ErrorCategory.INTERNAL,
    severity=ErrorSeverity.MEDIUM,
    context={'endpoint': 'open', 'component': 'agent_bridge'},
    return_error_response=True
)
# @limiter.limit("10 per minute")  # Disabled for async route to avoid AsyncToSync issues
async def open_site():
    request_id = generate_request_id()
    log_request_start(request_id, 'open', get_remote_address())
    try:
        data = request.get_json()
        # Accept either 'url' or 'query' for convenience
        url = data.get('url') or data.get('query') or ''
        url = url.strip()
        
        if not url:
            return jsonify({
                'error': 'URL or query is required',
                'type': 'validation_error'
            }), 400
        
        # Stricter validation for what constitutes a URL-like string
        if not SecurityValidator.validate_url(url) and (' ' in url or '.' not in url):
             return jsonify({
                'error': 'Invalid URL format',
                'type': 'validation_error'
            }), 400

        # Sanitize URL/query content
        url = SecurityValidator.sanitize_html(url)
        
        # Validate URL/query length
        if not SecurityValidator.validate_string_length(url, min_length=1, max_length=1000):
            return jsonify({
                'error': 'Invalid URL/query length',
                'type': 'validation_error'
            }), 400
        
        agent = WebAgent()
        result = await agent.execute(url, 'open')
        
        log_request_end(request_id, 'completed')
        return jsonify({
            'type': 'browser_open',
            'content': result,
            'metadata': {
                'url': url
            }
        })
    except Exception as e:
        log_request_end(request_id, 'error', str(e), e)
        raise

@app.route('/fallback/outlook', methods=['POST'])
@handle_async_errors(
    category=ErrorCategory.INTERNAL,
    severity=ErrorSeverity.MEDIUM,
    context={'endpoint': 'fallback_outlook', 'component': 'agent_bridge'},
    return_error_response=False
)
async def outlook_fallback():
    """Fallback endpoint for Outlook integration."""
    request_id = generate_request_id()
    log_request_start(request_id, 'fallback_outlook', get_remote_address())
    try:
        # Since this is a fallback, we might not have a specific message.
        # We can pass a generic one or extract from request if available.
        data = request.get_json(silent=True) or {}
        message = data.get('message', 'Default outlook action')
        
        result = await run_outlook_agent(message)
        
        log_request_end(request_id, 'completed', 'Outlook fallback processed successfully')
        return jsonify({
            'status': 'success',
            'request_id': request_id,
            'result': result
        })
    except Exception as e:
        log_request_end(request_id, 'error', str(e), e)
        return jsonify({
            'error': 'Internal server error',
            'type': 'error',
            'content': 'An error occurred while processing the Outlook fallback.',
            'metadata': {
                'request_id': request_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        }), 503

@app.route('/diagnostics', methods=['POST'])
@validate_request_data(required_fields=[], max_content_length=1024)  # 1KB limit for diagnostics
@handle_errors(
    category=ErrorCategory.INTERNAL,
    severity=ErrorSeverity.LOW,
    context={'endpoint': 'diagnostics', 'component': 'agent_bridge'}
)
def run_diagnostics():
    """Runs diagnostic checks and returns a report."""
    request_id = generate_request_id()
    log_request_start(request_id, 'diagnostics', get_remote_address())
    try:
        # Running with a default message for diagnostics
        asyncio.run(run_outlook_agent("diagnostic_check"))
        log_request_end(request_id, 'completed')
        return jsonify({'status': 'success', 'message': 'Diagnostics completed successfully'})
    except Exception as e:
        log_request_end(request_id, 'error', str(e), e)
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint"""
    try:
        # Quick health check
        result = health_manager.run_health_checks(timeout=5.0)
        
        status_code = 200 if result.overall_status.value == 'healthy' else 503
        
        return jsonify({
            'status': result.overall_status.value,
            'timestamp': result.timestamp.isoformat(),
            'checks_passed': result.checks_passed,
            'checks_failed': result.checks_failed,
            'total_checks': result.total_checks
        }), status_code
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 503

@app.route('/health/detailed', methods=['GET'])
@limiter.limit("30 per minute")
def detailed_health_check():
    """Detailed health check with individual check results"""
    try:
        result = health_manager.run_health_checks(timeout=10.0)
        
        status_code = 200 if result.overall_status.value == 'healthy' else 503
        
        return jsonify({
            'status': result.overall_status.value,
            'timestamp': result.timestamp.isoformat(),
            'summary': {
                'checks_passed': result.checks_passed,
                'checks_failed': result.checks_failed,
                'total_checks': result.total_checks,
                'execution_time': result.execution_time
            },
            'checks': [
                {
                    'name': check.name,
                    'status': check.status.value,
                    'message': check.message,
                    'execution_time': check.execution_time,
                    'metadata': check.metadata
                }
                for check in result.results
            ]
        }), status_code
    except Exception as e:
        logger.error(f"Detailed health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 503

@app.route('/health/ready', methods=['GET'])
def readiness_check():
    """Readiness check for Kubernetes/container orchestration"""
    try:
        # Check if critical components are ready
        if not hasattr(app, 'reasoner') or not hasattr(app, 'retriever'):
            return jsonify({
                'status': 'not_ready',
                'message': 'Core components not initialized'
            }), 503
        
        # Run quick health checks
        result = health_manager.run_health_checks(timeout=3.0)
        
        if result.overall_status.value == 'healthy':
            return jsonify({
                'status': 'ready',
                'timestamp': result.timestamp.isoformat()
            }), 200
        else:
            return jsonify({
                'status': 'not_ready',
                'message': f'Health checks failed: {result.checks_failed}/{result.total_checks}',
                'timestamp': result.timestamp.isoformat()
            }), 503
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return jsonify({
            'status': 'not_ready',
            'error': str(e)
        }), 503

@app.route('/health/live', methods=['GET'])
def liveness_check():
    """Liveness check for Kubernetes/container orchestration"""
    try:
        # Basic liveness check - just verify the app is responding
        return jsonify({
            'status': 'alive',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'uptime': time.time() - app.start_time if hasattr(app, 'start_time') else None
        }), 200
    except Exception as e:
        logger.error(f"Liveness check failed: {str(e)}")
        return jsonify({
            'status': 'dead',
            'error': str(e)
        }), 503

# ============================================================================
# BROWSER-USE INTEGRATION ENDPOINTS
# ============================================================================

@app.route('/browser-use/status', methods=['GET'])
def browser_use_status():
    """Check if browser-use integration is available"""
    return jsonify({
        'available': is_browser_integration_available(),
        'features': {
            'web_search': True,
            'content_extraction': True,
            'workflow_automation': True,
            'webui_available': True
        }
    })

@app.route('/browser-use/execute', methods=['POST'])
@validate_request_data(required_fields=['task'], max_content_length=10*1024)
@handle_async_errors(
    category=ErrorCategory.INTERNAL,
    severity=ErrorSeverity.MEDIUM,
    context={'endpoint': 'browser-use-execute', 'component': 'agent_bridge'},
    return_error_response=True
)
async def browser_use_execute():
    """Execute a browser automation task using browser-use"""
    request_id = generate_request_id()
    log_request_start(request_id, 'browser-use-execute', get_remote_address())
    
    try:
        if not is_browser_integration_available():
            return jsonify({
                'error': 'Browser-use integration not available',
                'type': 'feature_unavailable'
            }), 503
        
        data = request.get_json()
        task = data.get('task', '').strip()
        model = data.get('model', 'ollama/llama3')
        use_own_browser = data.get('use_own_browser', False)
        keep_browser_open = data.get('keep_browser_open', False)
        save_recording = data.get('save_recording', False)
        
        # Validate task
        if not SecurityValidator.validate_string_length(task, min_length=1, max_length=2000):
            return jsonify({
                'error': 'Invalid task length',
                'type': 'validation_error'
            }), 400
        
        # Sanitize task
        task = SecurityValidator.sanitize_html(task)
        
        # Execute the browser task
        result = await browser_integration.execute_browser_task(
            task=task,
            model=model,
            use_own_browser=use_own_browser,
            keep_browser_open=keep_browser_open,
            save_recording=save_recording
        )
        
        log_request_end(request_id, 'completed')
        return jsonify({
            'type': 'browser_use_task',
            'content': result,
            'metadata': {
                'request_id': request_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'task': task[:100] + '...' if len(task) > 100 else task
            }
        })
        
    except Exception as e:
        log_request_end(request_id, 'error', str(e), e)
        raise

@app.route('/browser-use/extract', methods=['POST'])
@validate_request_data(required_fields=['url'], max_content_length=5*1024)
@handle_async_errors(
    category=ErrorCategory.INTERNAL,
    severity=ErrorSeverity.MEDIUM,
    context={'endpoint': 'browser-use-extract', 'component': 'agent_bridge'},
    return_error_response=True
)
async def browser_use_extract():
    """Extract content from a website using browser-use"""
    request_id = generate_request_id()
    log_request_start(request_id, 'browser-use-extract', get_remote_address())
    
    try:
        if not is_browser_integration_available():
            return jsonify({
                'error': 'Browser-use integration not available',
                'type': 'feature_unavailable'
            }), 503
        
        data = request.get_json()
        url = data.get('url', '').strip()
        content_type = data.get('content_type', 'main')
        model = data.get('model', 'ollama/llama3')
        
        # Validate URL
        if not SecurityValidator.validate_url(url):
            return jsonify({
                'error': 'Invalid URL',
                'type': 'validation_error'
            }), 400
        
        # Extract content
        result = await browser_integration.extract_website_content(
            url=url,
            content_type=content_type,
            model=model
        )
        
        log_request_end(request_id, 'completed')
        return jsonify({
            'type': 'browser_use_extract',
            'content': result,
            'metadata': {
                'request_id': request_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'url': url
            }
        })
        
    except Exception as e:
        log_request_end(request_id, 'error', str(e), e)
        raise

@app.route('/browser-use/workflow', methods=['POST'])
@validate_request_data(required_fields=['workflow'], max_content_length=20*1024)
@handle_async_errors(
    category=ErrorCategory.INTERNAL,
    severity=ErrorSeverity.HIGH,
    context={'endpoint': 'browser-use-workflow', 'component': 'agent_bridge'},
    return_error_response=True
)
async def browser_use_workflow():
    """Execute a complex browser workflow using browser-use"""
    request_id = generate_request_id()
    log_request_start(request_id, 'browser-use-workflow', get_remote_address())
    
    try:
        if not is_browser_integration_available():
            return jsonify({
                'error': 'Browser-use integration not available',
                'type': 'feature_unavailable'
            }), 503
        
        data = request.get_json()
        workflow = data.get('workflow', '').strip()
        model = data.get('model', 'ollama/llama3')
        use_persistent = data.get('use_persistent_browser', True)
        
        # Validate workflow
        if not SecurityValidator.validate_string_length(workflow, min_length=10, max_length=5000):
            return jsonify({
                'error': 'Invalid workflow description length',
                'type': 'validation_error'
            }), 400
        
        # Sanitize workflow
        workflow = SecurityValidator.sanitize_html(workflow)
        
        # Execute workflow
        result = await browser_integration.automate_workflow(
            workflow_description=workflow,
            model=model,
            use_persistent_browser=use_persistent
        )
        
        log_request_end(request_id, 'completed')
        return jsonify({
            'type': 'browser_use_workflow',
            'content': result,
            'metadata': {
                'request_id': request_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'workflow_summary': workflow[:100] + '...' if len(workflow) > 100 else workflow
            }
        })
        
    except Exception as e:
        log_request_end(request_id, 'error', str(e), e)
        raise

class AgentBridge:
    def __init__(self):
        self.tool_invoker = ToolInvoker()
        self.outlook = OutlookLogin()
        self.active_connections: Dict[str, WebSocket] = {}
        
    async def process_message(self, message: str, tool: str, action: Optional[str] = None) -> dict:
        try:
            if tool == "outlook":
                result = await self.outlook.handle_request(message, action)
            else:
                # ToolInvoker.invoke_tool only takes tool_name as parameter
                tool_result = self.tool_invoker.invoke_tool(tool)
                result = {
                    "response": tool_result.message,
                    "available_actions": []
                }
                
            return {
                "response": result.get("response", ""),
                "actions": result.get("available_actions", [])
            }
        except Exception as e:
            return {"response": f"Error: {str(e)}", "actions": []}

    def check_status(self) -> bool:
        return self.tool_invoker.is_ready()

    async def register_websocket(self, websocket: WebSocket):
        connection_id = id(websocket)
        self.active_connections[connection_id] = websocket
        try:
            while True:
                data = await websocket.receive_json()
                response = await self.process_message(
                    data.get("message"), 
                    data.get("tool"),
                    data.get("action")
                )
                await websocket.send_json(response)
        except:
            del self.active_connections[connection_id]

async def run_outlook_agent(message: str):
    """
    Run Outlook agent orchestrator for diagnostics and troubleshooting.
    This function processes Outlook-related requests through the agent orchestrator.
    """
    try:
        logger.info(f"Running Outlook agent orchestrator with message: {message}")
        
        # Import agent orchestrator functions
        from agent_orchestrator import try_open_desktop_outlook, run_sara_diagnostics
        
        # Perform diagnostic actions
        results = []
        
        # Try to open Outlook desktop
        outlook_launched = try_open_desktop_outlook()
        if outlook_launched:
            results.append("✅ Outlook desktop application launched successfully")
        else:
            results.append("⚠️ Could not launch Outlook desktop - may already be running or not installed")
        
        # Try to launch SaRA diagnostics
        try:
            run_sara_diagnostics()
            results.append("✅ Microsoft Support and Recovery Assistant (SaRA) launched")
            results.append("📋 SaRA will perform comprehensive Outlook diagnostics")
        except Exception as e:
            logger.warning(f"SaRA launch failed: {e}")
            results.append("⚠️ SaRA not available - Install from: https://aka.ms/SaRA-OutlookSetupAssist")
        
        # Add diagnostic recommendations
        results.append("\n🔍 **Diagnostic Recommendations:**")
        results.append("1. Check Outlook is properly configured with your email account")
        results.append("2. Verify internet connectivity")
        results.append("3. Check Windows credentials are valid")
        results.append("4. Ensure Outlook is not in offline mode")
        results.append("5. Review Outlook send/receive logs")
        
        result_text = "\n".join(results)
        
        return {
            "status": "success",
            "result": result_text,
            "metadata": {
                "outlook_launched": outlook_launched,
                "diagnostics_run": True,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error in run_outlook_agent: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "result": f"Error running Outlook diagnostics: {str(e)}",
            "error": str(e)
        }

if __name__ == "__main__":
    # Get server configuration
    server_config = app_config.get("server", {})
    host = server_config.get("host", "127.0.0.1")
    port = server_config.get("port", 8000)
    debug = server_config.get("debug", False)
    
    try:
        print(f"Starting RAG Agent server on http://{host}:{port}")
        logger.info(f"Starting server on {host}:{port}")
        app.run(host=host, port=port, debug=debug, threaded=True, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server startup failed: {str(e)}")
        print(f"Error: {str(e)}")
    finally:
        executor.shutdown(wait=True)
        logger.info("Server shutdown complete")