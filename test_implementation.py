# test_implementation.py
import os
import logging
import time
from config import ConfigManager
from retriever import RAGRetriever
from credential_manager import get_outlook_credentials, setup_credentials


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_config():
    """Test environment variable integration in config.py"""
    logger.info("Testing config integration...")
    config = ConfigManager.get_config()
    
    # Print key config values
    logger.info(f"LLM Model: {config.llm.model_name}")
    logger.info(f"RAG Embedding Model: {config.rag.embedding_model}")
    logger.info(f"Max Worker Threads: {config.performance.max_worker_threads}")
    
    return True

def test_credential_manager():
    """Test secure credential manager functionality"""
    logger.info("Testing credential manager...")
    
    # Test setup credentials (this would normally be done once during setup)
    # In a real test, you'd use test credentials
    test_email = "test@example.com"
    test_password = "test_password"
    
    # Just test the retrieval function without actually setting up
    try:
        email, _ = get_outlook_credentials()
        logger.info(f"Retrieved email: {email}")
        return True
    except Exception as e:
        logger.error(f"Credential manager test failed: {e}")
        return False

def test_hybrid_search():
    """Test hybrid search in retriever.py"""
    logger.info("Testing hybrid search...")
    
    # Initialize retriever
    retriever = RAGRetriever()
    
    # Test queries
    test_queries = [
        "Outlook won't open",
        "email sync issues",
        "password problems"
    ]
    
    for query in test_queries:
        logger.info(f"Testing query: '{query}'")
        results = retriever.retrieve(query, k=3)
        logger.info(f"Found {len(results)} results")
        
        # Print match types to verify hybrid search
        match_types = [r.get('match_type', 'unknown') for r in results]
        logger.info(f"Match types: {match_types}")
    
    return True

def test_caching():
    """Test caching layer performance"""
    logger.info("Testing caching performance...")
    
    # Initialize retriever
    retriever = RAGRetriever()
    
    # Test query
    query = "Outlook crashes on startup"
    
    # First call (should be cache miss)
    start_time = time.time()
    results1 = retriever.retrieve(query)
    first_call_time = time.time() - start_time
    logger.info(f"First call (cache miss) took {first_call_time:.4f} seconds")
    
    # Second call with same query (should be cache hit)
    start_time = time.time()
    results2 = retriever.retrieve(query)
    second_call_time = time.time() - start_time
    logger.info(f"Second call (cache hit) took {second_call_time:.4f} seconds")
    
    # Verify cache is working
    if second_call_time < first_call_time:
        logger.info("Cache is working correctly - second call was faster")
        return True
    else:
        logger.warning("Cache may not be working as expected")
        return False

def run_tests():
    """Run all tests"""
    tests = [
        ("Config Integration", test_config),
        ("Credential Manager", test_credential_manager),
        ("Hybrid Search", test_hybrid_search),
        ("Caching Layer", test_caching)
    ]
    
    results = {}
    
    for name, test_func in tests:
        logger.info(f"\n{'='*50}\nRunning test: {name}\n{'='*50}")
        try:
            success = test_func()
            results[name] = "PASS" if success else "FAIL"
        except Exception as e:
            logger.error(f"Test failed with exception: {e}")
            results[name] = "ERROR"
    
    # Print summary
    logger.info("\n\n" + "="*50)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("="*50)
    
    for name, result in results.items():
        logger.info(f"{name}: {result}")

if __name__ == "__main__":
    run_tests()