# data_validator.py
"""
Comprehensive data validation and sanitization system for RAG Agent components.
Provides robust validation for all data inputs, outputs, and internal data structures.
"""

import re
import json
import logging
from typing import Any, Dict, List, Optional, Union, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import bleach
import validators
from standardized_error_handler import (
    handle_errors, ErrorCategory, ErrorSeverity,
    handle_validation_error
)

logger = logging.getLogger(__name__)

@dataclass
class ValidationRule:
    """A validation rule definition."""
    name: str
    validator: Callable[[Any], bool]
    error_message: str
    required: bool = False
    sanitizer: Optional[Callable[[Any], Any]] = None

@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    sanitized_data: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class DataValidator:
    """Comprehensive data validation and sanitization system."""
    
    def __init__(self):
        self.validation_rules = {}
        self.sanitizers = {}
        self._initialize_default_rules()
        
        logger.info("DataValidator initialized")
    
    def _initialize_default_rules(self):
        """Initialize default validation rules."""
        
        # String validation rules
        self.add_rule(ValidationRule(
            name="non_empty_string",
            validator=lambda x: isinstance(x, str) and len(x.strip()) > 0,
            error_message="Value must be a non-empty string",
            sanitizer=lambda x: x.strip() if isinstance(x, str) else str(x).strip()
        ))
        
        self.add_rule(ValidationRule(
            name="max_length_1000",
            validator=lambda x: isinstance(x, str) and len(x) <= 1000,
            error_message="String must be 1000 characters or less",
            sanitizer=lambda x: x[:1000] if isinstance(x, str) and len(x) > 1000 else x
        ))
        
        self.add_rule(ValidationRule(
            name="max_length_5000",
            validator=lambda x: isinstance(x, str) and len(x) <= 5000,
            error_message="String must be 5000 characters or less",
            sanitizer=lambda x: x[:5000] if isinstance(x, str) and len(x) > 5000 else x
        ))
        
        # Email validation
        self.add_rule(ValidationRule(
            name="valid_email",
            validator=lambda x: isinstance(x, str) and validators.email(x),
            error_message="Invalid email format",
            sanitizer=lambda x: x.lower().strip() if isinstance(x, str) else x
        ))
        
        # URL validation
        self.add_rule(ValidationRule(
            name="valid_url",
            validator=lambda x: isinstance(x, str) and validators.url(x),
            error_message="Invalid URL format",
            sanitizer=lambda x: x.strip() if isinstance(x, str) else x
        ))
        
        # Numeric validation
        self.add_rule(ValidationRule(
            name="positive_float",
            validator=lambda x: isinstance(x, (int, float)) and x >= 0,
            error_message="Value must be a positive number",
            sanitizer=lambda x: float(x) if isinstance(x, (int, str)) else x
        ))
        
        self.add_rule(ValidationRule(
            name="positive_int",
            validator=lambda x: isinstance(x, int) and x > 0,
            error_message="Value must be a positive integer",
            sanitizer=lambda x: int(float(x)) if isinstance(x, (str, float)) else x
        ))
        
        # List validation
        self.add_rule(ValidationRule(
            name="non_empty_list",
            validator=lambda x: isinstance(x, list) and len(x) > 0,
            error_message="Value must be a non-empty list"
        ))
        
        self.add_rule(ValidationRule(
            name="max_list_length_100",
            validator=lambda x: isinstance(x, list) and len(x) <= 100,
            error_message="List must contain 100 items or fewer",
            sanitizer=lambda x: x[:100] if isinstance(x, list) and len(x) > 100 else x
        ))
        
        # Dictionary validation
        self.add_rule(ValidationRule(
            name="non_empty_dict",
            validator=lambda x: isinstance(x, dict) and len(x) > 0,
            error_message="Value must be a non-empty dictionary"
        ))
        
        # File path validation
        self.add_rule(ValidationRule(
            name="valid_file_path",
            validator=lambda x: isinstance(x, str) and self._is_valid_file_path(x),
            error_message="Invalid file path",
            sanitizer=lambda x: str(Path(x).resolve()) if isinstance(x, str) else x
        ))
        
        # JSON validation
        self.add_rule(ValidationRule(
            name="valid_json",
            validator=lambda x: self._is_valid_json(x),
            error_message="Invalid JSON format"
        ))
        
        # HTML sanitization
        self.add_rule(ValidationRule(
            name="safe_html",
            validator=lambda x: isinstance(x, str),
            error_message="Value must be a string",
            sanitizer=lambda x: self._sanitize_html(x) if isinstance(x, str) else str(x)
        ))
        
        # SQL injection prevention
        self.add_rule(ValidationRule(
            name="sql_safe",
            validator=lambda x: isinstance(x, str) and not self._contains_sql_injection(x),
            error_message="Input contains potentially dangerous SQL patterns",
            sanitizer=lambda x: self._sanitize_sql(x) if isinstance(x, str) else str(x)
        ))
        
        # XSS prevention
        self.add_rule(ValidationRule(
            name="xss_safe",
            validator=lambda x: isinstance(x, str) and not self._contains_xss(x),
            error_message="Input contains potentially dangerous XSS patterns",
            sanitizer=lambda x: self._sanitize_xss(x) if isinstance(x, str) else str(x)
        ))
        
        logger.info("Default validation rules initialized")
    
    def add_rule(self, rule: ValidationRule):
        """Add a custom validation rule."""
        self.validation_rules[rule.name] = rule
        logger.debug(f"Added validation rule: {rule.name}")
    
    def remove_rule(self, rule_name: str):
        """Remove a validation rule."""
        if rule_name in self.validation_rules:
            del self.validation_rules[rule_name]
            logger.debug(f"Removed validation rule: {rule_name}")
    
    def validate(self, data: Any, rules: List[str], sanitize: bool = True) -> ValidationResult:
        """
        Validate data against specified rules.
        
        Args:
            data: Data to validate
            rules: List of rule names to apply
            sanitize: Whether to apply sanitizers
            
        Returns:
            ValidationResult with validation status and any errors
        """
        result = ValidationResult(is_valid=True)
        sanitized_data = data
        
        for rule_name in rules:
            if rule_name not in self.validation_rules:
                result.warnings.append(f"Unknown validation rule: {rule_name}")
                continue
            
            rule = self.validation_rules[rule_name]
            
            # Apply sanitizer if available and requested
            if sanitize and rule.sanitizer:
                try:
                    sanitized_data = rule.sanitizer(sanitized_data)
                except Exception as e:
                    result.warnings.append(f"Sanitization failed for rule {rule_name}: {str(e)}")
            
            # Apply validator
            try:
                if not rule.validator(sanitized_data):
                    result.is_valid = False
                    result.errors.append(f"{rule_name}: {rule.error_message}")
                    
                    if rule.required:
                        break  # Stop validation if required rule fails
            except Exception as e:
                result.is_valid = False
                result.errors.append(f"{rule_name}: Validation error - {str(e)}")
        
        result.sanitized_data = sanitized_data
        result.metadata["rules_applied"] = rules
        result.metadata["sanitization_enabled"] = sanitize
        
        return result
    
    def validate_rag_query(self, query: str) -> ValidationResult:
        """Validate RAG query input."""
        return self.validate(
            query,
            ["non_empty_string", "max_length_1000", "safe_html", "xss_safe"],
            sanitize=True
        )
    
    def validate_api_request(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate API request data."""
        result = ValidationResult(is_valid=True)
        
        # Validate message field
        if "message" in data:
            message_result = self.validate_rag_query(data["message"])
            if not message_result.is_valid:
                result.is_valid = False
                result.errors.extend(message_result.errors)
            result.warnings.extend(message_result.warnings)
        
        # Validate context field
        if "context" in data:
            if not isinstance(data["context"], list):
                result.is_valid = False
                result.errors.append("Context must be a list")
            else:
                for i, item in enumerate(data["context"]):
                    if not isinstance(item, dict):
                        result.is_valid = False
                        result.errors.append(f"Context item {i} must be a dictionary")
                    elif "role" not in item or "content" not in item:
                        result.is_valid = False
                        result.errors.append(f"Context item {i} must have 'role' and 'content' fields")
        
        # Validate browser_mode field
        if "browser_mode" in data:
            if not isinstance(data["browser_mode"], bool):
                result.is_valid = False
                result.errors.append("browser_mode must be a boolean")
        
        return result
    
    def validate_troubleshooting_entry(self, entry: Dict[str, Any]) -> ValidationResult:
        """Validate troubleshooting entry data."""
        result = ValidationResult(is_valid=True)
        
        # Required fields
        required_fields = ["title", "symptoms", "fix_steps"]
        for field in required_fields:
            if field not in entry:
                result.is_valid = False
                result.errors.append(f"Missing required field: {field}")
            elif not entry[field]:
                result.is_valid = False
                result.errors.append(f"Empty value for required field: {field}")
        
        # Validate title
        if "title" in entry:
            title_result = self.validate(
                entry["title"],
                ["non_empty_string", "max_length_500", "safe_html"],
                sanitize=True
            )
            if not title_result.is_valid:
                result.is_valid = False
                result.errors.extend(title_result.errors)
        
        # Validate symptoms
        if "symptoms" in entry:
            if not isinstance(entry["symptoms"], list):
                result.is_valid = False
                result.errors.append("Symptoms must be a list")
            else:
                for i, symptom in enumerate(entry["symptoms"]):
                    symptom_result = self.validate(
                        symptom,
                        ["non_empty_string", "max_length_500", "safe_html"],
                        sanitize=True
                    )
                    if not symptom_result.is_valid:
                        result.is_valid = False
                        result.errors.append(f"Symptom {i}: {', '.join(symptom_result.errors)}")
        
        # Validate fix_steps
        if "fix_steps" in entry:
            if not isinstance(entry["fix_steps"], list):
                result.is_valid = False
                result.errors.append("Fix steps must be a list")
            else:
                for i, step in enumerate(entry["fix_steps"]):
                    step_result = self.validate(
                        step,
                        ["non_empty_string", "max_length_1000", "safe_html"],
                        sanitize=True
                    )
                    if not step_result.is_valid:
                        result.is_valid = False
                        result.errors.append(f"Fix step {i}: {', '.join(step_result.errors)}")
        
        # Validate optional fields
        if "error_code" in entry and entry["error_code"]:
            error_code_result = self.validate(
                entry["error_code"],
                ["non_empty_string", "max_length_100"],
                sanitize=True
            )
            if not error_code_result.is_valid:
                result.warnings.extend(error_code_result.errors)
        
        if "severity" in entry and entry["severity"]:
            if entry["severity"] not in ["low", "medium", "high", "critical"]:
                result.warnings.append("Invalid severity level")
        
        if "tags" in entry and entry["tags"]:
            if not isinstance(entry["tags"], list):
                result.warnings.append("Tags must be a list")
            else:
                for i, tag in enumerate(entry["tags"]):
                    tag_result = self.validate(
                        tag,
                        ["non_empty_string", "max_length_100"],
                        sanitize=True
                    )
                    if not tag_result.is_valid:
                        result.warnings.append(f"Tag {i}: {', '.join(tag_result.errors)}")
        
        return result
    
    def validate_config_data(self, config_data: Dict[str, Any]) -> ValidationResult:
        """Validate configuration data."""
        result = ValidationResult(is_valid=True)
        
        # Validate required config sections
        required_sections = ["llm", "rag", "security"]
        for section in required_sections:
            if section not in config_data:
                result.is_valid = False
                result.errors.append(f"Missing required config section: {section}")
        
        # Validate LLM config
        if "llm" in config_data:
            llm_config = config_data["llm"]
            if "model_name" not in llm_config:
                result.is_valid = False
                result.errors.append("LLM config missing model_name")
            
            if "base_url" in llm_config:
                url_result = self.validate(llm_config["base_url"], ["valid_url"])
                if not url_result.is_valid:
                    result.warnings.extend(url_result.errors)
        
        # Validate RAG config
        if "rag" in config_data:
            rag_config = config_data["rag"]
            if "embedding_model" not in rag_config:
                result.is_valid = False
                result.errors.append("RAG config missing embedding_model")
            
            if "index_path" in rag_config:
                path_result = self.validate(rag_config["index_path"], ["valid_file_path"])
                if not path_result.is_valid:
                    result.warnings.extend(path_result.errors)
        
        # Validate security config
        if "security" in config_data:
            security_config = config_data["security"]
            if "secret_key" not in security_config:
                result.is_valid = False
                result.errors.append("Security config missing secret_key")
            elif len(security_config["secret_key"]) < 32:
                result.warnings.append("Secret key should be at least 32 characters long")
        
        return result
    
    # Helper methods for specific validations
    
    def _is_valid_file_path(self, path: str) -> bool:
        """Check if path is a valid file path."""
        try:
            Path(path).resolve()
            return True
        except (OSError, ValueError):
            return False
    
    def _is_valid_json(self, data: Any) -> bool:
        """Check if data is valid JSON."""
        try:
            if isinstance(data, str):
                json.loads(data)
            elif isinstance(data, (dict, list)):
                json.dumps(data)
            else:
                return False
            return True
        except (json.JSONDecodeError, TypeError):
            return False
    
    def _sanitize_html(self, text: str) -> str:
        """Sanitize HTML content."""
        # Allowed tags for rich text content
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        allowed_attributes = {}
        
        return bleach.clean(text, tags=allowed_tags, attributes=allowed_attributes, strip=True)
    
    def _contains_sql_injection(self, text: str) -> bool:
        """Check for SQL injection patterns."""
        sql_patterns = [
            r'(union\s+select|select\s+.*\s+from)',
            r'(insert\s+into|update\s+.*\s+set)',
            r'(delete\s+from|drop\s+table)',
            r'(exec\s*\(|execute\s*\()',
            r'(\'\s*or\s*\'|\"\s*or\s*\")',
            r'(\'\s*;\s*--|\"\s*;\s*--)'
        ]
        
        text_lower = text.lower()
        for pattern in sql_patterns:
            if re.search(pattern, text_lower):
                return True
        return False
    
    def _sanitize_sql(self, text: str) -> str:
        """Sanitize text to prevent SQL injection."""
        # Remove or escape dangerous characters
        dangerous_chars = [';', '--', '/*', '*/', "'", '"', '\\']
        for char in dangerous_chars:
            text = text.replace(char, '')
        return text
    
    def _contains_xss(self, text: str) -> bool:
        """Check for XSS patterns."""
        xss_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'vbscript:',
            r'onload\s*=',
            r'onerror\s*=',
            r'onclick\s*=',
            r'onmouseover\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>'
        ]
        
        text_lower = text.lower()
        for pattern in xss_patterns:
            if re.search(pattern, text_lower):
                return True
        return False
    
    def _sanitize_xss(self, text: str) -> str:
        """Sanitize text to prevent XSS."""
        # Use bleach for comprehensive XSS prevention
        return bleach.clean(text, tags=[], attributes={}, strip=True)

class RAGDataValidator:
    """Specialized validator for RAG-specific data structures."""
    
    def __init__(self):
        self.validator = DataValidator()
        self._initialize_rag_rules()
    
    def _initialize_rag_rules(self):
        """Initialize RAG-specific validation rules."""
        
        # Embedding validation
        self.validator.add_rule(ValidationRule(
            name="valid_embedding",
            validator=lambda x: isinstance(x, (list, tuple)) and len(x) > 0 and all(isinstance(i, (int, float)) for i in x),
            error_message="Embedding must be a list of numbers",
            sanitizer=lambda x: list(map(float, x)) if isinstance(x, (list, tuple)) else x
        ))
        
        # Relevance score validation
        self.validator.add_rule(ValidationRule(
            name="valid_relevance_score",
            validator=lambda x: isinstance(x, (int, float)) and 0 <= x <= 1,
            error_message="Relevance score must be between 0 and 1",
            sanitizer=lambda x: max(0, min(1, float(x))) if isinstance(x, (int, float, str)) else x
        ))
        
        # Search result validation
        self.validator.add_rule(ValidationRule(
            name="valid_search_result",
            validator=lambda x: isinstance(x, dict) and "title" in x and "content" in x,
            error_message="Search result must be a dictionary with title and content"
        ))
    
    @handle_errors(
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.MEDIUM,
        context={'component': 'rag_data_validator', 'operation': 'validate_query'},
        return_error_response=False
    )
    def validate_query(self, query: str) -> ValidationResult:
        """Validate RAG query."""
        return self.validator.validate_rag_query(query)
    
    @handle_errors(
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.MEDIUM,
        context={'component': 'rag_data_validator', 'operation': 'validate_embedding'},
        return_error_response=False
    )
    def validate_embedding(self, embedding: List[float]) -> ValidationResult:
        """Validate embedding vector."""
        return self.validator.validate(embedding, ["valid_embedding"])
    
    @handle_errors(
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.MEDIUM,
        context={'component': 'rag_data_validator', 'operation': 'validate_search_result'},
        return_error_response=False
    )
    def validate_search_result(self, result: Dict[str, Any]) -> ValidationResult:
        """Validate search result."""
        validation_result = self.validator.validate(result, ["valid_search_result"])
        
        if validation_result.is_valid:
            # Validate individual fields
            if "title" in result:
                title_result = self.validator.validate(
                    result["title"],
                    ["non_empty_string", "max_length_500", "safe_html"],
                    sanitize=True
                )
                if not title_result.is_valid:
                    validation_result.warnings.extend(title_result.errors)
            
            if "content" in result:
                content_result = self.validator.validate(
                    result["content"],
                    ["non_empty_string", "max_length_5000", "safe_html"],
                    sanitize=True
                )
                if not content_result.is_valid:
                    validation_result.warnings.extend(content_result.errors)
            
            if "relevance_score" in result:
                score_result = self.validator.validate(
                    result["relevance_score"],
                    ["valid_relevance_score"],
                    sanitize=True
                )
                if not score_result.is_valid:
                    validation_result.warnings.extend(score_result.errors)
        
        return validation_result
    
    @handle_errors(
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.MEDIUM,
        context={'component': 'rag_data_validator', 'operation': 'validate_troubleshooting_entry'},
        return_error_response=False
    )
    def validate_troubleshooting_entry(self, entry: Dict[str, Any]) -> ValidationResult:
        """Validate troubleshooting entry."""
        return self.validator.validate_troubleshooting_entry(entry)

# Global validator instances
_data_validator = None
_rag_data_validator = None

def get_data_validator() -> DataValidator:
    """Get or create global data validator."""
    global _data_validator
    if _data_validator is None:
        _data_validator = DataValidator()
    return _data_validator

def get_rag_data_validator() -> RAGDataValidator:
    """Get or create global RAG data validator."""
    global _rag_data_validator
    if _rag_data_validator is None:
        _rag_data_validator = RAGDataValidator()
    return _rag_data_validator

# Decorator for automatic validation
def validate_input(rules: List[str], sanitize: bool = True):
    """Decorator to automatically validate function inputs."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            validator = get_data_validator()
            
            # Validate positional arguments
            for i, arg in enumerate(args):
                if isinstance(arg, str):
                    result = validator.validate(arg, rules, sanitize)
                    if not result.is_valid:
                        raise ValueError(f"Validation failed for argument {i}: {', '.join(result.errors)}")
            
            # Validate keyword arguments
            for key, value in kwargs.items():
                if isinstance(value, str):
                    result = validator.validate(value, rules, sanitize)
                    if not result.is_valid:
                        raise ValueError(f"Validation failed for parameter {key}: {', '.join(result.errors)}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

if __name__ == "__main__":
    # Test the data validation system
    print("🔍 Data Validator Test")
    print("=" * 50)
    
    # Initialize validators
    validator = get_data_validator()
    rag_validator = get_rag_data_validator()
    
    # Test string validation
    print("Testing string validation...")
    test_strings = [
        "Valid string",
        "   ",
        "",
        "x" * 1001,
        "<script>alert('xss')</script>",
        "SELECT * FROM users; --"
    ]
    
    for test_str in test_strings:
        result = validator.validate(test_str, ["non_empty_string", "max_length_1000", "safe_html", "xss_safe"])
        status = "✅ VALID" if result.is_valid else "❌ INVALID"
        print(f"  '{test_str[:50]}...': {status}")
        if not result.is_valid:
            print(f"    Errors: {result.errors}")
        if result.warnings:
            print(f"    Warnings: {result.warnings}")
    
    # Test RAG query validation
    print("\nTesting RAG query validation...")
    test_queries = [
        "Outlook won't open",
        "",
        "x" * 1001,
        "<script>alert('test')</script>"
    ]
    
    for query in test_queries:
        result = rag_validator.validate_query(query)
        status = "✅ VALID" if result.is_valid else "❌ INVALID"
        print(f"  '{query[:50]}...': {status}")
        if not result.is_valid:
            print(f"    Errors: {result.errors}")
    
    # Test troubleshooting entry validation
    print("\nTesting troubleshooting entry validation...")
    test_entry = {
        "title": "Outlook Startup Issue",
        "symptoms": ["Won't open", "Error message appears"],
        "fix_steps": ["Restart Outlook", "Check for updates"],
        "severity": "high",
        "tags": ["outlook", "startup"]
    }
    
    result = rag_validator.validate_troubleshooting_entry(test_entry)
    status = "✅ VALID" if result.is_valid else "❌ INVALID"
    print(f"  Troubleshooting entry: {status}")
    if not result.is_valid:
        print(f"    Errors: {result.errors}")
    if result.warnings:
        print(f"    Warnings: {result.warnings}")
    
    print("\n✅ Data validation test completed")
