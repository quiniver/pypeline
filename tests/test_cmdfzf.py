"""Tests for cmdfzf.py - Testing command file selection functions."""

import sys
import os
from unittest.mock import patch, MagicMock
from io import StringIO

# Add src to path so we can import from it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestGetCmdFiles:
    """Test cases for get_cmd_files function."""
    
    def test_get_cmd_files_empty_directory(self):
        """Test getting cmd files from empty directory."""
        import cmdfzf
        
        with patch('cmdfzf.os.path.exists', return_value=True):
            with patch('cmdfzf.os.listdir', return_value=[]):
                result = cmdfzf.get_cmd_files('/fake/path')
                assert result == []
    
    def test_get_cmd_files_with_cmd_files(self):
        """Test getting cmd files from directory."""
        import cmdfzf
        
        with patch('cmdfzf.os.path.exists', return_value=True):
            with patch('cmdfzf.os.listdir', return_value=['script1.cmd', 'script2.cmd', 'other.txt']):
                result = cmdfzf.get_cmd_files('/fake/path')
                assert 'script1' in result
                assert 'script2' in result
                assert 'other' not in result
    
    def test_get_cmd_files_nonexistent_directory(self):
        """Test getting cmd files from nonexistent directory."""
        import cmdfzf
        
        with patch('cmdfzf.os.path.exists', return_value=False) as mock_exists:
            result = cmdfzf.get_cmd_files('/nonexistent/path')
            
            assert result == []
            mock_exists.assert_called_once_with('/nonexistent/path')


class TestRunFzfWithPreview:
    """Test cases for run_fzf_with_preview function."""
    
    def test_run_fzf_success(self):
        """Test successful FZF selection."""
        import cmdfzf
        
        with patch('cmdfzf.iterfzf', return_value='selected_script') as mock_iterfzf:
            result = cmdfzf.run_fzf_with_preview(['script1', 'script2'])
            
            assert result == 'selected_script'
            mock_iterfzf.assert_called_once()
    
    def test_run_fzf_keyboard_interrupt(self):
        """Test FZF interrupted by user."""
        import cmdfzf
        
        with patch('cmdfzf.iterfzf', side_effect=KeyboardInterrupt()):
            result = cmdfzf.run_fzf_with_preview(['script1'])
            
            assert result is None
    
    def test_run_fzf_exception(self):
        """Test FZF raises exception."""
        import cmdfzf
        
        with patch('cmdfzf.iterfzf', side_effect=Exception("FZF error")):
            result = cmdfzf.run_fzf_with_preview(['script1'])
            
            assert result is None


class TestGetUserEditedCommand:
    """Test cases for get_user_edited_command function."""
    
    def test_get_user_edited_command_with_args(self):
        """Test getting user edited command with arguments."""
        import cmdfzf
        
        with patch('builtins.input', return_value='--verbose --debug'):
            result = cmdfzf.get_user_edited_command('myscript')
            
            assert result == 'myscript.cmd --verbose --debug'
    
    def test_get_user_edited_command_no_args(self):
        """Test getting user edited command without arguments."""
        import cmdfzf
        
        with patch('builtins.input', return_value=''):
            result = cmdfzf.get_user_edited_command('myscript')
            
            assert result == 'myscript.cmd'
    
    def test_get_user_edited_command_none_input(self):
        """Test getting user edited command when input is None."""
        import cmdfzf
        
        with patch('builtins.input', return_value=None):
            result = cmdfzf.get_user_edited_command('myscript')
            
            # Should handle None gracefully
            assert 'myscript.cmd' in result
    
    def test_get_user_edited_command_none_selected(self):
        """Test getting user edited command when selected is None."""
        import cmdfzf
        
        result = cmdfzf.get_user_edited_command(None)
        
        assert result is None


class TestExecuteCommand:
    """Test cases for execute_command function."""
    
    def test_execute_command_success(self, capsys):
        """Test successful command execution."""
        import cmdfzf
        
        with patch('cmdfzf.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock()
            
            cmdfzf.execute_command('test_cmd')
            
            mock_run.assert_called_once_with('test_cmd', shell=True, check=True)
    
    def test_execute_command_failure(self, capsys):
        """Test failed command execution."""
        import cmdfzf
        
        with patch('cmdfzf.subprocess.run') as mock_run:
            from subprocess import CalledProcessError
            mock_run.side_effect = CalledProcessError(1, 'test_cmd')
            
            cmdfzf.execute_command('test_cmd')
            
            captured = capsys.readouterr()
            assert 'Error executing command' in captured.out


class TestMainFunction:
    """Test cases for main function."""
    
    def test_main_no_cmd_files(self, capsys):
        """Test main when no cmd files are found."""
        import cmdfzf
        
        with patch('cmdfzf.get_cmd_files', return_value=[]):
            with patch('cmdfzf.sys.exit') as mock_exit:
                cmdfzf.main()
                
                captured = capsys.readouterr()
                assert 'No .cmd files found' in captured.out
                mock_exit.assert_called_once_with(1)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
