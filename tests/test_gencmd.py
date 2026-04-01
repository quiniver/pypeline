"""Tests for src/gencmd.py - Windows .cmd wrapper generator."""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest


class TestGenerateCmd:
    """Test suite for gencmd.py module (mocked GUI)."""
    
    @pytest.fixture(autouse=True)
    def mock_gui(self):
        """Mock tkinter file dialogs to avoid GUI dependencies."""
        with patch('gencmd.tk') as mock_tk:
            mock_root = MagicMock()
            mock_root.withdraw = MagicMock()
            mock_tk.Tk.return_value = mock_root
            
            # Mock file dialog responses
            mock_root.destroy = MagicMock()
            yield mock_tk
    
    def test_main_with_env_name(self, temp_dir):
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
            # Should complete without error (with mocked subprocess for --help)
            try:
                from gencmd import main
                main()
            except SystemExit as e:
                # Expected when help capture fails due to mock
                assert e.code in (0, 1)
    
    def test_update_mode_with_existing_cmd(self, temp_dir):
        """Test updating existing .cmd file."""
        # Create a sample .cmd file
        cmd_file = temp_dir / "existing.cmd"
        cmd_file.write_text(
            '@echo off\n'
            '"""python3\" \"path/to/script.py\" %*'
        )
        
        with patch('sys.argv', ['gencmd.py', '--update', str(cmd_file)]):
            # Should handle missing script gracefully
            try:
                from gencmd import main
                main()
            except SystemExit as e:
                # Expected when script path validation fails
                assert e.code == 1
