"""Global pytest configuration and fixtures."""
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory with sample files."""
    # Create sample .cmd file
    cmd_file = tmp_path / "test.cmd"
    cmd_file.write_text("@echo off\necho Hello World")
    
    # Create sample Python script
    py_script = tmp_path / "sample.py"
    py_script.write_text('''#!/usr/bin/env python3
"""Sample script."""
import argparse

def main():
    print("Hello from sample")

if __name__ == "__main__":
    main()
''')
    
    return tmp_path


@pytest.fixture
def mock_config_yaml():
    """Mock YAML config content."""
    return '''
docs:
  - title: Home
    file: index.md
    type: page
  - title: Gallery
    file: images.md
    type: gallery
    media_dir: media
'''


@pytest.fixture
def mock_nav_yaml():
    """Mock deprecated nav YAML config content."""
    return '''
nav:
  - title: Old Navigation
    file: old.md
'''


@pytest.fixture
def mock_template_fragments(temp_dir):
    """Create template fragment files."""
    templates = temp_dir / "templates"
    templates.mkdir()
    
    (templates / "header.md").write_text("# Header\n")
    (templates / "footer.md").write_text("*Footer*\n")
    
    return templates


@pytest.fixture(autouse=True)
def mock_gh_cli(monkeypatch):
    """Mock GitHub CLI commands globally."""
    def mock_run(*args, **kwargs):
        result = MagicMock()
        result.returncode = 0
        if 'issue list' in str(args[0]):
            result.stdout = json.dumps([{"number": 1, "title": "Test Issue", "state": "open"}])
        elif '/issues/' in str(args[0]):
            result.stdout = json.dumps({"body": "Issue body", "created_at": "2024-01-01T00:00:00Z"})
        else:
            result.stdout = ''
        return result
    
    monkeypatch.setattr('subprocess.run', mock_run)


import json
