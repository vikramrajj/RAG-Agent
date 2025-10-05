import logging
import asyncio
import os
from typing import Dict, Optional, Union, Any, Union, Any, List
import wave
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field
from transformers import pipeline
from transformers.pipelines import Pipeline

# Project imports
from config_validation import load_and_validate_config
from health_checks import HealthCheckManager
from performance_monitor import get_metrics_collector, get_app_monitor
from enhanced_logging import get_enhanced_logger
from error_handling import handle_errors, CircuitBreakerConfig, RetryConfig

# Configure logging
logger = get_enhanced_logger(__name__)

# Load voice configuration
try:
    config = load_and_validate_config('config')
    VOICE_CONFIG = config.get('voice', {})
except Exception as e:
    logger.warning(f"Failed to load voice configuration: {e}. Using defaults.")
    VOICE_CONFIG = {
        'model': 'openai/whisper-small',
        'language': 'en',
        'sample_rate': 16000,
        'chunk_size': 1024
    }

@dataclass
class AudioConfig:
    model: str = VOICE_CONFIG.get('model', 'openai/whisper-small')
    language: str = VOICE_CONFIG.get('language', 'en')
    sample_rate: int = VOICE_CONFIG.get('sample_rate', 16000)
    chunk_size: int = VOICE_CONFIG.get('chunk_size', 1024)

class VoiceHandler(HealthCheckManager):
    def __init__(self, config: Optional[AudioConfig] = None):
        super().__init__()
        self.config = config or AudioConfig()
        self.transcriber = self._initialize_transcriber()
        # Create performance monitor adapter similar to reasoner
        self.metrics = get_metrics_collector()
        self.app_monitor = get_app_monitor()
        
        # Note: Health checks can be added via add_check() method if needed
        
        logger.info(
            f"Voice handler initialized with model={self.config.model}, language={self.config.language}, sample_rate={self.config.sample_rate}"
        )
        
    def _initialize_transcriber(self) -> Pipeline:
        """Initialize the transcription pipeline with retries"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                return pipeline(
                    "automatic-speech-recognition",
                    model=self.config.model,
                    device="cuda" if self._is_cuda_available() else "cpu"
                )
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Transcriber initialization attempt {attempt + 1} failed: {e}")
                asyncio.sleep(retry_delay * (attempt + 1))
                
    def _is_cuda_available(self) -> bool:
        """Check if CUDA is available for GPU acceleration"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    async def transcribe_audio(self, audio_data: Union[bytes, str, Path]) -> Dict:
        """Transcribe audio data to text with performance monitoring"""
        start_time = self.perf_monitor.start_operation('transcribe_audio')
        
        try:
            # Handle different input types
            if isinstance(audio_data, (str, Path)):
                audio_array = self._load_audio_file(audio_data)
            else:
                audio_array = self._convert_audio(audio_data)
            
            self.perf_monitor.record_metric('audio_length', len(audio_array))
            
            # Transcribe using Whisper with monitoring
            with self.perf_monitor.measure('whisper_transcription'):
                result = self.transcriber(
                    audio_array,
                    language=self.config.language,
                    return_timestamps=True
                )
            
            # Extract word-level confidence if available
            word_confidences = self._extract_word_confidences(result)
            avg_confidence = sum(word_confidences) / len(word_confidences) if word_confidences else 0.0
            
            self.perf_monitor.record_metric('confidence', avg_confidence)
            self.perf_monitor.end_operation('transcribe_audio', start_time)
            
            return {
                "status": "success",
                "text": result["text"],
                "confidence": avg_confidence,
                "word_timestamps": result.get("chunks", []),
                "language": result.get("language", self.config.language),
                "performance": self.perf_monitor.get_operation_stats('transcribe_audio')
            }
        except Exception as e:
            logger.error(
                "Error transcribing audio",
                exc_info=e,
                extra={
                    'audio_size': len(audio_data) if isinstance(audio_data, bytes) else 'file',
                    'error': str(e)
                }
            )
            self.perf_monitor.record_error('transcribe_audio', str(e))
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }

    def _convert_audio(self, audio_data: bytes) -> np.ndarray:
        """Convert audio bytes to numpy array with proper format checking"""
        try:
            # First try to read as WAV
            with wave.open(audio_data, 'rb') as wav_file:
                sample_width = wav_file.getsampwidth()
                channels = wav_file.getnchannels()
                rate = wav_file.getframerate()
                
                # Read audio data
                audio_data = wav_file.readframes(wav_file.getnframes())
                
                # Convert to float32
                dtype = {1: np.int8, 2: np.int16, 4: np.int32}[sample_width]
                audio_array = np.frombuffer(audio_data, dtype=dtype)
                audio_array = audio_array.astype(np.float32) / np.iinfo(dtype).max
                
                # Convert to mono if needed
                if channels > 1:
                    audio_array = audio_array.reshape(-1, channels).mean(axis=1)
                
                # Resample if needed
                if rate != self.config.sample_rate:
                    audio_array = self._resample(audio_array, rate, self.config.sample_rate)
                    
                return audio_array
        except Exception as e:
            logger.warning(f"Failed to process as WAV: {e}, trying raw PCM")
            # Fallback to raw PCM
            return np.frombuffer(audio_data, dtype=np.float32)
    
    def _load_audio_file(self, file_path: Union[str, Path]) -> np.ndarray:
        """Load audio from file path"""
        with open(file_path, 'rb') as f:
            return self._convert_audio(f.read())
    
    def _resample(self, audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """Resample audio to target sample rate"""
        try:
            from scipy import signal
            return signal.resample(
                audio,
                int(len(audio) * target_sr / orig_sr)
            )
        except ImportError:
            logger.warning("scipy not available for resampling, using linear interpolation")
            return np.interp(
                np.linspace(0, len(audio), int(len(audio) * target_sr / orig_sr)),
                np.arange(len(audio)),
                audio
            )
    
    def _extract_word_confidences(self, result: Dict) -> List[float]:
        """Extract word-level confidence scores from result"""
        confidences = []
        if "chunks" in result:
            for chunk in result["chunks"]:
                if "confidence" in chunk:
                    confidences.append(chunk["confidence"])
        return confidences
    
    async def _check_transcriber_health(self) -> Dict[str, Any]:
        """Health check for transcriber component"""
        try:
            # Create a simple test audio signal
            test_audio = np.sin(np.linspace(0, 2*np.pi, self.config.sample_rate)).astype(np.float32)
            
            # Try transcription
            result = self.transcriber(test_audio)
            
            return {
                'status': 'healthy',
                'message': 'Transcriber is functioning',
                'model': self.config.model,
                'device': 'cuda' if self._is_cuda_available() else 'cpu',
                'latency': self.perf_monitor.get_average_latency('whisper_transcription')
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Transcriber health check failed: {str(e)}',
                'error': str(e)
            }
    
    async def get_diagnostics(self) -> Dict[str, Any]:
        """Get diagnostic information about the voice handler"""
        return {
            'config': vars(self.config),
            'performance_metrics': self.perf_monitor.get_metrics(),
            'health_status': await self.get_health_status(),
            'cuda_available': self._is_cuda_available()
        }