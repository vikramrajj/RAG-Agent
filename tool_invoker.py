# tool_invoker.py
"""
Enhanced tool invoker with comprehensive error handling, logging, and configuration management.
Provides standardized interface for executing system tools and external applications.
"""

import subprocess
import os
import logging
import time
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from standardized_error_handler import (
    handle_errors, ErrorCategory, ErrorSeverity,
    handle_validation_error, handle_network_error
)
from config import ConfigManager

logger = logging.getLogger(__name__)

@dataclass
class ToolResult:
    """Result of tool execution."""
    success: bool
    message: str
    execution_time: float
    return_code: Optional[int] = None
    output: Optional[str] = None
    error: Optional[str] = None

class ToolInvoker:
    """Enhanced tool invoker with comprehensive error handling and logging."""
    
    def __init__(self):
        self.config = ConfigManager.get_config()
        self.tool_timeout = 30  # Default timeout in seconds
        self.supported_tools = {
            "open_outlook": self._open_outlook,
            "run_sara": self._run_sara,
            "open_edge": self._open_edge,
            "open_chrome": self._open_chrome,
            "system_info": self._get_system_info
        }
        
        logger.info("ToolInvoker initialized with supported tools: %s", list(self.supported_tools.keys()))
    
    @handle_errors(
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.MEDIUM,
        context={'component': 'tool_invoker', 'operation': 'open_outlook'},
        return_error_response=False
    )
    def _open_outlook(self) -> ToolResult:
        """Launch Microsoft Outlook desktop application."""
        logger.info("Launching Microsoft Outlook desktop application")
        start_time = time.time()
        
        try:
            # Check if Outlook is already running
            if self._is_process_running("OUTLOOK.EXE"):
                logger.info("Outlook is already running")
                return ToolResult(
                    success=True,
                    message="Outlook is already running",
                    execution_time=time.time() - start_time
                )
            
            # Launch Outlook - prefer os.startfile on Windows for better behavior
            try:
                if os.name == 'nt':
                    # os.startfile will raise if it fails
                    os.startfile('outlook.exe')
                    execution_time = time.time() - start_time
                    logger.info("Outlook launched via startfile")
                    return ToolResult(success=True, message="Launched Outlook", execution_time=execution_time)
                else:
                    proc = subprocess.Popen(["outlook.exe"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    try:
                        out, err = proc.communicate(timeout=self.tool_timeout)
                        execution_time = time.time() - start_time
                        if proc.returncode == 0:
                            return ToolResult(success=True, message="Outlook launched", execution_time=execution_time, return_code=proc.returncode, output=(out.decode() if out else ''))
                        else:
                            return ToolResult(success=False, message=f"Outlook returned code {proc.returncode}", execution_time=execution_time, return_code=proc.returncode, error=(err.decode() if err else ''))
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        return ToolResult(success=False, message="Outlook launch timed out", execution_time=time.time() - start_time, error="Timeout")
            except Exception as e:
                error_msg = f"Failed to launch Outlook: {e}"
                logger.error(error_msg)
                return ToolResult(success=False, message=error_msg, execution_time=time.time() - start_time, error=str(e))
                
        except subprocess.TimeoutExpired:
            error_msg = f"Outlook launch timed out after {self.tool_timeout} seconds"
            logger.error(error_msg)
            return ToolResult(
                success=False,
                message=error_msg,
                execution_time=time.time() - start_time,
                error="Timeout"
            )
        except Exception as e:
            error_msg = f"Failed to launch Outlook: {str(e)}"
            logger.error(error_msg)
            return ToolResult(
                success=False,
                message=error_msg,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    @handle_errors(
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.MEDIUM,
        context={'component': 'tool_invoker', 'operation': 'run_sara'},
        return_error_response=False
    )
    def _run_sara(self) -> ToolResult:
        """Launch Microsoft Support and Recovery Assistant."""
        logger.info("Launching Microsoft Support and Recovery Assistant")
        start_time = time.time()
        
        try:
            # Get SaRA path from configuration
            sara_path = self.config.paths.sara_path
            
            # Validate SaRA executable exists
            if not Path(sara_path).exists():
                error_msg = f"SaRA executable not found at: {sara_path}"
                logger.error(error_msg)
                return ToolResult(
                    success=False,
                    message=error_msg,
                    execution_time=time.time() - start_time,
                    error="File not found"
                )
            
            # Launch SaRA - prefer startfile on Windows if installed in Programs
            try:
                if os.name == 'nt':
                    try:
                        os.startfile(sara_path)
                        execution_time = time.time() - start_time
                        return ToolResult(success=True, message="Launched SaRA", execution_time=execution_time)
                    except OSError:
                        # Fallback to Popen
                        proc = subprocess.Popen([sara_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                else:
                    proc = subprocess.Popen([sara_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                try:
                    out, err = proc.communicate(timeout=self.tool_timeout)
                    execution_time = time.time() - start_time
                    if proc.returncode == 0:
                        return ToolResult(success=True, message="SaRA launched", execution_time=execution_time, return_code=proc.returncode, output=(out.decode() if out else ''))
                    else:
                        return ToolResult(success=False, message=f"SaRA returned code {proc.returncode}", execution_time=execution_time, return_code=proc.returncode, error=(err.decode() if err else ''))
                except subprocess.TimeoutExpired:
                    proc.kill()
                    return ToolResult(success=False, message="SaRA launch timed out", execution_time=time.time() - start_time, error="Timeout")
            except Exception as e:
                error_msg = f"Failed to launch SaRA: {e}"
                logger.error(error_msg)
                return ToolResult(success=False, message=error_msg, execution_time=time.time() - start_time, error=str(e))
                
        except subprocess.TimeoutExpired:
            error_msg = f"SaRA launch timed out after {self.tool_timeout} seconds"
            logger.error(error_msg)
            return ToolResult(
                success=False,
                message=error_msg,
                execution_time=time.time() - start_time,
                error="Timeout"
            )
        except Exception as e:
            error_msg = f"Failed to launch SaRA: {str(e)}"
            logger.error(error_msg)
            return ToolResult(
                success=False,
                message=error_msg,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    def _open_edge(self) -> ToolResult:
        """Launch Microsoft Edge browser."""
        logger.info("Launching Microsoft Edge browser")
        start_time = time.time()
        
        try:
            try:
                if os.name == 'nt':
                    os.startfile('msedge.exe')
                    return ToolResult(success=True, message="Launched Edge", execution_time=time.time() - start_time)
                else:
                    proc = subprocess.Popen(['msedge'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    out, err = proc.communicate(timeout=self.tool_timeout)
                    if proc.returncode == 0:
                        return ToolResult(success=True, message='Launched Edge', execution_time=time.time() - start_time, output=(out.decode() if out else ''))
                    else:
                        return ToolResult(success=False, message=f'Edge returned {proc.returncode}', execution_time=time.time() - start_time, error=(err.decode() if err else ''))
            except Exception as e:
                return ToolResult(success=False, message=f'Failed to launch Edge: {e}', execution_time=time.time() - start_time, error=str(e))
                
        except Exception as e:
            error_msg = f"Failed to launch Microsoft Edge: {str(e)}"
            logger.error(error_msg)
            return ToolResult(
                success=False,
                message=error_msg,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    def _open_chrome(self) -> ToolResult:
        """Launch Google Chrome browser."""
        logger.info("Launching Google Chrome browser")
        start_time = time.time()
        
        try:
            try:
                if os.name == 'nt':
                    os.startfile('chrome.exe')
                    return ToolResult(success=True, message='Launched Chrome', execution_time=time.time() - start_time)
                else:
                    proc = subprocess.Popen(['chrome'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    out, err = proc.communicate(timeout=self.tool_timeout)
                    if proc.returncode == 0:
                        return ToolResult(success=True, message='Launched Chrome', execution_time=time.time() - start_time, output=(out.decode() if out else ''))
                    else:
                        return ToolResult(success=False, message=f'Chrome returned {proc.returncode}', execution_time=time.time() - start_time, error=(err.decode() if err else ''))
            except Exception as e:
                return ToolResult(success=False, message=f'Failed to launch Chrome: {e}', execution_time=time.time() - start_time, error=str(e))
                
        except Exception as e:
            error_msg = f"Failed to launch Google Chrome: {str(e)}"
            logger.error(error_msg)
            return ToolResult(
                success=False,
                message=error_msg,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    def _get_system_info(self) -> ToolResult:
        """Get system information."""
        logger.info("Collecting system information")
        start_time = time.time()
        
        try:
            # Get system information using systeminfo command
            result = subprocess.run(
                ["systeminfo"],
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.tool_timeout
            )
            
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                logger.info("System information collected successfully")
                return ToolResult(
                    success=True,
                    message="System information collected successfully",
                    execution_time=execution_time,
                    return_code=result.returncode,
                    output=result.stdout
                )
            else:
                error_msg = f"Failed to collect system information: {result.stderr}"
                logger.error(error_msg)
                return ToolResult(
                    success=False,
                    message=error_msg,
                    execution_time=execution_time,
                    return_code=result.returncode,
                    error=result.stderr
                )
                
        except Exception as e:
            error_msg = f"Failed to collect system information: {str(e)}"
            logger.error(error_msg)
            return ToolResult(
                success=False,
                message=error_msg,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    def _is_process_running(self, process_name: str) -> bool:
        """Check if a process is currently running."""
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq {process_name}"],
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            return process_name.lower() in result.stdout.lower()
        except Exception:
            return False
    
    def invoke_tool(self, tool_name: str) -> ToolResult:
        """
        Invoke a tool by name with comprehensive error handling.
        
        Args:
            tool_name: Name of the tool to invoke
            
        Returns:
            ToolResult with execution details
        """
        logger.info(f"Invoking tool: {tool_name}")
        
        if tool_name not in self.supported_tools:
            error_msg = f"Tool '{tool_name}' not found. Supported tools: {list(self.supported_tools.keys())}"
            logger.error(error_msg)
            return ToolResult(
                success=False,
                message=error_msg,
                execution_time=0,
                error="Tool not found"
            )
        
        try:
            tool_func = self.supported_tools[tool_name]
            result = tool_func()
            
            if result.success:
                logger.info(f"Tool '{tool_name}' executed successfully")
            else:
                logger.error(f"Tool '{tool_name}' failed: {result.message}")
            
            return result
            
        except Exception as e:
            error_msg = f"Unexpected error invoking tool '{tool_name}': {str(e)}"
            logger.error(error_msg)
            return ToolResult(
                success=False,
                message=error_msg,
                execution_time=0,
                error=str(e)
            )
    
    def get_supported_tools(self) -> Dict[str, str]:
        """Get list of supported tools with descriptions."""
        return {
            "open_outlook": "Launch Microsoft Outlook desktop application",
            "run_sara": "Launch Microsoft Support and Recovery Assistant",
            "open_edge": "Launch Microsoft Edge browser",
            "open_chrome": "Launch Google Chrome browser",
            "system_info": "Collect system information"
        }
    
    def set_timeout(self, timeout: int):
        """Set tool execution timeout."""
        self.tool_timeout = timeout
        logger.info(f"Tool timeout set to {timeout} seconds")

# Global tool invoker instance
_tool_invoker = None

def get_tool_invoker() -> ToolInvoker:
    """Get or create global tool invoker instance."""
    global _tool_invoker
    if _tool_invoker is None:
        _tool_invoker = ToolInvoker()
    return _tool_invoker

# Legacy function for backward compatibility
def invoke_tool(tool_name: str) -> bool:
    """
    Legacy function for backward compatibility.
    
    Args:
        tool_name: Name of the tool to invoke
        
    Returns:
        bool: True if successful, False otherwise
    """
    invoker = get_tool_invoker()
    result = invoker.invoke_tool(tool_name)
    
    if result.success:
        print(f"✅ {result.message}")
    else:
        print(f"❌ {result.message}")
    
    return result.success

# Individual tool functions for backward compatibility
def open_outlook():
    """Legacy function for backward compatibility."""
    return invoke_tool("open_outlook")

def run_sara():
    """Legacy function for backward compatibility."""
    return invoke_tool("run_sara")

if __name__ == "__main__":
    # Test the enhanced tool invoker
    invoker = ToolInvoker()
    
    print("🔧 Enhanced Tool Invoker Test")
    print("=" * 50)
    
    # Test supported tools
    print(f"Supported tools: {list(invoker.get_supported_tools().keys())}")
    print()
    
    # Test each tool
    for tool_name in invoker.get_supported_tools().keys():
        print(f"Testing {tool_name}...")
        result = invoker.invoke_tool(tool_name)
        status = "✅ SUCCESS" if result.success else "❌ FAILED"
        print(f"  {status}: {result.message}")
        print(f"  Execution time: {result.execution_time:.2f}s")
        if result.error:
            print(f"  Error: {result.error}")
        print()
