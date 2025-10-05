# rag_loader.py
"""
Enhanced RAG loader with comprehensive configuration management, error handling, and data validation.
Provides robust functionality for loading, embedding, and indexing troubleshooting data.
"""

import json
import faiss
import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from sentence_transformers import SentenceTransformer
from standardized_error_handler import (
    handle_errors, ErrorCategory, ErrorSeverity,
    handle_database_error, handle_validation_error
)
from data_validator import get_rag_data_validator
from config import ConfigManager

logger = logging.getLogger(__name__)

class RAGLoader:
    """Enhanced RAG loader with comprehensive error handling and configuration management."""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Initialize RAG loader with configuration management.
        
        Args:
            config_manager: Optional ConfigManager instance
        """
        self.config = config_manager or ConfigManager.get_config()
        self.model = None
        self.index = None
        self.metadata_store = []
        self.embedding_dimension = 384  # Default for all-MiniLM-L6-v2
        self.validator = get_rag_data_validator()
        
        # Initialize components
        self._initialize_model()
        self._initialize_index()
        
        logger.info("RAGLoader initialized successfully")
    
    @handle_errors(
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.HIGH,
        context={'component': 'rag_loader', 'operation': 'initialize_model'},
        return_error_response=False
    )
    def _initialize_model(self):
        """Initialize the sentence transformer model."""
        try:
            model_name = self.config.rag.embedding_model
            logger.info(f"Loading sentence transformer model: {model_name}")
            
            self.model = SentenceTransformer(model_name)
            
            # Get actual embedding dimension
            test_embedding = self.model.encode(["test"])
            self.embedding_dimension = len(test_embedding[0])
            
            logger.info(f"Model loaded successfully. Embedding dimension: {self.embedding_dimension}")
            
        except Exception as e:
            error_msg = f"Failed to initialize embedding model: {str(e)}"
            logger.error(error_msg)
            handle_database_error(e, {'component': 'rag_loader', 'operation': 'initialize_model'})
            raise RuntimeError(error_msg)
    
    @handle_errors(
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.MEDIUM,
        context={'component': 'rag_loader', 'operation': 'initialize_index'},
        return_error_response=False
    )
    def _initialize_index(self):
        """Initialize the FAISS index."""
        try:
            # Create new index with proper dimension
            self.index = faiss.IndexFlatL2(self.embedding_dimension)
            logger.info(f"FAISS index initialized with dimension: {self.embedding_dimension}")
            
        except Exception as e:
            error_msg = f"Failed to initialize FAISS index: {str(e)}"
            logger.error(error_msg)
            handle_database_error(e, {'component': 'rag_loader', 'operation': 'initialize_index'})
            raise RuntimeError(error_msg)
    
    def validate_log_entry(self, log_entry: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate a log entry for required fields and data quality.
        
        Args:
            log_entry: Dictionary containing log entry data
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        required_fields = ['title', 'symptoms', 'fix_steps']
        
        # Check required fields
        for field in required_fields:
            if field not in log_entry:
                return False, f"Missing required field: {field}"
            
            if not log_entry[field]:
                return False, f"Empty value for required field: {field}"
        
        # Validate data types
        if not isinstance(log_entry['title'], str):
            return False, "Title must be a string"
        
        if not isinstance(log_entry['symptoms'], list):
            return False, "Symptoms must be a list"
        
        if not isinstance(log_entry['fix_steps'], list):
            return False, "Fix steps must be a list"
        
        # Check for minimum content length
        if len(log_entry['title'].strip()) < 3:
            return False, "Title must be at least 3 characters long"
        
        if len(log_entry['symptoms']) == 0:
            return False, "At least one symptom must be provided"
        
        if len(log_entry['fix_steps']) == 0:
            return False, "At least one fix step must be provided"
        
        return True, "Valid"
    
    @handle_errors(
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.MEDIUM,
        context={'component': 'rag_loader', 'operation': 'embed_text'},
        return_error_response=False
    )
    def embed_text(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for text with validation.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None if failed
        """
        try:
            if not text or not isinstance(text, str):
                logger.warning("Invalid text provided for embedding")
                return None
            
            # Clean and validate text
            text = text.strip()
            if len(text) < 3:
                logger.warning("Text too short for meaningful embedding")
                return None
            
            # Limit text length to prevent memory issues
            if len(text) > 10000:
                text = text[:10000]
                logger.warning("Text truncated to 10000 characters for embedding")
            
            embedding = self.model.encode([text])[0]
            logger.debug(f"Generated embedding for text: {text[:50]}...")
            
            return embedding.tolist()
            
        except Exception as e:
            error_msg = f"Failed to generate embedding: {str(e)}"
            logger.error(error_msg)
            handle_validation_error(e, {'component': 'rag_loader', 'operation': 'embed_text', 'text_length': len(text) if text else 0})
            return None
    
    @handle_errors(
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.MEDIUM,
        context={'component': 'rag_loader', 'operation': 'load_logs'},
        return_error_response=False
    )
    def load_logs(self, json_path: str) -> Dict[str, Any]:
        """
        Load and process logs from JSON file with comprehensive validation.
        
        Args:
            json_path: Path to JSON file containing logs
            
        Returns:
            Dictionary with loading results and statistics
        """
        logger.info(f"Loading logs from: {json_path}")
        
        results = {
            'total_entries': 0,
            'processed_entries': 0,
            'skipped_entries': 0,
            'errors': [],
            'validation_errors': []
        }
        
        try:
            # Validate file exists
            if not Path(json_path).exists():
                error_msg = f"JSON file not found: {json_path}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                return results
            
            # Load JSON data
            with open(json_path, 'r', encoding='utf-8') as f:
                logs = json.load(f)

            if not isinstance(logs, list):
                error_msg = "JSON file must contain a list of log entries"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                return results
            
            results['total_entries'] = len(logs)
            logger.info(f"Found {len(logs)} log entries")
            
            # Process each log entry
            for i, log in enumerate(logs):
                try:
                    # Use comprehensive validation from data validator
                    validation_result = self.validator.validate_troubleshooting_entry(log)
                    if not validation_result.is_valid:
                        logger.warning(f"Invalid log entry at index {i}: {validation_result.errors}")
                        results['validation_errors'].extend([f"Index {i}: {error}" for error in validation_result.errors])
                        results['skipped_entries'] += 1
                        continue
                    
                    # Use sanitized data if available
                    sanitized_log = validation_result.sanitized_data or log
                    
                    # Create text representation
                    text = f"{sanitized_log['title']} {' '.join(sanitized_log['symptoms'])} {' '.join(sanitized_log['fix_steps'])}"
                    
                    # Validate text before embedding
                    text_validation = self.validator.validate_query(text)
                    if not text_validation.is_valid:
                        logger.warning(f"Text validation failed for entry at index {i}: {text_validation.errors}")
                        results['skipped_entries'] += 1
                        continue
                    
                    text = text_validation.sanitized_data or text
                    
                    # Generate embedding
                    embedding = self.embed_text(text)
                    if embedding is None:
                        logger.warning(f"Failed to generate embedding for entry at index {i}")
                        results['skipped_entries'] += 1
                        continue
                    
                    # Validate embedding
                    embedding_validation = self.validator.validate_embedding(embedding)
                    if not embedding_validation.is_valid:
                        logger.warning(f"Embedding validation failed for entry at index {i}: {embedding_validation.errors}")
                        results['skipped_entries'] += 1
                        continue
                    
                    # Add to index
                    import numpy as np
                    self.index.add(np.array([embedding]).astype('float32'))
                    
                    # Store metadata
                    metadata = {
                        'title': sanitized_log['title'],
                        'symptoms': sanitized_log['symptoms'],
                        'fix_steps': sanitized_log['fix_steps'],
                        'original_index': i,
                        'text_length': len(text)
                    }
                    
                    # Add optional fields if present
                    for field in ['error_code', 'severity', 'tags', 'category']:
                        if field in sanitized_log:
                            metadata[field] = sanitized_log[field]
                    
                    self.metadata_store.append(metadata)
                    results['processed_entries'] += 1
                    
                except Exception as e:
                    error_msg = f"Error processing log entry at index {i}: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    results['skipped_entries'] += 1
            
            logger.info(f"Log loading completed. Processed: {results['processed_entries']}, "
                       f"Skipped: {results['skipped_entries']}, Errors: {len(results['errors'])}")
            
            return results
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON format in {json_path}: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            return results
        except Exception as e:
            error_msg = f"Failed to load logs from {json_path}: {str(e)}"
            logger.error(error_msg)
            handle_database_error(e, {'component': 'rag_loader', 'operation': 'load_logs', 'file_path': json_path})
            results['errors'].append(error_msg)
            return results
    
    @handle_errors(
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.HIGH,
        context={'component': 'rag_loader', 'operation': 'save_index'},
        return_error_response=False
    )
    def save_index(self, index_path: Optional[str] = None, metadata_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Save FAISS index and metadata with comprehensive error handling.
        
        Args:
            index_path: Optional custom path for index file
            metadata_path: Optional custom path for metadata file
            
        Returns:
            Dictionary with save results
        """
        logger.info("Saving FAISS index and metadata")
        
        results = {
            'index_saved': False,
            'metadata_saved': False,
            'index_path': None,
            'metadata_path': None,
            'errors': []
        }
        
        try:
            # Use configuration paths if not provided
            if index_path is None:
                index_path = self.config.rag.index_path
            if metadata_path is None:
                metadata_path = self.config.rag.metadata_path
            
            # Ensure directory exists
            Path(index_path).parent.mkdir(parents=True, exist_ok=True)
            Path(metadata_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Save FAISS index
            try:
                faiss.write_index(self.index, index_path)
                results['index_saved'] = True
                results['index_path'] = index_path
                logger.info(f"FAISS index saved to: {index_path}")
            except Exception as e:
                error_msg = f"Failed to save FAISS index: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
            
            # Save metadata
            try:
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(self.metadata_store, f, indent=4, ensure_ascii=False)
                results['metadata_saved'] = True
                results['metadata_path'] = metadata_path
                logger.info(f"Metadata saved to: {metadata_path}")
            except Exception as e:
                error_msg = f"Failed to save metadata: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
            
            # Log summary
            if results['index_saved'] and results['metadata_saved']:
                logger.info("Index and metadata saved successfully")
            else:
                logger.warning("Some files failed to save. Check errors for details.")
            
            return results
            
        except Exception as e:
            error_msg = f"Failed to save index and metadata: {str(e)}"
            logger.error(error_msg)
            handle_database_error(e, {'component': 'rag_loader', 'operation': 'save_index'})
            results['errors'].append(error_msg)
            return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the loaded data."""
        return {
            'total_entries': len(self.metadata_store),
            'index_size': self.index.ntotal if self.index else 0,
            'embedding_dimension': self.embedding_dimension,
            'model_name': self.config.rag.embedding_model,
            'average_text_length': sum(entry.get('text_length', 0) for entry in self.metadata_store) / len(self.metadata_store) if self.metadata_store else 0,
            'categories': list(set(entry.get('category', 'unknown') for entry in self.metadata_store)),
            'severities': list(set(entry.get('severity', 'unknown') for entry in self.metadata_store)),
            'error_codes': [entry.get('error_code') for entry in self.metadata_store if entry.get('error_code')]
        }
    
    def clear_data(self):
        """Clear all loaded data and reset to initial state."""
        logger.info("Clearing all loaded data")
        
        # Reset index
        if self.index:
            self.index = faiss.IndexFlatL2(self.embedding_dimension)
        
        # Clear metadata
        self.metadata_store.clear()
        
        logger.info("Data cleared successfully")

# Global RAG loader instance
_rag_loader = None

def get_rag_loader() -> RAGLoader:
    """Get or create global RAG loader instance."""
    global _rag_loader
    if _rag_loader is None:
        _rag_loader = RAGLoader()
    return _rag_loader

# Legacy functions for backward compatibility
def embed_text(text: str) -> Optional[List[float]]:
    """Legacy function for backward compatibility."""
    loader = get_rag_loader()
    return loader.embed_text(text)

def load_logs(json_path: str) -> Dict[str, Any]:
    """Legacy function for backward compatibility."""
    loader = get_rag_loader()
    return loader.load_logs(json_path)

def save_index(index_path: str = 'outlook_index.faiss'):
    """Legacy function for backward compatibility."""
    loader = get_rag_loader()
    results = loader.save_index(index_path, 'metadata.json')
    
    if results['index_saved'] and results['metadata_saved']:
        print("✅ Index and metadata saved successfully")
    else:
        print("❌ Some files failed to save")
        for error in results['errors']:
            print(f"  Error: {error}")

if __name__ == "__main__":
    # Test the enhanced RAG loader
    print("🔍 Enhanced RAG Loader Test")
    print("=" * 50)
    
    try:
        loader = RAGLoader()
        
        # Test with sample data if available
        sample_json_path = "outlook_logs.json"
        if Path(sample_json_path).exists():
            print(f"Loading logs from: {sample_json_path}")
            results = loader.load_logs(sample_json_path)
            
            print(f"Total entries: {results['total_entries']}")
            print(f"Processed: {results['processed_entries']}")
            print(f"Skipped: {results['skipped_entries']}")
            print(f"Errors: {len(results['errors'])}")
            
            if results['errors']:
                print("\nErrors:")
                for error in results['errors']:
                    print(f"  - {error}")
            
            # Save index
            print("\nSaving index and metadata...")
            save_results = loader.save_index()
            
            if save_results['index_saved'] and save_results['metadata_saved']:
                print("✅ Index and metadata saved successfully")
            else:
                print("❌ Some files failed to save")
            
            # Show statistics
            print("\nStatistics:")
            stats = loader.get_statistics()
            for key, value in stats.items():
                print(f"  {key}: {value}")
                
        else:
            print(f"Sample file {sample_json_path} not found")
            print("Creating test index with empty data...")
            
            # Save empty index
            save_results = loader.save_index()
            if save_results['index_saved'] and save_results['metadata_saved']:
                print("✅ Empty index and metadata saved successfully")
            else:
                print("❌ Failed to save empty index")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.error(f"RAG loader test failed: {e}")