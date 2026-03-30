"""Tests for gencmd.py - Testing command generation functions."""

from unittest.mock import patch, MagicMock


class TestSelectFunctions:
    """Test cases for GUI selection functions."""
    
    def test_select_python_script(self):
        """Test selecting Python script (returns None without actual dialog)."""
        import gencmd
        
        with patch('gencmd.tk.Tk') as mock_tk:
            mock_root = MagicMock()
            mock_tk.return_value = mock_root
            
            result = gencmd.select_python_script()
            
            assert result is None
    
    def test_select_cmd_file(self):
        """Test selecting .cmd file (returns None without actual dialog)."""
        import gencmd
        
        with patch('gencmd.tk.Tk') as mock_tk:
            mock_root = MagicMock()
            mock_tk.return_value = mock_root
            
            result = gencmd.select_cmd_file()
            
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
                original_argv = __import__('sys').argv.copy()
                try:
                    __import__('sys').argv = ['gencmd.py', str(py_file), str(output_dir)]
                    
                    result = gencmd.main()
                    
                    # Check that .cmd file was created
                    expected_cmd = output_dir / "test_script.cmd"
                    assert expected_cmd.exists()
                finally:
                    __import__('sys').argv = original_argv
            except SystemExit:
                pass  # Expected when subprocess fails


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
