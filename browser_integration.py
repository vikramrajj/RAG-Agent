"""
Browser-Use WebUI Integration Module
Integrates the browser-use-webui functionality into the RAG Agent
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import asyncio

# Add browser-use-webui to path
BROWSER_UI_PATH = Path(__file__).parent / "browser-use-webui"
if BROWSER_UI_PATH.exists():
    sys.path.insert(0, str(BROWSER_UI_PATH))

from enhanced_logging import get_enhanced_logger

logger = get_enhanced_logger('browser_integration')

class BrowserUseIntegration:
    """
    Integration class for browser-use-webui functionality
    Provides enhanced browser automation capabilities for the RAG Agent
    """
    
    def __init__(self):
        """Initialize the browser-use integration"""
        self.browser_ui_available = False
        self.webui_manager = None
        self.agent_controller = None
        self._initialize()
    
    def _initialize(self):
        """Initialize browser-use components"""
        try:
            # Check if browser-use-webui is available
            if not BROWSER_UI_PATH.exists():
                logger.warning("browser-use-webui directory not found")
                return
            
            # Import browser-use components
            from src.webui.webui_manager import WebUIManager  # type: ignore
            from src.controller.custom_controller import CustomController  # type: ignore
            
            self.webui_manager = WebUIManager
            self.agent_controller = CustomController
            self.browser_ui_available = True
            
            logger.info("Browser-use WebUI integration initialized successfully")
            
        except ImportError as e:
            logger.warning(f"Could not import browser-use components: {e}")
            logger.warning("Browser-use features will not be available")
        except Exception as e:
            logger.error(f"Error initializing browser-use integration: {e}")
    
    def is_available(self) -> bool:
        """Check if browser-use integration is available"""
        return self.browser_ui_available
    
    async def execute_browser_task(
        self, 
        task: str, 
        model: str = "ollama/llama3",
        use_own_browser: bool = False,
        keep_browser_open: bool = False,
        save_recording: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a browser task using browser-use agent
        
        Args:
            task: The task description for the browser agent
            model: LLM model to use for the agent
            use_own_browser: Whether to use persistent browser session
            keep_browser_open: Keep browser open after task completion
            save_recording: Save screen recording of the session
            
        Returns:
            Dict containing task results and metadata
        """
        if not self.browser_ui_available:
            return {
                'success': False,
                'error': 'Browser-use integration not available',
                'result': None
            }
        
        try:
            from src.agent.browser_use_agent import run_browser_use_agent  # type: ignore
            
            logger.info(f"Executing browser task: {task[:100]}...")
            
            # Configure agent parameters
            agent_params = {
                'task': task,
                'llm_provider': self._parse_model_provider(model),
                'llm_model_name': self._parse_model_name(model),
                'use_own_browser': use_own_browser,
                'keep_browser_open': keep_browser_open,
                'save_recording_path': './recordings' if save_recording else None,
                'max_steps': 50,  # Maximum steps for the agent
            }
            
            # Execute the browser agent task
            result = await run_browser_use_agent(**agent_params)
            
            logger.info("Browser task completed successfully")
            
            return {
                'success': True,
                'result': result,
                'task': task,
                'model': model
            }
            
        except Exception as e:
            logger.error(f"Error executing browser task: {e}")
            return {
                'success': False,
                'error': str(e),
                'result': None
            }
    
    def _parse_model_provider(self, model: str) -> str:
        """Extract provider from model string (e.g., 'ollama/llama3' -> 'ollama')"""
        if '/' in model:
            return model.split('/')[0].lower()
        return 'ollama'  # Default to ollama
    
    def _parse_model_name(self, model: str) -> str:
        """Extract model name from model string (e.g., 'ollama/llama3' -> 'llama3')"""
        if '/' in model:
            return model.split('/', 1)[1]
        return model
    
    async def search_web(
        self, 
        query: str,
        max_results: int = 5,
        model: str = "ollama/llama3"
    ) -> Dict[str, Any]:
        """
        Perform web search using browser agent
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            model: LLM model to use
            
        Returns:
            Search results with metadata
        """
        task = f"Search for '{query}' and summarize the top {max_results} results"
        return await self.execute_browser_task(
            task=task,
            model=model,
            keep_browser_open=False,
            save_recording=False
        )
    
    async def extract_website_content(
        self, 
        url: str,
        content_type: str = "main",
        model: str = "ollama/llama3"
    ) -> Dict[str, Any]:
        """
        Extract content from a website
        
        Args:
            url: Website URL
            content_type: Type of content to extract (main, all, specific)
            model: LLM model to use
            
        Returns:
            Extracted content
        """
        task = f"Go to {url} and extract the {content_type} content from the page"
        return await self.execute_browser_task(
            task=task,
            model=model,
            keep_browser_open=False,
            save_recording=False
        )
    
    async def automate_workflow(
        self, 
        workflow_description: str,
        model: str = "ollama/llama3",
        use_persistent_browser: bool = True
    ) -> Dict[str, Any]:
        """
        Automate a complex browser workflow
        
        Args:
            workflow_description: Description of the workflow to automate
            model: LLM model to use
            use_persistent_browser: Use persistent browser session
            
        Returns:
            Workflow execution results
        """
        return await self.execute_browser_task(
            task=workflow_description,
            model=model,
            use_own_browser=use_persistent_browser,
            keep_browser_open=use_persistent_browser,
            save_recording=True
        )
    
    def launch_webui(
        self,
        ip: str = "127.0.0.1",
        port: int = 7788,
        theme: str = "Ocean"
    ):
        """
        Launch the browser-use WebUI interface
        
        Args:
            ip: IP address to bind to
            port: Port to listen on
            theme: UI theme to use
        """
        if not self.browser_ui_available:
            logger.error("Browser-use WebUI not available")
            return
        
        try:
            from src.webui.interface import create_ui, theme_map  # type: ignore
            
            if theme not in theme_map:
                logger.warning(f"Theme '{theme}' not found, using default 'Ocean'")
                theme = "Ocean"
            
            logger.info(f"Launching browser-use WebUI on {ip}:{port} with theme '{theme}'")
            
            demo = create_ui(theme_name=theme)
            demo.queue().launch(server_name=ip, server_port=port, share=False)
            
        except Exception as e:
            logger.error(f"Error launching browser-use WebUI: {e}")

# Global instance
_browser_integration = None

def get_browser_integration() -> BrowserUseIntegration:
    """Get or create the browser integration instance"""
    global _browser_integration
    if _browser_integration is None:
        _browser_integration = BrowserUseIntegration()
    return _browser_integration

# Convenience functions
async def execute_browser_task(task: str, **kwargs) -> Dict[str, Any]:
    """Execute a browser task"""
    integration = get_browser_integration()
    return await integration.execute_browser_task(task, **kwargs)

async def search_web(query: str, **kwargs) -> Dict[str, Any]:
    """Search the web"""
    integration = get_browser_integration()
    return await integration.search_web(query, **kwargs)

async def extract_website_content(url: str, **kwargs) -> Dict[str, Any]:
    """Extract website content"""
    integration = get_browser_integration()
    return await integration.extract_website_content(url, **kwargs)

async def automate_workflow(workflow: str, **kwargs) -> Dict[str, Any]:
    """Automate a browser workflow"""
    integration = get_browser_integration()
    return await integration.automate_workflow(workflow, **kwargs)

def launch_browser_webui(**kwargs):
    """Launch the browser WebUI"""
    integration = get_browser_integration()
    integration.launch_webui(**kwargs)

def is_browser_integration_available() -> bool:
    """Check if browser integration is available"""
    integration = get_browser_integration()
    return integration.is_available()
