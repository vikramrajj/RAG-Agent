import logging
import os
import asyncio
from datetime import datetime
from typing import Dict, Optional, List, Any, Union
from pathlib import Path
from dataclasses import dataclass, field

# Browser dependencies - optional, will use fallback if not available
try:
    from browser_use.browser.browser import Browser, BrowserConfig
    from browser_use.browser.context import BrowserContextConfig
    BROWSER_AVAILABLE = True
except ImportError:
    BROWSER_AVAILABLE = False
    # Define placeholder classes for type hints
    Browser = None
    BrowserConfig = None
    BrowserContextConfig = None

# Project imports
from config_validation import load_and_validate_config
from health_checks import HealthCheckManager
from performance_monitor import get_metrics_collector, get_app_monitor
from enhanced_logging import get_enhanced_logger
from error_handling import handle_errors, CircuitBreakerConfig, RetryConfig

# Configure logging
logger = get_enhanced_logger(__name__)

# Load browser configuration
try:
    config = load_and_validate_config('config')
    BROWSER_CONFIG = config.get('browser', {})
except Exception as e:
    logger.warning(f"Failed to load browser configuration: {e}. Using defaults.")
    BROWSER_CONFIG = {
        'headless': True,
        'timeout': 30,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'default_viewport': {'width': 1920, 'height': 1080}
    }

@dataclass
class AutomationConfig:
    headless: bool = BROWSER_CONFIG.get('headless', True)
    timeout: int = BROWSER_CONFIG.get('timeout', 30)
    user_agent: str = BROWSER_CONFIG.get('user_agent', 'Mozilla/5.0')
    viewport_width: int = BROWSER_CONFIG.get('default_viewport', {}).get('width', 1920)
    viewport_height: int = BROWSER_CONFIG.get('default_viewport', {}).get('height', 1080)
    browser_path: Optional[str] = None
    downloads_path: str = './downloads'
    screenshots_path: str = './screenshots'

class BrowserAutomation(HealthCheckManager):
    def __init__(self, config: Optional[AutomationConfig] = None):
        super().__init__()
        self.config = config or AutomationConfig()
        self.browser = None
        self.browser_context = None
        self.metrics = get_metrics_collector()
        self.app_monitor = get_app_monitor()
        
        # Create necessary directories
        Path(self.config.downloads_path).mkdir(parents=True, exist_ok=True)
        Path(self.config.screenshots_path).mkdir(parents=True, exist_ok=True)
        
        # Initialize browser only if module is available
        if BROWSER_AVAILABLE:
            self._initialize_browser()
        else:
            logger.warning("Browser module not available - using fallback mode")
        
        logger.info(
            f"Browser automation initialized: headless={self.config.headless}, timeout={self.config.timeout}, viewport={self.config.viewport_width}x{self.config.viewport_height}"
        )
        
    def _initialize_browser(self) -> None:
        """Initialize the browser with configuration"""
        if not BROWSER_AVAILABLE:
            logger.warning("Browser module not available")
            return
            
        try:
            browser_config = BrowserConfig(
                headless=self.config.headless,
                browser_binary_path=self.config.browser_path,
                new_context_config=BrowserContextConfig(
                    window_width=self.config.viewport_width,
                    window_height=self.config.viewport_height
                ),
                extra_browser_args=[
                    f"--user-agent={self.config.user_agent}",
                    "--disable-web-security",
                    "--no-sandbox"
                ]
            )
            
            self.browser = Browser(config=browser_config)
            self.browser_context = self.browser.new_context(
                config=BrowserContextConfig(
                    save_downloads_path=self.config.downloads_path
                )
            )
            logger.info("Browser initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            # Set browser to None to allow fallback functionality
            self.browser = None
            self.browser_context = None

    async def execute_action(self, action_plan: Dict) -> Dict:
        """Execute browser automation action with monitoring"""
        start_time = self.perf_monitor.start_operation('browser_action')
        
        try:
            # Validate browser health
            health_status = await self._check_browser_health()
            if health_status['status'] != 'healthy':
                raise Exception(f"Browser unhealthy: {health_status['message']}")
            
            # Convert and validate action plan
            with self.perf_monitor.measure('action_conversion'):
                browser_action = self._convert_action_plan(action_plan)
            
            # Record action metrics
            self.perf_monitor.record_metric('action_type', browser_action['mode'])
            
            # Execute action with timeout
            with self.perf_monitor.measure('browser_execution'):
                result = await asyncio.wait_for(
                    self.browser_agent.execute(
                        browser_action["command"],
                        browser_action["mode"]
                    ),
                    timeout=self.config.timeout
                )
            
            # Take screenshot if configured
            screenshot_path = None
            if action_plan.get('capture_screenshot', False):
                screenshot_path = await self._capture_screenshot(action_plan['action'])
            
            self.perf_monitor.end_operation('browser_action', start_time)
            
            return {
                "status": "success",
                "result": result,
                "action": action_plan["action"],
                "screenshot": screenshot_path,
                "performance": self.perf_monitor.get_operation_stats('browser_action')
            }
            
        except asyncio.TimeoutError:
            error_msg = f"Browser action timed out after {self.config.timeout} seconds"
            logger.error(error_msg)
            self.perf_monitor.record_error('browser_action', 'timeout')
            return {
                "status": "error",
                "error": error_msg,
                "action": action_plan.get("action"),
                "error_type": "timeout"
            }
            
        except Exception as e:
            logger.error(
                "Error executing browser action",
                exc_info=e,
                extra={
                    'action': action_plan.get('action'),
                    'error': str(e)
                }
            )
            self.perf_monitor.record_error('browser_action', str(e))
            return {
                "status": "error",
                "error": str(e),
                "action": action_plan.get("action"),
                "error_type": type(e).__name__
            }

    def _convert_action_plan(self, action_plan: Dict) -> Dict:
        """Convert reasoner action plan to browser-use format with validation"""
        action_type = action_plan.get("action")
        if not action_type:
            raise ValueError("Action plan must specify an action type")
            
        params = action_plan.get("params", {})
        
        action_mapping = {
            "search": lambda p: {
                "command": p.get("query", ""),
                "mode": "search"
            },
            "shop": lambda p: {
                "command": p.get("query", ""),
                "mode": "shopping"
            },
            "navigate": lambda p: {
                "command": p.get("url", ""),
                "mode": "open"
            }
        }
        
        if action_type not in action_mapping:
            raise ValueError(f"Unsupported action type: {action_type}")
            
        result = action_mapping[action_type](params)
        
        if not result["command"]:
            raise ValueError(f"Missing required parameter for action {action_type}")
            
        return result
    
    async def _capture_screenshot(self, action_name: str) -> Optional[str]:
        """Capture screenshot of current page"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{action_name}_{timestamp}.png"
            filepath = Path(self.config.screenshots_path) / filename
            
            await self.browser_context.current_page.screenshot(path=str(filepath))
            return str(filepath)
        except Exception as e:
            logger.warning(f"Failed to capture screenshot: {e}")
            return None
    
    async def _check_browser_health(self) -> Dict[str, Any]:
        """Health check for browser component"""
        try:
            if not self.browser or not self.browser_context:
                return {
                    'status': 'unhealthy',
                    'message': 'Browser or context not initialized'
                }
                
            # Try to open a simple page
            test_result = await self.execute_action({
                'action': 'navigate',
                'params': {'url': 'about:blank'}
            })
            
            if test_result['status'] != 'success':
                return {
                    'status': 'unhealthy',
                    'message': f'Browser navigation failed: {test_result.get("error")}'                }
                
            return {
                'status': 'healthy',
                'message': 'Browser is functioning',
                'headless': self.config.headless,
                'latency': self.perf_monitor.get_average_latency('browser_execution')
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Browser health check failed: {str(e)}',
                'error': str(e)
            }
    
    async def get_diagnostics(self) -> Dict[str, Any]:
        """Get diagnostic information about the browser automation"""
        return {
            'config': vars(self.config),
            'performance_metrics': self.perf_monitor.get_metrics(),
            'health_status': await self.get_health_status(),
            'browser_info': {
                'initialized': bool(self.browser and self.browser_context),
                'headless': self.config.headless,
                'viewport': f"{self.config.viewport_width}x{self.config.viewport_height}"
            }
        }
    
    async def cleanup(self) -> None:
        """Clean up browser resources"""
        try:
            if self.browser_context:
                await self.browser_context.close()
            if self.browser:
                await self.browser.close()
        except Exception as e:
            logger.error(f"Error during browser cleanup: {e}")
        finally:
            self.browser_context = None
            self.browser = None