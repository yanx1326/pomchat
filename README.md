# Git-Backed Messaging Application

A simple web-based messaging application that uses Git as a backend storage system. This application allows users to send and receive messages while maintaining a complete history of all communications using Git.

## Features

- Simple and clean web interface
- Message persistence using SQLite database
- Git integration for message history and backup
- Real-time message updates
- User authentication via GitHub
- Markdown support for messages

## Tech Stack

- Backend: Python (no frameworks)
- Database: SQLite
- Frontend: HTML, CSS, JavaScript (vanilla)
- Version Control & Authentication: GitHub API
- Message Format: JSON

## Project Structure

```
.
├── README.md
├── .env                 # Environment variables
├── .gitignore          # Git ignore file
├── static/             # Static files
│   ├── css/           
│   └── js/            
├── templates/          # HTML templates
├── database/          
│   └── messages.db    # SQLite database
├── server.py          # Main server file
└── requirements.txt    # Python dependencies
```

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd git-messaging-app
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file with the following:
   ```
   GITHUB_CLIENT_ID=your_github_client_id
   GITHUB_CLIENT_SECRET=your_github_client_secret
   ```

5. Initialize the database:
   ```bash
   python server.py --init-db
   ```

6. Run the application:
   ```bash
   python server.py
   ```

7. Open your browser and navigate to `http://localhost:8000`

## Development Status

Project started: January 7, 2025
Status: In Development

## License

MIT License
