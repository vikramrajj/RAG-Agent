"""
Lightweight Reasoning Models Configuration
Supports multiple efficient models for local inference through Ollama
Optimized for fast response times and lower resource usage
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

@dataclass
class ModelConfig:
    """Configuration for a lightweight model"""
    name: str
    display_name: str
    ollama_model: str
    size_gb: float
    context_length: int
    temperature: float
    top_p: float
    description: str
    best_for: List[str]
    recommended_ram: int  # in GB
    speed_rating: int  # 1-5, 5 being fastest
    quality_rating: int  # 1-5, 5 being best quality

class ModelCategory(Enum):
    """Categories of lightweight models"""
    ULTRA_FAST = "ultra_fast"  # < 1GB, fastest response
    BALANCED = "balanced"       # 1-4GB, good balance
    QUALITY = "quality"         # 4-8GB, best quality
    REASONING = "reasoning"     # Specialized for reasoning tasks

# Lightweight Models Database
LIGHTWEIGHT_MODELS: Dict[str, ModelConfig] = {
    # ULTRA FAST MODELS (< 1GB)
    "phi3-mini": ModelConfig(
        name="phi3-mini",
        display_name="Phi-3 Mini (3.8B)",
        ollama_model="phi3:3.8b",
        size_gb=0.5,
        context_length=4096,
        temperature=0.1,
        top_p=0.9,
        description="Microsoft's ultra-fast small model, excellent for quick responses",
        best_for=["Quick Q&A", "Simple homework", "Fast chat"],
        recommended_ram=2,
        speed_rating=5,
        quality_rating=3
    ),
    
    "tinyllama": ModelConfig(
        name="tinyllama",
        display_name="TinyLlama (1.1B)",
        ollama_model="tinyllama:1.1b",
        size_gb=0.6,
        context_length=2048,
        temperature=0.2,
        top_p=0.9,
        description="Smallest Llama model, extremely fast but basic capabilities",
        best_for=["Very quick responses", "Basic chat", "Low-end devices"],
        recommended_ram=2,
        speed_rating=5,
        quality_rating=2
    ),
    
    # BALANCED MODELS (1-4GB)
    "mistral": ModelConfig(
        name="mistral",
        display_name="Mistral 7B",
        ollama_model="mistral:7b",
        size_gb=4.1,
        context_length=8192,
        temperature=0.1,
        top_p=0.9,
        description="Excellent balanced model, great performance for size",
        best_for=["General chat", "Homework help", "Essay writing", "Research"],
        recommended_ram=8,
        speed_rating=4,
        quality_rating=4
    ),
    
    "llama3.2": ModelConfig(
        name="llama3.2",
        display_name="Llama 3.2 (3B)",
        ollama_model="llama3.2:3b",
        size_gb=2.0,
        context_length=8192,
        temperature=0.1,
        top_p=0.9,
        description="Latest Llama 3.2 small model, excellent reasoning for size",
        best_for=["Academic questions", "Code help", "Math problems"],
        recommended_ram=4,
        speed_rating=4,
        quality_rating=4
    ),
    
    "gemma2-2b": ModelConfig(
        name="gemma2-2b",
        display_name="Gemma 2 (2B)",
        ollama_model="gemma2:2b",
        size_gb=1.6,
        context_length=8192,
        temperature=0.1,
        top_p=0.9,
        description="Google's efficient small model, good for instruction following",
        best_for=["Study guides", "Summaries", "Simple explanations"],
        recommended_ram=4,
        speed_rating=4,
        quality_rating=3
    ),
    
    # QUALITY MODELS (4-8GB)
    "llama3.1": ModelConfig(
        name="llama3.1",
        display_name="Llama 3.1 (8B)",
        ollama_model="llama3.1:8b",
        size_gb=4.7,
        context_length=128000,  # Large context window
        temperature=0.1,
        top_p=0.9,
        description="Meta's powerful 8B model with huge context, best balance of speed and quality",
        best_for=["Complex reasoning", "Long documents", "Research papers", "Coding"],
        recommended_ram=8,
        speed_rating=3,
        quality_rating=5
    ),
    
    "mixtral-8x7b": ModelConfig(
        name="mixtral-8x7b",
        display_name="Mixtral 8x7B",
        ollama_model="mixtral:8x7b",
        size_gb=26.0,
        context_length=32768,
        temperature=0.1,
        top_p=0.9,
        description="Mixture of Experts model, very powerful but larger",
        best_for=["Advanced reasoning", "Complex problems", "Professional writing"],
        recommended_ram=16,
        speed_rating=2,
        quality_rating=5
    ),
    
    # REASONING SPECIALIZED
    "qwen2.5": ModelConfig(
        name="qwen2.5",
        display_name="Qwen 2.5 (7B)",
        ollama_model="qwen2.5:7b",
        size_gb=4.7,
        context_length=32768,
        temperature=0.1,
        top_p=0.9,
        description="Alibaba's reasoning-focused model, excellent for math and logic",
        best_for=["Math problems", "Logic puzzles", "Step-by-step reasoning", "Code"],
        recommended_ram=8,
        speed_rating=3,
        quality_rating=4
    ),
    
    "deepseek-r1": ModelConfig(
        name="deepseek-r1",
        display_name="DeepSeek R1 (1.5B)",
        ollama_model="deepseek-r1:1.5b",
        size_gb=1.0,
        context_length=8192,
        temperature=0.2,
        top_p=0.95,
        description="Specialized reasoning model, shows thinking process",
        best_for=["Math reasoning", "Problem solving", "Logical deduction"],
        recommended_ram=4,
        speed_rating=4,
        quality_rating=4
    ),
}

# Model recommendations by use case
MODEL_RECOMMENDATIONS = {
    "quick_chat": ["phi3-mini", "tinyllama", "gemma2-2b"],
    "homework_help": ["mistral", "llama3.2", "qwen2.5"],
    "essay_writing": ["mistral", "llama3.1"],
    "math_reasoning": ["qwen2.5", "deepseek-r1", "llama3.1"],
    "research": ["llama3.1", "mistral"],
    "coding": ["llama3.1", "qwen2.5"],
    "low_resource": ["phi3-mini", "tinyllama", "gemma2-2b"],
    "balanced": ["mistral", "llama3.2"],
    "best_quality": ["llama3.1", "mixtral-8x7b"]
}

def get_model_config(model_name: str) -> Optional[ModelConfig]:
    """Get configuration for a specific model"""
    return LIGHTWEIGHT_MODELS.get(model_name)

def get_models_by_category(category: ModelCategory) -> List[ModelConfig]:
    """Get all models in a specific category"""
    if category == ModelCategory.ULTRA_FAST:
        return [m for m in LIGHTWEIGHT_MODELS.values() if m.size_gb < 1.0]
    elif category == ModelCategory.BALANCED:
        return [m for m in LIGHTWEIGHT_MODELS.values() if 1.0 <= m.size_gb < 5.0]
    elif category == ModelCategory.QUALITY:
        return [m for m in LIGHTWEIGHT_MODELS.values() if m.size_gb >= 5.0]
    elif category == ModelCategory.REASONING:
        return [m for m in LIGHTWEIGHT_MODELS.values() if "reasoning" in m.description.lower() or "math" in " ".join(m.best_for).lower()]
    return []

def recommend_model(use_case: str, available_ram_gb: int = 8) -> List[str]:
    """
    Recommend models based on use case and available RAM
    
    Args:
        use_case: The primary use case (e.g., 'homework_help', 'quick_chat')
        available_ram_gb: Available RAM in GB
        
    Returns:
        List of recommended model names
    """
    # Get recommendations for use case
    recommended = MODEL_RECOMMENDATIONS.get(use_case, ["mistral", "llama3.2"])
    
    # Filter by available RAM
    suitable_models = []
    for model_name in recommended:
        config = get_model_config(model_name)
        if config and config.recommended_ram <= available_ram_gb:
            suitable_models.append(model_name)
    
    # If no suitable models, recommend smallest ones
    if not suitable_models:
        suitable_models = ["tinyllama", "phi3-mini"]
    
    return suitable_models

def get_ollama_model_name(model_name: str) -> str:
    """Get the Ollama model identifier"""
    config = get_model_config(model_name)
    return config.ollama_model if config else "mistral:7b"

def list_all_models() -> Dict[str, Any]:
    """Get a formatted list of all available models"""
    return {
        "ultra_fast": [
            {
                "name": m.name,
                "display_name": m.display_name,
                "size": f"{m.size_gb}GB",
                "speed": "⚡" * m.speed_rating,
                "quality": "⭐" * m.quality_rating,
                "best_for": m.best_for
            }
            for m in get_models_by_category(ModelCategory.ULTRA_FAST)
        ],
        "balanced": [
            {
                "name": m.name,
                "display_name": m.display_name,
                "size": f"{m.size_gb}GB",
                "speed": "⚡" * m.speed_rating,
                "quality": "⭐" * m.quality_rating,
                "best_for": m.best_for
            }
            for m in get_models_by_category(ModelCategory.BALANCED)
        ],
        "quality": [
            {
                "name": m.name,
                "display_name": m.display_name,
                "size": f"{m.size_gb}GB",
                "speed": "⚡" * m.speed_rating,
                "quality": "⭐" * m.quality_rating,
                "best_for": m.best_for
            }
            for m in get_models_by_category(ModelCategory.QUALITY)
        ]
    }

# Default model selection
DEFAULT_MODEL = "mistral"  # Best balance of speed and quality
FALLBACK_MODEL = "phi3-mini"  # Fastest fallback
