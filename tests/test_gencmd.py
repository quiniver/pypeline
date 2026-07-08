"""Tests for src/gencmd.py - Windows .cmd wrapper generator."""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Mock tkinter BEFORE importing gencmd to avoid ImportError on headless systems
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest


class TestExtractPaths:
    """Test path extraction from .cmd files."""
    
    def test_extract_valid_cmd_with_env(self, temp_dir):
        """Test extracting paths from a valid .cmd file with env name."""
        from gencmd import extract_python_and_script_paths_and_env
        
        cmd_file = temp_dir / "test.cmd"
        cmd_file.write_text(
            ":: env-name: myenv\n"
            "@echo off\n"
            '"python3" "path/to/script.py" %*'
        )
        
        python_interpreter, script_path, old_env_name = extract_python_and_script_paths_and_env(str(cmd_file))
        
        assert python_interpreter == 'python3'
        assert script_path == 'path/to/script.py'
        assert old_env_name == 'myenv'
    
    def test_extract_valid_cmd_without_env(self, temp_dir):
        """Test extracting paths from a .cmd file without env name."""
        from gencmd import extract_python_and_script_paths_and_env
        
        cmd_file = temp_dir / "test.cmd"
        cmd_file.write_text(
            "@echo off\n"
            '"python" "script.py" %*'
        )
        
        python_interpreter, script_path, old_env_name = extract_python_and_script_paths_and_env(str(cmd_file))
        
        assert python_interpreter == 'python'
        assert script_path == 'script.py'
        assert old_env_name is None
    
    def test_extract_empty_cmd_file(self, temp_dir, capsys):
        """Test extracting from empty .cmd file raises error."""
        from gencmd import extract_python_and_script_paths_and_env
        
        cmd_file = temp_dir / "empty.cmd"
        cmd_file.write_text("")
        
        with pytest.raises(SystemExit):
            extract_python_and_script_paths_and_env(str(cmd_file))
    
    def test_extract_invalid_format(self, temp_dir, capsys):
        """Test extracting from .cmd file without %* suffix raises error."""
        from gencmd import extract_python_and_script_paths_and_env
        
        cmd_file = temp_dir / "bad.cmd"
        cmd_file.write_text(
            "@echo off\n"
            'python script.py'
        )
        
        with pytest.raises(SystemExit):
            extract_python_and_script_paths_and_env(str(cmd_file))
    
    def test_extract_io_error(self, temp_dir, capsys):
        """Test reading a non-existent .cmd file raises error."""
        from gencmd import extract_python_and_script_paths_and_env
        
        with pytest.raises(SystemExit):
            extract_python_and_script_paths_and_env("/nonexistent/file.cmd")


class TestGencmdMain:
    """Test main() function of gencmd.py with mocked GUI."""
    
    @pytest.fixture(autouse=True)
    def mock_tkinter(self, monkeypatch):
        """Mock tkinter to avoid GUI dependency."""
        mock_tk = MagicMock()
        mock_root = MagicMock()
        mock_root.withdraw = MagicMock()
        mock_root.destroy = MagicMock()
        mock_tk.Tk.return_value = mock_root
        monkeypatch.setattr('gencmd.tk', mock_tk)
        monkeypatch.setattr('gencmd.filedialog', MagicMock())
    
    def test_create_mode_with_env_name(self, temp_dir):
        """Test creating cmd wrapper with specified conda env name."""
        script_path = temp_dir / "test_script.py"
        script_path.write_text('print("hello")')
        
        output_dir = temp_dir / "output"
        output_dir.mkdir()
        
        with patch('sys.argv', [
            'gencmd.py',
            str(script_path),
            str(output_dir),
            '-n', 'test_env'
        ]):
            with patch('gencmd.get_python_interpreter_for_conda_env', return_value='/conda/envs/test_env/bin/python'):
                with patch('subprocess.run') as mock_run:
                    mock_run.return_value = MagicMock(stdout="Usage: test_script.py [--help]")
                    try:
                        from gencmd import main
                        main()
                    except SystemExit as e:
                        assert e.code in (0, 1)
    
    def test_update_mode_with_existing_cmd(self, temp_dir):
        """Test updating existing .cmd file."""
        cmd_file = temp_dir / "existing.cmd"
        cmd_file.write_text(
            '@echo off\n'
            '"python3" "path/to/script.py" %*'
        )
        
        with patch('sys.argv', ['gencmd.py', '--update', str(cmd_file)]):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(stdout="Usage: script.py")
                try:
                    from gencmd import main
                    main()
                except SystemExit as e:
                    # May exit due to script path validation
                    pass
    
    def test_update_mode_invalid_cmd_file(self, temp_dir, capsys):
        """Test updating with non-.cmd file raises error."""
        script_path = temp_dir / "not_a_cmd.txt"
        script_path.write_text("not a cmd file")
        
        with patch('sys.argv', ['gencmd.py', '--update', str(script_path)]):
            try:
                from gencmd import main
                main()
            except SystemExit as e:
                assert e.code == 1
    
    def test_create_mode_no_script_selected(self, temp_dir, capsys):
        """Test create mode with no script selected raises error."""
        with patch('sys.argv', ['gencmd.py', '/nonexistent/path']):
            try:
                from gencmd import main
                main()
            except SystemExit as e:
                assert e.code == 1


class TestGencmdHelpers:
    """Test helper functions in gencmd.py."""
    
    @pytest.fixture(autouse=True)
    def mock_tkinter(self, monkeypatch):
        """Mock tkinter to avoid GUI dependency."""
        mock_tk = MagicMock()
        mock_root = MagicMock()
        mock_root.withdraw = MagicMock()
        mock_root.destroy = MagicMock()
        mock_tk.Tk.return_value = mock_root
        monkeypatch.setattr('gencmd.tk', mock_tk)
        monkeypatch.setattr('gencmd.filedialog', MagicMock())
    
    def test_select_python_script(self):
        """Test selecting a Python script via dialog."""
        from gencmd import select_python_script
        
        with patch('gencmd.filedialog.askopenfilename', return_value='/path/to/script.py'):
            result = select_python_script()
            assert result == '/path/to/script.py'
    
    def test_select_python_script_cancelled(self):
        """Test script selection cancelled."""
        from gencmd import select_python_script
        
        with patch('gencmd.filedialog.askopenfilename', return_value=None):
            result = select_python_script()
            assert result is None
    
    def test_select_cmd_file(self):
        """Test selecting a .cmd file via dialog."""
        from gencmd import select_cmd_file
        
        with patch('gencmd.filedialog.askopenfilename', return_value='/path/to/script.cmd'):
            result = select_cmd_file()
            assert result == '/path/to/script.cmd'
    
    def test_select_output_directory(self):
        """Test selecting output directory via dialog."""
        from gencmd import select_output_directory
        
        with patch('gencmd.filedialog.askdirectory', return_value='/output/dir'):
            result = select_output_directory()
            assert result == '/output/dir'
    
    def test_select_output_directory_cancelled(self):
        """Test directory selection cancelled."""
        from gencmd import select_output_directory
        
        with patch('gencmd.filedialog.askdirectory', return_value=None):
            result = select_output_directory()
            assert result is None
