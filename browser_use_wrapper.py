# browser_use_wrapper.py
"""
Wrapper for browser-use web automation
Integrates browser-use/web-ui for shopping and web search tasks
"""

import logging
import os
import asyncio
from typing import Dict, Optional, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import browser-use components
try:
    from browser_use import Agent, Browser, ChatGoogle
    from browser_use.agent.views import AgentHistoryList
    BROWSER_USE_AVAILABLE = True
    logger.info("browser-use components imported successfully")
    
except ImportError as e:
    BROWSER_USE_AVAILABLE = False
    logger.warning(f"browser-use not available: {e}")
    Agent = None
    Browser = None
    ChatGoogle = None


class BrowserUseWrapper:
    """
    Wrapper class for browser-use automation
    Handles web search, shopping, and automation tasks
    """
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        """
        Initialize the browser-use wrapper
        
        Args:
            gemini_api_key: Google Gemini API key for LLM
        """
        self.available = BROWSER_USE_AVAILABLE
        self.gemini_api_key = gemini_api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        self.browser = None
        self.agent = None
        
        if not self.available:
            logger.warning("Browser-use not available. Web automation features disabled.")
            return
        
        if not self.gemini_api_key:
            logger.warning("No Gemini API key found. Browser-use features will be limited.")
        
        logger.info("BrowserUseWrapper initialized")
    
    async def initialize_browser(self, headless: bool = False):
        """
        Initialize the browser instance
        
        Args:
            headless: Run browser in headless mode (default: False for visible browser)
        """
        if not self.available:
            raise RuntimeError("Browser-use is not available")
        
        try:
            # Browser is BrowserSession - pass parameters directly
            self.browser = Browser(
                headless=headless,
                disable_security=False,  # Keep security enabled
                keep_alive=True,  # Keep browser open after task completes
            )
            logger.info(f"Browser initialized (headless={headless}, keep_alive=True)")
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise
    
    async def search_and_automate(
        self, 
        task: str, 
        max_steps: int = 30
    ) -> Dict[str, Any]:
        """
        Execute a web search or automation task
        
        Args:
            task: Task description (e.g., "Search for best laptops under $1000")
            max_steps: Maximum number of automation steps
            
        Returns:
            Result dict with status, content, and metadata
        """
        if not self.available:
            return {
                'success': False,
                'error': 'Browser automation not available. Please install browser-use.',
                'message': 'Browser-use module is not installed.'
            }
        
        if not self.gemini_api_key:
            return {
                'success': False,
                'error': 'No Gemini API key configured',
                'message': 'Please set GEMINI_API_KEY or GOOGLE_API_KEY environment variable.'
            }
        
        browser_instance = None
        agent_instance = None
        
        try:
            # Always create a fresh browser instance for each task
            # This prevents state issues from previous tasks
            browser_instance = Browser(
                headless=False,
                disable_security=False,
                keep_alive=True,  # Keep browser open after task
            )
            logger.info("Created fresh browser instance for task")
            
            # Create Gemini LLM instance using browser-use's ChatGoogle
            # Using gemini-2.0-flash-exp (higher quota than other exp models)
            llm = ChatGoogle(
                model="gemini-2.0-flash-exp",
                api_key=self.gemini_api_key,
                temperature=0.5
            )
            
            # Create browser agent with browser_session parameter and optimized settings
            agent_instance = Agent(
                task=task,
                llm=llm,
                browser_session=browser_instance,
                use_vision=True,  # Enable vision to see the page better
                max_actions_per_step=10,  # Allow multiple actions per step
                max_failures=3,  # Allow retries
            )
            
            logger.info(f"Starting browser automation task: {task}")
            
            # Run the agent
            history: AgentHistoryList = await agent_instance.run(max_steps=max_steps)
            
            # Extract results
            result_text = self._extract_result_from_history(history)
            
            return {
                'success': True,
                'content': result_text,
                'task': task,
                'steps_taken': len(history.history),
                'max_steps': max_steps,
                'metadata': {
                    'model': 'gemini-2.0-flash-exp',
                    'completed': history.is_done(),
                    'final_url': history.history[-1].state.url if history.history else None
                }
            }
            
        except Exception as e:
            logger.error(f"Browser automation failed: {e}", exc_info=True)
            
            # Check for quota exceeded error
            error_str = str(e)
            if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str or 'quota' in error_str.lower():
                return {
                    'success': False,
                    'error': 'Gemini API quota exceeded',
                    'task': task,
                    'message': '⚠️ Daily API quota reached (50 requests/day). The quota resets every 24 hours. Please try again later or upgrade to a paid plan for unlimited usage. Visit: https://ai.google.dev/pricing'
                }
            
            return {
                'success': False,
                'error': str(e),
                'task': task,
                'message': f'Failed to complete automation task: {str(e)}'
            }
        
        finally:
            # Don't close agent or browser - keep everything open
            # The browser window and session remain active for user interaction
            if agent_instance:
                logger.info("Agent and browser left open for user review")
            
            # Note: Browser stays open with keep_alive=True
            # User can manually close the browser window when done
    
    async def shop_online(
        self, 
        product: str, 
        max_price: Optional[float] = None,
        website: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for products and find best deals
        
        Args:
            product: Product name/description
            max_price: Maximum price filter
            website: Specific website to search (e.g., "amazon.com")
            
        Returns:
            Shopping results dict
        """
        # Build detailed task description with explicit steps and clear goal
        if website:
            # Direct navigation to website with explicit steps
            if 'amazon' in website.lower():
                # Determine correct Amazon domain
                if '.in' in website or 'india' in product.lower():
                    base_url = "https://www.amazon.in"
                    currency = "₹"
                else:
                    base_url = "https://www.amazon.com"
                    currency = "$"
                
                # Build comprehensive task with clear extraction goal
                task = f"""Your goal is to find and extract product information from Amazon for: "{product}"

Step-by-step instructions:
1. Navigate directly to {base_url}
2. Locate the main search bar (usually has id="twotabsearchtextbox")
3. Click on the search bar to focus it
4. Type the search term: {product}
5. Press Enter or click the search button (magnifying glass icon)
6. Wait for the search results page to fully load
7. Scroll down slightly to see multiple products
8. From the search results, extract information for the TOP 5 products:
   - Product name/title
   - Price (in {currency})
   - Star rating (if available)
   - Number of reviews (if available)
9. Format the results as a clear list with all details

IMPORTANT: You must complete ALL steps and return the actual product information. Do not stop after just navigating to the website."""
            
            elif 'asda' in website.lower():
                task = f"""Your goal is to find and extract product information from ASDA (UK supermarket) for: "{product}"

Step-by-step instructions:
1. Navigate directly to https://groceries.asda.com/
2. Find the search bar (usually at the top of the page)
3. Click on the search bar and type: {product}
4. Press Enter or click the search button
5. Wait for search results to load
6. Extract information for the TOP 5 products:
   - Product name/title
   - Price (in £)
   - Unit price if available (e.g., £ per kg)
   - Product image/description
7. Format results as a clear list with all details

IMPORTANT: Complete all steps and return actual product information from ASDA."""
            
            elif 'tesco' in website.lower():
                task = f"""Your goal is to find and extract product information from Tesco (UK supermarket) for: "{product}"

Step-by-step instructions:
1. Navigate to https://www.tesco.com/groceries/
2. Find and click the search bar
3. Type: {product}
4. Press Enter or click search
5. Wait for results to load
6. Extract TOP 5 products with names, prices (£), and availability
7. Format as a clear list

IMPORTANT: Return actual product information from Tesco."""
            
            elif 'walmart' in website.lower():
                task = f"""Search for "{product}" on https://www.walmart.com and extract the top 5 products with names, prices ($), and ratings."""
            
            elif 'target' in website.lower():
                task = f"""Search for "{product}" on https://www.target.com and extract the top 5 products with names, prices ($), and availability."""
            
            else:
                task = f"""Search for "{product}" on {website} and extract the top 5 product results with names and prices."""
        else:
            task = f"""Search for "{product}" on Amazon.com and extract the top 5 product results with names, prices, and ratings."""
        
        # Add price filter instruction if specified
        if max_price:
            currency = "₹" if (website and '.in' in website) else "$"
            task += f"\n\nADDITIONAL FILTER: Only include products priced under {currency}{max_price}. Skip products above this price."
        
        # Use higher max_steps for shopping tasks as they require multiple interactions
        # Shopping tasks typically need: navigate (1) + search (2-3) + wait (1-2) + scroll (2-3) + extract (10-15) = ~20-25 steps
        return await self.search_and_automate(task, max_steps=60)
    
    async def web_search(
        self, 
        query: str,
        num_results: int = 5
    ) -> Dict[str, Any]:
        """
        Perform a web search and extract key information
        
        Args:
            query: Search query
            num_results: Number of results to gather
            
        Returns:
            Search results dict
        """
        task = f"Search Google for '{query}' and summarize the top {num_results} results with key information."
        return await self.search_and_automate(task, max_steps=20)
    
    async def fill_form(
        self,
        url: str,
        form_data: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Navigate to a URL and fill out a form
        
        Args:
            url: Website URL
            form_data: Dict of field names to values
            
        Returns:
            Result dict
        """
        # Convert form data to natural language instructions
        form_instructions = []
        for field, value in form_data.items():
            form_instructions.append(f"Fill '{field}' with '{value}'")
        
        task = f"Navigate to {url}, {', '.join(form_instructions)}, then submit the form."
        return await self.search_and_automate(task, max_steps=25)
    
    def _extract_result_from_history(self, history: Any) -> str:
        """
        Extract meaningful results from agent history
        
        Args:
            history: Agent history object
            
        Returns:
            Formatted result string
        """
        if not history or not history.history:
            return "No results found."
        
        results = []
        actions_taken = []
        
        # Extract content and actions from all steps
        for i, step in enumerate(history.history):
            # Log what actions were taken
            if hasattr(step, 'model_output') and step.model_output:
                if hasattr(step.model_output, 'action'):
                    action = step.model_output.action
                    action_name = action.__class__.__name__ if hasattr(action, '__class__') else str(action)
                    actions_taken.append(f"Step {i+1}: {action_name}")
            
            # Extract content from step results
            if hasattr(step, 'result') and step.result:
                for action_result in step.result:
                    if hasattr(action_result, 'extracted_content') and action_result.extracted_content:
                        content = action_result.extracted_content.strip()
                        if content and len(content) > 10 and content not in results:
                            results.append(content)
                    
                    # Also check for error messages
                    if hasattr(action_result, 'error') and action_result.error:
                        results.append(f"⚠️ Error encountered: {action_result.error}")
        
        # Get final result from model output
        if history.is_done() and history.history:
            final_step = history.history[-1]
            
            # Try multiple ways to get the final output
            if hasattr(final_step, 'model_output') and final_step.model_output:
                model_output = final_step.model_output
                
                # Check for completion message
                if hasattr(model_output, 'done') and hasattr(model_output, 'done_reason'):
                    if model_output.done_reason:
                        results.append(f"✅ Task completed: {model_output.done_reason}")
                
                # Check for current state summary
                if hasattr(model_output, 'current_state'):
                    state = model_output.current_state
                    if hasattr(state, 'summary') and state.summary:
                        results.append(f"📋 Summary: {state.summary}")
                    if hasattr(state, 'evaluation_previous_goal') and state.evaluation_previous_goal:
                        results.append(f"📊 Evaluation: {state.evaluation_previous_goal}")
            
            # Get final URL and page info
            if hasattr(final_step, 'state'):
                final_state = final_step.state
                final_url = getattr(final_state, 'url', 'unknown')
                
                if final_url and final_url != 'about:blank':
                    results.append(f"🌐 Final page: {final_url}")
                    
                    # Try to get page content or title
                    if hasattr(final_state, 'items') and final_state.items:
                        results.append(f"📄 Page has {len(final_state.items)} interactive elements")
        
        # If we got meaningful results, return them
        if results:
            return "\n\n".join(results)
        
        # Fallback: provide activity summary
        summary_parts = []
        summary_parts.append(f"🤖 Browser automation completed {len(history.history)} steps")
        
        if actions_taken:
            summary_parts.append(f"\n📝 Actions taken:\n" + "\n".join(actions_taken[-5:]))  # Last 5 actions
        
        if history.history:
            final_url = getattr(history.history[-1].state, 'url', 'unknown')
            if final_url != 'about:blank':
                summary_parts.append(f"\n🌐 Final page: {final_url}")
            else:
                summary_parts.append(f"\n⚠️ Browser closed or navigation incomplete")
        
        summary_parts.append(f"\n💡 Tip: The browser window should still be open for you to view the results")
        
        return "\n".join(summary_parts)
    
    async def close(self):
        """Close the browser and cleanup resources"""
        if self.browser:
            try:
                await self.browser.close()
                logger.info("Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
    
    def is_available(self) -> bool:
        """Check if browser-use is available"""
        return self.available and self.gemini_api_key is not None


# Singleton instance
_browser_wrapper_instance = None


def get_browser_use_wrapper() -> BrowserUseWrapper:
    """Get or create the singleton BrowserUseWrapper instance"""
    global _browser_wrapper_instance
    if _browser_wrapper_instance is None:
        _browser_wrapper_instance = BrowserUseWrapper()
    return _browser_wrapper_instance


async def execute_web_task(task: str, task_type: str = "search") -> Dict[str, Any]:
    """
    Helper function to execute web automation tasks
    
    Args:
        task: Task description or query
        task_type: Type of task ('search', 'shop', 'automate')
        
    Returns:
        Result dict
    """
    wrapper = get_browser_use_wrapper()
    
    if not wrapper.is_available():
        return {
            'success': False,
            'error': 'Browser automation not available',
            'message': 'Please install browser-use and configure Gemini API key.'
        }
    
    if task_type == "shop":
        # Parse shopping query to extract product, website, and price
        import re
        
        # Extract website (amazon, asda, tesco, walmart, etc.)
        website = None
        task_lower = task.lower()
        # Check for Amazon India variations
        if 'amazon.in' in task_lower or 'amazon dot in' in task_lower or 'amazon india' in task_lower:
            website = 'amazon.in'
        elif 'amazon.com' in task_lower or 'amazon dot com' in task_lower or 'amazon' in task_lower:
            website = 'amazon.com'
        elif 'asda' in task_lower:
            website = 'asda.com'
        elif 'tesco' in task_lower:
            website = 'tesco.com'
        elif 'walmart' in task_lower:
            website = 'walmart.com'
        elif 'target' in task_lower:
            website = 'target.com'
        
        # Extract price limit (e.g., "under 5k", "under 50000")
        max_price = None
        price_match = re.search(r'under\s+(\d+k?)\s*(inr|rupees|rs)?', task.lower())
        if price_match:
            price_str = price_match.group(1)
            if 'k' in price_str.lower():
                max_price = float(price_str.lower().replace('k', '')) * 1000
            else:
                max_price = float(price_str)
        
        # Extract product name (remove common prefixes and price info)
        product = task.lower()
        # Remove "open" command
        product = re.sub(r'\b(open)\s+', '', product, flags=re.IGNORECASE).strip()
        # Remove action words including "search for", "find", etc.
        product = re.sub(r'\b(search|find|look|get|buy)\s+(for\s+)?', '', product, flags=re.IGNORECASE).strip()
        # Remove "for" at the beginning if left over
        product = re.sub(r'^\s*for\s+', '', product, flags=re.IGNORECASE).strip()
        # Remove website references (including "dot in" and "dot com" variations)
        product = re.sub(r'\b(on\s+)?amazon(\s+dot\s+in|\s+dot\s+com|\.in|\.com)?\b', '', product, flags=re.IGNORECASE).strip()
        product = re.sub(r'\b(on\s+)?(asda|tesco|walmart|target)(\s+dot\s+com|\.com)?\b', '', product, flags=re.IGNORECASE).strip()
        # Remove "and" at the beginning if left over
        product = re.sub(r'^\s*and\s+', '', product, flags=re.IGNORECASE).strip()
        # Remove price information
        product = re.sub(r'\bunder\s+\d+k?\s*(inr|rupees|rs)?\b', '', product, flags=re.IGNORECASE).strip()
        # Final cleanup - remove extra spaces and periods
        product = re.sub(r'\s+', ' ', product).strip()
        product = product.replace(' .', '').strip()
        
        return await wrapper.shop_online(product, max_price=max_price, website=website)
    elif task_type == "search":
        return await wrapper.web_search(task)
    else:
        return await wrapper.search_and_automate(task)


if __name__ == "__main__":
    # Test the wrapper
    async def test():
        logging.basicConfig(level=logging.INFO)
        
        wrapper = BrowserUseWrapper()
        
        if not wrapper.is_available():
            print("Browser-use not available. Please install:")
            print("  pip install browser-use langchain-google-genai")
            print("  Set GEMINI_API_KEY environment variable")
            return
        
        print("\n=== Browser-use Wrapper Test ===\n")
        
        # Test web search
        print("Testing web search...")
        result = await wrapper.web_search("best Python frameworks 2024")
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Results: {result['content'][:200]}...")
        
        await wrapper.close()
    
    asyncio.run(test())
