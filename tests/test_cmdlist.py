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
    
    def test_list_empty_directory(self, temp_dir, capsys):
        """Test listing from empty directory."""
        list_cmd_files(str(temp_dir))
        captured = capsys.readouterr()
        # Should just print an empty line
        assert captured.out.strip() == ""
    
    def test_list_single_cmd_file(self, temp_dir, capsys):
        """Test listing a single .cmd file."""
        cmd_file = temp_dir / "test.cmd"
        cmd_file.write_text("@echo off\necho hello")
        
        list_cmd_files(str(temp_dir), pattern="*", show_cmd=True, show_comments=False)
        
        captured = capsys.readouterr()
        assert "test" in captured.out
    
    def test_list_cmd_file_with_comments(self, temp_dir, capsys):
        """Test listing .cmd file with comments."""
        cmd_file = temp_dir / "test.cmd"
        cmd_file.write_text(":: This is a comment\n:: Another comment\n@echo off\necho hello")
        
        list_cmd_files(str(temp_dir), pattern="*", show_cmd=True, show_comments=True)
        
        captured = capsys.readouterr()
        assert "This is a comment" in captured.out
        assert "Another comment" in captured.out
    
    def test_list_cmd_file_no_comments(self, temp_dir, capsys):
        """Test listing .cmd file without comments."""
        cmd_file = temp_dir / "test.cmd"
        cmd_file.write_text(":: This is a comment\n@echo off\necho hello")
        
        list_cmd_files(str(temp_dir), pattern="*", show_cmd=True, show_comments=False)
        
        captured = capsys.readouterr()
        assert "This is a comment" not in captured.out
        assert "test" in captured.out
    
    def test_list_exe_files(self, temp_dir, capsys):
        """Test listing .exe files."""
        exe_file = temp_dir / "mytool.exe"
        exe_file.write_bytes(b"fake exe")
        
        list_cmd_files(str(temp_dir), show_exe=True, show_cmd=False)
        
        captured = capsys.readouterr()
        assert "mytool" in captured.out
    
    def test_list_both_cmd_and_exe(self, temp_dir, capsys):
        """Test listing both .cmd and .exe files."""
        (temp_dir / "script.cmd").write_text("@echo off")
        (temp_dir / "tool.exe").write_bytes(b"fake")
        
        list_cmd_files(str(temp_dir), show_cmd=True, show_exe=True)
        
        captured = capsys.readouterr()
        assert "script" in captured.out
        assert "tool" in captured.out
    
    def test_list_with_pattern(self, temp_dir, capsys):
        """Test listing files matching a pattern."""
        (temp_dir / "alpha.cmd").write_text("@echo off")
        (temp_dir / "beta.cmd").write_text("@echo off")
        (temp_dir / "gamma.exe").write_bytes(b"fake")
        
        list_cmd_files(str(temp_dir), pattern="alpha", show_cmd=True, show_exe=False)
        
        captured = capsys.readouterr()
        assert "alpha" in captured.out
        assert "beta" not in captured.out
    
    def test_list_empty_comment_line(self, temp_dir, capsys):
        """Test handling of empty comment lines (::)."""
        cmd_file = temp_dir / "test.cmd"
        cmd_file.write_text("::\n:: comment\n@echo off")
        
        list_cmd_files(str(temp_dir), show_comments=True)
        
        captured = capsys.readouterr()
        assert "comment" in captured.out
    
    def test_list_non_cmd_comments_stopped(self, temp_dir, capsys):
        """Test that comments stop at first non-comment line."""
        cmd_file = temp_dir / "test.cmd"
        cmd_file.write_text(":: comment 1\n:: comment 2\n:: comment 3\n@echo off\necho hello")
        
        list_cmd_files(str(temp_dir), show_comments=True)
        
        captured = capsys.readouterr()
        # Should show all comments before @echo off
        assert "comment 1" in captured.out
        assert "comment 2" in captured.out
        assert "comment 3" in captured.out
    
    def test_list_reading_error(self, temp_dir, capsys):
        """Test handling of file read errors."""
        cmd_file = temp_dir / "test.cmd"
        cmd_file.write_text("@echo off")
        
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            list_cmd_files(str(temp_dir))
        
        captured = capsys.readouterr()
        assert "Error reading" in captured.err


class TestCmdListMain:
    """Test main() function of cmdlist.py."""
    
    def test_main_default(self, temp_dir):
        """Test main with default arguments."""
        (temp_dir / "test.cmd").write_text("@echo off")
        
        with patch('sys.argv', ['cmdlist.py', '--cmddir', str(temp_dir)]):
            try:
                cmdlist_main()
            except SystemExit as e:
                assert e.code is None or e.code == 0
    
    def test_main_pattern_filter(self, temp_dir):
        """Test main with pattern filter."""
        (temp_dir / "alpha.cmd").write_text("@echo off")
        (temp_dir / "beta.cmd").write_text("@echo off")
        
        with patch('sys.argv', ['cmdlist.py', 'alpha', '--cmddir', str(temp_dir)]):
            try:
                cmdlist_main()
            except SystemExit:
                pass
    
    def test_main_bare_mode(self, temp_dir):
        """Test main with --bare flag (no comments)."""
        (temp_dir / "test.cmd").write_text(":: comment\n@echo off")
        
        with patch('sys.argv', ['cmdlist.py', '--bare', '--cmddir', str(temp_dir)]):
            try:
                cmdlist_main()
            except SystemExit:
                pass
    
    def test_main_cmdonly_mode(self, temp_dir):
        """Test main with --cmdonly flag."""
        (temp_dir / "test.cmd").write_text("@echo off")
        (temp_dir / "tool.exe").write_bytes(b"fake")
        
        with patch('sys.argv', ['cmdlist.py', '--cmdonly', '--cmddir', str(temp_dir)]):
            try:
                cmdlist_main()
            except SystemExit:
                pass
    
    def test_main_exeonly_mode(self, temp_dir):
        """Test main with --exeonly flag."""
        (temp_dir / "test.cmd").write_text("@echo off")
        (temp_dir / "tool.exe").write_bytes(b"fake")
        
        with patch('sys.argv', ['cmdlist.py', '--exeonly', '--cmddir', str(temp_dir)]):
            try:
                cmdlist_main()
            except SystemExit:
                pass
    
    def test_main_bat_mode(self, temp_dir):
        """Test main with --bat flag to display file with bat."""
        cmd_file = temp_dir / "test.cmd"
        cmd_file.write_text("@echo off\necho hello")
        
        with patch('sys.argv', ['cmdlist.py', '--bat', 'test', '--cmddir', str(temp_dir)]):
            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = FileNotFoundError("bat not found")
                try:
                    cmdlist_main()
                except SystemExit as e:
                    assert e.code == 1
    
    def test_main_bat_mode_success(self, temp_dir):
        """Test main with --bat flag when bat succeeds."""
        cmd_file = temp_dir / "test.cmd"
        cmd_file.write_text("@echo off\necho hello")
        
        with patch('sys.argv', ['cmdlist.py', '--bat', 'test', '--cmddir', str(temp_dir)]):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                try:
                    cmdlist_main()
                except SystemExit:
                    pass
    
    def test_main_bat_file_not_found(self, temp_dir):
        """Test --bat with non-existent file."""
        with patch('sys.argv', ['cmdlist.py', '--bat', 'nonexistent', '--cmddir', str(temp_dir)]):
            try:
                cmdlist_main()
            except SystemExit as e:
                assert e.code == 1
    
    def test_main_nonexistent_dir(self):
        """Test main with non-existent directory."""
        with patch('sys.argv', ['cmdlist.py', '--cmddir', '/nonexistent']):
            try:
                cmdlist_main()
            except SystemExit as e:
                assert e.code == 1


class TestCmdListPatternMatching:
    """Test pattern matching in cmdlist.py."""
    
    def test_pattern_with_wildcard(self, temp_dir, capsys):
        """Test pattern matching with wildcard."""
        (temp_dir / "test1.cmd").write_text("@echo off")
        (temp_dir / "test2.cmd").write_text("@echo off")
        (temp_dir / "other.cmd").write_text("@echo off")
        
        list_cmd_files(str(temp_dir), pattern="test", show_cmd=True, show_exe=False)
        
        captured = capsys.readouterr()
        assert "test1" in captured.out
        assert "test2" in captured.out
        assert "other" not in captured.out
    
    def test_pattern_empty_matches_all(self, temp_dir, capsys):
        """Test empty pattern matches all files."""
        (temp_dir / "a.cmd").write_text("@echo off")
        (temp_dir / "b.cmd").write_text("@echo off")
        
        list_cmd_files(str(temp_dir), pattern="", show_cmd=True, show_exe=False)
        
        captured = capsys.readouterr()
        assert "a" in captured.out
        assert "b" in captured.out
