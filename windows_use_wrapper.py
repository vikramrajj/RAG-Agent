"""
Windows Automation Wrapper using windows-use library.
Similar to browser_use_wrapper.py but for Windows desktop automation.
"""

import os
import logging
from typing import Dict, Any, Optional
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from windows_use.agent import Agent

logger = logging.getLogger(__name__)

class WindowsUseWrapper:
    """Wrapper for Windows desktop automation using windows-use library."""
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        """
        Initialize Windows automation with Gemini API.
        
        Args:
            gemini_api_key: Google Gemini API key (optional, uses env var if not provided)
        """
        # Check both GEMINI_API_KEY and GOOGLE_API_KEY (same as browser_use_wrapper)
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not found. Please set it in environment or pass it.")
        
        # Initialize LLM (same model as browser-use for consistency)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            api_key=self.gemini_api_key,
            temperature=0.5
        )
        
        # Initialize Windows agent
        # windows_use Agent parameters: instructions, additional_tools, llm, max_steps, use_vision
        self.agent = Agent(
            llm=self.llm,
            use_vision=False,      # Disable vision for faster performance
            max_steps=100          # Maximum steps for task execution
        )
        
        logger.info("Windows automation initialized with Gemini API")
    
    def execute_task(self, task: str) -> Dict[str, Any]:
        """
        Execute a Windows automation task.
        
        Args:
            task: Natural language description of the task
            
        Returns:
            Dictionary with success status and result message
        """
        logger.info(f"Executing Windows task: {task}")
        
        try:
            # Execute the task using the agent
            # windows_use Agent.invoke() executes the task
            result = self.agent.invoke(query=task)
            
            logger.info(f"Windows task completed: {task}")
            
            return {
                'success': True,
                'result': str(result) if result else f"Executed: {task}",
                'message': f"✅ Task completed: {task}"
            }
            
        except Exception as e:
            error_str = str(e)
            logger.error(f"Windows automation error: {error_str}")
            
            # Check for quota errors (same as browser-use)
            if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str or 'quota' in error_str.lower():
                return {
                    'success': False,
                    'error': 'quota_exceeded',
                    'message': (
                        "⚠️ Daily API quota reached (50 requests/day)\n\n"
                        "The quota resets every 24 hours. Please try again later or "
                        "upgrade to a paid plan for unlimited usage.\n\n"
                        "Visit: https://ai.google.dev/pricing"
                    )
                }
            
            return {
                'success': False,
                'error': str(e),
                'message': f"❌ Error: {error_str}"
            }
    
    def open_application(self, app_name: str) -> Dict[str, Any]:
        """
        Open a Windows application.
        
        Args:
            app_name: Name of the application (e.g., "Calculator", "Notepad")
            
        Returns:
            Dictionary with success status and result
        """
        task = f"Open {app_name}"
        return self.execute_task(task)
    
    def open_file_explorer(self, location: Optional[str] = None) -> Dict[str, Any]:
        """
        Open File Explorer, optionally navigating to a specific location.
        
        Args:
            location: Optional folder path (e.g., "Downloads", "Documents")
            
        Returns:
            Dictionary with success status and result
        """
        if location:
            task = f"Open File Explorer and navigate to {location}"
        else:
            task = "Open File Explorer"
        
        return self.execute_task(task)
    
    def open_settings(self, section: Optional[str] = None) -> Dict[str, Any]:
        """
        Open Windows Settings, optionally to a specific section.
        
        Args:
            section: Optional settings section (e.g., "Network", "Display")
            
        Returns:
            Dictionary with success status and result
        """
        if section:
            task = f"Open Windows Settings and go to {section}"
        else:
            task = "Open Windows Settings"
        
        return self.execute_task(task)
    
    def type_text(self, text: str, app: Optional[str] = None) -> Dict[str, Any]:
        """
        Type text, optionally in a specific application.
        
        Args:
            text: Text to type
            app: Optional application name to open first
            
        Returns:
            Dictionary with success status and result
        """
        if app:
            task = f"Open {app} and type: {text}"
        else:
            task = f"Type: {text}"
        
        return self.execute_task(task)
    
    def execute_command(self, command: str) -> Dict[str, Any]:
        """
        Execute a shell command via Windows automation.
        
        Args:
            command: Command to execute
            
        Returns:
            Dictionary with success status and result
        """
        task = f"Execute command: {command}"
        return self.execute_task(task)


def get_windows_wrapper(gemini_api_key: Optional[str] = None) -> WindowsUseWrapper:
    """
    Get or create a Windows automation wrapper instance.
    
    Args:
        gemini_api_key: Optional Gemini API key
        
    Returns:
        WindowsUseWrapper instance
    """
    return WindowsUseWrapper(gemini_api_key=gemini_api_key)


# Example usage for testing
if __name__ == "__main__":
    # Test the Windows automation wrapper
    wrapper = WindowsUseWrapper()
    
    print("🪟 Windows Automation Test")
    print("=" * 50)
    
    # Test opening Calculator
    print("\nTest 1: Open Calculator")
    result = wrapper.open_application("Calculator")
    print(result['message'])
    
    # Test File Explorer
    print("\nTest 2: Open File Explorer")
    result = wrapper.open_file_explorer()
    print(result['message'])
    
    # Test opening Notepad with text
    print("\nTest 3: Open Notepad and type")
    result = wrapper.type_text("Hello from Windows-Use!", "Notepad")
    print(result['message'])
