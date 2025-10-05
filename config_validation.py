"""
Configuration validation and environment management
"""

import os
import json
import yaml
from typing import Dict, Any, List, Optional, Union, Type
from dataclasses import dataclass, field
from pathlib import Path
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class ConfigError(Exception):
    """Configuration validation error"""
    pass

class Environment(Enum):
    """Application environments"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class ValidationRule:
    """Configuration validation rule"""
    required: bool = False
    type_check: Optional[Type] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    allowed_values: Optional[List[Any]] = None
    pattern: Optional[str] = None
    custom_validator: Optional[callable] = None
    default: Any = None
    description: str = ""

@dataclass
class ConfigSchema:
    """Configuration schema definition"""
    rules: Dict[str, ValidationRule] = field(default_factory=dict)
    nested_schemas: Dict[str, 'ConfigSchema'] = field(default_factory=dict)
    
    def add_rule(self, key: str, rule: ValidationRule):
        """Add validation rule"""
        self.rules[key] = rule
    
    def add_nested_schema(self, key: str, schema: 'ConfigSchema'):
        """Add nested schema"""
        self.nested_schemas[key] = schema

class ConfigValidator:
    """Configuration validator"""
    
    def __init__(self, schema: ConfigSchema):
        self.schema = schema
        self.errors: List[str] = []
    
    def validate(self, config: Dict[str, Any], path: str = "") -> bool:
        """Validate configuration against schema"""
        self.errors = []
        self._validate_dict(config, self.schema, path)
        return len(self.errors) == 0
    
    def _validate_dict(self, config: Dict[str, Any], schema: ConfigSchema, path: str):
        """Validate dictionary against schema"""
        # Check required fields
        for key, rule in schema.rules.items():
            current_path = f"{path}.{key}" if path else key
            
            if key not in config:
                if rule.required:
                    self.errors.append(f"Required field '{current_path}' is missing")
                elif rule.default is not None:
                    config[key] = rule.default
                continue
            
            self._validate_value(config[key], rule, current_path)
        
        # Check nested schemas
        for key, nested_schema in schema.nested_schemas.items():
            current_path = f"{path}.{key}" if path else key
            
            if key in config:
                if isinstance(config[key], dict):
                    self._validate_dict(config[key], nested_schema, current_path)
                else:
                    self.errors.append(f"Field '{current_path}' must be a dictionary")
    
    def _validate_value(self, value: Any, rule: ValidationRule, path: str):
        """Validate single value against rule"""
        # Type check
        if rule.type_check and not isinstance(value, rule.type_check):
            self.errors.append(
                f"Field '{path}' must be of type {rule.type_check.__name__}, "
                f"got {type(value).__name__}"
            )
            return
        
        # Numeric range checks
        if rule.min_value is not None and isinstance(value, (int, float)):
            if value < rule.min_value:
                self.errors.append(
                    f"Field '{path}' value {value} is below minimum {rule.min_value}"
                )
        
        if rule.max_value is not None and isinstance(value, (int, float)):
            if value > rule.max_value:
                self.errors.append(
                    f"Field '{path}' value {value} is above maximum {rule.max_value}"
                )
        
        # String length checks
        if rule.min_length is not None and isinstance(value, str):
            if len(value) < rule.min_length:
                self.errors.append(
                    f"Field '{path}' length {len(value)} is below minimum {rule.min_length}"
                )
        
        if rule.max_length is not None and isinstance(value, str):
            if len(value) > rule.max_length:
                self.errors.append(
                    f"Field '{path}' length {len(value)} is above maximum {rule.max_length}"
                )
        
        # Allowed values check
        if rule.allowed_values is not None:
            if value not in rule.allowed_values:
                self.errors.append(
                    f"Field '{path}' value '{value}' not in allowed values: {rule.allowed_values}"
                )
        
        # Pattern check
        if rule.pattern is not None and isinstance(value, str):
            import re
            if not re.match(rule.pattern, value):
                self.errors.append(
                    f"Field '{path}' value '{value}' does not match pattern '{rule.pattern}'"
                )
        
        # Custom validator
        if rule.custom_validator:
            try:
                if not rule.custom_validator(value):
                    self.errors.append(
                        f"Field '{path}' failed custom validation"
                    )
            except Exception as e:
                self.errors.append(
                    f"Field '{path}' custom validation error: {str(e)}"
                )

class EnvironmentManager:
    """Environment configuration manager"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.current_env = self._detect_environment()
        self.config_cache: Dict[str, Any] = {}
    
    def _detect_environment(self) -> Environment:
        """Detect current environment"""
        env_name = os.getenv("APP_ENV", "development").lower()
        
        try:
            return Environment(env_name)
        except ValueError:
            logger.warning(f"Unknown environment '{env_name}', defaulting to development")
            return Environment.DEVELOPMENT
    
    def load_config(self, config_name: str = "app") -> Dict[str, Any]:
        """Load configuration for current environment"""
        cache_key = f"{config_name}_{self.current_env.value}"
        
        if cache_key in self.config_cache:
            return self.config_cache[cache_key]
        
        config = {}
        
        # Load base config
        base_config = self._load_config_file(f"{config_name}.yaml")
        if base_config:
            config.update(base_config)
        
        # Load environment-specific config
        env_config = self._load_config_file(f"{config_name}.{self.current_env.value}.yaml")
        if env_config:
            config = self._deep_merge(config, env_config)
        
        # Override with environment variables
        config = self._apply_env_overrides(config)
        
        self.config_cache[cache_key] = config
        return config
    
    def _load_config_file(self, filename: str) -> Optional[Dict[str, Any]]:
        """Load configuration from file"""
        file_path = self.config_dir / filename
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if filename.endswith('.yaml') or filename.endswith('.yml'):
                    return yaml.safe_load(f)
                elif filename.endswith('.json'):
                    return json.load(f)
                else:
                    logger.warning(f"Unsupported config file format: {filename}")
                    return None
        except Exception as e:
            logger.error(f"Error loading config file {filename}: {str(e)}")
            return None
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides"""
        # Convert nested config keys to environment variable format
        # e.g., database.host -> DATABASE_HOST
        env_vars = self._flatten_config(config)
        
        for key, current_value in env_vars.items():
            env_key = key.upper().replace('.', '_')
            env_value = os.getenv(env_key)
            
            if env_value is not None:
                # Try to convert to appropriate type
                converted_value = self._convert_env_value(env_value, current_value)
                self._set_nested_value(config, key, converted_value)
        
        return config
    
    def _flatten_config(self, config: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """Flatten nested configuration dictionary"""
        result = {}
        
        for key, value in config.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                result.update(self._flatten_config(value, full_key))
            else:
                result[full_key] = value
        
        return result
    
    def _convert_env_value(self, env_value: str, current_value: Any) -> Any:
        """Convert environment variable value to appropriate type"""
        if isinstance(current_value, bool):
            return env_value.lower() in ('true', '1', 'yes', 'on')
        elif isinstance(current_value, int):
            try:
                return int(env_value)
            except ValueError:
                return env_value
        elif isinstance(current_value, float):
            try:
                return float(env_value)
            except ValueError:
                return env_value
        elif isinstance(current_value, list):
            # Assume comma-separated values
            return [item.strip() for item in env_value.split(',')]
        else:
            return env_value
    
    def _set_nested_value(self, config: Dict[str, Any], key: str, value: Any):
        """Set value in nested dictionary using dot notation"""
        keys = key.split('.')
        current = config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def get_environment(self) -> Environment:
        """Get current environment"""
        return self.current_env
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.current_env == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.current_env == Environment.DEVELOPMENT

def create_app_config_schema() -> ConfigSchema:
    """Create application configuration schema"""
    schema = ConfigSchema()
    
    # Server configuration
    server_schema = ConfigSchema()
    server_schema.add_rule("host", ValidationRule(
        required=True,
        type_check=str,
        default="localhost",
        description="Server host address"
    ))
    server_schema.add_rule("port", ValidationRule(
        required=True,
        type_check=int,
        min_value=1,
        max_value=65535,
        default=5000,
        description="Server port number"
    ))
    server_schema.add_rule("debug", ValidationRule(
        type_check=bool,
        default=False,
        description="Enable debug mode"
    ))
    schema.add_nested_schema("server", server_schema)
    
    # Database configuration
    database_schema = ConfigSchema()
    database_schema.add_rule("faiss_index_path", ValidationRule(
        required=True,
        type_check=str,
        description="Path to FAISS index file"
    ))
    database_schema.add_rule("chunk_size", ValidationRule(
        type_check=int,
        min_value=100,
        max_value=10000,
        default=1000,
        description="Text chunk size for processing"
    ))
    database_schema.add_rule("overlap", ValidationRule(
        type_check=int,
        min_value=0,
        max_value=500,
        default=100,
        description="Text chunk overlap"
    ))
    schema.add_nested_schema("database", database_schema)
    
    # Security configuration
    security_schema = ConfigSchema()
    security_schema.add_rule("secret_key", ValidationRule(
        required=True,
        type_check=str,
        min_length=32,
        description="Application secret key"
    ))
    security_schema.add_rule("session_timeout", ValidationRule(
        type_check=int,
        min_value=300,  # 5 minutes
        max_value=86400,  # 24 hours
        default=3600,  # 1 hour
        description="Session timeout in seconds"
    ))
    security_schema.add_rule("rate_limit_per_minute", ValidationRule(
        type_check=int,
        min_value=1,
        max_value=1000,
        default=60,
        description="Rate limit per minute"
    ))
    schema.add_nested_schema("security", security_schema)
    
    # Logging configuration
    logging_schema = ConfigSchema()
    logging_schema.add_rule("level", ValidationRule(
        type_check=str,
        allowed_values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        description="Logging level"
    ))
    logging_schema.add_rule("log_dir", ValidationRule(
        type_check=str,
        default="logs",
        description="Log directory path"
    ))
    logging_schema.add_rule("max_file_size", ValidationRule(
        type_check=int,
        min_value=1024,  # 1KB
        default=10485760,  # 10MB
        description="Maximum log file size in bytes"
    ))
    schema.add_nested_schema("logging", logging_schema)
    
    # Cache configuration
    cache_schema = ConfigSchema()
    cache_schema.add_rule("memory_cache_size", ValidationRule(
        type_check=int,
        min_value=10,
        default=1000,
        description="Memory cache size"
    ))
    cache_schema.add_rule("persistent_cache_dir", ValidationRule(
        type_check=str,
        default="cache",
        description="Persistent cache directory"
    ))
    cache_schema.add_rule("enable_redis", ValidationRule(
        type_check=bool,
        default=False,
        description="Enable Redis caching"
    ))
    cache_schema.add_rule("redis_url", ValidationRule(
        type_check=str,
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    ))
    schema.add_nested_schema("cache", cache_schema)
    
    # Health check configuration
    health_schema = ConfigSchema()
    health_schema.add_rule("enabled", ValidationRule(
        type_check=bool,
        default=True,
        description="Enable health checks"
    ))
    health_schema.add_rule("check_interval", ValidationRule(
        type_check=int,
        min_value=10,
        default=60,
        description="Health check interval in seconds"
    ))
    health_schema.add_rule("timeout", ValidationRule(
        type_check=int,
        min_value=1,
        default=10,
        description="Health check timeout in seconds"
    ))
    schema.add_nested_schema("health", health_schema)
    
    return schema

def validate_app_config(config: Dict[str, Any]) -> bool:
    """Validate application configuration"""
    schema = create_app_config_schema()
    validator = ConfigValidator(schema)
    
    is_valid = validator.validate(config)
    
    if not is_valid:
        logger.error("Configuration validation failed:")
        for error in validator.errors:
            logger.error(f"  - {error}")
        raise ConfigError(f"Configuration validation failed: {validator.errors}")
    
    return True

def load_and_validate_config(config_dir: str = "config") -> Dict[str, Any]:
    """Load and validate application configuration"""
    env_manager = EnvironmentManager(config_dir)
    config = env_manager.load_config("app")
    
    # Validate configuration
    validate_app_config(config)
    
    logger.info(f"Configuration loaded and validated for environment: {env_manager.get_environment().value}")
    
    return config

def create_default_config_files(config_dir: str = "config"):
    """Create default configuration files"""
    config_path = Path(config_dir)
    config_path.mkdir(exist_ok=True)
    
    # Base configuration
    base_config = {
        "server": {
            "host": "localhost",
            "port": 5000,
            "debug": False
        },
        "database": {
            "faiss_index_path": "data/faiss_index.bin",
            "chunk_size": 1000,
            "overlap": 100
        },
        "security": {
            "secret_key": "your-secret-key-here-change-in-production",
            "session_timeout": 3600,
            "rate_limit_per_minute": 60
        },
        "logging": {
            "level": "INFO",
            "log_dir": "logs",
            "max_file_size": 10485760
        },
        "cache": {
            "memory_cache_size": 1000,
            "persistent_cache_dir": "cache",
            "enable_redis": False,
            "redis_url": "redis://localhost:6379/0"
        },
        "health": {
            "enabled": True,
            "check_interval": 60,
            "timeout": 10
        }
    }
    
    # Development configuration
    dev_config = {
        "server": {
            "debug": True
        },
        "logging": {
            "level": "DEBUG"
        }
    }
    
    # Production configuration
    prod_config = {
        "server": {
            "host": "0.0.0.0",
            "debug": False
        },
        "logging": {
            "level": "WARNING"
        },
        "security": {
            "rate_limit_per_minute": 30
        }
    }
    
    # Write configuration files
    configs = [
        ("app.yaml", base_config),
        ("app.development.yaml", dev_config),
        ("app.production.yaml", prod_config)
    ]
    
    for filename, config in configs:
        file_path = config_path / filename
        if not file_path.exists():
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            logger.info(f"Created default config file: {file_path}")

if __name__ == "__main__":
    # Create default configuration files
    create_default_config_files()
    
    # Load and validate configuration
    try:
        config = load_and_validate_config()
        print("Configuration loaded successfully:")
        print(yaml.dump(config, default_flow_style=False, indent=2))
    except ConfigError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")