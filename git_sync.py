import os
import json
from datetime import datetime
from typing import Optional, Dict, List
import logging
from github import Github
from pathlib import Path
import subprocess
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GitSyncManager:
    def __init__(self, repo_path: str):
        """
        Initialize GitSyncManager.
        
        Args:
            repo_path: Path to the local Git repository
        """
        load_dotenv()
        self.repo_path = repo_path
        self.messages_dir = os.path.join(repo_path, 'messages')
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repo_name = os.getenv('GITHUB_REPO')
        
        if not self.github_token or not self.repo_name:
            raise ValueError("GITHUB_TOKEN and GITHUB_REPO must be set in .env file")
            
        self.github = Github(self.github_token)
        Path(self.messages_dir).mkdir(parents=True, exist_ok=True)

    def _run_git_command(self, command: List[str]) -> tuple[int, str, str]:
        """
        Run a git command and return the result.
        
        Args:
            command: List of command arguments
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        try:
            process = subprocess.Popen(
                ['git'] + command,
                cwd=self.repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()
            return process.returncode, stdout, stderr
        except subprocess.SubprocessError as e:
            logger.error(f"Git command failed: {e}")
            return 1, "", str(e)

    def sync_message(self, message: Dict) -> Optional[str]:
        """
        Sync a message to GitHub.
        
        Args:
            message: Dictionary containing message data
            
        Returns:
            Git commit hash if successful, None otherwise
        """
        try:
            # Create message file
            timestamp = datetime.fromisoformat(message['timestamp'])
            filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{message['id']}.json"
            file_path = os.path.join(self.messages_dir, filename)
            
            # Write message to file
            with open(file_path, 'w') as f:
                json.dump(message, f, indent=2)
            
            # Stage the file
            returncode, stdout, stderr = self._run_git_command(['add', file_path])
            if returncode != 0:
                logger.error(f"Failed to stage file: {stderr}")
                return None
            
            # Create commit
            commit_message = f"Add message {message['id']} from {message['sender']}"
            returncode, stdout, stderr = self._run_git_command([
                'commit',
                '-m', commit_message,
                '--author', f"{message['sender']} <{message['sender']}@example.com>"
            ])
            if returncode != 0:
                logger.error(f"Failed to commit: {stderr}")
                return None
            
            # Get commit hash
            returncode, stdout, stderr = self._run_git_command([
                'rev-parse',
                'HEAD'
            ])
            if returncode != 0:
                logger.error(f"Failed to get commit hash: {stderr}")
                return None
            
            commit_hash = stdout.strip()
            
            # Push to GitHub
            returncode, stdout, stderr = self._run_git_command(['push'])
            if returncode != 0:
                logger.error(f"Failed to push: {stderr}")
                return None
            
            logger.info(f"Successfully synced message {message['id']} with commit {commit_hash}")
            return commit_hash
            
        except Exception as e:
            logger.error(f"Failed to sync message: {str(e)}")
            return None

    @staticmethod
    def clone_repository(repo_url: str, local_path: str) -> bool:
        """
        Clone a GitHub repository to local path.
        
        Args:
            repo_url: URL of the GitHub repository
            local_path: Local path to clone to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = subprocess.run(
                ['git', 'clone', repo_url, local_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully cloned repository to {local_path}")
                return True
            else:
                logger.error(f"Failed to clone repository: {result.stderr}")
                return False
                
        except subprocess.SubprocessError as e:
            logger.error(f"Failed to clone repository: {str(e)}")
            return False

def init_repository(repo_url: str, local_path: str) -> Optional[GitSyncManager]:
    """
    Initialize or clone the repository and return a GitSyncManager instance.
    
    Args:
        repo_url: URL of the GitHub repository
        local_path: Local path for the repository
        
    Returns:
        GitSyncManager instance if successful, None otherwise
    """
    try:
        if not os.path.exists(os.path.join(local_path, '.git')):
            success = GitSyncManager.clone_repository(repo_url, local_path)
            if not success:
                return None
        
        return GitSyncManager(local_path)
        
    except Exception as e:
        logger.error(f"Failed to initialize repository: {str(e)}")
        return None
