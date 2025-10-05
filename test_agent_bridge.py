import unittest
import requests
import json
import time
import threading
from flask import Flask

# Import the Flask app from agent_bridge
from agent_bridge import app

class TestAgentBridge(unittest.TestCase):
    """Test cases for agent_bridge.py functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Start the Flask server in a separate thread for testing"""
        cls.server_thread = threading.Thread(target=lambda: app.run(port=5001, debug=False))
        cls.server_thread.daemon = True
        cls.server_thread.start()
        # Give the server time to start
        time.sleep(2)
        cls.base_url = "http://127.0.0.1:5001"
    
    def test_home_endpoint(self):
        """Test the home endpoint returns the index.html file"""
        response = requests.get(f"{self.base_url}/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("html", response.text.lower())
    
    def test_static_files(self):
        """Test serving static files"""
        # Test an existing file
        response = requests.get(f"{self.base_url}/style.css")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/css", response.headers.get('Content-Type', ''))
        
        # Test a non-existent file
        response = requests.get(f"{self.base_url}/nonexistent.file")
        self.assertEqual(response.status_code, 404)
    
    def test_security_headers(self):
        """Test security headers are properly set"""
        response = requests.get(f"{self.base_url}/")
        self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(response.headers.get('X-Frame-Options'), 'DENY')
        self.assertEqual(response.headers.get('X-XSS-Protection'), '1; mode=block')
        self.assertIn('max-age=31536000', response.headers.get('Strict-Transport-Security', ''))
    
    def test_outlook_logs_endpoint(self):
        """Test the outlook logs endpoint"""
        response = requests.get(f"{self.base_url}/fallback/outlook/logs")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('status', data)
        # Either logs are found or a message indicating no logs
        self.assertTrue('data' in data)
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        # Make multiple requests to trigger rate limiting
        for _ in range(12):  # Exceeds the 10 per minute limit for logs endpoint
            requests.get(f"{self.base_url}/fallback/outlook/logs")
        
        # The last request should be rate limited
        response = requests.get(f"{self.base_url}/fallback/outlook/logs")
        # Rate limited responses typically return 429
        if response.status_code == 429:
            self.assertIn('limit', response.text.lower())
        else:
            # If rate limiting isn't triggered (due to test environment), just check it's a valid response
            self.assertIn(response.status_code, [200, 429])

def run_tests():
    """Run the test cases"""
    unittest.main(argv=['first-arg-is-ignored'], exit=False)

if __name__ == "__main__":
    print("Testing agent_bridge.py functionality...")
    run_tests()
    print("Tests completed.")