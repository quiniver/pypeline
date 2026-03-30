"""Tests for debug.py - Testing the Debug class functionality."""

import sys
from unittest.mock import patch, MagicMock

# Import paths are handled by conftest.py


class TestDebugClass:
    """Test cases for the Debug class."""
    
    def test_init_default_values(self):
        """Test that default values are set correctly."""
        from debug import Debug
        debug = Debug()
        assert debug.enabled is False
        assert debug.prefix == ""
    
    def test_init_with_enabled_true(self):
        """Test initialization with enabled=True."""
        from debug import Debug
        debug = Debug(enabled=True)
        assert debug.enabled is True
        assert debug.prefix == ""
    
    def test_init_with_prefix(self):
        """Test initialization with custom prefix."""
        from debug import Debug
        debug = Debug(prefix="[TEST]")
        assert debug.enabled is False
        assert debug.prefix == "[TEST] "
    
    def test_init_with_prefix_and_enabled(self):
        """Test initialization with both prefix and enabled=True."""
        from debug import Debug
        debug = Debug(enabled=True, prefix="DEBUG")
        assert debug.enabled is True
        assert debug.prefix == "DEBUG "
    
    def test_print_disabled_no_output(self, capsys):
        """Test that nothing is printed when disabled."""
        from debug import Debug
        debug = Debug(enabled=False)
        debug.print("This should not appear")
        
        captured = capsys.readouterr()
        assert captured.out == ""
    
    @patch('builtins.print')
    def test_print_enabled_with_prefix(self, mock_print):
        """Test printing with prefix when enabled."""
        from debug import Debug
        debug = Debug(enabled=True, prefix="[DEBUG]")
        debug.print("test message", "extra")
        
        mock_print.assert_called_once_with("[DEBUG] ", "test message", "extra")
    
    @patch('builtins.print')
    def test_print_enabled_without_prefix(self, mock_print):
        """Test printing without prefix when enabled."""
        from debug import Debug
        debug = Debug(enabled=True)
        debug.print("test message")
        
        mock_print.assert_called_once_with("test message")
    
    @patch('builtins.print')
    def test_print_with_kwargs(self, mock_print):
        """Test print with keyword arguments."""
        from debug import Debug
        debug = Debug(enabled=True, prefix="[TEST]")
        debug.print("hello", sep="-", end="!")
        
        mock_print.assert_called_once_with("[TEST] ", "hello", sep="-", end="!")
    
    def test_on_method(self):
        """Test the on() method enables printing."""
        from debug import Debug
        debug = Debug(enabled=False)
        assert debug.enabled is False
        
        debug.on()
        assert debug.enabled is True
    
    def test_off_method(self):
        """Test the off() method disables printing."""
        from debug import Debug
        debug = Debug(enabled=True)
        assert debug.enabled is True
        
        debug.off()
        assert debug.enabled is False
    
    def test_toggle_enable_disable(self):
        """Test toggling between enabled and disabled."""
        from debug import Debug
        debug = Debug(enabled=False)
        
        debug.on()
        assert debug.enabled is True
        
        debug.off()
        assert debug.enabled is False
        
        debug.on()
        assert debug.enabled is True


class TestDebugInstances:
    """Test the shared debug and verbose instances."""
    
    def test_debug_instance_defaults(self):
        """Test that default debug instance has correct settings."""
        from debug import debug, verbose
        
        assert debug.enabled is False
        assert debug.prefix == "[DEBUG]   "
        
        assert verbose.enabled is False
        assert verbose.prefix == ""
    
    def test_verbose_instance_no_prefix(self):
        """Test that verbose instance has no prefix."""
        from debug import verbose
        
        assert verbose.prefix == ""
    
    def test_debug_instance_can_be_enabled(self):
        """Test that debug instance can be enabled."""
        from debug import debug
        
        assert debug.enabled is False
        
        debug.on()
        assert debug.enabled is True
        
        # Reset for other tests
        debug.off()


class TestDebugEdgeCases:
    """Edge case tests for Debug class."""
    
    def test_print_with_none(self, capsys):
        """Test printing None value."""
        from debug import Debug
        debug = Debug(enabled=True)
        debug.print(None)
        
        captured = capsys.readouterr()
        assert "None" in captured.out
    
    def test_prefix_with_empty_string(self):
        """Test that empty string prefix works."""
        from debug import Debug
        debug = Debug(prefix="")
        assert debug.prefix == ""


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
