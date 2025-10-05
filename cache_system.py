# cache_system.py
"""
Caching system for the RAG Agent application.
Provides Redis-like interface with memory fallback for performance optimization.
"""

import json
import time
import hashlib
import pickle
import logging
from typing import Any, Optional, Dict, List, Union
from dataclasses import dataclass
from threading import Lock, RLock
from collections import OrderedDict
import os
from pathlib import Path
from standardized_error_handler import (
    handle_errors, ErrorCategory, ErrorSeverity,
    handle_database_error
)

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    value: Any
    created_at: float
    expires_at: Optional[float] = None
    access_count: int = 0
    last_accessed: float = None
    
    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.created_at
    
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def touch(self):
        """Update access metadata."""
        self.access_count += 1
        self.last_accessed = time.time()

class MemoryCache:
    """Thread-safe in-memory cache with LRU eviction."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expired': 0
        }
    
    def _evict_expired(self):
        """Remove expired entries."""
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self._cache.items():
            if entry.is_expired():
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
            self._stats['expired'] += 1
    
    def _evict_lru(self):
        """Evict least recently used entries if cache is full."""
        while len(self._cache) >= self.max_size:
            # Remove oldest entry (LRU)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            self._stats['evictions'] += 1
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            self._evict_expired()
            
            if key not in self._cache:
                self._stats['misses'] += 1
                return None
            
            entry = self._cache[key]
            if entry.is_expired():
                del self._cache[key]
                self._stats['expired'] += 1
                self._stats['misses'] += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.touch()
            self._stats['hits'] += 1
            
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        with self._lock:
            current_time = time.time()
            expires_at = None
            
            if ttl is not None:
                expires_at = current_time + ttl
            elif self.default_ttl > 0:
                expires_at = current_time + self.default_ttl
            
            entry = CacheEntry(
                value=value,
                created_at=current_time,
                expires_at=expires_at
            )
            
            self._cache[key] = entry
            self._cache.move_to_end(key)
            
            self._evict_lru()
            return True
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._stats = {
                'hits': 0,
                'misses': 0,
                'evictions': 0,
                'expired': 0
            }
    
    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        with self._lock:
            if key not in self._cache:
                return False
            
            entry = self._cache[key]
            if entry.is_expired():
                del self._cache[key]
                self._stats['expired'] += 1
                return False
            
            return True
    
    def keys(self) -> List[str]:
        """Get all non-expired keys."""
        with self._lock:
            self._evict_expired()
            return list(self._cache.keys())
    
    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            self._evict_expired()
            return len(self._cache)
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0
            
            return {
                **self._stats,
                'size': len(self._cache),
                'max_size': self.max_size,
                'hit_rate': hit_rate,
                'total_requests': total_requests
            }

class PersistentCache:
    """Persistent cache with file-based storage."""
    
    def __init__(self, cache_dir: str = "cache", max_file_size: int = 10*1024*1024):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_file_size = max_file_size
        self._lock = Lock()
    
    def _get_file_path(self, key: str) -> Path:
        """Get file path for cache key."""
        # Create safe filename from key
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"
    
    @handle_errors(
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.LOW,
        context={'component': 'cache_system', 'operation': 'persistent_get'},
        return_error_response=False
    )
    def get(self, key: str) -> Optional[Any]:
        """Get value from persistent cache."""
        file_path = self._get_file_path(key)
        
        try:
            with self._lock:
                if not file_path.exists():
                    return None
                
                with open(file_path, 'rb') as f:
                    entry_data = pickle.load(f)
                
                entry = CacheEntry(**entry_data)
                
                if entry.is_expired():
                    file_path.unlink(missing_ok=True)
                    return None
                
                # Update access metadata
                entry.touch()
                with open(file_path, 'wb') as f:
                    pickle.dump(entry.__dict__, f)
                
                return entry.value
                
        except Exception as e:
            handle_database_error(e, {'component': 'cache_system', 'operation': 'persistent_get', 'key': key})
            file_path.unlink(missing_ok=True)
            return None
    
    @handle_errors(
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.LOW,
        context={'component': 'cache_system', 'operation': 'persistent_set'},
        return_error_response=False
    )
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in persistent cache."""
        file_path = self._get_file_path(key)
        
        try:
            current_time = time.time()
            expires_at = None
            
            if ttl is not None:
                expires_at = current_time + ttl
            
            entry = CacheEntry(
                value=value,
                created_at=current_time,
                expires_at=expires_at
            )
            
            # Check if serialized data is too large
            serialized_data = pickle.dumps(entry.__dict__)
            if len(serialized_data) > self.max_file_size:
                logger.warning(f"Cache entry too large for key {key}: {len(serialized_data)} bytes")
                return False
            
            with self._lock:
                with open(file_path, 'wb') as f:
                    f.write(serialized_data)
            
            return True
            
        except Exception as e:
            handle_database_error(e, {'component': 'cache_system', 'operation': 'persistent_set', 'key': key})
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from persistent cache."""
        file_path = self._get_file_path(key)
        
        try:
            with self._lock:
                if file_path.exists():
                    file_path.unlink()
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting from persistent cache: {e}")
            return False
    
    def clear(self):
        """Clear all persistent cache files."""
        try:
            with self._lock:
                for file_path in self.cache_dir.glob("*.cache"):
                    file_path.unlink(missing_ok=True)
        except Exception as e:
            logger.error(f"Error clearing persistent cache: {e}")

class CacheManager:
    """Unified cache manager with multiple cache layers."""
    
    def __init__(
        self,
        memory_cache_size: int = 1000,
        memory_ttl: int = 3600,
        enable_persistent: bool = True,
        persistent_cache_dir: str = "cache"
    ):
        self.memory_cache = MemoryCache(memory_cache_size, memory_ttl)
        self.persistent_cache = PersistentCache(persistent_cache_dir) if enable_persistent else None
        self._key_prefix = ""
    
    def _make_key(self, key: str) -> str:
        """Create prefixed cache key."""
        return f"{self._key_prefix}{key}" if self._key_prefix else key
    
    def set_key_prefix(self, prefix: str):
        """Set key prefix for namespace isolation."""
        self._key_prefix = f"{prefix}:" if prefix else ""
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache (memory first, then persistent)."""
        cache_key = self._make_key(key)
        
        # Try memory cache first
        value = self.memory_cache.get(cache_key)
        if value is not None:
            return value
        
        # Try persistent cache
        if self.persistent_cache:
            value = self.persistent_cache.get(cache_key)
            if value is not None:
                # Populate memory cache
                self.memory_cache.set(cache_key, value)
                return value
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, persistent: bool = True) -> bool:
        """Set value in cache."""
        cache_key = self._make_key(key)
        
        # Set in memory cache
        memory_success = self.memory_cache.set(cache_key, value, ttl)
        
        # Set in persistent cache if enabled
        persistent_success = True
        if persistent and self.persistent_cache:
            persistent_success = self.persistent_cache.set(cache_key, value, ttl)
        
        return memory_success and persistent_success
    
    def delete(self, key: str) -> bool:
        """Delete key from all cache layers."""
        cache_key = self._make_key(key)
        
        memory_deleted = self.memory_cache.delete(cache_key)
        persistent_deleted = True
        
        if self.persistent_cache:
            persistent_deleted = self.persistent_cache.delete(cache_key)
        
        return memory_deleted or persistent_deleted
    
    def clear(self):
        """Clear all cache layers."""
        self.memory_cache.clear()
        if self.persistent_cache:
            self.persistent_cache.clear()
    
    def exists(self, key: str) -> bool:
        """Check if key exists in any cache layer."""
        cache_key = self._make_key(key)
        
        if self.memory_cache.exists(cache_key):
            return True
        
        if self.persistent_cache:
            value = self.persistent_cache.get(cache_key)
            if value is not None:
                # Populate memory cache
                self.memory_cache.set(cache_key, value)
                return True
        
        return False
    
    def stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        memory_stats = self.memory_cache.stats()
        
        stats = {
            'memory': memory_stats,
            'persistent': {
                'enabled': self.persistent_cache is not None
            }
        }
        
        if self.persistent_cache:
            try:
                cache_files = list(self.persistent_cache.cache_dir.glob("*.cache"))
                total_size = sum(f.stat().st_size for f in cache_files)
                stats['persistent'].update({
                    'files': len(cache_files),
                    'total_size_bytes': total_size,
                    'total_size_mb': total_size / (1024 * 1024)
                })
            except Exception as e:
                logger.warning(f"Error getting persistent cache stats: {e}")
        
        return stats

# Utility functions for common caching patterns
def cache_key_for_query(query: str, context: Dict[str, Any] = None) -> str:
    """Generate cache key for query with context."""
    key_data = {'query': query}
    if context:
        key_data['context'] = context
    
    key_str = json.dumps(key_data, sort_keys=True)
    return hashlib.sha256(key_str.encode()).hexdigest()

def cache_key_for_url(url: str, params: Dict[str, Any] = None) -> str:
    """Generate cache key for URL with parameters."""
    key_data = {'url': url}
    if params:
        key_data['params'] = params
    
    key_str = json.dumps(key_data, sort_keys=True)
    return hashlib.sha256(key_str.encode()).hexdigest()

# Global cache manager instance
cache_manager = CacheManager()

# Decorator for caching function results
def cached(ttl: int = 3600, key_func: Optional[callable] = None, persistent: bool = True):
    """Decorator for caching function results."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                key_data = {
                    'func': func.__name__,
                    'args': args,
                    'kwargs': kwargs
                }
                key_str = json.dumps(key_data, sort_keys=True, default=str)
                cache_key = hashlib.sha256(key_str.encode()).hexdigest()
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl=ttl, persistent=persistent)
            
            return result
        
        return wrapper
    return decorator