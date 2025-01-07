import unittest
import json
import os
import sqlite3
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from http import HTTPStatus
from datetime import datetime

# Add parent directory to Python path to import server module
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import MessageHandler
from database import DatabaseManager

class MockServer:
    """Mock server class to simulate the server environment."""
    def __init__(self):
        self.headers = {}
        self.response_code = None
        self.response_headers = []
        self.wfile = MagicMock()
        self.rfile = MagicMock()

    def send_response(self, code):
        self.response_code = code

    def send_header(self, key, value):
        self.response_headers.append((key, value))

    def end_headers(self):
        pass

class TestMessageEndpoints(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)
        
        # Set up test database path
        self.db_path = os.path.join(self.test_dir, 'test.db')
        
        # Mock environment variables
        self.env_patcher = patch.dict('os.environ', {
            'GITHUB_TOKEN': 'test_token',
            'GITHUB_REPO': 'test/repo'
        })
        self.env_patcher.start()
        self.addCleanup(self.env_patcher.stop)
        
        # Initialize database
        self.db_manager = DatabaseManager(self.db_path)
        self.db_manager.init_database()
        
        # Create mock server
        self.server = MockServer()
        
        # Create message handler instance
        self.handler = MessageHandler(self.server, ('localhost', 8000), None)
        self.handler.db_manager = self.db_manager

    def test_post_message_success(self):
        """Test successful message creation via POST endpoint."""
        # Prepare test message
        test_message = {
            'content': 'Test message content',
            'sender': 'test_user'
        }
        
        # Mock request body
        self.server.rfile.read = MagicMock(return_value=json.dumps(test_message).encode())
        self.server.headers = {'Content-Length': str(len(json.dumps(test_message)))}
        
        # Mock Git sync
        with patch('git_sync.GitSyncManager.sync_message') as mock_sync:
            mock_sync.return_value = 'test_commit_hash'
            
            # Call the handler
            self.handler.handle_new_message(json.dumps(test_message).encode())
        
        # Verify response
        self.assertEqual(self.server.response_code, HTTPStatus.CREATED)
        
        # Verify message was stored in database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT content, sender, is_synchronized, git_hash FROM messages")
            result = cursor.fetchone()
            
            self.assertIsNotNone(result)
            self.assertEqual(result[0], test_message['content'])
            self.assertEqual(result[1], test_message['sender'])
            self.assertTrue(result[2])  # is_synchronized should be True
            self.assertEqual(result[3], 'test_commit_hash')

    def test_post_message_missing_fields(self):
        """Test message creation with missing required fields."""
        # Test messages with missing fields
        test_cases = [
            {'sender': 'test_user'},  # Missing content
            {'content': 'Test content'},  # Missing sender
            {}  # Missing both
        ]
        
        for test_message in test_cases:
            # Mock request body
            self.server.rfile.read = MagicMock(return_value=json.dumps(test_message).encode())
            self.server.headers = {'Content-Length': str(len(json.dumps(test_message)))}
            
            # Call the handler
            self.handler.handle_new_message(json.dumps(test_message).encode())
            
            # Verify response
            self.assertEqual(self.server.response_code, HTTPStatus.BAD_REQUEST)
            
            # Verify no message was stored
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM messages")
                count = cursor.fetchone()[0]
                self.assertEqual(count, 0)

    def test_post_message_git_sync_failure(self):
        """Test message creation when Git sync fails."""
        # Prepare test message
        test_message = {
            'content': 'Test message content',
            'sender': 'test_user'
        }
        
        # Mock request body
        self.server.rfile.read = MagicMock(return_value=json.dumps(test_message).encode())
        self.server.headers = {'Content-Length': str(len(json.dumps(test_message)))}
        
        # Mock Git sync failure
        with patch('git_sync.GitSyncManager.sync_message') as mock_sync:
            mock_sync.return_value = None  # Simulate sync failure
            
            # Call the handler
            self.handler.handle_new_message(json.dumps(test_message).encode())
        
        # Verify message was stored but not marked as synchronized
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT content, sender, is_synchronized, git_hash FROM messages")
            result = cursor.fetchone()
            
            self.assertIsNotNone(result)
            self.assertEqual(result[0], test_message['content'])
            self.assertEqual(result[1], test_message['sender'])
            self.assertFalse(result[2])  # is_synchronized should be False
            self.assertIsNone(result[3])  # git_hash should be None

if __name__ == '__main__':
    unittest.main()
