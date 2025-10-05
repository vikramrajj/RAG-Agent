"""
Comprehensive tests for cache system
"""

import pytest
import time
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from cache_system import (
    CacheEntry, MemoryCache, PersistentCache, CacheManager,
    generate_cache_key, cached
)

class TestCacheEntry:
    """Test cases for CacheEntry"""
    
    def test_cache_entry_creation(self):
        """Test cache entry creation"""
        entry = CacheEntry("test_value", ttl=60)
        assert entry.value == "test_value"
        assert entry.ttl == 60
        assert entry.access_count == 0
        assert isinstance(entry.created_at, float)
        assert isinstance(entry.last_accessed, float)
    
    def test_cache_entry_is_expired(self):
        """Test cache entry expiration"""
        # Entry with short TTL
        entry = CacheEntry("test_value", ttl=0.1)
        assert not entry.is_expired()
        
        time.sleep(0.2)
        assert entry.is_expired()
    
    def test_cache_entry_no_ttl(self):
        """Test cache entry without TTL"""
        entry = CacheEntry("test_value")
        assert not entry.is_expired()
    
    def test_cache_entry_access(self):
        """Test cache entry access tracking"""
        entry = CacheEntry("test_value")
        initial_access_time = entry.last_accessed
        initial_count = entry.access_count
        
        time.sleep(0.01)  # Small delay to ensure time difference
        entry.access()
        
        assert entry.access_count == initial_count + 1
        assert entry.last_accessed > initial_access_time

class TestMemoryCache:
    """Test cases for MemoryCache"""
    
    def setup_method(self):
        """Setup test environment"""
        self.cache = MemoryCache(max_size=3)
    
    def test_set_and_get(self):
        """Test basic set and get operations"""
        self.cache.set("key1", "value1")
        assert self.cache.get("key1") == "value1"
    
    def test_get_nonexistent_key(self):
        """Test getting non-existent key"""
        assert self.cache.get("nonexistent") is None
        assert self.cache.get("nonexistent", "default") == "default"
    
    def test_set_with_ttl(self):
        """Test set with TTL"""
        self.cache.set("key1", "value1", ttl=0.1)
        assert self.cache.get("key1") == "value1"
        
        time.sleep(0.2)
        assert self.cache.get("key1") is None
    
    def test_delete(self):
        """Test delete operation"""
        self.cache.set("key1", "value1")
        assert self.cache.get("key1") == "value1"
        
        self.cache.delete("key1")
        assert self.cache.get("key1") is None
    
    def test_exists(self):
        """Test exists operation"""
        assert not self.cache.exists("key1")
        
        self.cache.set("key1", "value1")
        assert self.cache.exists("key1")
        
        self.cache.delete("key1")
        assert not self.cache.exists("key1")
    
    def test_clear(self):
        """Test clear operation"""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        
        self.cache.clear()
        assert self.cache.get("key1") is None
        assert self.cache.get("key2") is None
        assert len(self.cache._cache) == 0
    
    def test_lru_eviction(self):
        """Test LRU eviction when cache is full"""
        # Fill cache to capacity
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.set("key3", "value3")
        
        # Access key1 to make it recently used
        self.cache.get("key1")
        
        # Add new key, should evict key2 (least recently used)
        self.cache.set("key4", "value4")
        
        assert self.cache.get("key1") == "value1"  # Still exists
        assert self.cache.get("key2") is None      # Evicted
        assert self.cache.get("key3") == "value3"  # Still exists
        assert self.cache.get("key4") == "value4"  # New key
    
    def test_cleanup_expired(self):
        """Test cleanup of expired entries"""
        self.cache.set("key1", "value1", ttl=0.1)
        self.cache.set("key2", "value2")  # No TTL
        
        time.sleep(0.2)
        self.cache._cleanup_expired()
        
        assert self.cache.get("key1") is None
        assert self.cache.get("key2") == "value2"
    
    def test_stats(self):
        """Test cache statistics"""
        stats = self.cache.stats()
        assert stats['size'] == 0
        assert stats['max_size'] == 3
        assert stats['hits'] == 0
        assert stats['misses'] == 0
        
        self.cache.set("key1", "value1")
        self.cache.get("key1")  # Hit
        self.cache.get("key2")  # Miss
        
        stats = self.cache.stats()
        assert stats['size'] == 1
        assert stats['hits'] == 1
        assert stats['misses'] == 1

class TestPersistentCache:
    """Test cases for PersistentCache"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = PersistentCache(cache_dir=self.temp_dir, max_size=100*1024)  # 100KB
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_set_and_get(self):
        """Test basic set and get operations"""
        self.cache.set("key1", "value1")
        assert self.cache.get("key1") == "value1"
    
    def test_persistence(self):
        """Test data persistence across cache instances"""
        self.cache.set("key1", "value1")
        
        # Create new cache instance with same directory
        new_cache = PersistentCache(cache_dir=self.temp_dir)
        assert new_cache.get("key1") == "value1"
    
    def test_set_with_ttl(self):
        """Test set with TTL"""
        self.cache.set("key1", "value1", ttl=0.1)
        assert self.cache.get("key1") == "value1"
        
        time.sleep(0.2)
        assert self.cache.get("key1") is None
    
    def test_delete(self):
        """Test delete operation"""
        self.cache.set("key1", "value1")
        assert self.cache.get("key1") == "value1"
        
        self.cache.delete("key1")
        assert self.cache.get("key1") is None
        
        # Check file is actually deleted
        key_file = Path(self.temp_dir) / f"key1.cache"
        assert not key_file.exists()
    
    def test_clear(self):
        """Test clear operation"""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        
        self.cache.clear()
        assert self.cache.get("key1") is None
        assert self.cache.get("key2") is None
        
        # Check directory is empty
        cache_files = list(Path(self.temp_dir).glob("*.cache"))
        assert len(cache_files) == 0
    
    def test_size_limit_eviction(self):
        """Test eviction when size limit is reached"""
        # Create cache with very small size limit
        small_cache = PersistentCache(cache_dir=self.temp_dir, max_size=100)
        
        # Add data that exceeds size limit
        large_value = "x" * 50
        small_cache.set("key1", large_value)
        small_cache.set("key2", large_value)
        small_cache.set("key3", large_value)  # Should trigger eviction
        
        # At least one key should be evicted
        existing_keys = [
            small_cache.exists("key1"),
            small_cache.exists("key2"),
            small_cache.exists("key3")
        ]
        assert sum(existing_keys) < 3

class TestCacheManager:
    """Test cases for CacheManager"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_manager = CacheManager(
            memory_cache_size=3,
            persistent_cache_dir=self.temp_dir,
            enable_redis=False  # Disable Redis for testing
        )
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_set_and_get_memory_cache(self):
        """Test set and get from memory cache"""
        self.cache_manager.set("key1", "value1", cache_level="memory")
        assert self.cache_manager.get("key1") == "value1"
    
    def test_set_and_get_persistent_cache(self):
        """Test set and get from persistent cache"""
        self.cache_manager.set("key1", "value1", cache_level="persistent")
        assert self.cache_manager.get("key1") == "value1"
    
    def test_cache_hierarchy(self):
        """Test cache hierarchy (memory -> persistent -> redis)"""
        # Set in persistent cache only
        self.cache_manager.persistent_cache.set("key1", "value1")
        
        # Get should find it and promote to memory cache
        value = self.cache_manager.get("key1")
        assert value == "value1"
        assert self.cache_manager.memory_cache.exists("key1")
    
    def test_set_with_ttl(self):
        """Test set with TTL"""
        self.cache_manager.set("key1", "value1", ttl=0.1)
        assert self.cache_manager.get("key1") == "value1"
        
        time.sleep(0.2)
        assert self.cache_manager.get("key1") is None
    
    def test_delete(self):
        """Test delete from all cache levels"""
        self.cache_manager.set("key1", "value1")
        assert self.cache_manager.get("key1") == "value1"
        
        self.cache_manager.delete("key1")
        assert self.cache_manager.get("key1") is None
        assert not self.cache_manager.memory_cache.exists("key1")
        assert not self.cache_manager.persistent_cache.exists("key1")
    
    def test_clear_all(self):
        """Test clearing all cache levels"""
        self.cache_manager.set("key1", "value1")
        self.cache_manager.set("key2", "value2")
        
        self.cache_manager.clear()
        assert self.cache_manager.get("key1") is None
        assert self.cache_manager.get("key2") is None
    
    def test_stats(self):
        """Test cache statistics"""
        stats = self.cache_manager.stats()
        assert 'memory' in stats
        assert 'persistent' in stats
        assert 'total_operations' in stats
    
    @patch('cache_system.redis')
    def test_redis_integration(self, mock_redis):
        """Test Redis integration"""
        # Mock Redis client
        mock_redis_client = Mock()
        mock_redis.Redis.return_value = mock_redis_client
        mock_redis_client.ping.return_value = True
        mock_redis_client.get.return_value = json.dumps("redis_value").encode()
        
        # Create cache manager with Redis enabled
        cache_manager = CacheManager(enable_redis=True)
        
        # Test Redis operations
        mock_redis_client.get.return_value = json.dumps("redis_value").encode()
        value = cache_manager.get("redis_key")
        assert value == "redis_value"

class TestUtilityFunctions:
    """Test cases for utility functions"""
    
    def test_generate_cache_key_simple(self):
        """Test simple cache key generation"""
        key = generate_cache_key("prefix", "arg1", "arg2")
        assert key.startswith("prefix:")
        assert "arg1" in key
        assert "arg2" in key
    
    def test_generate_cache_key_with_kwargs(self):
        """Test cache key generation with kwargs"""
        key = generate_cache_key("prefix", "arg1", param1="value1", param2="value2")
        assert key.startswith("prefix:")
        assert "arg1" in key
        assert "param1=value1" in key
        assert "param2=value2" in key
    
    def test_generate_cache_key_consistency(self):
        """Test cache key consistency"""
        key1 = generate_cache_key("prefix", "arg1", param="value")
        key2 = generate_cache_key("prefix", "arg1", param="value")
        assert key1 == key2
    
    def test_cached_decorator(self):
        """Test cached decorator"""
        call_count = 0
        
        @cached(ttl=60)
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # First call should execute function
        result1 = expensive_function(1, 2)
        assert result1 == 3
        assert call_count == 1
        
        # Second call should use cache
        result2 = expensive_function(1, 2)
        assert result2 == 3
        assert call_count == 1  # Function not called again
        
        # Different arguments should execute function
        result3 = expensive_function(2, 3)
        assert result3 == 5
        assert call_count == 2
    
    def test_cached_decorator_with_ttl(self):
        """Test cached decorator with TTL"""
        call_count = 0
        
        @cached(ttl=0.1)
        def function_with_ttl(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call
        result1 = function_with_ttl(5)
        assert result1 == 10
        assert call_count == 1
        
        # Second call within TTL
        result2 = function_with_ttl(5)
        assert result2 == 10
        assert call_count == 1
        
        # Wait for TTL to expire
        time.sleep(0.2)
        
        # Third call after TTL expiry
        result3 = function_with_ttl(5)
        assert result3 == 10
        assert call_count == 2
    
    def test_cached_decorator_custom_cache(self):
        """Test cached decorator with custom cache"""
        custom_cache = MemoryCache(max_size=10)
        call_count = 0
        
        @cached(cache=custom_cache)
        def function_with_custom_cache(x):
            nonlocal call_count
            call_count += 1
            return x ** 2
        
        result1 = function_with_custom_cache(4)
        assert result1 == 16
        assert call_count == 1
        
        # Verify it's using the custom cache
        assert custom_cache.exists("function_with_custom_cache:4")
        
        result2 = function_with_custom_cache(4)
        assert result2 == 16
        assert call_count == 1

class TestIntegration:
    """Integration tests for cache system"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_full_cache_pipeline(self):
        """Test complete cache pipeline"""
        cache_manager = CacheManager(
            memory_cache_size=2,
            persistent_cache_dir=self.temp_dir,
            enable_redis=False
        )
        
        # Test cache hierarchy
        cache_manager.set("key1", "value1")
        cache_manager.set("key2", "value2")
        cache_manager.set("key3", "value3")  # Should evict key1 from memory
        
        # key1 should be in persistent cache but not memory
        assert cache_manager.get("key1") == "value1"
        assert cache_manager.memory_cache.exists("key1")  # Promoted back to memory
        
        # Test TTL across cache levels
        cache_manager.set("ttl_key", "ttl_value", ttl=0.1)
        assert cache_manager.get("ttl_key") == "ttl_value"
        
        time.sleep(0.2)
        assert cache_manager.get("ttl_key") is None
    
    def test_cache_with_complex_data(self):
        """Test caching with complex data types"""
        cache_manager = CacheManager(
            persistent_cache_dir=self.temp_dir,
            enable_redis=False
        )
        
        complex_data = {
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "tuple": (4, 5, 6),
            "string": "test"
        }
        
        cache_manager.set("complex_key", complex_data)
        retrieved_data = cache_manager.get("complex_key")
        
        assert retrieved_data == complex_data

if __name__ == '__main__':
    pytest.main([__file__])