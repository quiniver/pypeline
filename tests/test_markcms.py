"""Tests for markcms.py - Testing markdown documentation generator functions."""

import sys
import os
from unittest.mock import patch, MagicMock
from io import StringIO
from pathlib import Path

# Add src to path so we can import from it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestResolvePath:
    """Test cases for resolve_path function."""
    
    def test_resolve_absolute_path(self):
        """Test resolving absolute path."""
        from markcms import resolve_path
        
        result = resolve_path('/absolute/path', Path('/base'))
        
        assert result.is_absolute()
        assert str(result) == '/absolute/path'
    
    def test_resolve_relative_path(self):
        """Test resolving relative path."""
        from markcms import resolve_path
        
        result = resolve_path('relative/path', Path('/base'))
        
        expected = Path('/base/relative/path').resolve()
        assert result == expected


class TestLoadConfig:
    """Test cases for load_config function."""
    
    def test_load_config_success(self, tmp_path):
        """Test loading valid config file."""
        from markcms import load_config
        
        config_file = tmp_path / "_config.yml"
        config_content = """
docs:
  - title: Test
    file: test.md
"""
        config_file.write_text(config_content)
        
        config = load_config(config_file)
        
        assert 'docs' in config
    
    def test_load_config_not_found(self, tmp_path):
        """Test loading nonexistent config file."""
        from markcms import load_config
        
        with patch('Path.exists', return_value=False):
            try:
                load_config(tmp_path / "nonexistent.yml")
            except FileNotFoundError as e:
                assert 'Config file not found' in str(e)
    
    def test_load_config_invalid_yaml(self, tmp_path):
        """Test loading invalid YAML config."""
        from markcms import load_config
        
        config_file = tmp_path / "_config.yml"
        # Invalid YAML with tab character
        config_content = "docs:\n\t- title: Test\n"
        config_file.write_text(config_content)
        
        try:
            load_config(config_file)
        except ValueError as e:
            assert 'Invalid YAML' in str(e)


class TestExtractFrontmatter:
    """Test cases for extract_frontmatter function."""
    
    def test_extract_with_frontmatter(self):
        """Test extracting frontmatter from content with YAML block."""
        from markcms import extract_frontmatter
        
        content = "---\ntitle: Test\n---\nThis is the body"
        
        frontmatter, body = extract_frontmatter(content)
        
        assert frontmatter is not None
        assert 'title: Test' in frontmatter
        assert 'This is the body' in body
    
    def test_extract_without_frontmatter(self):
        """Test extracting from content without frontmatter."""
        from markcms import extract_frontmatter
        
        content = "Just plain text"
        
        frontmatter, body = extract_frontmatter(content)
        
        assert frontmatter is None
        assert body == "Just plain text"


class TestGetMenuKey:
    """Test cases for get_menu_key function."""
    
    def test_get_menu_key_with_file(self):
        """Test getting menu key with file attribute."""
        from markcms import get_menu_key
        
        item = {"title": "Home", "file": "index.md"}
        
        key = get_menu_key(item)
        
        assert key == "index.md"
    
    def test_get_menu_key_link(self):
        """Test getting menu key for link type."""
        from markcms import get_menu_key
        
        item = {"title": "External Link", "type": "link"}
        
        key = get_menu_key(item)
        
        assert "__link__" in key
    
    def test_get_menu_key_without_file(self):
        """Test getting menu key without file attribute."""
        from markcms import get_menu_key
        
        item = {"title": "Unnamed Page"}
        
        key = get_menu_key(item)
        
        assert key == "Unnamed Page"


class TestGetMenuContent:
    """Test cases for get_menu_content function."""
    
    def test_get_menu_content_with_items(self):
        """Test getting menu content with multiple items."""
        from markcms import get_menu_content
        
        nav_items = [
            {"title": "Home", "file": "index.md"},
            {"title": "About", "file": "about.md"},
            {"title": "Contact", "file": "contact.md"}
        ]
        
        menu = get_menu_content(nav_items, "about.md")
        
        assert "**About**" in menu  # Active item should be bold
        assert "[" in menu  # Other items should have links
    
    def test_get_menu_content_single_item(self):
        """Test getting menu content with single item."""
        from markcms import get_menu_content
        
        nav_items = [{"title": "Home", "file": "index.md"}]
        
        menu = get_menu_content(nav_items, "index.md")
        
        assert "**Home**" in menu


class TestGetSitemapContent:
    """Test cases for get_sitemap_content function."""
    
    def test_get_sitemap_content_with_items(self):
        """Test getting sitemap content with multiple items."""
        from markcms import get_sitemap_content
        
        nav_items = [
            {"title": "Home", "file": "index.md"},
            {"title": "About", "file": "about.md"}
        ]
        
        sitemap = get_sitemap_content(nav_items, "about.md")
        
        assert "- **About**" in sitemap  # Active item should be bold
        assert "- [Home]" in sitemap
    
    def test_get_sitemap_content_single_item(self):
        """Test getting sitemap content with single item."""
        from markcms import get_sitemap_content
        
        nav_items = [{"title": "Home", "file": "index.md"}]
        
        sitemap = get_sitemap_content(nav_items, "index.md")
        
        assert "- **Home**" in sitemap


class TestMakeRelativePath:
    """Test cases for make_relative_path function."""
    
    def test_make_relative_same_root(self):
        """Test making relative path when both are under same root."""
        from markcms import make_relative_path
        
        start = Path('/project/docs').resolve()
        target = Path('/project/docs/page.md').resolve()
        
        rel = make_relative_path(target, start)
        
        assert str(rel) == 'page.md'


class TestListPlaceholders:
    """Test cases for list_placeholders function."""
    
    def test_list_placeholders_prints_builtins(self, capsys):
        """Test that list placeholders prints built-in placeholders."""
        from markcms import list_placeholders
        
        with patch('pathlib.Path.exists', return_value=False):
            list_placeholders(None)
            
            captured = capsys.readouterr()
            assert 'Built-in placeholders' in captured.out


class TestContextPlaceholders:
    """Test cases for context placeholder handling."""
    
    def test_context_placeholder_set(self):
        """Test that CONTEXT_PLACEHOLDERS is correctly defined."""
        from markcms import CONTEXT_PLACEHOLDERS
        
        assert 'frontmatter' in CONTEXT_PLACEHOLDERS
        assert 'menu' in CONTEXT_PLACEHOLDERS
        assert 'content' in CONTEXT_PLACEHOLDERS
        assert 'sitemap' in CONTEXT_PLACEHOLDERS


class TestReservedTemplateNames:
    """Test cases for reserved template names."""
    
    def test_reserved_names_includes_builtins(self):
        """Test that RESERVED_TEMPLATE_NAMES includes built-in fragments."""
        from markcms import RESERVED_TEMPLATE_NAMES
        
        assert 'header' in RESERVED_TEMPLATE_NAMES
        assert 'footer' in RESERVED_TEMPLATE_NAMES
        assert 'special' in RESERVED_TEMPLATE_NAMES


class TestIMAGE_EXTENSIONS:
    """Test cases for IMAGE_EXTENSIONS constant."""
    
    def test_image_extensions_includes_common_formats(self):
        """Test that common image extensions are included."""
        from markcms import IMAGE_EXTENSIONS
        
        assert '.jpg' in IMAGE_EXTENSIONS
        assert '.png' in IMAGE_EXTENSIONS
        assert '.gif' in IMAGE_EXTENSIONS
        assert '.svg' in IMAGE_EXTENSIONS


class TestFRONTMATTER_RE:
    """Test cases for FRONTMATTER_RE regex."""
    
    def test_frontmatter_re_matches_yaml(self):
        """Test that FRONTMATTER_RE matches YAML frontmatter."""
        from markcms import FRONTMATTER_RE
        
        content = "---\ntitle: Test\n---\nBody"
        
        match = FRONTMATTER_RE.match(content)
        
        assert match is not None


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
