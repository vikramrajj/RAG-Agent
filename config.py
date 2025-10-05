# config.py
import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_env_or_default(key, default, required=False):
    """Get environment variable with fallback to default value"""
    value = os.getenv(key)
    if value is None:
        if required:
            logger.error(f"Required environment variable {key} not set")
            raise ValueError(f"Required environment variable {key} not set")
        logger.warning(f"Environment variable {key} not set, using default: {default}")
        return default
    return value

@dataclass
class SecurityConfig:
    flask_secret_key: str = get_env_or_default("FLASK_SECRET_KEY", "", required=True)
    enable_security_headers: bool = True
    cors_origins: list = None
    rate_limit_per_hour: int = int(get_env_or_default("RATE_LIMIT_PER_HOUR", "100"))
    rate_limit_per_minute: int = int(get_env_or_default("RATE_LIMIT_PER_MINUTE", "20"))

@dataclass
class LLMConfig:
    model_name: str = get_env_or_default("OLLAMA_MODEL", "llama3")
    base_url: str = get_env_or_default("OLLAMA_BASE_URL", "http://localhost:11434")
    temperature: float = float(get_env_or_default("LLM_TEMPERATURE", "0.1"))
    max_tokens: int = int(get_env_or_default("MAX_TOKENS", "500"))
    timeout_seconds: int = int(get_env_or_default("REQUEST_TIMEOUT_SECONDS", "30"))

@dataclass
class RAGConfig:
    embedding_model: str = get_env_or_default("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    index_path: str = get_env_or_default("FAISS_INDEX_PATH", "outlook_index.faiss")
    metadata_path: str = get_env_or_default("METADATA_PATH", "metadata.json")
    min_relevance_score: float = float(get_env_or_default("MIN_RELEVANCE_SCORE", "0.3"))
    max_retrieval_results: int = int(get_env_or_default("MAX_RETRIEVAL_RESULTS", "5"))

@dataclass
class PathConfig:
    sara_path: str = get_env_or_default("SARA_PATH", r"C:\Program Files\Microsoft Support and Recovery Assistant\SaRA.exe")
    diagnostics_output_dir: str = get_env_or_default("DIAGNOSTICS_OUTPUT_DIR", r"C:\Diagnostics\Outlook")
    log_directory: str = get_env_or_default("LOG_DIRECTORY", "logs")
    
    def __post_init__(self):
        """Create directories if they don't exist"""
        Path(self.log_directory).mkdir(exist_ok=True)
        Path(self.diagnostics_output_dir).mkdir(parents=True, exist_ok=True)

@dataclass
class PerformanceConfig:
    max_worker_threads: int = int(get_env_or_default("MAX_WORKER_THREADS", "3"))
    request_timeout_seconds: int = int(get_env_or_default("REQUEST_TIMEOUT_SECONDS", "60"))
    max_request_history: int = int(get_env_or_default("MAX_REQUEST_HISTORY", "1000"))
    cleanup_interval_minutes: int = int(get_env_or_default("CLEANUP_INTERVAL_MINUTES", "60"))

class ConfigManager:
    """Centralized configuration management with validation"""
    
    _instance = None
    
    @classmethod
    def get_config(cls):
        """Get or create singleton config instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self, env_file: str = ".env"):
        self.env_file = env_file
        self.config_loaded = False
        self._load_environment()
        self._initialize_configs()
        
    def _load_environment(self):
        """Load environment variables from .env file if it exists"""
        env_path = Path(self.env_file)
        
        if env_path.exists():
            try:
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            
                            # Remove quotes if present
                            if value.startswith('"') and value.endswith('"'):
                                value = value[1:-1]
                            elif value.startswith("'") and value.endswith("'"):
                                value = value[1:-1]
                            
                            os.environ[key] = value
                
                logger.info(f"Environment variables loaded from {env_path}")
                
            except Exception as e:
                logger.warning(f"Could not load .env file: {e}")
        else:
            logger.warning(f"Environment file {env_path} not found")
    
    def _get_env_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean from environment variable"""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    def _get_env_int(self, key: str, default: int) -> int:
        """Get integer from environment variable with validation"""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            logger.warning(f"Invalid integer value for {key}, using default: {default}")
            return default
    
    def _get_env_float(self, key: str, default: float) -> float:
        """Get float from environment variable with validation"""
        try:
            return float(os.getenv(key, str(default)))
        except ValueError:
            logger.warning(f"Invalid float value for {key}, using default: {default}")
            return default
    
    def _get_env_list(self, key: str, default: list = None, separator: str = ',') -> list:
        """Get list from environment variable"""
        value = os.getenv(key)
        if value:
            return [item.strip() for item in value.split(separator) if item.strip()]
        return default or []
    
    def _initialize_configs(self):
        """Initialize all configuration objects"""
        try:
            # Security configuration
            flask_secret = os.getenv('FLASK_SECRET_KEY')
            if not flask_secret or flask_secret == 'your_secure_random_key_here_change_this':
                logger.warning("FLASK_SECRET_KEY not set or using default value! Using a temporary key for testing.")
                flask_secret = "temporary_test_key_do_not_use_in_production"
            
            self.security = SecurityConfig(
                flask_secret_key=flask_secret,
                enable_security_headers=self._get_env_bool('ENABLE_SECURITY_HEADERS', True),
                cors_origins=self._get_env_list('CORS_ORIGINS'),
                rate_limit_per_hour=self._get_env_int('RATE_LIMIT_PER_HOUR', 100),
                rate_limit_per_minute=self._get_env_int('RATE_LIMIT_PER_MINUTE', 20)
            )
            
            # LLM configuration
            self.llm = LLMConfig(
                model_name=os.getenv('OLLAMA_MODEL', 'llama3'),
                base_url=os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),
                temperature=self._get_env_float('LLM_TEMPERATURE', 0.1),
                max_tokens=self._get_env_int('MAX_TOKENS', 500),
                timeout_seconds=self._get_env_int('REQUEST_TIMEOUT_SECONDS', 30)
            )
            
            # RAG configuration
            self.rag = RAGConfig(
                embedding_model=os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2'),
                index_path=os.getenv('FAISS_INDEX_PATH', 'outlook_index.faiss'),
                metadata_path=os.getenv('METADATA_PATH', 'metadata.json'),
                min_relevance_score=self._get_env_float('MIN_RELEVANCE_SCORE', 0.3),
                max_retrieval_results=self._get_env_int('MAX_RETRIEVAL_RESULTS', 5)
            )
            
            # Path configuration
            self.paths = PathConfig(
                sara_path=os.getenv('SARA_PATH', r"C:\Program Files\Microsoft Support and Recovery Assistant\SaRA.exe"),
                diagnostics_output_dir=os.getenv('DIAGNOSTICS_OUTPUT_DIR', r"C:\Diagnostics\Outlook"),
                log_directory=os.getenv('LOG_DIRECTORY', 'logs')
            )
            
            # Performance configuration
            self.performance = PerformanceConfig(
                max_worker_threads=self._get_env_int('MAX_WORKER_THREADS', 3),
                request_timeout_seconds=self._get_env_int('REQUEST_TIMEOUT_SECONDS', 60),
                max_request_history=self._get_env_int('MAX_REQUEST_HISTORY', 1000),
                cleanup_interval_minutes=self._get_env_int('CLEANUP_INTERVAL_MINUTES', 60)
            )
            
            self.config_loaded = True
            logger.info("Configuration initialized successfully")
            
        except Exception as e:
            logger.error(f"Configuration initialization failed: {e}")
            raise
    
    def validate_credentials(self) -> bool:
        """Validate that required credentials are set"""
        email = os.getenv('OUTLOOK_EMAIL')
        password = os.getenv('OUTLOOK_PASSWORD')
        
        if not email:
            logger.error("OUTLOOK_EMAIL not set in environment variables")
            return False
            
        if not password:
            logger.error("OUTLOOK_PASSWORD not set in environment variables")
            return False
            
        if email == 'your_email@aston.ac.uk' or password == 'your_app_specific_password':
            logger.error("Default credential values detected - please update .env file")
            return False
            
        logger.info("Credentials validation passed")
        return True
    
    def validate_paths(self) -> Dict[str, bool]:
        """Validate that required paths and files exist"""
        validation_results = {}
        
        # Check RAG files
        validation_results['faiss_index'] = Path(self.rag.index_path).exists()
        validation_results['metadata'] = Path(self.rag.metadata_path).exists()
        
        # Check SaRA executable
        validation_results['sara_executable'] = Path(self.paths.sara_path).exists()
        
        # Check directories
        validation_results['log_directory'] = Path(self.paths.log_directory).is_dir()
        validation_results['diagnostics_directory'] = Path(self.paths.diagnostics_output_dir).is_dir()
        
        # Log results
        for check, passed in validation_results.items():
            if passed:
                logger.info(f"Path validation passed: {check}")
            else:
                logger.warning(f"Path validation failed: {check}")
        
        return validation_results
    
    def get_llm_config_dict(self) -> Dict[str, Any]:
        """Get LLM configuration as dictionary for easy use with libraries"""
        return {
            'model': self.llm.model_name,
            'base_url': self.llm.base_url,
            'temperature': self.llm.temperature,
            'max_tokens': self.llm.max_tokens,
            'timeout': self.llm.timeout_seconds
        }
    
    def get_credentials(self) -> tuple:
        """Get credentials safely"""
        if not self.validate_credentials():
            raise ValueError("Invalid or missing credentials")
        
        return os.getenv('OUTLOOK_EMAIL'), os.getenv('OUTLOOK_PASSWORD')
    
    def export_config(self, file_path: str = "config_export.json"):
        """Export current configuration to JSON (without sensitive data)"""
        export_data = {
            'security': {
                'enable_security_headers': self.security.enable_security_headers,
                'cors_origins': self.security.cors_origins,
                'rate_limits': {
                    'per_hour': self.security.rate_limit_per_hour,
                    'per_minute': self.security.rate_limit_per_minute
                }
            },
            'llm': {
                'model_name': self.llm.model_name,
                'base_url': self.llm.base_url,
                'temperature': self.llm.temperature,
                'max_tokens': self.llm.max_tokens
            },
            'rag': {
                'embedding_model': self.rag.embedding_model,
                'min_relevance_score': self.rag.min_relevance_score,
                'max_retrieval_results': self.rag.max_retrieval_results
            },
            'performance': {
                'max_worker_threads': self.performance.max_worker_threads,
                'request_timeout_seconds': self.performance.request_timeout_seconds
            }
        }
        
        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Configuration exported to {file_path}")
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information and configuration status"""
        path_validation = self.validate_paths()
        
        return {
            'config_loaded': self.config_loaded,
            'credentials_valid': self.validate_credentials(),
            'path_validation': path_validation,
            'environment_file_exists': Path(self.env_file).exists(),
            'required_files_missing': [k for k, v in path_validation.items() if not v],
            'llm_model': self.llm.model_name,
            'embedding_model': self.rag.embedding_model,
            'worker_threads': self.performance.max_worker_threads
        }

# Global configuration instance
_config_manager = None

def get_config() -> ConfigManager:
    """Get or create global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def init_config(env_file: str = ".env") -> ConfigManager:
    """Initialize configuration manager with specific env file"""
    global _config_manager
    _config_manager = ConfigManager(env_file)
    return _config_manager

if __name__ == "__main__":
    # Test configuration manager
    try:
        config = ConfigManager()
        
        print("Configuration Manager Test")
        print("=" * 40)
        
        # Display system info
        system_info = config.get_system_info()
        for key, value in system_info.items():
            print(f"{key}: {value}")
        
        print("\nLLM Configuration:")
        llm_config = config.get_llm_config_dict()
        for key, value in llm_config.items():
            print(f"  {key}: {value}")
        
        # Export configuration
        config.export_config("test_config_export.json")
        print("\nConfiguration exported successfully")
        
    except Exception as e:
        print(f"Configuration test failed: {e}")