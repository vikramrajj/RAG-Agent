# web_agent.py
import logging
import json
from typing import Dict, List, Any, Optional
from functools import lru_cache

from langchain_community.chat_models import ChatOllama
from browser_use import Agent
from standardized_error_handler import (
    handle_async_errors, ErrorCategory, ErrorSeverity,
    handle_network_error, handle_external_service_error
)

logger = logging.getLogger(__name__)

# Define constants for modes
MODE_OPEN = "open"
MODE_SEARCH = "search"
MODE_SHOPPING = "shopping"

# Define task templates
TASK_TEMPLATES = {
    MODE_SEARCH: "Search for {query} on the web and summarize the top 5 results.",
    MODE_SHOPPING: "Find and list the top 5 products for {query} with prices and links."
}

class WebAgent:
    def __init__(self):
        self._llm = None
    
    @property
    def llm(self):
        """Lazy initialization of LLM."""
        if self._llm is None:
            self._llm = ChatOllama(model="llama3.1")
        return self._llm
    
    def _create_agent_result(self, mode: str, query: str) -> Dict[str, Any]:
        """Create a base agent result dictionary."""
        return {
            "status": "ok",
            "final_result": None,
            "steps": [],
            "errors": [],
            "metadata": {"mode": mode, "query": query}
        }
    
    def _handle_open_mode(self, query: str, agent_result: Dict[str, Any]) -> Dict[str, Any]:
        """Handle open mode request."""
        # Format URL properly
        url = self._format_url(query)
        
        agent_result["status"] = "success"
        agent_result["final_result"] = {
            "title": "Open in embedded browser",
            "summary": f"Opening {url} in browser...",
            "url": url
        }
        return agent_result
    
    def _format_url(self, query: str) -> str:
        """Format query into a valid URL."""
        if not isinstance(query, str):
            return "https://www.google.com"
        
        query = query.strip().lower()
        
        # Remove common prefixes like "open", "go to", "visit"
        for prefix in ['open ', 'go to ', 'visit ', 'browse ', 'navigate to ']:
            if query.startswith(prefix):
                query = query[len(prefix):].strip()
        
        # If already a valid URL, return it
        if query.startswith('http://') or query.startswith('https://'):
            return query
        
        # Handle domain names (amazon.in, google.com, etc.)
        # Add https:// and www. if not present
        if '.' in query and ' ' not in query:
            # It's likely a domain
            if not query.startswith('www.'):
                # Check if it's a known domain pattern
                parts = query.split('.')
                if len(parts) >= 2:
                    # Valid domain pattern (e.g., amazon.in, google.com)
                    query = f"www.{query}"
            return f"https://{query}"
        
        # For search queries, use Google search
        return f"https://www.google.com/search?q={query.replace(' ', '+')}"
    
    def _extract_final_result(self, history, agent_result: Dict[str, Any]) -> None:
        """Extract final result from history."""
        try:
            final = history.final_result()
            if final:
                agent_result["final_result"] = {
                    "title": "Final Result",
                    "summary": json.dumps(final, indent=2) if not isinstance(final, str) else final
                }
        except Exception as e:
            logger.debug(f"final_result extraction error: {e}")
    
    def _extract_errors(self, history, agent_result: Dict[str, Any]) -> None:
        """Extract errors from history."""
        try:
            errs = history.errors()
            if errs and any(errs):
                for err in errs:
                    agent_result["errors"].append({
                        "message": str(err),
                        "stage": "agent"
                    })
        except Exception as e:
            logger.debug(f"errors extraction error: {e}")
    
    def _extract_steps(self, history, agent_result: Dict[str, Any]) -> None:
        """Extract step-level results from history."""
        try:
            hist_list = getattr(history, "history", []) or []
            for idx, h in enumerate(hist_list):
                step_results = getattr(h, "result", []) or []
                for r in step_results:
                    details = []
                    extracted = getattr(r, "extracted_content", None)
                    error_text = getattr(r, "error", "") or ""
                    success_val = getattr(r, "success", None)
                    is_done_flag = getattr(r, "is_done", False)
                    
                    # Build details list more efficiently
                    if extracted:
                        details.append(str(extracted))
                    if error_text:
                        details.append(f"Error: {error_text}")
                    if success_val is not None:
                        details.append(f"Success: {success_val}")
                    if is_done_flag:
                        details.append("Done")
                        
                    if details:
                        agent_result["steps"].append({
                            "id": f"step-{idx}",
                            "title": "Agent Step",
                            "status": "ok" if not error_text else "error",
                            "details": "\n".join(details)
                        })
        except Exception as e:
            logger.debug(f"step-level extraction error: {e}")
    
    @handle_async_errors(
        category=ErrorCategory.EXTERNAL_SERVICE,
        severity=ErrorSeverity.MEDIUM,
        context={'component': 'web_agent', 'operation': 'execute'},
        return_error_response=False
    )
    async def execute(self, query: str, mode: str) -> Dict[str, Any]:
        """Execute web action based on mode using browser-use agent and return AgentResult."""
        agent_result = self._create_agent_result(mode, query)
        
        # Fast path for open mode
        if mode == MODE_OPEN:
            return self._handle_open_mode(query, agent_result)
            
        try:
            # Get task template based on mode
            if mode in TASK_TEMPLATES:
                task = TASK_TEMPLATES[mode].format(query=query)
            else:
                agent_result["status"] = "error"
                agent_result["errors"].append({"message": f"Invalid mode: {mode}", "stage": "init"})
                return agent_result
            
            # Create and run agent
            agent = Agent(
                task=task,
                llm=self.llm,
                use_vision=True,
                max_actions_per_step=10
            )
            history = await agent.run(max_steps=5)

            # Process results
            self._extract_final_result(history, agent_result)
            self._extract_errors(history, agent_result)
            self._extract_steps(history, agent_result)

            # Fallback final_result if none
            if agent_result["final_result"] is None:
                agent_result["final_result"] = {
                    "title": "Agent Result",
                    "summary": str(history) if history else "No result obtained."
                }

            return agent_result
            
        except Exception as e:
            logger.error(f"Error in web agent: {str(e)}")
            agent_result["status"] = "error"
            agent_result["errors"].append({"message": str(e), "stage": "exception"})
            if agent_result["final_result"] is None:
                agent_result["final_result"] = {
                    "title": "Error",
                    "summary": f"Error: {str(e)}"
                }
            return agent_result