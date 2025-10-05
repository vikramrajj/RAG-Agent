"""
Model Manager for Lightweight Reasoning Models
Handles model selection, loading, and inference optimization
"""

import os
import subprocess
import json
from typing import Optional, Dict, Any, List
import requests
from datetime import datetime
from pathlib import Path

from lightweight_models_config import (
    LIGHTWEIGHT_MODELS, get_model_config, get_ollama_model_name,
    recommend_model, DEFAULT_MODEL, FALLBACK_MODEL
)
from enhanced_logging import get_enhanced_logger

logger = get_enhanced_logger('model_manager')

class ModelManager:
    """
    Manages lightweight reasoning models for the SAT interface
    Supports Ollama-based local inference
    """
    
    def __init__(self, ollama_base_url: str = "http://localhost:11434"):
        """
        Initialize the model manager
        
        Args:
            ollama_base_url: Base URL for Ollama API
        """
        self.ollama_base_url = ollama_base_url
        self.current_model = None
        self.model_config = None
        self.available_models = []
        self._check_ollama_status()
        
    def _check_ollama_status(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.available_models = [model['name'] for model in data.get('models', [])]
                logger.info(f"Ollama is running. Available models: {len(self.available_models)}")
                return True
            else:
                logger.warning("Ollama is not responding correctly")
                return False
        except requests.exceptions.RequestException as e:
            logger.warning(f"Ollama is not accessible: {e}")
            logger.info("Please start Ollama with: ollama serve")
            return False
    
    def is_model_available(self, model_name: str) -> bool:
        """Check if a model is already downloaded in Ollama"""
        ollama_name = get_ollama_model_name(model_name)
        return any(ollama_name in available for available in self.available_models)
    
    def pull_model(self, model_name: str) -> bool:
        """
        Download a model using Ollama
        
        Args:
            model_name: Name of the model from LIGHTWEIGHT_MODELS
            
        Returns:
            True if successful, False otherwise
        """
        config = get_model_config(model_name)
        if not config:
            logger.error(f"Model {model_name} not found in configuration")
            return False
        
        ollama_model = config.ollama_model
        logger.info(f"Pulling model {config.display_name} ({ollama_model})...")
        logger.info(f"Size: {config.size_gb}GB - This may take a few minutes")
        
        try:
            # Use Ollama CLI to pull the model
            result = subprocess.run(
                ['ollama', 'pull', ollama_model],
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout for large models
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully pulled {config.display_name}")
                self._check_ollama_status()  # Refresh available models
                return True
            else:
                logger.error(f"Failed to pull model: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Model pull timed out")
            return False
        except FileNotFoundError:
            logger.error("Ollama CLI not found. Please install Ollama from https://ollama.ai")
            return False
        except Exception as e:
            logger.error(f"Error pulling model: {e}")
            return False
    
    def load_model(self, model_name: str, auto_pull: bool = True) -> bool:
        """
        Load a model for inference
        
        Args:
            model_name: Name of the model to load
            auto_pull: Automatically pull the model if not available
            
        Returns:
            True if model is ready, False otherwise
        """
        config = get_model_config(model_name)
        if not config:
            logger.error(f"Model {model_name} not found")
            return False
        
        # Check if model is available
        if not self.is_model_available(model_name):
            if auto_pull:
                logger.info(f"Model {config.display_name} not found locally, pulling...")
                if not self.pull_model(model_name):
                    logger.error(f"Failed to pull model {config.display_name}")
                    return False
            else:
                logger.error(f"Model {config.display_name} not available and auto_pull is disabled")
                return False
        
        # Set current model
        self.current_model = model_name
        self.model_config = config
        logger.info(f"Loaded model: {config.display_name}")
        logger.info(f"Context length: {config.context_length}, Speed: {'⚡' * config.speed_rating}, Quality: {'⭐' * config.quality_rating}")
        
        return True
    
    def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 2048,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a response using the current model
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Override default temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            
        Returns:
            Response dictionary with content and metadata
        """
        if not self.current_model or not self.model_config:
            logger.error("No model loaded. Call load_model() first")
            return {
                'success': False,
                'error': 'No model loaded',
                'content': None
            }
        
        try:
            # Prepare request
            ollama_model = self.model_config.ollama_model
            temp = temperature if temperature is not None else self.model_config.temperature
            
            payload = {
                'model': ollama_model,
                'prompt': prompt,
                'stream': stream,
                'options': {
                    'temperature': temp,
                    'top_p': self.model_config.top_p,
                    'num_predict': max_tokens
                }
            }
            
            if system_prompt:
                payload['system'] = system_prompt
            
            # Make request to Ollama
            start_time = datetime.now()
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                duration = (datetime.now() - start_time).total_seconds()
                
                return {
                    'success': True,
                    'content': result.get('response', ''),
                    'model': self.model_config.display_name,
                    'model_key': self.current_model,
                    'duration_seconds': duration,
                    'tokens_generated': result.get('eval_count', 0),
                    'tokens_per_second': result.get('eval_count', 0) / duration if duration > 0 else 0,
                    'context_length': self.model_config.context_length,
                    'metadata': {
                        'temperature': temp,
                        'model_size_gb': self.model_config.size_gb,
                        'speed_rating': self.model_config.speed_rating,
                        'quality_rating': self.model_config.quality_rating
                    }
                }
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return {
                    'success': False,
                    'error': f"API error: {response.status_code}",
                    'content': None
                }
                
        except requests.exceptions.Timeout:
            logger.error("Request timed out")
            return {
                'success': False,
                'error': 'Request timed out',
                'content': None
            }
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                'success': False,
                'error': str(e),
                'content': None
            }
    
    def chat(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Chat interface with conversation history
        
        Args:
            message: User message
            conversation_history: Previous conversation messages
            system_prompt: System prompt for the conversation
            temperature: Temperature override
            
        Returns:
            Response with conversation context
        """
        # Build prompt with conversation history
        if conversation_history:
            context = "\n".join([
                f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                for msg in conversation_history[-10:]  # Last 10 messages
            ])
            full_prompt = f"{context}\nUser: {message}\nAssistant:"
        else:
            full_prompt = message
        
        return self.generate_response(
            prompt=full_prompt,
            system_prompt=system_prompt,
            temperature=temperature
        )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        if not self.model_config:
            return {'error': 'No model loaded'}
        
        return {
            'name': self.current_model,
            'display_name': self.model_config.display_name,
            'size_gb': self.model_config.size_gb,
            'context_length': self.model_config.context_length,
            'speed_rating': self.model_config.speed_rating,
            'quality_rating': self.model_config.quality_rating,
            'best_for': self.model_config.best_for,
            'description': self.model_config.description,
            'temperature': self.model_config.temperature,
            'recommended_ram_gb': self.model_config.recommended_ram
        }
    
    def list_downloaded_models(self) -> List[Dict[str, Any]]:
        """List all downloaded models with their configurations"""
        downloaded = []
        
        for model_name, config in LIGHTWEIGHT_MODELS.items():
            if self.is_model_available(model_name):
                downloaded.append({
                    'name': model_name,
                    'display_name': config.display_name,
                    'size_gb': config.size_gb,
                    'speed': '⚡' * config.speed_rating,
                    'quality': '⭐' * config.quality_rating,
                    'best_for': config.best_for
                })
        
        return downloaded
    
    def recommend_for_use_case(self, use_case: str, available_ram_gb: int = 8) -> List[Dict[str, Any]]:
        """Get model recommendations for a specific use case"""
        recommended_names = recommend_model(use_case, available_ram_gb)
        
        recommendations = []
        for model_name in recommended_names:
            config = get_model_config(model_name)
            if config:
                recommendations.append({
                    'name': model_name,
                    'display_name': config.display_name,
                    'size_gb': config.size_gb,
                    'is_downloaded': self.is_model_available(model_name),
                    'description': config.description,
                    'speed': '⚡' * config.speed_rating,
                    'quality': '⭐' * config.quality_rating
                })
        
        return recommendations

# Global model manager instance
_model_manager = None

def get_model_manager(ollama_base_url: str = "http://localhost:11434") -> ModelManager:
    """Get or create the global model manager instance"""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager(ollama_base_url)
    return _model_manager

# Convenience functions
def load_model(model_name: str, auto_pull: bool = True) -> bool:
    """Load a model"""
    manager = get_model_manager()
    return manager.load_model(model_name, auto_pull)

def generate(prompt: str, **kwargs) -> Dict[str, Any]:
    """Generate a response"""
    manager = get_model_manager()
    return manager.generate_response(prompt, **kwargs)

def chat(message: str, **kwargs) -> Dict[str, Any]:
    """Chat with the model"""
    manager = get_model_manager()
    return manager.chat(message, **kwargs)
