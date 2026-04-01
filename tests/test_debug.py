"""Tests for src/debug.py - Debug and verbose output helpers."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from debug import Debug, debug, verbose


class TestDebugClass:
    """Test suite for the Debug class."""
    
    def test_init_defaults(self):
        """Test default initialization values."""
        d = Debug()
        assert d.enabled is False
        assert d.prefix == ""
    
    def test_init_with_enabled_true(self):
        """Test initialization with enabled=True."""
        d = Debug(enabled=True)
        assert d.enabled is True
        assert d.prefix == ""
    
    def test_init_with_prefix(self):
        """Test initialization with custom prefix."""
        d = Debug(prefix="[TEST]")
        assert d.prefix == "[TEST] "
    
    def test_init_with_prefix_no_trailing_space(self):
        """Test that trailing spaces are stripped from prefix."""
        d = Debug(prefix="DEBUG  ")
        assert d.prefix == "DEBUG "
    
    def test_print_disabled_by_default(self, capsys):
        """Test that print does nothing when disabled."""
        d = Debug()
        d.print("test message")
        captured = capsys.readouterr()
        assert captured.out == ""
    
    def test_print_enabled(self, capsys):
        """Test that print works when enabled."""
        d = Debug(enabled=True)
        d.print("hello", "world")
        captured = capsys.readouterr()
        assert captured.out == "hello world\n"
    
    def test_print_with_prefix(self, capsys):
        """Test print with custom prefix."""
        d = Debug(enabled=True, prefix="[DBG]")
        d.print("message")
        captured = capsys.readouterr()
        assert captured.out == "[DBG] message\n"
    
    def test_print_with_kwargs(self, capsys):
        """Test print passes kwargs to built-in print."""
        d = Debug(enabled=True)
        d.print("test", sep="-", end="!\n")
        captured = capsys.readouterr()
        assert captured.out == "test!\n"
    
    def test_on_method(self):
        """Test the on() method enables printing."""
        d = Debug(enabled=False)
        d.on()
        assert d.enabled is True
    
    def test_off_method(self):
        """Test the off() method disables printing."""
        d = Debug(enabled=True)
        d.off()
        assert d.enabled is False
    
    def test_shared_debug_instance_disabled(self):
        """Test that shared debug instance is disabled by default."""
        assert debug.enabled is False
    
    def test_shared_verbose_instance_disabled(self):
        """Test that shared verbose instance is disabled by default."""
        assert verbose.enabled is False
    
    def test_print_empty_args(self, capsys):
        """Test print with no arguments when enabled."""
        d = Debug(enabled=True)
        d.print()
        captured = capsys.readouterr()
        assert captured.out == "\n"


class TestDebugEdgeCases:
    """Edge case tests for Debug class."""
    
    def test_print_none_value(self, capsys):
        """Test print with None value."""
        d = Debug(enabled=True)
        d.print(None)
        captured = capsys.readouterr()
        assert captured.out == "None\n"
    
    def test_print_empty_string(self, capsys):
        """Test print with empty string."""
        d = Debug(enabled=True)
        d.print("")
        captured = capsys.readouterr()
        assert captured.out == "\n"
    
    def test_prefix_with_empty_string(self):
        """Test prefix as empty string."""
        d = Debug(prefix="")
        assert d.prefix == ""
    
    def test_multiple_on_off_cycles(self):
        """Test toggling on/off multiple times."""
        d = Debug(enabled=False)
        for _ in range(5):
            d.on()
            assert d.enabled is True
            d.off()
            assert d.enabled is False
