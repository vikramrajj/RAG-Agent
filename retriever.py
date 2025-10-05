# retriever.py
import faiss
import json
import numpy as np
import logging
import re
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import os
from pathlib import Path
from cache_system import cached
import asyncio
from standardized_error_handler import (
    handle_errors, handle_async_errors, ErrorCategory, ErrorSeverity,
    handle_database_error, handle_validation_error
)
from data_validator import get_rag_data_validator, validate_input

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGRetriever:
    def __init__(self, index_path="outlook_index.faiss", metadata_path="metadata.json", model_name='all-MiniLM-L6-v2'):
        """
        Initialize RAG retriever with better error handling and configuration
        
        Args:
            index_path: Path to FAISS index file
            metadata_path: Path to metadata JSON file
            model_name: Sentence transformer model name
        """
        self.model_name = model_name
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.model = None
        self.index = None
        self.metadata_store = []
        self.validator = get_rag_data_validator()
        
        # Query expansion mappings for better retrieval
        self.query_expansions = {
            "won't open": ["startup", "launch", "boot", "initialize", "start"],
            "slow": ["performance", "lag", "hang", "freeze", "timeout"],
            "crash": ["error", "failure", "stop", "terminate", "exception"],
            "email": ["mail", "message", "send", "receive", "inbox"],
            "login": ["authentication", "sign in", "password", "credentials"],
            "sync": ["synchronize", "update", "refresh", "download"]
        }
        
        self._load_components()
    
    @handle_errors(
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.HIGH,
        context={'component': 'rag_retriever', 'operation': 'load_components'},
        return_error_response=False
    )
    def _load_components(self):
        """Load model, index, and metadata with proper error handling"""
        try:
            # Load sentence transformer model
            logger.info(f"Loading sentence transformer model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Model loaded successfully")
            
            # Load FAISS index
            if os.path.exists(self.index_path):
                self.index = faiss.read_index(self.index_path)
                logger.info(f"FAISS index loaded from {self.index_path}")
            else:
                logger.error(f"FAISS index not found at {self.index_path}")
                raise FileNotFoundError(f"Index file not found: {self.index_path}")
            
            # Load metadata
            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    self.metadata_store = json.load(f)
                logger.info(f"Metadata loaded: {len(self.metadata_store)} entries")
            else:
                logger.error(f"Metadata file not found at {self.metadata_path}")
                raise FileNotFoundError(f"Metadata file not found: {self.metadata_path}")
                
        except Exception as e:
            logger.error(f"Failed to load RAG components: {str(e)}")
            handle_database_error(e, {'component': 'rag_retriever', 'operation': 'load_components'})
            raise
    
    @cached(ttl=3600)
    def expand_query(self, query: str) -> str:
        """
        Expand query with related terms for better retrieval
        
        Args:
            query: Original user query
            
        Returns:
            Expanded query string
        """
        # Validate input query
        validation_result = self.validator.validate_query(query)
        if not validation_result.is_valid:
            logger.warning(f"Query validation failed: {validation_result.errors}")
            query = validation_result.sanitized_data or query
        
        query_lower = query.lower()
        expanded_terms = []
        
        for trigger, expansions in self.query_expansions.items():
            if trigger in query_lower:
                expanded_terms.extend(expansions)
        
        # Add original query terms
        expanded_query = query
        if expanded_terms:
            expanded_query += " " + " ".join(expanded_terms)
            logger.info(f"Expanded query: '{query}' -> '{expanded_query}'")
        
        return expanded_query
    
    def calculate_relevance_score(self, distance: float, max_distance: float) -> float:
        """
        Convert FAISS distance to relevance score (0-1, higher is better)
        
        Args:
            distance: FAISS L2 distance
            max_distance: Maximum distance in the result set
            
        Returns:
            Relevance score between 0 and 1
        """
        if max_distance == 0:
            return 1.0
        return max(0.0, 1.0 - (distance / max_distance))
    
    def filter_by_relevance(self, results: List[Dict], min_relevance: float = 0.3) -> List[Dict]:
        """
        Filter results by minimum relevance score
        
        Args:
            results: List of retrieval results with relevance scores
            min_relevance: Minimum relevance threshold (0-1)
            
        Returns:
            Filtered results list
        """
        filtered = [r for r in results if r.get('relevance_score', 0) >= min_relevance]
        logger.info(f"Filtered {len(results)} -> {len(filtered)} results (min_relevance={min_relevance})")
        return filtered
    
    @cached(ttl=3600)
    async def retrieve_async(self, query: str, k: int = 5, min_relevance: float = 0.3, expand_query: bool = True) -> List[Dict]:
        try:
            return await asyncio.to_thread(self.retrieve, query, k, min_relevance, expand_query)
        except Exception as e:
            logger.error(f"Async retrieval failed: {str(e)}")
            raise
    
    def retrieve(self, query: str, k: int = 5, min_relevance: float = 0.3, expand_query: bool = True) -> List[Dict]:
        """
        Retrieve relevant troubleshooting information with enhanced accuracy using hybrid search
        
        Args:
            query: User query string
            k: Number of results to retrieve
            min_relevance: Minimum relevance score threshold
            expand_query: Whether to expand query with related terms
            
        Returns:
            List of relevant troubleshooting entries with relevance scores
        """
        try:
            if not self.model or not self.index:
                raise RuntimeError("RAG components not properly loaded")
            
            # Validate input parameters
            query_validation = self.validator.validate_query(query)
            if not query_validation.is_valid:
                logger.error(f"Query validation failed: {query_validation.errors}")
                return []
            
            # Use sanitized query
            query = query_validation.sanitized_data or query
            
            # Validate relevance score
            relevance_validation = self.validator.validate_embedding([min_relevance])
            if not relevance_validation.is_valid:
                min_relevance = 0.3  # Default fallback
                logger.warning("Invalid relevance score, using default")
            
            # Expand query if enabled
            search_query = self.expand_query(query) if expand_query else query
            
            # Generate query embedding
            query_vector = self.model.encode([search_query])[0].reshape(1, -1)
            
            # Validate embedding
            embedding_validation = self.validator.validate_embedding(query_vector[0].tolist())
            if not embedding_validation.is_valid:
                logger.error("Generated embedding validation failed")
                return []
            
            # Search FAISS index (vector search)
            distances, indices = self.index.search(query_vector.astype('float32'), k * 2)  # Get more results for filtering
            
            # Process vector search results
            vector_results = []
            max_distance = max(distances[0]) if len(distances[0]) > 0 else 0
            
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx >= 0 and idx < len(self.metadata_store):  # Valid index
                    relevance_score = self.calculate_relevance_score(distance, max_distance)
                    
                    result = {
                        **self.metadata_store[idx],
                        'relevance_score': relevance_score,
                        'search_rank': i + 1,
                        'distance': float(distance),
                        'match_type': 'vector'
                    }
                    
                    # Validate search result
                    result_validation = self.validator.validate_search_result(result)
                    if result_validation.is_valid:
                        vector_results.append(result)
                    else:
                        logger.warning(f"Search result validation failed: {result_validation.errors}")
            
            # Perform keyword search on metadata
            keyword_results = self._keyword_search(query, min_relevance)
            
            # Combine results with deduplication
            combined_results = self._combine_search_results(vector_results, keyword_results)
            
            # Filter by relevance
            filtered_results = self.filter_by_relevance(combined_results, min_relevance)
            
            # Sort by relevance score (highest first)
            filtered_results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            logger.info(f"Retrieved {len(filtered_results)} relevant results for query: '{query}' (hybrid search)")
            
            return filtered_results[:k]  # Limit to k results
            
        except Exception as e:
            logger.error(f"Error during retrieval: {str(e)}")
            handle_database_error(e, {'component': 'rag_retriever', 'operation': 'retrieve', 'query': query})
            return []
            
    @cached(ttl=3600)
    def _keyword_search(self, query: str, min_relevance: float = 0.3) -> List[Dict]:
        """
        Perform keyword-based search on document metadata
        
        Args:
            query: User query
            min_relevance: Minimum relevance score threshold
            
        Returns:
            List of relevant documents with metadata
        """
        results = []
        # Preprocess query once
        query_terms = set(query.lower().split())
        if not query_terms:
            return results
            
        # Pre-calculate query term count for repeated use
        query_term_count = len(query_terms)
        
        # Use a list comprehension with early filtering
        for doc in self.metadata_store:
            # Extract text fields for matching - only process fields that exist
            doc_text_parts = []
            if 'title' in doc and doc['title']:
                doc_text_parts.append(doc['title'].lower())
            if 'content' in doc and doc['content']:
                doc_text_parts.append(doc['content'].lower())
            if 'symptoms' in doc and doc['symptoms']:
                doc_text_parts.append(' '.join(doc['symptoms']).lower())
                
            # Skip empty documents
            if not doc_text_parts:
                continue
                
            # Join parts only once
            doc_text = ' '.join(doc_text_parts)
            doc_terms = set(doc_text.split())
            
            # Skip if document has no terms
            if not doc_terms:
                continue
                
            # Calculate score using pre-computed query term count
            matching_terms = query_terms.intersection(doc_terms)
            if matching_terms:  # Only calculate score if there are matches
                score = len(matching_terms) / query_term_count
                
                if score >= min_relevance:
                    result = doc.copy()
                    result['relevance_score'] = score
                    result['match_type'] = 'keyword'
                    result['search_rank'] = 0
                    results.append(result)
        
        return results
        
    def _combine_search_results(self, vector_results: List[Dict], keyword_results: List[Dict]) -> List[Dict]:
        """
        Combine and deduplicate results from vector and keyword search
        
        Args:
            vector_results: Results from vector search
            keyword_results: Results from keyword search
            
        Returns:
            Combined unique results with boosted scores for items found by both methods
        """
        # Fast path for empty results
        if not vector_results and not keyword_results:
            return []
        if not vector_results:
            return keyword_results
        if not keyword_results:
            return vector_results
            
        # Create a dictionary to track unique documents by error_code or title
        combined = {}
        
        # Process vector results - use a more efficient approach
        for result in vector_results:
            doc_id = result.get('error_code', '') or result.get('title', '')
            if not doc_id:  # Skip items without an identifier
                continue
            combined[doc_id] = result
        
        # Boost factor as constant
        BOOST_FACTOR = 1.2
        
        # Process keyword results with optimized logic
        for result in keyword_results:
            doc_id = result.get('error_code', '') or result.get('title', '')
            if not doc_id:  # Skip items without an identifier
                continue
                
            if doc_id in combined:
                # Document found in both searches, boost score
                vector_score = combined[doc_id]['relevance_score']
                keyword_score = result['relevance_score']
                # Boost score but cap at 1.0
                combined[doc_id]['relevance_score'] = min(1.0, vector_score * BOOST_FACTOR)
                combined[doc_id]['match_type'] = 'hybrid'
            else:
                # New document from keyword search
                combined[doc_id] = result
        
        return list(combined.values())
    
    def get_related_issues(self, current_issue: Dict, k: int = 3) -> List[Dict]:
        """
        Find related issues based on tags and symptoms
        
        Args:
            current_issue: Current troubleshooting issue
            k: Number of related issues to return
            
        Returns:
            List of related troubleshooting issues
        """
        try:
            current_tags = set(current_issue.get('tags', []))
            current_symptoms = ' '.join(current_issue.get('symptoms', []))
            
            # Search based on symptoms
            related = self.retrieve(current_symptoms, k=k+1, min_relevance=0.2)
            
            # Filter out the current issue and score by tag overlap
            related_issues = []
            for issue in related:
                if issue.get('error_code') != current_issue.get('error_code'):
                    issue_tags = set(issue.get('tags', []))
                    tag_overlap = len(current_tags.intersection(issue_tags))
                    issue['tag_similarity'] = tag_overlap / len(current_tags) if current_tags else 0
                    related_issues.append(issue)
            
            # Sort by tag similarity and relevance
            related_issues.sort(key=lambda x: (x['tag_similarity'], x['relevance_score']), reverse=True)
            
            return related_issues[:k]
            
        except Exception as e:
            logger.error(f"Error finding related issues: {str(e)}")
            return []
    
    def search_by_error_code(self, error_code: str) -> Optional[Dict]:
        """
        Search for specific error code
        
        Args:
            error_code: Microsoft error code (e.g., 0x80042108)
            
        Returns:
            Matching troubleshooting entry or None
        """
        try:
            for entry in self.metadata_store:
                if entry.get('error_code', '').lower() == error_code.lower():
                    return {**entry, 'relevance_score': 1.0}
            
            logger.info(f"No exact match found for error code: {error_code}")
            return None
            
        except Exception as e:
            logger.error(f"Error searching by error code: {str(e)}")
            return None
    
    def get_stats(self) -> Dict:
        """Get retriever statistics"""
        return {
            'total_entries': len(self.metadata_store),
            'index_dimension': self.index.d if self.index else 0,
            'model_name': self.model_name,
            'available_tags': list(set(tag for entry in self.metadata_store 
                                     for tag in entry.get('tags', []))),
            'severity_distribution': {
                severity: sum(1 for entry in self.metadata_store 
                            if entry.get('severity') == severity)
                for severity in ['low', 'medium', 'high', 'critical']
            }
        }

    def load_additional_data(self, new_data: List[Dict[str, str]]) -> None:
        """Load additional troubleshooting data into the vector store.
        
        Args:
            new_data: List of dictionaries with 'title', 'content', 'tags', 'symptoms', etc.
        """
        if not self.model or not self.index:
            raise RuntimeError("RAG components not loaded")
        
        for entry in new_data:
            embedding = self.model.encode([entry.get('content', '')])[0]
            self.index.add(np.array([embedding]).astype('float32'))
            self.metadata_store.append(entry)
        
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata_store, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Added {len(new_data)} new entries to the vector store")

# Global retriever instance
_retriever = None
_vector_store = None

def get_default_vector_store():
    """Get or create a default vector store instance"""
    global _vector_store
    if _vector_store is None:
        # Create a simple in-memory vector store as fallback
        _vector_store = {}
        logging.info("Created default in-memory vector store")
    return _vector_store

def get_retriever() -> RAGRetriever:
    """Get or create global retriever instance"""
    global _retriever
    if _retriever is None:
        _retriever = RAGRetriever()
    return _retriever

class EnhancedRetriever:
    def __init__(self, vector_store=None, k=3):
        self.vector_store = vector_store or get_default_vector_store()
        self.k = k
        
        # Office-specific configuration
        self.office_apps = {
            'outlook': {
                'keywords': ['email', 'mail', 'calendar', 'contact', 'outlook'],
                'error_patterns': [
                    r'0x8[\dA-F]{7}',  # Outlook error codes
                    r'[\dA-F]{8}-[\dA-F]{4}-[\dA-F]{4}-[\dA-F]{4}-[\dA-F]{12}'  # Exchange errors
                ]
            },
            'teams': {
                'keywords': ['teams', 'chat', 'meeting', 'call', 'video'],
                'error_patterns': [
                    r'caa[\d]{5}',  # Teams error codes
                    r'meeting_[\w]+_error'
                ]
            },
            'excel': {
                'keywords': ['excel', 'spreadsheet', 'workbook', 'cell', 'formula'],
                'error_patterns': [
                    r'#[A-Z]+!',  # Excel formula errors
                    r'0x800[\dA-F]{5}'  # Excel application errors
                ]
            }
        }
        
        # Common Office issues
        self.common_issues = {
            'authentication': ['sign in', 'login', 'credentials', 'password'],
            'performance': ['slow', 'freeze', 'crash', 'not responding'],
            'connectivity': ['offline', 'cannot connect', 'network', 'server'],
            'startup': ['won\'t open', 'won\'t start', 'launch', 'loading'],
            'update': ['update', 'version', 'patch', 'install']
        }
    
    def retrieve(self, query: str, k: int = 3) -> List[Dict]:
        """
        Retrieve relevant troubleshooting steps for Office applications
        
        Args:
            query: User's troubleshooting query
            k: Number of results to return
            
        Returns:
            List of relevant troubleshooting steps
        """
        try:
            # Identify the Office app
            app = self._identify_app(query)
            
            # Extract error codes if present
            error_codes = self._extract_error_codes(query, app)
            
            # Identify issue type
            issue_type = self._identify_issue_type(query)
            
            # Get relevant results
            results = []
            
            # First, check for exact error code matches
            if error_codes:
                error_results = self.search_by_error_code(error_codes)
                if error_results:
                    results.extend(error_results)
            
            # Then get semantic search results
            vector_results = self.vector_store.similarity_search(
                query,
                filter={'app': app} if app else None,
                k=max(k - len(results), 0)
            )
            
            # Combine and deduplicate results
            all_results = self._combine_results(results, vector_results, query)
            
            # Add confidence scores
            scored_results = self._add_confidence_scores(all_results, query, app, issue_type)
            
            # Sort by confidence and return top k
            return sorted(scored_results, key=lambda x: x['confidence'], reverse=True)[:k]
            
        except Exception as e:
            logger.error(f"Error retrieving results: {str(e)}")
            return []
    
    def _identify_app(self, query: str) -> Optional[str]:
        """Identify which Office app the query is about"""
        query_lower = query.lower()
        
        for app, config in self.office_apps.items():
            if any(kw in query_lower for kw in config['keywords']):
                return app
        
        return None
    
    def _extract_error_codes(self, query: str, app: Optional[str] = None) -> List[str]:
        """Extract error codes from query"""
        error_codes = []
        
        # Check app-specific error patterns
        if app and app in self.office_apps:
            for pattern in self.office_apps[app]['error_patterns']:
                matches = re.findall(pattern, query)
                error_codes.extend(matches)
        
        # Check common Office error patterns
        common_patterns = [
            r'0x8[\dA-F]{7}',  # Common Office error codes
            r'error [\d]{4,6}'  # Generic error numbers
        ]
        
        for pattern in common_patterns:
            matches = re.findall(pattern, query)
            error_codes.extend(matches)
        
        return list(set(error_codes))  # Remove duplicates
    
    def _identify_issue_type(self, query: str) -> Optional[str]:
        """Identify the type of issue from common categories"""
        query_lower = query.lower()
        
        for issue_type, keywords in self.common_issues.items():
            if any(kw in query_lower for kw in keywords):
                return issue_type
        
        return None
    
    def _combine_results(self, exact_matches: List[Dict], vector_matches: List[Dict], query: str) -> List[Dict]:
        """Combine and deduplicate results"""
        seen_ids = set()
        combined = []
        
        for result in exact_matches:
            if result['id'] not in seen_ids:
                seen_ids.add(result['id'])
                combined.append(result)
        
        for result in vector_matches:
            if result['id'] not in seen_ids:
                seen_ids.add(result['id'])
                combined.append(result)
        
        return combined
    
    def _add_confidence_scores(self, results: List[Dict], query: str, app: Optional[str], issue_type: Optional[str]) -> List[Dict]:
        """Add confidence scores to results based on relevance factors"""
        for result in results:
            confidence = 0.0
            
            # App match bonus
            if app and app.lower() in result['content'].lower():
                confidence += 0.3
            
            # Issue type match bonus
            if issue_type and issue_type in result['tags']:
                confidence += 0.2
            
            # Keyword overlap score
            query_words = set(query.lower().split())
            content_words = set(result['content'].lower().split())
            overlap = len(query_words.intersection(content_words))
            confidence += min(0.3, overlap * 0.1)  # Cap at 0.3
            
            # Solution completeness
            if 'steps' in result and result['steps']:
                confidence += 0.2
            
            result['confidence'] = min(1.0, confidence)  # Cap at 1.0
        
        return results

if __name__ == "__main__":
    # Test the enhanced retriever
    try:
        retriever = RAGRetriever()
        
        test_queries = [
            "Outlook won't open",
            "Can't send emails",
            "Error 0x80042108",
            "Outlook is slow"
        ]
        
        print("\n🔍 Testing Enhanced RAG Retriever\n")
        
        for query in test_queries:
            print(f"Query: '{query}'")
            results = retriever.retrieve(query, k=3)
            
            if results:
                for i, result in enumerate(results, 1):
                    print(f"  {i}. {result['title']} (Score: {result['relevance_score']:.3f})")
                    print(f"     Tags: {', '.join(result['tags'])}")
                    print(f"     Symptoms: {', '.join(result['symptoms'])}")
            else:
                print("  No relevant results found")
            print()
        
        # Show stats
        stats = retriever.get_stats()
        print("📊 Retriever Statistics:")
        print(f"  Total entries: {stats['total_entries']}")
        print(f"  Available tags: {', '.join(stats['available_tags'])}")
        print(f"  Severity distribution: {stats['severity_distribution']}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")