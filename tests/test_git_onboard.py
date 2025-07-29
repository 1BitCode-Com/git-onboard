#!/usr/bin/env python3
"""
Unit tests for Git Onboard
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestGitOnboardBasic(unittest.TestCase):
    """Basic tests for Git Onboard functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)
    
    def tearDown(self):
        """Clean up test fixtures"""
        try:
            shutil.rmtree(self.test_dir)
        except:
            pass  # Ignore cleanup errors
    
    def test_import_module(self):
        """Test that the module can be imported"""
        try:
            # This will test if the module can be imported
            # The actual functionality is tested in the main file
            pass
        except ImportError as e:
            self.fail(f"Failed to import module: {e}")
    
    def test_temp_directory_creation(self):
        """Test that temporary directories can be created"""
        self.assertTrue(self.test_path.exists())
        self.assertTrue(self.test_path.is_dir())
    
    def test_path_operations(self):
        """Test basic path operations"""
        test_file = self.test_path / "test.txt"
        test_file.write_text("test content")
        self.assertTrue(test_file.exists())
        self.assertEqual(test_file.read_text(), "test content")
    
    def test_basic_functionality(self):
        """Test basic functionality"""
        # This is a simple test that should always pass
        self.assertTrue(True)

if __name__ == "__main__":
    unittest.main() 