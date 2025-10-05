# security_utils.py
"""
Security utilities for the RAG Agent application.
Provides input validation, CSRF protection, and security headers.
"""

import re
import secrets
import hashlib
import bleach
from typing import Dict, Any, Optional, List
from functools import wraps
from flask import request, jsonify, session, current_app
import logging
import asyncio

logger = logging.getLogger(__name__)

class SecurityValidator:
    """Input validation and sanitization utilities."""
    
    # Regex patterns for validation
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    URL_PATTERN = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    # Allowed HTML tags for sanitization
    ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li']
    ALLOWED_ATTRIBUTES = {}
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        if not email or len(email) > 254:
            return False
        return bool(SecurityValidator.EMAIL_PATTERN.match(email))
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format."""
        if not url or len(url) > 2048:
            return False
        return bool(SecurityValidator.URL_PATTERN.match(url))
    
    @staticmethod
    def sanitize_html(content: str) -> str:
        """Sanitize HTML content to prevent XSS."""
        if not content:
            return ""
        return bleach.clean(
            content,
            tags=SecurityValidator.ALLOWED_TAGS,
            attributes=SecurityValidator.ALLOWED_ATTRIBUTES,
            strip=True
        )
    
    @staticmethod
    def validate_string_length(value: str, min_length: int = 0, max_length: int = 1000) -> bool:
        """Validate string length."""
        if not isinstance(value, str):
            return False
        return min_length <= len(value) <= max_length
    
    @staticmethod
    def validate_json_payload(data: Dict[str, Any], required_fields: List[str]) -> tuple[bool, str]:
        """Validate JSON payload structure and required fields."""
        if not isinstance(data, dict):
            return False, "Invalid JSON format"
        
        for field in required_fields:
            if field not in data:
                return False, f"Missing required field: {field}"
        
        return True, "Valid"
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal."""
        if not filename:
            return ""
        
        # Remove path separators and dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = re.sub(r'\.\.', '', filename)  # Remove parent directory references
        filename = filename.strip('. ')  # Remove leading/trailing dots and spaces
        
        return filename[:255]  # Limit length

class CSRFProtection:
    """CSRF protection utilities."""
    
    @staticmethod
    def generate_csrf_token() -> str:
        """Generate a new CSRF token."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_csrf_token(token: str) -> bool:
        """Validate CSRF token."""
        session_token = session.get('csrf_token')
        if not session_token or not token:
            return False
        return secrets.compare_digest(session_token, token)
    
    @staticmethod
    def csrf_required(f):
        """Decorator to require CSRF token validation."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
                token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
                if not CSRFProtection.validate_csrf_token(token):
                    logger.warning(f"CSRF validation failed for {request.endpoint}")
                    return jsonify({'error': 'CSRF token validation failed'}), 403
            return f(*args, **kwargs)
        return decorated_function

class SecurityHeaders:
    """Security headers management."""
    
    @staticmethod
    def apply_security_headers(response):
        """Apply security headers to response."""
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers['Content-Security-Policy'] = csp
        
        # HSTS (only for HTTPS)
        if request.is_secure:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response

class RateLimitValidator:
    """Enhanced rate limiting validation."""
    
    @staticmethod
    def get_client_id() -> str:
        """Get client identifier for rate limiting."""
        # Use X-Forwarded-For if behind proxy, otherwise remote_addr
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            client_ip = forwarded_for.split(',')[0].strip()
        else:
            client_ip = request.remote_addr
        
        # Include user agent for more specific identification
        user_agent = request.headers.get('User-Agent', '')
        client_hash = hashlib.sha256(f"{client_ip}:{user_agent}".encode()).hexdigest()[:16]
        
        return client_hash
    
    @staticmethod
    def is_suspicious_request() -> bool:
        """Check for suspicious request patterns."""
        # Check for common attack patterns in headers
        suspicious_patterns = [
            r'<script',
            r'javascript:',
            r'vbscript:',
            r'onload=',
            r'onerror=',
            r'\.\./\.\.',
            r'union\s+select',
            r'drop\s+table'
        ]
        
        # Check headers and query parameters
        check_values = []
        check_values.extend(request.headers.values())
        check_values.extend(request.args.values())
        
        if request.is_json:
            try:
                json_str = str(request.get_json())
                check_values.append(json_str)
            except:
                pass
        
        for value in check_values:
            if isinstance(value, str):
                for pattern in suspicious_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        logger.warning(f"Suspicious pattern detected: {pattern} in {value[:100]}")
                        return True
        
        return False

def validate_request_data(required_fields: List[str] = None, max_content_length: int = 1024*1024):
    """Decorator for request data validation.
    Supports both sync and async Flask view functions.
    """
    def decorator(f):
        # Async-aware wrapper: if the endpoint is async, use an async wrapper and await f
        if asyncio.iscoroutinefunction(f):
            @wraps(f)
            async def decorated_function(*args, **kwargs):
                # Check content length
                if request.content_length and request.content_length > max_content_length:
                    return jsonify({'error': 'Request too large'}), 413
                
                # Check for suspicious patterns
                if RateLimitValidator.is_suspicious_request():
                    return jsonify({'error': 'Suspicious request detected'}), 400
                
                # Validate JSON payload if required
                if required_fields and request.is_json:
                    data = request.get_json()
                    is_valid, error_msg = SecurityValidator.validate_json_payload(data, required_fields)
                    if not is_valid:
                        return jsonify({'error': error_msg}), 400
                
                return await f(*args, **kwargs)
            return decorated_function
        else:
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Check content length
                if request.content_length and request.content_length > max_content_length:
                    return jsonify({'error': 'Request too large'}), 413
                
                # Check for suspicious patterns
                if RateLimitValidator.is_suspicious_request():
                    return jsonify({'error': 'Suspicious request detected'}), 400
                
                # Validate JSON payload if required
                if required_fields and request.is_json:
                    data = request.get_json()
                    is_valid, error_msg = SecurityValidator.validate_json_payload(data, required_fields)
                    if not is_valid:
                        return jsonify({'error': error_msg}), 400
                
                return f(*args, **kwargs)
            return decorated_function
    return decorator

# Security configuration
SECURITY_CONFIG = {
    'SESSION_COOKIE_SECURE': True,  # Only send cookies over HTTPS
    'SESSION_COOKIE_HTTPONLY': True,  # Prevent XSS access to cookies
    'SESSION_COOKIE_SAMESITE': 'Lax',  # CSRF protection
    'PERMANENT_SESSION_LIFETIME': 3600,  # 1 hour session timeout
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB max request size
}