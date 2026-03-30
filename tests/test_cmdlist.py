"""Tests for cmdlist.py - Testing command listing functions."""

from unittest.mock import patch, MagicMock


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


class TestMainFunction:
    """Test cases for main function."""
    
    def test_main_default_args(self, capsys):
        """Test main with default arguments."""
        import cmdlist
        
        original_argv = __import__('sys').argv.copy()
        try:
            with patch('cmdlist.list_cmd_files') as mock_list:
                mock_list.return_value = None
                
                __import__('sys').argv = ['cmdlist.py']
                
                cmdlist.main()
                
                assert mock_list.called
        finally:
            __import__('sys').argv = original_argv
    
    def test_main_bare_argument(self, capsys):
        """Test main with --bare argument."""
        import cmdlist
        
        original_argv = __import__('sys').argv.copy()
        try:
            __import__('sys').argv = ['cmdlist.py', '--bare']
            
            with patch('cmdlist.list_cmd_files') as mock_list:
                mock_list.return_value = None
                
                cmdlist.main()
                
                # Verify show_comments is False
                call_kwargs = mock_list.call_args[1] or {}
                assert call_kwargs.get('show_comments', True) == False
        finally:
            __import__('sys').argv = original_argv


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
