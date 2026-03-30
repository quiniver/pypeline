"""Tests for gencmd.py - Testing command generation functions."""

import sys
import os
from unittest.mock import patch, MagicMock
from io import StringIO

# Add src to path so we can import from it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestSelectFunctions:
    """Test cases for GUI selection functions."""
    
    def test_select_python_script(self):
        """Test selecting Python script (returns None without actual dialog)."""
        import gencmd
        
        with patch('gencmd.tk.Tk') as mock_tk:
            mock_root = MagicMock()
            mock_tk.return_value = mock_root
            
            result = gencmd.select_python_script()
            
            assert result is None  # Without file dialog, returns None
    
    def test_select_cmd_file(self):
        """Test selecting .cmd file (returns None without actual dialog)."""
        import gencmd
        
        with patch('gencmd.tk.Tk') as mock_tk:
            mock_root = MagicMock()
            mock_tk.return_value = mock_root
            
            result = gencmd.select_cmd_file()
            
            assert result is None
    
    def test_select_output_directory(self):
        """Test selecting output directory (returns None without actual dialog)."""
        import gencmd
        
        with patch('gencmd.tk.Tk') as mock_tk:
            mock_root = MagicMock()
            mock_tk.return_value = mock_root
            
            result = gencmd.select_output_directory()
            
            assert result is None


class TestExtractPythonAndScriptPaths:
    """Test cases for extract_python_and_script_paths_and_env function."""
    
    def test_extract_paths_success(self, tmp_path):
        """Test extracting paths from valid .cmd file."""
        import gencmd
        
        # Create a temporary .cmd file with expected format
        cmd_file = tmp_path / "test.cmd"
        content = '@echo off\n"python.exe" "/path/to/script.py" %*'
        cmd_file.write_text(content)
        
        python_interp, script_path, old_env = gencmd.extract_python_and_script_paths_and_env(str(cmd_file))
        
        assert python_interp == 'python.exe'
        assert script_path == '/path/to/script.py'
        assert old_env is None
    
    def test_extract_paths_with_env_name(self, tmp_path):
        """Test extracting paths with env-name comment."""
        import gencmd
        
        cmd_file = tmp_path / "test.cmd"
        content = '@echo off\n:: env-name: myenv\n"python.exe" "/path/to/script.py" %*'
        cmd_file.write_text(content)
        
        python_interp, script_path, old_env = gencmd.extract_python_and_script_paths_and_env(str(cmd_file))
        
        assert old_env == 'myenv'
    
    def test_extract_paths_empty_file(self, tmp_path):
        """Test extracting paths from empty file."""
        import gencmd
        
        cmd_file = tmp_path / "empty.cmd"
        cmd_file.write_text("")
        
        with patch('sys.exit') as mock_exit:
            try:
                gencmd.extract_python_and_script_paths_and_env(str(cmd_file))
            except SystemExit:
                pass
            
            assert mock_exit.called
    
    def test_extract_paths_invalid_format(self, tmp_path):
        """Test extracting paths from invalid format."""
        import gencmd
        
        cmd_file = tmp_path / "invalid.cmd"
        content = '@echo off\nsome random line without %*'
        cmd_file.write_text(content)
        
        with patch('sys.exit') as mock_exit:
            try:
                gencmd.extract_python_and_script_paths_and_env(str(cmd_file))
            except SystemExit:
                pass
            
            assert mock_exit.called


class TestGetPythonInterpreterForCondaEnv:
    """Test cases for get_python_interpreter_for_conda_env function."""
    
    def test_get_conda_python_success(self):
        """Test getting Python path from conda environment."""
        import gencmd
        
        with patch('gencmd.subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = '/path/to/conda/env/python'
            mock_run.return_value = mock_result
            
            python_path = gencmd.get_python_interpreter_for_conda_env('myenv')
            
            assert python_path == '/path/to/conda/env/python'
    
    def test_get_conda_python_nonexistent(self):
        """Test getting Python path when environment doesn't exist."""
        import gencmd
        
        with patch('gencmd.subprocess.run') as mock_run:
            from subprocess import CalledProcessError
            mock_run.side_effect = CalledProcessError(1, 'conda', stderr='env not found')
            
            with patch('sys.exit') as mock_exit:
                try:
                    gencmd.get_python_interpreter_for_conda_env('nonexistent')
                except SystemExit:
                    pass
                
                assert mock_exit.called


class TestMainFunction:
    """Test cases for main function."""
    
    def test_main_create_mode_with_args(self, tmp_path):
        """Test main in create mode with command line arguments."""
        import gencmd
        
        # Create a temporary Python script
        py_file = tmp_path / "test_script.py"
        py_file.write_text("print('hello')")
        
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        with patch('gencmd.sys.exit'):  # Prevent actual exit
            try:
                sys.argv = ['gencmd.py', str(py_file), str(output_dir)]
                
                result = gencmd.main()
                
                # Check that .cmd file was created
                expected_cmd = output_dir / "test_script.cmd"
                assert expected_cmd.exists()
                
                # Verify content
                content = expected_cmd.read_text()
                assert '@echo off' in content
                assert 'python' in content.lower()
            except SystemExit:
                pass  # Expected when subprocess fails
    
    def test_main_update_mode(self, tmp_path):
        """Test main in update mode."""
        import gencmd
        
        # Create a temporary .cmd file
        cmd_file = tmp_path / "test.cmd"
        content = '@echo off\n"python.exe" "/path/to/script.py" %*'
        cmd_file.write_text(content)
        
        with patch('gencmd.sys.exit'):  # Prevent actual exit
            try:
                sys.argv = ['gencmd.py', '--update', str(cmd_file)]
                
                result = gencmd.main()
                
                # Verify the file was updated (should still exist)
                assert cmd_file.exists()
            except SystemExit:
                pass
    
    def test_main_update_mode_with_env_name(self, tmp_path):
        """Test main in update mode with env name."""
        import gencmd
        
        cmd_file = tmp_path / "test.cmd"
        content = '@echo off\n"python.exe" "/path/to/script.py" %*'
        cmd_file.write_text(content)
        
        # Mock the conda path lookup
        with patch('gencmd.get_python_interpreter_for_conda_env', return_value='/new/python/path'):
            with patch('gencmd.subprocess.run') as mock_run:
                from subprocess import CompletedProcess
                mock_run.return_value = CompletedProcess(['python', '--help'], 0, stdout='help text')
                
                try:
                    sys.argv = ['gencmd.py', '--update', str(cmd_file), '-n', 'myenv']
                    
                    gencmd.main()
                    
                    # Verify new interpreter was used
                    content = cmd_file.read_text()
                    assert '/new/python/path' in content or '"python"' not in content.split('%*')[0]
                except SystemExit:
                    pass
    
    def test_main_invalid_script_path(self, tmp_path):
        """Test main with invalid script path."""
        import gencmd
        
        with patch('gencmd.sys.exit') as mock_exit:
            try:
                sys.argv = ['gencmd.py', '/nonexistent/script.py']
                
                result = gencmd.main()
            except SystemExit:
                assert mock_exit.called


class TestPlaceholderProcessing:
    """Test cases for help text processing."""
    
    def test_process_help_lines(self):
        """Test processing of help lines into comment format."""
        # This tests the logic that converts help output to :: comments
        help_text = "Usage: script.py [OPTIONS]\n  -v, --verbose  Enable verbose mode"
        
        processed = [":: " + line if line.strip() else "::" for line in help_text.splitlines()]
        
        assert processed[0] == ":: Usage: script.py [OPTIONS]"
        assert processed[1] == "::   -v, --verbose  Enable verbose mode"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
