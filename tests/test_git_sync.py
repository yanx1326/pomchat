import unittest
import os
import shutil
import tempfile
import json
from datetime import datetime
from unittest.mock import patch, MagicMock
from git_sync import GitSyncManager, init_repository

class TestGitSync(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary directory for test repository
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)
        
        # Mock environment variables
        self.env_patcher = patch.dict('os.environ', {
            'GITHUB_TOKEN': 'test_token',
            'GITHUB_REPO': 'test/repo'
        })
        self.env_patcher.start()
        self.addCleanup(self.env_patcher.stop)

    def test_init_git_sync_manager(self):
        """Test GitSyncManager initialization."""
        manager = GitSyncManager(self.test_dir)
        self.assertEqual(manager.repo_path, self.test_dir)
        self.assertEqual(manager.messages_dir, os.path.join(self.test_dir, 'messages'))
        self.assertTrue(os.path.exists(manager.messages_dir))

    @patch('subprocess.Popen')
    def test_run_git_command(self, mock_popen):
        """Test running git commands."""
        # Mock successful git command
        process_mock = MagicMock()
        process_mock.communicate.return_value = ('output', '')
        process_mock.returncode = 0
        mock_popen.return_value = process_mock

        manager = GitSyncManager(self.test_dir)
        returncode, stdout, stderr = manager._run_git_command(['status'])
        
        self.assertEqual(returncode, 0)
        self.assertEqual(stdout, 'output')
        self.assertEqual(stderr, '')
        
        # Verify git command was called correctly
        mock_popen.assert_called_with(
            ['git', 'status'],
            cwd=self.test_dir,
            stdout=-1,
            stderr=-1,
            text=True
        )

    @patch('subprocess.Popen')
    def test_sync_message(self, mock_popen):
        """Test message synchronization."""
        # Mock successful git commands
        process_mock = MagicMock()
        process_mock.communicate.return_value = ('commit_hash', '')
        process_mock.returncode = 0
        mock_popen.return_value = process_mock

        manager = GitSyncManager(self.test_dir)
        test_message = {
            'id': 1,
            'content': 'Test message',
            'timestamp': datetime.now().isoformat(),
            'sender': 'test_user',
            'created_at': datetime.now().isoformat()
        }

        # Test message sync
        commit_hash = manager.sync_message(test_message)
        self.assertIsNotNone(commit_hash)
        
        # Verify message file was created
        message_files = os.listdir(manager.messages_dir)
        self.assertEqual(len(message_files), 1)
        
        # Verify message content
        with open(os.path.join(manager.messages_dir, message_files[0])) as f:
            saved_message = json.load(f)
        self.assertEqual(saved_message['content'], test_message['content'])
        self.assertEqual(saved_message['sender'], test_message['sender'])

    @patch('subprocess.run')
    def test_clone_repository(self, mock_run):
        """Test repository cloning."""
        # Mock successful clone
        mock_run.return_value = MagicMock(returncode=0)

        success = GitSyncManager.clone_repository(
            'https://github.com/test/repo.git',
            self.test_dir
        )
        self.assertTrue(success)
        
        # Verify clone command was called correctly
        mock_run.assert_called_with(
            ['git', 'clone', 'https://github.com/test/repo.git', self.test_dir],
            capture_output=True,
            text=True
        )

    @patch('git_sync.GitSyncManager.clone_repository')
    def test_init_repository(self, mock_clone):
        """Test repository initialization."""
        # Mock successful clone
        mock_clone.return_value = True

        # Test initialization of new repository
        manager = init_repository('https://github.com/test/repo.git', self.test_dir)
        self.assertIsNotNone(manager)
        self.assertIsInstance(manager, GitSyncManager)
        
        # Verify clone was called
        mock_clone.assert_called_with(
            'https://github.com/test/repo.git',
            self.test_dir
        )

    def test_missing_env_variables(self):
        """Test handling of missing environment variables."""
        # Remove environment variables
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(ValueError):
                GitSyncManager(self.test_dir)

if __name__ == '__main__':
    unittest.main()
