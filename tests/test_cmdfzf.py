"""Tests for src/cmdfzf.py - Testing command file selection functions."""

from unittest.mock import patch, MagicMock


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
    
    def test_get_cmd_files_nonexistent_directory(self, capsys):
        """Test getting cmd files from nonexistent directory."""
        import cmdfzf
        
        with patch('cmdfzf.os.path.exists', return_value=False) as mock_exists:
            result = cmdfzf.get_cmd_files('/nonexistent/path')
            
            assert result == []
            mock_exists.assert_called_once_with('/nonexistent/path')
            captured = capsys.readouterr()
            assert "does not exist" in captured.out
    
    def test_get_cmd_files_mixed_extensions(self):
        """Test filtering out non-.cmd files."""
        import cmdfzf
        
        with patch('cmdfzf.os.path.exists', return_value=True):
            with patch('cmdfzf.os.listdir', return_value=['a.cmd', 'b.exe', 'c.py', 'd.cmd']):
                result = cmdfzf.get_cmd_files('/fake/path')
                assert 'a' in result
                assert 'd' in result
                assert 'b' not in result  # .exe
                assert 'c' not in result  # .py
    
    def test_get_cmd_files_nested_name(self):
        """Test cmd file with dots in name."""
        import cmdfzf
        
        with patch('cmdfzf.os.path.exists', return_value=True):
            with patch('cmdfzf.os.listdir', return_value=['my.script.cmd']):
                result = cmdfzf.get_cmd_files('/fake/path')
                assert 'my.script' in result


class TestRunFzfWithPreview:
    """Test cases for run_fzf_with_preview function."""
    
    def test_run_fzf_success(self):
        """Test successful FZF selection."""
        import cmdfzf
        
        with patch('cmdfzf.iterfzf', return_value='selected_script') as mock_iterfzf:
            result = cmdfzf.run_fzf_with_preview(['script1', 'script2'])
            
            assert result == 'selected_script'
    
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
    
    def test_run_fzf_with_query(self):
        """Test FZF with initial query."""
        import cmdfzf
        
        with patch('cmdfzf.iterfzf', return_value='matched_script') as mock_iterfzf:
            result = cmdfzf.run_fzf_with_preview(['script1', 'script2'], query='match')
            
            assert result == 'matched_script'
            # Verify query was passed
            call_kwargs = mock_iterfzf.call_args
            assert call_kwargs[1]['query'] == 'match'
    
    def test_run_fzf_with_custom_preview_percent(self):
        """Test FZF with custom preview percentage."""
        import cmdfzf
        
        with patch('cmdfzf.iterfzf', return_value='script') as mock_iterfzf:
            cmdfzf.run_fzf_with_preview(['script'], preview_percent=80)
            
            call_kwargs = mock_iterfzf.call_args
            assert call_kwargs[1]['__extra__'] is not None


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
    
    def test_get_user_edited_command_with_spaces_in_args(self):
        """Test getting user edited command with spaces in arguments."""
        import cmdfzf
        
        with patch('builtins.input', return_value='--arg "hello world"'):
            result = cmdfzf.get_user_edited_command('myscript')
            
            assert result == 'myscript.cmd --arg "hello world"'
    
    def test_get_user_edited_command_none_selected(self):
        """Test when no command is selected."""
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
            captured = capsys.readouterr()
            assert "Running test_cmd" in captured.out
    
    def test_execute_command_failure(self, capsys):
        """Test command execution failure."""
        import cmdfzf
        
        with patch('cmdfzf.subprocess.run') as mock_run:
            mock_run.side_effect = Exception("Command failed")
            
            cmdfzf.execute_command('bad_cmd')
            
            captured = capsys.readouterr()
            assert "Error executing command" in captured.out
    
    def test_execute_command_none(self, capsys):
        """Test executing None command."""
        import cmdfzf
        
        cmdfzf.execute_command(None)
        # Should not print anything or crash


class TestMainFunction:
    """Test cases for main function."""
    
    def test_main_no_cmd_files(self, capsys):
        """Test main when no cmd files are found."""
        import cmdfzf
        
        with patch('cmdfzf.get_cmd_files', return_value=[]):
            with patch('cmdfzf.sys.exit') as mock_exit:
                # Reset sys.argv to avoid conflicts
                import sys
                original_argv = sys.argv.copy()
                try:
                    sys.argv = ['cmdfzf.py']
                    cmdfzf.main()
                    
                    captured = capsys.readouterr()
                    assert 'No .cmd files found' in captured.out or mock_exit.called
                finally:
                    sys.argv = original_argv
    
    def test_main_selection_cancelled(self, capsys):
        """Test main when user cancels FZF selection."""
        import cmdfzf
        
        with patch('cmdfzf.get_cmd_files', return_value=['script1']):
            with patch('cmdfzf.run_fzf_with_preview', return_value=None):
                with patch('cmdfzf.sys.exit') as mock_exit:
                    import sys
                    original_argv = sys.argv.copy()
                    try:
                        sys.argv = ['cmdfzf.py']
                        cmdfzf.main()
                        
                        captured = capsys.readouterr()
                        assert 'cancelled' in captured.out.lower() or mock_exit.called
                    finally:
                        sys.argv = original_argv
    
    def test_main_execution_cancelled(self, capsys):
        """Test main when user cancels after selection."""
        import cmdfzf
        
        with patch('cmdfzf.get_cmd_files', return_value=['script1']):
            with patch('cmdfzf.run_fzf_with_preview', return_value='script1'):
                with patch('cmdfzf.get_user_edited_command', return_value=None):
                    with patch('cmdfzf.sys.exit') as mock_exit:
                        import sys
                        original_argv = sys.argv.copy()
                        try:
                            sys.argv = ['cmdfzf.py']
                            cmdfzf.main()
                            
                            captured = capsys.readouterr()
                            assert 'cancelled' in captured.out.lower() or mock_exit.called
                        finally:
                            sys.argv = original_argv
    
    def test_main_show_preview(self):
        """Test the show_preview function."""
        import cmdfzf
        
        with patch('cmdfzf.subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "echo hello"
            mock_run.return_value = mock_result
            
            cmdfzf.show_preview('myscript')
            
            mock_run.assert_called_once()


class TestCMDDIR:
    """Test CMDDIR constant."""
    
    def test_cmddir_is_set(self):
        """Test that CMDDIR is properly set."""
        import cmdfzf
        
        assert hasattr(cmdfzf, 'CMDDIR')
        assert isinstance(cmdfzf.CMDDIR, str)
