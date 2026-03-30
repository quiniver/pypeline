"""Simple tests to verify the test infrastructure works."""

import sys
import os


def test_import_debug():
    """Test that debug module can be imported."""
    from debug import Debug, debug, verbose
    
    assert Debug is not None
    assert debug is not None
    assert verbose is not None


def test_import_cmdfzf():
    """Test that cmdfzf module can be imported."""
    import cmdfzf
    
    assert hasattr(cmdfzf, 'get_cmd_files')
    assert hasattr(cmdfzf, 'run_fzf_with_preview')


def test_import_cmdlist():
    """Test that cmdlist module can be imported."""
    import cmdlist
    
    assert hasattr(cmdlist, 'list_cmd_files')


def test_import_gencmd():
    """Test that gencmd module can be imported."""
    import gencmd
    
    assert hasattr(gencmd, 'extract_python_and_script_paths_and_env')


def test_import_markcms():
    """Test that markcms module can be imported."""
    import markcms
    
    assert hasattr(markcms, 'resolve_path')
    assert hasattr(markcms, 'load_config')


def test_debug_class_initialization():
    """Test Debug class basic initialization."""
    from debug import Debug
    
    # Test default initialization
    debug = Debug()
    assert debug.enabled is False
    assert isinstance(debug.prefix, str)
    
    # Test with enabled=True
    debug_enabled = Debug(enabled=True)
    assert debug_enabled.enabled is True
    
    # Test with custom prefix
    debug_custom = Debug(prefix="[TEST]")
    assert debug_custom.prefix == "[TEST] "


def test_debug_on_off():
    """Test turning debug on and off."""
    from debug import Debug
    
    debug = Debug(enabled=False)
    assert debug.enabled is False
    
    debug.on()
    assert debug.enabled is True
    
    debug.off()
    assert debug.enabled is False
