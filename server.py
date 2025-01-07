#!/usr/bin/env python3

import http.server
import socketserver
import json
import os
import sqlite3
from urllib.parse import parse_qs, urlparse
from http import HTTPStatus
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
HOST = "localhost"
PORT = 8000
DATABASE_PATH = "database/messages.db"

class MessageHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP request handler for the messaging application."""

    def __init__(self, *args, **kwargs):
        # Set the directory for serving static files
        self.static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests."""
        try:
            parsed_path = urlparse(self.path)
            
            # Route handling
            if parsed_path.path == "/":
                self.serve_file("templates/index.html", "text/html")
            elif parsed_path.path == "/messages":
                self.handle_get_messages()
            elif parsed_path.path.startswith("/static/"):
                # Serve static files
                file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                       parsed_path.path[1:])
                self.serve_static_file(file_path)
            else:
                self.send_error(HTTPStatus.NOT_FOUND, "Resource not found")
                
        except Exception as e:
            logger.error(f"Error handling GET request: {str(e)}")
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(e))

    def do_POST(self):
        """Handle POST requests."""
        try:
            parsed_path = urlparse(self.path)
            
            # Read the request body
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            if parsed_path.path == "/messages":
                # Handle new message
                self.handle_new_message(post_data)
            else:
                self.send_error(HTTPStatus.NOT_FOUND, "Resource not found")
                
        except Exception as e:
            logger.error(f"Error handling POST request: {str(e)}")
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(e))

    def serve_file(self, filepath, content_type):
        """Serve a file with the specified content type."""
        try:
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), filepath), 'rb') as f:
                content = f.read()
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")

    def serve_static_file(self, filepath):
        """Serve static files with appropriate content types."""
        content_types = {
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.gif': 'image/gif'
        }
        
        _, ext = os.path.splitext(filepath)
        content_type = content_types.get(ext, 'application/octet-stream')
        self.serve_file(filepath, content_type)

    def handle_get_messages(self):
        """Retrieve messages from the database."""
        try:
            # Connect to SQLite database
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, content, timestamp, sender
                    FROM messages
                    ORDER BY timestamp DESC
                    LIMIT 50
                """)
                messages = cursor.fetchall()
                
                # Convert to JSON
                messages_json = json.dumps([{
                    'id': msg[0],
                    'content': msg[1],
                    'timestamp': msg[2],
                    'sender': msg[3]
                } for msg in messages])
                
                # Send response
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(messages_json.encode())
                
        except sqlite3.Error as e:
            logger.error(f"Database error: {str(e)}")
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "Database error")

    def handle_new_message(self, post_data):
        """Store a new message in the database."""
        try:
            message_data = json.loads(post_data.decode('utf-8'))
            
            # Validate message data
            if not message_data.get('content') or not message_data.get('sender'):
                self.send_error(HTTPStatus.BAD_REQUEST, "Missing required fields")
                return
            
            # Connect to SQLite database
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO messages (content, timestamp, sender)
                    VALUES (?, ?, ?)
                """, (
                    message_data['content'],
                    datetime.now().isoformat(),
                    message_data['sender']
                ))
                conn.commit()
            
            # Send success response
            self.send_response(HTTPStatus.CREATED)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode())
            
        except json.JSONDecodeError:
            self.send_error(HTTPStatus.BAD_REQUEST, "Invalid JSON")
        except sqlite3.Error as e:
            logger.error(f"Database error: {str(e)}")
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "Database error")

def init_database():
    """Initialize the SQLite database and create necessary tables."""
    try:
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    sender TEXT NOT NULL
                )
            """)
            conn.commit()
        logger.info("Database initialized successfully")
    except sqlite3.Error as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

def run_server():
    """Start the HTTP server."""
    try:
        # Initialize the database
        init_database()
        
        # Create a threaded HTTP server
        with socketserver.ThreadingTCPServer((HOST, PORT), MessageHandler) as httpd:
            logger.info(f"Server running at http://{HOST}:{PORT}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        raise

if __name__ == "__main__":
    run_server()
