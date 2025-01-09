# Git-Backed Messaging Application Specification

## Overview
This project implements a messaging application with GitHub integration for authentication and message storage. The application features a Python backend server, SQLite database for local storage, and a web interface with Markdown support and real-time updates.

## Core Features

### 1. Message Management
- Store and retrieve messages with the following attributes:
  - Content (text with Markdown support)
  - Sender information
  - Timestamp
  - Git synchronization status
  - Git commit hash (when synchronized)
- Support for retrieving the most recent messages (default: 50 messages)
- Messages are stored both in SQLite and as individual JSON files in the Git repository
- Markdown formatting support for message content

### 2. Authentication
- GitHub OAuth integration for user authentication
- User session management
- Secure password hashing using Werkzeug
- Environment variable configuration for GitHub OAuth credentials

### 3. Git Integration
- Automatic synchronization of messages to a GitHub repository
- Each message is stored as a separate JSON file in the repository
- Commit messages include sender information and message ID
- Support for Git operations:
  - Staging files
  - Creating commits
  - Pushing to remote repository
  - Repository cloning for initial setup

### 4. Web Interface
- Modern HTML interface with CSS styling
- Real-time message updates
- Markdown editor for message composition
- Test controls for:
  - Sending messages
  - Retrieving messages
- Real-time display of API responses
- Static file organization:
  - `/static/css/` for stylesheets
  - `/static/js/` for JavaScript files

## Technical Requirements

### Backend Server
1. HTTP Server:
   - Built using Python's `http.server` module
   - Support for GET and POST methods
   - JSON request/response handling
   - Static file serving capability
   - Error handling with appropriate HTTP status codes

2. Database:
   - SQLite3 database with schema versioning
   - Tables:
     - `messages`: Store message data
     - `schema_version`: Track database schema updates
   - Indexes on timestamp and sender fields
   - Support for:
     - Message creation
     - Message retrieval with pagination
     - Synchronization status updates

3. Git Integration:
   - GitHub API integration using PyGithub and GitPython
   - Local Git operations using GitPython
   - Environment variables for configuration:
     - `GITHUB_TOKEN`: GitHub API access token
     - `GITHUB_REPO`: Target repository name
     - `GITHUB_CLIENT_ID`: OAuth client ID
     - `GITHUB_CLIENT_SECRET`: OAuth client secret

### Project Structure
```
/
├── server.py           # Main HTTP server implementation
├── database.py         # Database management
├── git_sync.py         # Git synchronization logic
├── templates/          # HTML templates
│   └── index.html     # Main web interface
├── static/            # Static assets
│   ├── css/          # Stylesheets
│   └── js/           # JavaScript files
├── database/          # SQLite database directory
├── messages/          # Git-tracked message files
└── tests/             # Test suite
    └── test_server.py # Server tests
```

### Dependencies
- Python 3.x
- Required packages:
  - `PyGithub`: GitHub API integration
  - `GitPython`: Git operations
  - `python-dotenv`: Environment variable management
  - `Werkzeug`: Password hashing and web utilities
  - `markdown2`: Message formatting
  - `requests`: HTTP client
  - `python-dateutil`: Date handling
  - `cryptography`: Security features
  - Standard library modules:
    - `http.server`
    - `sqlite3`
    - `json`
    - `logging`
    - `subprocess`

### Command Line Interface
- Server initialization: `python server.py`
- Database initialization: `python server.py --init-db`
- Optional arguments:
  - `--host`: Specify host address (default: localhost)
  - `--port`: Specify port number (default: 8000)
  - `--debug`: Enable debug mode

## API Endpoints

### GET /messages
Retrieve recent messages

**Response:**
```json
[
  {
    "id": 1,
    "content": "Message content",
    "timestamp": "2025-01-08T19:06:41-05:00",
    "sender": "username",
    "git_hash": "commit_hash",
    "is_synchronized": true,
    "created_at": "2025-01-08T19:06:41-05:00",
    "updated_at": "2025-01-08T19:06:41-05:00"
  }
]
```

### POST /messages
Create a new message

**Request:**
```json
{
  "content": "Message content",
  "sender": "username"
}
```

**Response:**
```json
{
  "status": "success",
  "message_id": 1
}
```

## Testing
- Unit tests for all core functionality
- Test coverage for:
  - Message creation
  - Message retrieval
  - Error handling
  - Git synchronization
- Mock external dependencies (GitHub API, file system)
- Temporary test database and directories

## Security Considerations
- GitHub token must be stored securely in environment variables
- Input validation for message content and sender information
- Error handling to prevent information disclosure
- Logging for monitoring and debugging

## Future Enhancements
1. User authentication and authorization
2. Message editing and deletion
3. Rich text message support
4. Real-time message updates using WebSocket
5. Message search functionality
6. Enhanced web interface with modern UI framework
7. Rate limiting and spam protection
8. Message threading and replies
9. File attachments
10. Message encryption
