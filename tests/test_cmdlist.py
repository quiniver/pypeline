"""Tests for cmdlist.py - Testing command listing functions."""

import sys
import os
from unittest.mock import patch, MagicMock
from io import StringIO

# Add src to path so we can import from it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestListCmdFiles:
    """Test cases for list_cmd_files function."""
    
    def test_list_cmd_files_nonexistent_directory(self):
        """Test listing cmd files from nonexistent directory."""
        import cmdlist
        
        with patch('sys.exit') as mock_exit:
            with patch('os.path.exists', return_value=False) as mock_exists:
                cmdlist.list_cmd_files('/nonexistent/path')
                
                assert mock_exists.called
                mock_exit.assert_called_once_with(1)
    
    def test_list_cmd_files_bat_file(self):
        """Test displaying single file with bat."""
        import cmdlist
        
        with patch('cmdlist.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock()
            
            result = cmdlist.list_cmd_files('/fake/path', bat_file='myscript')
            
            assert result is None  # Function returns None when displaying file
            mock_run.assert_called_once_with(
                ['bat', '--style=plain', '--color=always', '/fake/path/myscript.cmd'],
                check=True
            )
    
    def test_list_cmd_files_bat_not_found(self):
        """Test bat command not found."""
        import cmdlist
        
        with patch('sys.exit') as mock_exit:
            with patch('cmdlist.subprocess.run', side_effect=FileNotFoundError()):
                result = cmdlist.list_cmd_files('/fake/path', bat_file='myscript')
                
                assert result is None
                mock_exit.assert_called_once_with(1)
    
    def test_list_cmd_files_subprocess_error(self):
        """Test subprocess error when running bat."""
        import cmdlist
        
        with patch('sys.exit') as mock_exit:
            from subprocess import CalledProcessError
            with patch('cmdlist.subprocess.run', side_effect=CalledProcessError(1, 'bat')):
                result = cmdlist.list_cmd_files('/fake/path', bat_file='myscript')
                
                assert result is None
                mock_exit.assert_called_once_with(1)


class TestMainFunction:
    """Test cases for main function."""
    
    def test_main_default_args(self, capsys):
        """Test main with default arguments."""
        import cmdlist
        
        with patch('cmdlist.list_cmd_files') as mock_list:
            mock_list.return_value = None
            
            sys.argv = ['cmdlist.py']  # Reset argv
            
            cmdlist.main()
            
            # Check that list_cmd_files was called with default values
            assert mock_list.called
    
    def test_main_pattern_argument(self, capsys):
        """Test main with pattern argument."""
        import cmdlist
        
        original_argv = sys.argv.copy()
        try:
            sys.argv = ['cmdlist.py', 'test*']
            
            with patch('cmdlist.list_cmd_files') as mock_list:
                mock_list.return_value = None
                
                cmdlist.main()
                
                # Verify pattern was passed correctly
                call_args = mock_list.call_args[0]
                assert call_args[1] == 'test*'  # second positional arg is pattern
        finally:
            sys.argv = original_argv
    
    def test_main_bare_argument(self, capsys):
        """Test main with --bare argument."""
        import cmdlist
        
        original_argv = sys.argv.copy()
        try:
            sys.argv = ['cmdlist.py', '--bare']
            
            with patch('cmdlist.list_cmd_files') as mock_list:
                mock_list.return_value = None
                
                cmdlist.main()
                
                # Verify show_comments is False
                call_kwargs = mock_list.call_args[1] or {}
                assert call_kwargs.get('show_comments', True) == False
        finally:
            sys.argv = original_argv
    
    def test_main_cmdonly_argument(self, capsys):
        """Test main with --cmdonly argument."""
        import cmdlist
        
        original_argv = sys.argv.copy()
        try:
            sys.argv = ['cmdlist.py', '--cmdonly']
            
            with patch('cmdlist.list_cmd_files') as mock_list:
                mock_list.return_value = None
                
                cmdlist.main()
                
                # Verify show_exe is False, show_cmd is True
                call_args = mock_list.call_args[0]
                assert call_args[2] == True  # show_cmd
                assert call_args[3] == False  # show_exe
        finally:
            sys.argv = original_argv
    
    def test_main_exeonly_argument(self, capsys):
        """Test main with --exeonly argument."""
        import cmdlist
        
        original_argv = sys.argv.copy()
        try:
            sys.argv = ['cmdlist.py', '--exeonly']
            
            with patch('cmdlist.list_cmd_files') as mock_list:
                mock_list.return_value = None
                
                cmdlist.main()
                
                # Verify show_exe is True, show_cmd is False
                call_args = mock_list.call_args[0]
                assert call_args[2] == False  # show_cmd
                assert call_args[3] == True  # show_exe
        finally:
            sys.argv = original_argv
    
    def test_main_bat_argument(self, capsys):
        """Test main with --bat argument."""
        import cmdlist
        
        original_argv = sys.argv.copy()
        try:
            sys.argv = ['cmdlist.py', '--bat', 'myscript']
            
            with patch('cmdlist.list_cmd_files') as mock_list:
                mock_list.return_value = None
                
                cmdlist.main()
                
                # Verify bat_file was set correctly
                call_args = mock_list.call_args[0]
                assert call_args[5] == 'myscript'  # bat_file argument
        finally:
            sys.argv = original_argv
    
    def test_main_cmddir_argument(self, capsys):
        """Test main with --cmddir argument."""
        import cmdlist
        
        original_argv = sys.argv.copy()
        try:
            sys.argv = ['cmdlist.py', '--cmddir', '/custom/path']
            
            with patch('cmdlist.list_cmd_files') as mock_list:
                mock_list.return_value = None
                
                cmdlist.main()
                
                # Verify cmddir was set correctly
                call_args = mock_list.call_args[0]
                assert call_args[4] == '/custom/path'  # cmddir argument
        finally:
            sys.argv = original_argv


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
