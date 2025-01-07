import sqlite3
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional
from git_sync import GitSyncManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database constants
DATABASE_PATH = "database/messages.db"
SCHEMA_VERSION = 1

class DatabaseManager:
    def __init__(self, db_path: str = DATABASE_PATH):
        """Initialize database manager with the given database path."""
        self.db_path = db_path
        self._ensure_db_directory()
        self.git_sync = GitSyncManager(os.path.dirname(os.path.abspath(__file__)))

    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """Create a database connection with proper configuration."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable row factory for named columns
        return conn

    def init_database(self):
        """Initialize the database schema."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Create schema_version table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS schema_version (
                        version INTEGER PRIMARY KEY,
                        updated_at TEXT NOT NULL
                    )
                """)

                # Create messages table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        content TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        sender TEXT NOT NULL,
                        git_hash TEXT,
                        is_synchronized BOOLEAN DEFAULT FALSE,
                        created_at TEXT NOT NULL,
                        updated_at TEXT
                    )
                """)

                # Create indexes
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_messages_timestamp 
                    ON messages(timestamp)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_messages_sender 
                    ON messages(sender)
                """)

                # Insert or update schema version
                cursor.execute("""
                    INSERT OR REPLACE INTO schema_version (version, updated_at)
                    VALUES (?, ?)
                """, (SCHEMA_VERSION, datetime.now().isoformat()))

                conn.commit()
                logger.info(f"Database initialized successfully with schema version {SCHEMA_VERSION}")
                
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise

    def add_message(self, content: str, sender: str, git_hash: Optional[str] = None) -> int:
        """
        Add a new message to the database and sync with Git.
        
        Args:
            content: The message content
            sender: The message sender
            git_hash: Optional Git commit hash for message versioning
            
        Returns:
            The ID of the newly inserted message
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                
                cursor.execute("""
                    INSERT INTO messages (
                        content, timestamp, sender, git_hash, 
                        is_synchronized, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (content, now, sender, git_hash, False, now))
                
                message_id = cursor.lastrowid
                
                # Prepare message for Git sync
                message = {
                    'id': message_id,
                    'content': content,
                    'timestamp': now,
                    'sender': sender,
                    'created_at': now
                }
                
                # Sync with Git
                commit_hash = self.git_sync.sync_message(message)
                if commit_hash:
                    # Update message with Git information
                    cursor.execute("""
                        UPDATE messages
                        SET git_hash = ?,
                            is_synchronized = TRUE,
                            updated_at = ?
                        WHERE id = ?
                    """, (commit_hash, now, message_id))
                
                logger.info(f"Added message with ID: {message_id}")
                return message_id
                
        except sqlite3.Error as e:
            logger.error(f"Failed to add message: {str(e)}")
            raise

    def get_messages(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """
        Retrieve messages from the database.
        
        Args:
            limit: Maximum number of messages to retrieve
            offset: Number of messages to skip
            
        Returns:
            List of message dictionaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, content, timestamp, sender, git_hash, 
                           is_synchronized, created_at, updated_at
                    FROM messages
                    ORDER BY timestamp DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve messages: {str(e)}")
            raise

    def update_message_sync_status(self, message_id: int, git_hash: str):
        """
        Update the synchronization status of a message.
        
        Args:
            message_id: The ID of the message to update
            git_hash: The Git commit hash after synchronization
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                
                cursor.execute("""
                    UPDATE messages
                    SET is_synchronized = TRUE,
                        git_hash = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (git_hash, now, message_id))
                
                if cursor.rowcount == 1:
                    logger.info(f"Updated sync status for message {message_id}")
                else:
                    logger.warning(f"No message found with ID {message_id}")
                    
        except sqlite3.Error as e:
            logger.error(f"Failed to update message sync status: {str(e)}")
            raise

def init_db():
    """Initialize the database with the latest schema."""
    db_manager = DatabaseManager()
    db_manager.init_database()

if __name__ == "__main__":
    init_db()
