"""
Comprehensive tests for security utilities
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, request, session
from security_utils import (
    SecurityValidator, CSRFProtection, SecurityHeaders, 
    validate_request_data, SECURITY_CONFIG, RateLimitValidator
)

class TestSecurityValidator:
    """Test cases for SecurityValidator"""
    
    def test_validate_email_valid(self):
        """Test valid email validation"""
        assert SecurityValidator.validate_email("test@example.com") == True
        assert SecurityValidator.validate_email("user.name+tag@domain.co.uk") == True
    
    def test_validate_email_invalid(self):
        """Test invalid email validation"""
        assert SecurityValidator.validate_email("invalid-email") == False
        assert SecurityValidator.validate_email("@domain.com") == False
        assert SecurityValidator.validate_email("user@") == False
        assert SecurityValidator.validate_email("") == False
        assert SecurityValidator.validate_email(None) == False
        # Test length limit
        long_email = "a" * 250 + "@domain.com"
        assert SecurityValidator.validate_email(long_email) == False
    
    def test_validate_url_valid(self):
        """Test valid URL validation"""
        assert SecurityValidator.validate_url("https://example.com") == True
        assert SecurityValidator.validate_url("http://localhost:8080") == True
        assert SecurityValidator.validate_url("https://sub.domain.com/path?param=value") == True
    
    def test_validate_url_invalid(self):
        """Test invalid URL validation"""
        assert SecurityValidator.validate_url("not-a-url") == False
        assert SecurityValidator.validate_url("ftp://example.com") == False
        assert SecurityValidator.validate_url("") == False
        assert SecurityValidator.validate_url(None) == False
        # Test length limit
        long_url = "https://example.com/" + "a" * 2050
        assert SecurityValidator.validate_url(long_url) == False
    
    def test_sanitize_html(self):
        """Test HTML sanitization"""
        # Test XSS prevention
        malicious_html = "<script>alert('xss')</script><p>Safe content</p>"
        sanitized = SecurityValidator.sanitize_html(malicious_html)
        assert "<script>" not in sanitized
        assert "</script>" not in sanitized
        assert "Safe content" in sanitized
        
        # Test empty input
        assert SecurityValidator.sanitize_html("") == ""
        assert SecurityValidator.sanitize_html(None) == ""
    
    def test_validate_json_payload(self):
        """Test JSON payload validation"""
        # Valid payload
        valid_data = {"name": "test", "email": "test@example.com"}
        is_valid, message = SecurityValidator.validate_json_payload(valid_data, ["name", "email"])
        assert is_valid == True
        assert message == "Valid"
        
        # Missing required field
        invalid_data = {"name": "test"}
        is_valid, error = SecurityValidator.validate_json_payload(invalid_data, ["name", "email"])
        assert is_valid == False
        assert "email" in error
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        # Test dangerous characters removal
        dangerous_name = "../../../etc/passwd"
        sanitized = SecurityValidator.sanitize_filename(dangerous_name)
        assert "../" not in sanitized
        assert sanitized == "etcpasswd"
        
        # Test length limit
        long_name = "a" * 300
        sanitized = SecurityValidator.sanitize_filename(long_name)
        assert len(sanitized) <= 255

class TestCSRFProtection:
    """Test cases for CSRF protection"""
    
    def test_generate_csrf_token(self):
        """Test CSRF token generation"""
        token1 = CSRFProtection.generate_csrf_token()
        token2 = CSRFProtection.generate_csrf_token()
        
        assert token1 != token2
        assert len(token1) > 0
        assert len(token2) > 0
    
    def test_validate_csrf_token_valid(self):
        """Test valid CSRF token validation"""
        app = Flask(__name__)
        app.secret_key = 'test-secret'
        
        with app.test_request_context():
            # Set the session token directly
            from flask import session
            token = "test_token"
            session['csrf_token'] = token
            
            assert CSRFProtection.validate_csrf_token(token) == True
    
    def test_validate_csrf_token_invalid(self):
        """Test invalid CSRF token validation"""
        app = Flask(__name__)
        app.secret_key = 'test-secret'
        
        with app.test_request_context():
            # Set the session token directly
            from flask import session
            session['csrf_token'] = "correct_token"
            
            assert CSRFProtection.validate_csrf_token("wrong_token") == False
            assert CSRFProtection.validate_csrf_token("") == False
            assert CSRFProtection.validate_csrf_token(None) == False
    
    def test_csrf_required_decorator(self):
        """Test CSRF required decorator"""
        app = Flask(__name__)
        
        @CSRFProtection.csrf_required
        def test_endpoint():
            return "success"
        
        with app.test_request_context('/test', method='POST'):
            with patch('security_utils.CSRFProtection.validate_csrf_token') as mock_validate:
                mock_validate.return_value = False
                
                response = test_endpoint()
                assert response[1] == 403  # Should return 403 for invalid CSRF

class TestSecurityHeaders:
    """Test cases for security headers"""
    
    def test_apply_security_headers(self):
        """Test security headers application"""
        app = Flask(__name__)
        
        with app.test_request_context('/test'):
            response = app.response_class()
            SecurityHeaders.apply_security_headers(response)
            
            # Check required headers
            assert response.headers['X-Frame-Options'] == 'DENY'
            assert response.headers['X-Content-Type-Options'] == 'nosniff'
            assert response.headers['X-XSS-Protection'] == '1; mode=block'
            assert 'Content-Security-Policy' in response.headers
            assert 'Referrer-Policy' in response.headers

class TestRateLimitValidator:
    """Test cases for rate limit validator"""
    
    def test_get_client_id(self):
        """Test client ID generation"""
        app = Flask(__name__)
        
        with app.test_request_context('/test', environ_base={'REMOTE_ADDR': '127.0.0.1'}):
            client_id = RateLimitValidator.get_client_id()
            assert len(client_id) == 16  # SHA256 hash truncated to 16 chars
            assert isinstance(client_id, str)
    
    def test_is_suspicious_request_clean(self):
        """Test suspicious request detection with clean request"""
        app = Flask(__name__)
        
        with app.test_request_context('/test'):
            assert RateLimitValidator.is_suspicious_request() == False
    
    def test_is_suspicious_request_malicious(self):
        """Test suspicious request detection with malicious patterns"""
        app = Flask(__name__)
        
        # Test with script injection in query parameter
        with app.test_request_context('/test?param=<script>alert("xss")</script>'):
            assert RateLimitValidator.is_suspicious_request() == True
        
        # Test with SQL injection pattern
        with app.test_request_context('/test?param=union select * from users'):
            assert RateLimitValidator.is_suspicious_request() == True

class TestValidateRequestDataDecorator:
    """Test cases for request data validation decorator"""
    
    def test_validate_request_data_valid(self):
        """Test valid request data"""
        app = Flask(__name__)
        
        @validate_request_data(required_fields=["name"], max_content_length=1024)
        def test_endpoint():
            return "success"
        
        with app.test_request_context('/test', method='POST', 
                                    json={"name": "test"}, 
                                    content_type='application/json'):
            response = test_endpoint()
            assert response == "success"
    
    def test_validate_request_data_content_too_large(self):
        """Test request with content too large"""
        app = Flask(__name__)
        
        @validate_request_data(max_content_length=10)
        def test_endpoint():
            return "success"
        
        with app.test_request_context('/test', method='POST', 
                                    data="a" * 20,
                                    content_length=20):
            response = test_endpoint()
            assert response[1] == 413  # Request too large

class TestSecurityConfig:
    """Test cases for security configuration"""
    
    def test_security_config_values(self):
        """Test security configuration values"""
        assert 'SESSION_COOKIE_SECURE' in SECURITY_CONFIG
        assert 'SESSION_COOKIE_HTTPONLY' in SECURITY_CONFIG
        assert 'SESSION_COOKIE_SAMESITE' in SECURITY_CONFIG
        assert 'PERMANENT_SESSION_LIFETIME' in SECURITY_CONFIG
        assert 'MAX_CONTENT_LENGTH' in SECURITY_CONFIG
        
        assert SECURITY_CONFIG['SESSION_COOKIE_SECURE'] == True
        assert SECURITY_CONFIG['SESSION_COOKIE_HTTPONLY'] == True
        assert SECURITY_CONFIG['PERMANENT_SESSION_LIFETIME'] == 3600

class TestIntegration:
    """Integration tests for security utilities"""
    
    def test_full_security_pipeline(self):
        """Test complete security validation pipeline"""
        app = Flask(__name__)
        
        @validate_request_data(required_fields=["email"])
        @CSRFProtection.csrf_required
        def secure_endpoint():
            return "success"
        
        with app.test_request_context('/test', method='POST',
                                    json={"email": "test@example.com"},
                                    content_type='application/json'):
            with patch('security_utils.CSRFProtection.validate_csrf_token') as mock_csrf:
                mock_csrf.return_value = True
                
                response = secure_endpoint()
                assert response == "success"

@pytest.fixture
def app():
    """Create test Flask app"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()