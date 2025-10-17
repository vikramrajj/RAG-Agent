"""
Action Sequence Manager - Template-based task automation
Executes pre-recorded action sequences for precision tasks without LLM page analysis

This system provides:
- Fast, precise execution of common tasks
- No need to analyze entire pages
- Consistent, reliable results
- Easy template creation and management
"""

import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ActionSequenceManager:
    """
    Manages and executes action sequence templates for precision automation.
    
    Templates are stored as JSON and define exact action sequences for common tasks.
    This approach is much faster than LLM-based page analysis for repetitive tasks.
    """
    
    def __init__(self, templates_path: str = "action_templates.json"):
        """
        Initialize the action sequence manager.
        
        Args:
            templates_path: Path to JSON file containing action templates
        """
        self.templates_path = Path(templates_path)
        self.templates: Dict[str, Dict] = {}
        self.usage_stats: Dict[str, int] = {}  # Track template usage
        self.load_templates()
    
    def load_templates(self):
        """Load action templates from JSON file"""
        if self.templates_path.exists():
            try:
                with open(self.templates_path, 'r', encoding='utf-8') as f:
                    self.templates = json.load(f)
                logger.info(f"✅ Loaded {len(self.templates)} action templates from {self.templates_path}")
            except Exception as e:
                logger.error(f"Failed to load templates: {e}")
                self.templates = {}
        else:
            logger.warning(f"⚠️ No templates found at {self.templates_path}, starting with empty library")
            self.templates = {}
    
    def match_template(self, query: str) -> Optional[str]:
        """
        Match user query to best template using keyword matching.
        
        Args:
            query: User's task description
            
        Returns:
            Template name if matched, None otherwise
        """
        query_lower = query.lower()
        
        # Check each template's keywords
        for template_name, template in self.templates.items():
            keywords = template.get('keywords', [])
            
            # Check if any keyword matches
            if any(keyword.lower() in query_lower for keyword in keywords):
                logger.info(f"✅ Matched query to template: {template_name}")
                self._record_usage(template_name)
                return template_name
        
        logger.debug(f"No template matched for query: {query}")
        return None
    
    def _record_usage(self, template_name: str):
        """Record template usage for analytics"""
        if template_name not in self.usage_stats:
            self.usage_stats[template_name] = 0
        self.usage_stats[template_name] += 1
    
    def extract_variables(self, query: str, template_name: str) -> Dict[str, str]:
        """
        Extract variable values from query for template substitution.
        
        Args:
            query: User's task description
            template_name: Name of matched template
            
        Returns:
            Dictionary mapping variable names to extracted values
        """
        template = self.templates[template_name]
        variables = {}
        query_lower = query.lower()
        
        # Get variable list from template
        var_names = template.get('variables', [])
        
        if not var_names:
            return variables
        
        # Template-specific extraction logic
        # This is simplified - in production, use LLM for better extraction
        
        if template_name == "amazon_purchase":
            # Extract product name (text after "buy", "purchase", "order")
            for keyword in ["buy", "purchase", "order", "get"]:
                if keyword in query_lower:
                    parts = query_lower.split(keyword)
                    if len(parts) > 1:
                        # Get text after keyword, remove "on amazon" suffix
                        product = parts[1].strip()
                        product = product.replace("on amazon", "").replace("from amazon", "").strip()
                        variables["PRODUCT"] = product
                        break
        
        elif template_name == "windows_uninstall":
            # Extract app name (text after "uninstall", "remove")
            for keyword in ["uninstall", "remove", "delete"]:
                if keyword in query_lower:
                    parts = query_lower.split(keyword)
                    if len(parts) > 1:
                        app_name = parts[1].strip()
                        # Clean up common suffixes
                        app_name = app_name.replace("app", "").replace("application", "").strip()
                        variables["APP_NAME"] = app_name
                        break
        
        elif template_name == "google_search":
            # Extract search query
            for keyword in ["search for", "search", "google", "find"]:
                if keyword in query_lower:
                    parts = query_lower.split(keyword)
                    if len(parts) > 1:
                        search_query = parts[1].strip()
                        search_query = search_query.replace("on google", "").strip()
                        variables["QUERY"] = search_query
                        break
        
        logger.info(f"Extracted variables: {variables}")
        return variables
    
    async def execute_template(
        self, 
        template_name: str, 
        variables: Dict[str, str],
        automation_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute action template with given variables.
        
        Args:
            template_name: Name of template to execute
            variables: Variable values to substitute
            automation_type: "browser" or "windows" (auto-detected if None)
            
        Returns:
            Execution result dictionary
        """
        if template_name not in self.templates:
            return {
                'success': False,
                'error': f'Template not found: {template_name}',
                'message': f'❌ Template "{template_name}" does not exist'
            }
        
        template = self.templates[template_name]
        steps = template['steps']
        
        # Auto-detect automation type if not specified
        if automation_type is None:
            # Check template metadata or infer from name/steps
            if 'type' in template:
                automation_type = template['type']
            elif any(keyword in template_name.lower() for keyword in ['amazon', 'google', 'website', 'browser']):
                automation_type = 'browser'
            elif any(keyword in template_name.lower() for keyword in ['windows', 'app', 'settings']):
                automation_type = 'windows'
            else:
                # Check first step to infer
                if steps and steps[0].get('action') in ['goto', 'navigate']:
                    automation_type = 'browser'
                else:
                    automation_type = 'windows'
        
        logger.info(f"🚀 Executing template: {template_name} ({automation_type}, {len(steps)} steps)")
        
        try:
            if automation_type == "browser":
                result = await self._execute_browser_template(template_name, steps, variables)
            else:
                result = self._execute_windows_template(template_name, steps, variables)
            
            return result
        
        except Exception as e:
            logger.error(f"Template execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f'❌ Template execution error: {str(e)}'
            }
    
    async def _execute_browser_template(
        self, 
        template_name: str,
        steps: List[Dict], 
        variables: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Execute browser automation template using browser_use_wrapper.
        
        Converts template steps into detailed instructions for the browser agent.
        """
        try:
            from browser_use_wrapper import get_browser_use_wrapper
        except ImportError:
            return {
                'success': False,
                'error': 'browser_use_wrapper not available',
                'message': '❌ Browser automation not available'
            }
        
        browser_wrapper = get_browser_use_wrapper()
        
        # Build detailed step-by-step instructions
        instructions = []
        for i, step in enumerate(steps, 1):
            action = step['action']
            
            if action == "goto" or action == "navigate":
                url = step['url']
                instructions.append(f"{i}. Navigate to {url}")
            
            elif action == "click":
                target = step.get('selector', step.get('text', ''))
                # Substitute variables
                for var, value in variables.items():
                    target = target.replace(f"{{{var}}}", value)
                instructions.append(f"{i}. Click on element: {target}")
            
            elif action == "type" or action == "input":
                text = step['text']
                # Substitute variables
                for var, value in variables.items():
                    text = text.replace(f"{{{var}}}", value)
                selector = step.get('selector', 'input field')
                instructions.append(f"{i}. Type '{text}' in {selector}")
            
            elif action == "wait":
                seconds = step.get('seconds', 1)
                instructions.append(f"{i}. Wait {seconds} seconds")
            
            elif action == "scroll":
                direction = step.get('direction', 'down')
                instructions.append(f"{i}. Scroll {direction}")
            
            elif action == "submit":
                instructions.append(f"{i}. Submit the form")
            
            else:
                # Generic action
                instructions.append(f"{i}. {action}")
        
        # Create precise task instruction
        task = f"""Execute this action sequence precisely (Template: {template_name}):

STEPS TO FOLLOW:
{chr(10).join(instructions)}

IMPORTANT:
- Follow these steps EXACTLY in order
- Do not deviate from the sequence
- Complete all steps before finishing
- Report progress after each step
"""
        
        logger.info(f"Sending browser task with {len(instructions)} steps")
        result = await browser_wrapper.search_and_automate(task=task, max_steps=len(steps) * 2)
        
        # Add template info to result
        result['template'] = template_name
        result['steps_executed'] = len(steps)
        
        return result
    
    def _execute_windows_template(
        self, 
        template_name: str,
        steps: List[Dict], 
        variables: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Execute Windows automation template using windows_use_wrapper.
        
        Converts template steps into detailed instructions for the Windows agent.
        """
        try:
            from windows_use_wrapper import get_windows_wrapper
        except ImportError:
            return {
                'success': False,
                'error': 'windows_use_wrapper not available',
                'message': '❌ Windows automation not available'
            }
        
        windows_wrapper = get_windows_wrapper()
        
        # Build detailed step-by-step instructions
        instructions = []
        for i, step in enumerate(steps, 1):
            action = step['action']
            
            if action == "open":
                app = step['app']
                # Substitute variables
                for var, value in variables.items():
                    app = app.replace(f"{{{var}}}", value)
                instructions.append(f"{i}. Open {app}")
            
            elif action == "search" or action == "find":
                query = step.get('query', step.get('text', ''))
                # Substitute variables
                for var, value in variables.items():
                    query = query.replace(f"{{{var}}}", value)
                instructions.append(f"{i}. Search for: {query}")
            
            elif action == "click":
                target = step.get('text', step.get('selector', ''))
                # Substitute variables
                for var, value in variables.items():
                    target = target.replace(f"{{{var}}}", value)
                instructions.append(f"{i}. Click on: {target}")
            
            elif action == "type" or action == "input":
                text = step.get('text', step.get('value', ''))
                # Substitute variables
                for var, value in variables.items():
                    text = text.replace(f"{{{var}}}", value)
                instructions.append(f"{i}. Type: {text}")
            
            elif action == "wait":
                seconds = step.get('seconds', 1)
                instructions.append(f"{i}. Wait {seconds} seconds")
            
            elif action == "confirm":
                instructions.append(f"{i}. Confirm the action")
            
            elif action == "press":
                key = step.get('key', '')
                instructions.append(f"{i}. Press {key} key")
            
            else:
                # Generic action
                instructions.append(f"{i}. {action}")
        
        # Create precise task instruction
        task = f"""Execute this Windows action sequence precisely (Template: {template_name}):

STEPS TO FOLLOW:
{chr(10).join(instructions)}

IMPORTANT:
- Follow these steps EXACTLY in order
- Do not deviate from the sequence
- Complete all steps before finishing
"""
        
        logger.info(f"Sending Windows task with {len(instructions)} steps")
        result = windows_wrapper.execute_task(task)
        
        # Add template info to result
        result['template'] = template_name
        result['steps_executed'] = len(steps)
        
        return result
    
    def add_template(
        self, 
        name: str, 
        description: str, 
        keywords: List[str],
        steps: List[Dict],
        variables: List[str],
        automation_type: str = "browser"
    ):
        """
        Add new action template to library.
        
        Args:
            name: Unique template identifier (snake_case)
            description: Human-readable description
            keywords: List of keywords for matching queries
            steps: List of action step dictionaries
            variables: List of variable names to extract (e.g., ["PRODUCT", "QUERY"])
            automation_type: "browser" or "windows"
        """
        self.templates[name] = {
            "description": description,
            "keywords": keywords,
            "steps": steps,
            "variables": variables,
            "type": automation_type
        }
        
        self._save_templates()
        logger.info(f"✅ Added new template: {name} ({automation_type})")
    
    def remove_template(self, name: str):
        """Remove template from library"""
        if name in self.templates:
            del self.templates[name]
            self._save_templates()
            logger.info(f"🗑️ Removed template: {name}")
        else:
            logger.warning(f"Template not found: {name}")
    
    def list_templates(self) -> List[Dict[str, str]]:
        """
        Get list of all templates with metadata.
        
        Returns:
            List of template info dictionaries
        """
        templates_list = []
        for name, template in self.templates.items():
            templates_list.append({
                'name': name,
                'description': template.get('description', ''),
                'keywords': ', '.join(template.get('keywords', [])),
                'steps': len(template.get('steps', [])),
                'variables': ', '.join(template.get('variables', [])),
                'type': template.get('type', 'unknown'),
                'usage_count': self.usage_stats.get(name, 0)
            })
        return templates_list
    
    def get_template(self, name: str) -> Optional[Dict]:
        """Get template by name"""
        return self.templates.get(name)
    
    def get_usage_stats(self) -> Dict[str, int]:
        """Get template usage statistics"""
        return self.usage_stats.copy()
    
    def _save_templates(self):
        """Save templates to JSON file"""
        try:
            with open(self.templates_path, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Saved {len(self.templates)} templates to {self.templates_path}")
        except Exception as e:
            logger.error(f"Failed to save templates: {e}")


# Global instance for easy access
_sequence_manager = None

def get_sequence_manager(templates_path: str = "action_templates.json") -> ActionSequenceManager:
    """
    Get or create global ActionSequenceManager instance.
    
    Args:
        templates_path: Path to templates JSON file
        
    Returns:
        ActionSequenceManager singleton instance
    """
    global _sequence_manager
    if _sequence_manager is None:
        _sequence_manager = ActionSequenceManager(templates_path)
    return _sequence_manager


# Example usage and testing
if __name__ == "__main__":
    # Initialize manager
    manager = ActionSequenceManager()
    
    print("🎯 Action Sequence Manager Test")
    print("=" * 60)
    
    # Add example template
    manager.add_template(
        name="google_search",
        description="Search Google for a query",
        keywords=["search google", "google search", "find on google"],
        steps=[
            {"action": "goto", "url": "https://google.com"},
            {"action": "type", "selector": "textarea[name=q]", "text": "{QUERY}"},
            {"action": "press", "key": "Enter"},
            {"action": "wait", "seconds": 2}
        ],
        variables=["QUERY"],
        automation_type="browser"
    )
    
    print(f"\n✅ Created example template")
    
    # Test matching
    query = "search google for best laptops"
    matched = manager.match_template(query)
    print(f"\n🔍 Query: '{query}'")
    print(f"✅ Matched template: {matched}")
    
    # Test variable extraction
    if matched:
        variables = manager.extract_variables(query, matched)
        print(f"📝 Extracted variables: {variables}")
    
    # List all templates
    print(f"\n📋 All templates:")
    for template in manager.list_templates():
        print(f"  • {template['name']}: {template['description']}")
    
    print("\n✅ Test complete!")
