# Tests for pypeline

This directory contains pytest tests for the Python scripts in the `src/` directory.

## Overview

The test suite covers the following modules:

- **test_debug.py** - Tests for the `debug.py` module (Debug class functionality)
- **test_cmdfzf.py** - Tests for the `cmdfzf.py` module (FZF-based command selection)
- **test_cmdlist.py** - Tests for the `cmdlist.py` module (Command file listing)
- **test_gencmd.py** - Tests for the `gencmd.py` module (Windows .cmd wrapper generation)
- **test_markcms.py** - Tests for the `markcms.py` module (Markdown documentation generator)

## Requirements

To run the tests, you need:

```bash
pip install -r requirements-test.txt
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run with verbose output
```bash
pytest -v
```

### Run specific test file
```bash
pytest tests/test_debug.py
pytest tests/test_cmdfzf.py
```

### Run specific test class
```bash
pytest tests/test_debug.py::TestDebugClass
```

### Run specific test function
```bash
pytest tests/test_debug.py::TestDebugClass::test_init_default_values
```

### Run with coverage report
```bash
pytest --cov=src --cov-report=html
```

Then open `htmlcov/index.html` in your browser.

## Test Structure

Each test file follows the pytest naming conventions:

- Files are named `test_*.py`
- Classes are named `Test*`
- Functions are named `test_*`

### Example Test Class

```python
class TestDebugClass:
    """Test cases for the Debug class."""
    
    def test_init_default_values(self):
        """Test that default values are set correctly."""
        debug = Debug()
        assert debug.enabled is False
        assert debug.prefix == ""
```

### Using Mocks and Fixtures

The tests use `unittest.mock` for mocking external dependencies:

```python
from unittest.mock import patch, MagicMock

@patch('builtins.print')
def test_print_enabled(mock_print):
    """Test printing when enabled."""
    debug = Debug(enabled=True)
    debug.print("test message")
    
    mock_print.assert_called_once_with("test message")
```

### Using Temporary Directories

For file-based tests, `tmp_path` fixture is used:

```python
def test_extract_paths_success(tmp_path):
    """Test extracting paths from valid .cmd file."""
    cmd_file = tmp_path / "test.cmd"
    content = '@echo off\n"python.exe" "/path/to/script.py" %*'
    cmd_file.write_text(content)
    
    python_interp, script_path, old_env = extract_python_and_script_paths_and_env(str(cmd_file))
    
    assert python_interp == 'python.exe'
```

## Test Coverage Goals

The goal is to achieve comprehensive test coverage for all non-GUI functionality:

- **debug.py**: 100% coverage (all Debug class methods)
- **cmdfzf.py**: High coverage for core functions (FZF integration excluded)
- **cmdlist.py**: High coverage for file listing logic
- **gencmd.py**: Coverage for non-GUI functions (file dialogs mocked)
- **markcms.py**: Coverage for template and path resolution logic

## CI/CD Integration

To integrate with GitHub Actions, create `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'
      - name: Install dependencies
        run: |
          pip install -r requirements-test.txt
      - name: Run tests
        run: pytest --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Contributing to Tests

When adding new features or modifying existing code:

1. Write a test first (Test-Driven Development)
2. Ensure all existing tests pass
3. Add tests for edge cases and error conditions
4. Update this README if test structure changes

## Troubleshooting

### Test failures due to missing dependencies
```bash
pip install -r requirements-test.txt --upgrade
```

### Import errors when running tests
Ensure you're running from the repository root:
```bash
cd /path/to/pypeline
pytest
```

### GUI-related test issues
GUI functions (file dialogs) are mocked in tests. If you see unexpected behavior, check that mocks are properly set up.

## License

Tests follow the same license as the main project.
