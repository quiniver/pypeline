"""Tests for src/cmdlist.py - CMD/EXE file listing utility."""
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from cmdlist import list_cmd_files, main as cmdlist_main


class TestListCmdFiles:
    """Test suite for list_cmd_files function."""
    
    def test_nonexistent_directory(self, capsys):
        """Test listing from non-existent directory shows error."""
        with pytest.raises(SystemExit) as exc_info:
            list_cmd_files("/nonexistent/path")
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "does not exist" in captured.err
    
    def test_list_empty_directory(self, temp_dir):
        """Test listing from empty directory."""
        list_cmd_files(str(temp_dir))
    
    def test_list_single_cmd_file(self, temp_dir):
        """Test listing a single .cmd file."""
        cmd_file = temp_dir / "test.cmd"
        cmd_file.write_text("@echo off\necho hello")
        
        list_cmd_files(str(temp_dir), pattern="*", show_cmd=True, show_comments=False)
