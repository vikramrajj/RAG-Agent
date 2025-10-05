"""
Comprehensive tests for configuration validation
"""

import pytest
import os
import tempfile
import shutil
import yaml
import json
from pathlib import Path
from unittest.mock import patch, Mock
from config_validation import (
    ConfigError, Environment, ValidationRule, ConfigSchema,
    ConfigValidator, EnvironmentManager, create_app_config_schema,
    validate_app_config, load_and_validate_config, create_default_config_files
)

class TestEnvironment:
    """Test cases for Environment enum"""
    
    def test_environment_values(self):
        """Test environment enum values"""
        assert Environment.DEVELOPMENT.value == "development"
        assert Environment.TESTING.value == "testing"
        assert Environment.STAGING.value == "staging"
        assert Environment.PRODUCTION.value == "production"

class TestValidationRule:
    """Test cases for ValidationRule"""
    
    def test_validation_rule_creation(self):
        """Test validation rule creation"""
        rule = ValidationRule(
            required=True,
            type_check=str,
            min_length=5,
            max_length=50,
            description="Test rule"
        )
        
        assert rule.required is True
        assert rule.type_check == str
        assert rule.min_length == 5
        assert rule.max_length == 50
        assert rule.description == "Test rule"
    
    def test_validation_rule_defaults(self):
        """Test validation rule with defaults"""
        rule = ValidationRule()
        
        assert rule.required is False
        assert rule.type_check is None
        assert rule.default is None
        assert rule.description == ""

class TestConfigSchema:
    """Test cases for ConfigSchema"""
    
    def test_config_schema_creation(self):
        """Test config schema creation"""
        schema = ConfigSchema()
        assert len(schema.rules) == 0
        assert len(schema.nested_schemas) == 0
    
    def test_add_rule(self):
        """Test adding validation rule"""
        schema = ConfigSchema()
        rule = ValidationRule(required=True, type_check=str)
        
        schema.add_rule("test_key", rule)
        assert "test_key" in schema.rules
        assert schema.rules["test_key"] == rule
    
    def test_add_nested_schema(self):
        """Test adding nested schema"""
        parent_schema = ConfigSchema()
        child_schema = ConfigSchema()
        
        parent_schema.add_nested_schema("child", child_schema)
        assert "child" in parent_schema.nested_schemas
        assert parent_schema.nested_schemas["child"] == child_schema

class TestConfigValidator:
    """Test cases for ConfigValidator"""
    
    def setup_method(self):
        """Setup test environment"""
        self.schema = ConfigSchema()
        self.schema.add_rule("required_string", ValidationRule(
            required=True,
            type_check=str,
            min_length=3,
            max_length=20
        ))
        self.schema.add_rule("optional_int", ValidationRule(
            type_check=int,
            min_value=0,
            max_value=100,
            default=50
        ))
        self.schema.add_rule("enum_value", ValidationRule(
            allowed_values=["option1", "option2", "option3"]
        ))
        
        self.validator = ConfigValidator(self.schema)
    
    def test_validate_valid_config(self):
        """Test validating valid configuration"""
        config = {
            "required_string": "test_value",
            "optional_int": 25,
            "enum_value": "option1"
        }
        
        is_valid = self.validator.validate(config)
        assert is_valid is True
        assert len(self.validator.errors) == 0
    
    def test_validate_missing_required_field(self):
        """Test validation with missing required field"""
        config = {
            "optional_int": 25
        }
        
        is_valid = self.validator.validate(config)
        assert is_valid is False
        assert len(self.validator.errors) == 1
        assert "required_string" in self.validator.errors[0]
        assert "missing" in self.validator.errors[0].lower()
    
    def test_validate_wrong_type(self):
        """Test validation with wrong type"""
        config = {
            "required_string": 123,  # Should be string
            "optional_int": "not_int"  # Should be int
        }
        
        is_valid = self.validator.validate(config)
        assert is_valid is False
        assert len(self.validator.errors) == 2
    
    def test_validate_value_out_of_range(self):
        """Test validation with values out of range"""
        config = {
            "required_string": "ab",  # Too short
            "optional_int": 150  # Too high
        }
        
        is_valid = self.validator.validate(config)
        assert is_valid is False
        assert len(self.validator.errors) == 2
    
    def test_validate_invalid_enum_value(self):
        """Test validation with invalid enum value"""
        config = {
            "required_string": "valid_string",
            "enum_value": "invalid_option"
        }
        
        is_valid = self.validator.validate(config)
        assert is_valid is False
        assert len(self.validator.errors) == 1
        assert "allowed values" in self.validator.errors[0]
    
    def test_validate_with_defaults(self):
        """Test validation applies default values"""
        config = {
            "required_string": "test_value"
        }
        
        is_valid = self.validator.validate(config)
        assert is_valid is True
        assert config["optional_int"] == 50  # Default value applied
    
    def test_validate_pattern_matching(self):
        """Test validation with pattern matching"""
        schema = ConfigSchema()
        schema.add_rule("email", ValidationRule(
            pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        ))
        
        validator = ConfigValidator(schema)
        
        # Valid email
        config = {"email": "test@example.com"}
        assert validator.validate(config) is True
        
        # Invalid email
        config = {"email": "invalid-email"}
        assert validator.validate(config) is False
    
    def test_validate_custom_validator(self):
        """Test validation with custom validator"""
        def is_even(value):
            return isinstance(value, int) and value % 2 == 0
        
        schema = ConfigSchema()
        schema.add_rule("even_number", ValidationRule(
            custom_validator=is_even
        ))
        
        validator = ConfigValidator(schema)
        
        # Valid even number
        config = {"even_number": 4}
        assert validator.validate(config) is True
        
        # Invalid odd number
        config = {"even_number": 5}
        assert validator.validate(config) is False
    
    def test_validate_nested_schema(self):
        """Test validation with nested schema"""
        nested_schema = ConfigSchema()
        nested_schema.add_rule("nested_field", ValidationRule(
            required=True,
            type_check=str
        ))
        
        parent_schema = ConfigSchema()
        parent_schema.add_nested_schema("nested", nested_schema)
        
        validator = ConfigValidator(parent_schema)
        
        # Valid nested config
        config = {
            "nested": {
                "nested_field": "value"
            }
        }
        assert validator.validate(config) is True
        
        # Missing nested field
        config = {
            "nested": {}
        }
        assert validator.validate(config) is False
        
        # Wrong type for nested section
        config = {
            "nested": "not_a_dict"
        }
        assert validator.validate(config) is False

class TestEnvironmentManager:
    """Test cases for EnvironmentManager"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "config"
        self.config_dir.mkdir()
        
        # Create test config files
        base_config = {
            "server": {"host": "localhost", "port": 5000},
            "database": {"url": "sqlite:///base.db"}
        }
        
        dev_config = {
            "server": {"debug": True},
            "database": {"url": "sqlite:///dev.db"}
        }
        
        prod_config = {
            "server": {"host": "0.0.0.0", "debug": False},
            "database": {"url": "postgresql://prod.db"}
        }
        
        with open(self.config_dir / "app.yaml", 'w') as f:
            yaml.dump(base_config, f)
        
        with open(self.config_dir / "app.development.yaml", 'w') as f:
            yaml.dump(dev_config, f)
        
        with open(self.config_dir / "app.production.yaml", 'w') as f:
            yaml.dump(prod_config, f)
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_detect_environment_default(self):
        """Test environment detection with default"""
        manager = EnvironmentManager(str(self.config_dir))
        assert manager.get_environment() == Environment.DEVELOPMENT
    
    @patch.dict(os.environ, {"APP_ENV": "production"})
    def test_detect_environment_from_env_var(self):
        """Test environment detection from environment variable"""
        manager = EnvironmentManager(str(self.config_dir))
        assert manager.get_environment() == Environment.PRODUCTION
    
    @patch.dict(os.environ, {"APP_ENV": "invalid"})
    def test_detect_environment_invalid(self):
        """Test environment detection with invalid value"""
        manager = EnvironmentManager(str(self.config_dir))
        assert manager.get_environment() == Environment.DEVELOPMENT
    
    @patch.dict(os.environ, {"APP_ENV": "development"})
    def test_load_config_development(self):
        """Test loading development configuration"""
        manager = EnvironmentManager(str(self.config_dir))
        config = manager.load_config("app")
        
        assert config["server"]["host"] == "localhost"
        assert config["server"]["port"] == 5000
        assert config["server"]["debug"] is True  # From dev config
        assert config["database"]["url"] == "sqlite:///dev.db"  # From dev config
    
    @patch.dict(os.environ, {"APP_ENV": "production"})
    def test_load_config_production(self):
        """Test loading production configuration"""
        manager = EnvironmentManager(str(self.config_dir))
        config = manager.load_config("app")
        
        assert config["server"]["host"] == "0.0.0.0"  # From prod config
        assert config["server"]["port"] == 5000  # From base config
        assert config["server"]["debug"] is False  # From prod config
        assert config["database"]["url"] == "postgresql://prod.db"  # From prod config
    
    @patch.dict(os.environ, {"APP_ENV": "development", "SERVER_PORT": "8080", "SERVER_DEBUG": "false"})
    def test_load_config_with_env_overrides(self):
        """Test loading configuration with environment variable overrides"""
        manager = EnvironmentManager(str(self.config_dir))
        config = manager.load_config("app")
        
        assert config["server"]["port"] == 8080  # Overridden by env var
        assert config["server"]["debug"] is False  # Overridden by env var
    
    def test_config_caching(self):
        """Test configuration caching"""
        manager = EnvironmentManager(str(self.config_dir))
        
        # Load config twice
        config1 = manager.load_config("app")
        config2 = manager.load_config("app")
        
        # Should be the same object (cached)
        assert config1 is config2
    
    def test_is_production(self):
        """Test is_production method"""
        with patch.dict(os.environ, {"APP_ENV": "production"}):
            manager = EnvironmentManager(str(self.config_dir))
            assert manager.is_production() is True
        
        with patch.dict(os.environ, {"APP_ENV": "development"}):
            manager = EnvironmentManager(str(self.config_dir))
            assert manager.is_production() is False
    
    def test_is_development(self):
        """Test is_development method"""
        with patch.dict(os.environ, {"APP_ENV": "development"}):
            manager = EnvironmentManager(str(self.config_dir))
            assert manager.is_development() is True
        
        with patch.dict(os.environ, {"APP_ENV": "production"}):
            manager = EnvironmentManager(str(self.config_dir))
            assert manager.is_development() is False

class TestAppConfigSchema:
    """Test cases for application config schema"""
    
    def test_create_app_config_schema(self):
        """Test creating application config schema"""
        schema = create_app_config_schema()
        
        assert isinstance(schema, ConfigSchema)
        assert "server" in schema.nested_schemas
        assert "database" in schema.nested_schemas
        assert "security" in schema.nested_schemas
        assert "logging" in schema.nested_schemas
        assert "cache" in schema.nested_schemas
        assert "health" in schema.nested_schemas
    
    def test_validate_valid_app_config(self):
        """Test validating valid application configuration"""
        config = {
            "server": {
                "host": "localhost",
                "port": 5000,
                "debug": False
            },
            "database": {
                "faiss_index_path": "/path/to/index.bin",
                "chunk_size": 1000,
                "overlap": 100
            },
            "security": {
                "secret_key": "a-very-long-secret-key-for-testing-purposes",
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
        
        assert validate_app_config(config) is True
    
    def test_validate_invalid_app_config(self):
        """Test validating invalid application configuration"""
        config = {
            "server": {
                "port": 70000,  # Invalid port
                "debug": "not_boolean"  # Wrong type
            },
            "security": {
                "secret_key": "short",  # Too short
                "session_timeout": 100  # Too low
            }
        }
        
        with pytest.raises(ConfigError):
            validate_app_config(config)

class TestConfigFileOperations:
    """Test cases for configuration file operations"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_create_default_config_files(self):
        """Test creating default configuration files"""
        config_dir = Path(self.temp_dir) / "config"
        create_default_config_files(str(config_dir))
        
        # Check that files are created
        assert (config_dir / "app.yaml").exists()
        assert (config_dir / "app.development.yaml").exists()
        assert (config_dir / "app.production.yaml").exists()
        
        # Check that files contain valid YAML
        with open(config_dir / "app.yaml", 'r') as f:
            base_config = yaml.safe_load(f)
            assert "server" in base_config
            assert "database" in base_config
    
    def test_load_and_validate_config(self):
        """Test loading and validating configuration"""
        config_dir = Path(self.temp_dir) / "config"
        create_default_config_files(str(config_dir))
        
        # Update secret key to be valid
        app_config_path = config_dir / "app.yaml"
        with open(app_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        config["security"]["secret_key"] = "a-very-long-secret-key-for-testing-purposes-that-meets-minimum-length"
        
        with open(app_config_path, 'w') as f:
            yaml.dump(config, f)
        
        with patch.dict(os.environ, {"APP_ENV": "development"}):
            loaded_config = load_and_validate_config(str(config_dir))
            assert isinstance(loaded_config, dict)
            assert "server" in loaded_config

class TestIntegration:
    """Integration tests for configuration validation"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "config"
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_full_config_pipeline(self):
        """Test complete configuration pipeline"""
        # Create default config files
        create_default_config_files(str(self.config_dir))
        
        # Update secret key to be valid
        app_config_path = self.config_dir / "app.yaml"
        with open(app_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        config["security"]["secret_key"] = "a-very-long-secret-key-for-testing-purposes-that-meets-minimum-length"
        
        with open(app_config_path, 'w') as f:
            yaml.dump(config, f)
        
        # Test different environments
        environments = ["development", "production"]
        
        for env in environments:
            with patch.dict(os.environ, {"APP_ENV": env}):
                manager = EnvironmentManager(str(self.config_dir))
                config = manager.load_config("app")
                
                # Validate configuration
                assert validate_app_config(config) is True
                
                # Check environment-specific settings
                if env == "development":
                    assert config["server"]["debug"] is True
                    assert config["logging"]["level"] == "DEBUG"
                elif env == "production":
                    assert config["server"]["debug"] is False
                    assert config["logging"]["level"] == "WARNING"
    
    def test_config_with_environment_overrides(self):
        """Test configuration with environment variable overrides"""
        create_default_config_files(str(self.config_dir))
        
        # Update secret key to be valid
        app_config_path = self.config_dir / "app.yaml"
        with open(app_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        config["security"]["secret_key"] = "a-very-long-secret-key-for-testing-purposes-that-meets-minimum-length"
        
        with open(app_config_path, 'w') as f:
            yaml.dump(config, f)
        
        # Test with environment overrides
        env_vars = {
            "APP_ENV": "development",
            "SERVER_PORT": "8080",
            "SERVER_HOST": "0.0.0.0",
            "SECURITY_RATE_LIMIT_PER_MINUTE": "120",
            "LOGGING_LEVEL": "DEBUG"
        }
        
        with patch.dict(os.environ, env_vars):
            config = load_and_validate_config(str(self.config_dir))
            
            assert config["server"]["port"] == 8080
            assert config["server"]["host"] == "0.0.0.0"
            assert config["security"]["rate_limit_per_minute"] == 120
            assert config["logging"]["level"] == "DEBUG"
    
    def test_config_validation_error_handling(self):
        """Test configuration validation error handling"""
        create_default_config_files(str(self.config_dir))
        
        # Create invalid configuration
        app_config_path = self.config_dir / "app.yaml"
        invalid_config = {
            "server": {
                "port": "invalid_port",  # Wrong type
                "host": ""  # Empty string
            },
            "security": {
                "secret_key": "short",  # Too short
                "session_timeout": -1  # Invalid value
            }
        }
        
        with open(app_config_path, 'w') as f:
            yaml.dump(invalid_config, f)
        
        with patch.dict(os.environ, {"APP_ENV": "development"}):
            with pytest.raises(ConfigError) as exc_info:
                load_and_validate_config(str(self.config_dir))
            
            # Check that error contains validation details
            assert "validation failed" in str(exc_info.value).lower()

if __name__ == '__main__':
    pytest.main([__file__])