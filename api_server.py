from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import uvicorn
from agent_bridge import AgentBridge
from tool_invoker import ToolInvoker
from outlook_login import OutlookLogin
from reasoner import EnhancedReasoner
from retriever import get_retriever
import logging

logger = logging.getLogger(__name__)

app = FastAPI()
agent_bridge = AgentBridge()
tool_invoker = ToolInvoker()

# Lazy-load reasoner to avoid slow startup
_reasoner = None

def get_reasoner():
    """Lazy-load reasoner on first use"""
    global _reasoner
    if _reasoner is None:
        retriever = get_retriever()
        _reasoner = EnhancedReasoner(retriever=retriever, model_name='llama3')
    return _reasoner

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root():
    return FileResponse("index.html")

@app.get("/sat")
async def read_sat():
    """Default SAT interface - Improved version"""
    return FileResponse("sat_ui_improved.html")

@app.get("/sat-legacy")
async def read_sat_legacy():
    """Legacy SAT interface for reference"""
    return FileResponse("sat_ui.html")

@app.get("/api/bridge/status")
async def get_status():
    return {"active": agent_bridge.check_status()}

@app.post("/api/bridge")
async def handle_message(data: dict):
    message = data.get("message", "").strip()
    smart_routing = data.get("smart_routing", True)
    force_browser = data.get("force_browser", False)
    rag_only = data.get("rag_only", False)
    model_name = data.get("model", "mistral")
    context = data.get("context", [])
    
    logger.info(f"API Bridge called - message: {message[:50]}, smart_routing: {smart_routing}, force_browser: {force_browser}")
    
    # If smart routing is enabled, process through reasoner
    if smart_routing:
        try:
            logger.info(f"Processing message with smart routing: {message[:50]}...")
            
            # Lazy-load reasoner on first use (for non-browser queries)
            reasoner = get_reasoner()
            
            # First: Quick keyword-based detection for browser queries (no LLM needed)
            browser_keywords = ['open', 'search', 'find', 'buy', 'shop', 'asda', 'tesco', 'amazon', 'walmart', 'target', 'browse', 'look for', 'purchase']
            message_lower = message.lower()
            is_browser_query = any(keyword in message_lower for keyword in browser_keywords) or force_browser
            
            logger.info(f"Keyword-based browser detection: {is_browser_query}")
            
            # Check if it's a browser query - handle directly without loading RAG
            if is_browser_query:
                # Import browser wrapper
                try:
                    from browser_use_wrapper import execute_web_task
                    
                    # Determine task type
                    task_type = 'shop' if 'shop' in message.lower() or 'buy' in message.lower() or 'find' in message.lower() else 'search'
                    
                    logger.info(f"Executing browser task: {task_type}")
                    browser_result = await execute_web_task(message, task_type=task_type)
                    
                    if browser_result.get('success'):
                        return JSONResponse(content={
                            'type': 'browser_automation',
                            'content': browser_result.get('content', ''),
                            'response': browser_result.get('content', ''),
                            'route': 'browser_use',
                            'confidence': 0.95,
                            'metadata': browser_result.get('metadata', {})
                        })
                    else:
                        # Browser task failed
                        logger.warning(f"Browser task failed: {browser_result.get('error')}")
                        return JSONResponse(content={
                            'type': 'error',
                            'content': f"Browser automation failed: {browser_result.get('error', 'Unknown error')}",
                            'metadata': {'error': browser_result.get('error')}
                        })
                        
                except ImportError as ie:
                    logger.error(f"Could not import browser_use_wrapper: {ie}")
                    return JSONResponse(content={
                        'type': 'error',
                        'content': f"Browser automation not available: {str(ie)}",
                        'metadata': {'error': str(ie)}
                    })
                except Exception as be:
                    logger.error(f"Browser execution error: {be}")
                    return JSONResponse(content={
                        'type': 'error',
                        'content': f"Browser automation error: {str(be)}",
                        'metadata': {'error': str(be)}
                    })
            
            # For non-browser queries, use full reasoner with RAG
            logger.info("Processing non-browser query with full RAG pipeline")
            response = await reasoner.process_message(message, context)
            
            # Post-process: Ensure Outlook queries have OWA link
            outlook_keywords = ['outlook', 'email not working', 'cant send', 'cant receive', 'owa']
            if any(keyword in message.lower() for keyword in outlook_keywords):
                response_content = response.get('content', '')
                # If OWA link is missing, prepend it
                if 'outlook.office.com' not in response_content:
                    owa_prompt = "🌐 **FIRST, try Outlook Web Access (OWA):**\n👉 [Click here to open OWA](https://outlook.office.com)\n\nThis helps determine if the issue is with your desktop Outlook app or your email account.\n\n---\n\n"
                    response['content'] = owa_prompt + response_content
                    logger.info("Injected OWA link into Outlook troubleshooting response")
            
            return JSONResponse(content=response)
            
        except Exception as e:
            logger.error(f"Error in smart routing: {str(e)}")
            return JSONResponse(content={
                "type": "error",
                "content": f"Error processing message: {str(e)}",
                "metadata": {"error": str(e)}
            })
    else:
        # Legacy path: direct tool invocation
        tool = data.get("tool", "chat")
        action = data.get("action")
        response = await agent_bridge.process_message(message, tool, action)
        return response

@app.post("/api/tools/sara")
async def launch_sara(data: dict):
    """Launch Microsoft Support and Recovery Assistant (SaRA) tool"""
    try:
        result = tool_invoker.invoke_tool("run_sara")
        return {
            "success": result.success,
            "message": result.message if result.success else f"Failed to launch SaRA: {result.error}",
            "execution_time": result.execution_time
        }
    except Exception as e:
        logger.error(f"Error launching SaRA: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }

@app.post("/api/tools/outlook")
async def open_outlook(data: dict):
    """Open Microsoft Outlook desktop client"""
    try:
        result = tool_invoker.invoke_tool("open_outlook")
        return {
            "success": result.success,
            "message": result.message if result.success else f"Failed to open Outlook: {result.error}",
            "execution_time": result.execution_time
        }
    except Exception as e:
        logger.error(f"Error opening Outlook: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }

@app.post("/api/run_diagnostics")
async def run_diagnostics(data: dict):
    """Run Outlook diagnostics via agent orchestrator"""
    import subprocess
    import sys
    from pathlib import Path
    
    try:
        action = data.get("action", "outlook_diagnostics")
        
        # Get the path to agent_orchestrator.py
        orchestrator_path = Path(__file__).parent / "agent_orchestrator.py"
        
        if not orchestrator_path.exists():
            return {
                "success": False,
                "message": "❌ agent_orchestrator.py not found"
            }
        
        # Run the agent orchestrator
        result = subprocess.run(
            [sys.executable, str(orchestrator_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout if result.stdout else result.stderr
        
        return {
            "success": result.returncode == 0,
            "message": f"🔧 **Outlook Diagnostics Results:**\n\n{output}\n\n{'✅ Diagnostics completed successfully' if result.returncode == 0 else '⚠️ Diagnostics completed with warnings'}",
            "output": output,
            "return_code": result.returncode
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "message": "⏱️ Diagnostics timed out (30s limit exceeded)"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Error running diagnostics: {str(e)}"
        }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await agent_bridge.register_websocket(websocket)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
