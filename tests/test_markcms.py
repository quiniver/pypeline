"""Tests for markcms.py - Testing markdown documentation generator functions."""

from pathlib import Path
from unittest.mock import patch, MagicMock


class TestResolvePath:
    """Test cases for resolve_path function."""
    
    def test_resolve_absolute_path(self):
        """Test resolving absolute path."""
        from markcms import resolve_path
        
        result = resolve_path('/absolute/path', Path('/base'))
        
        assert result.is_absolute()
        assert str(result) == '/absolute/path'


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


class TestGetMenuKey:
    """Test cases for get_menu_key function."""
    
    def test_get_menu_key_with_file(self):
        """Test getting menu key with file attribute."""
        from markcms import get_menu_key
        
        item = {"title": "Home", "file": "index.md"}
        
        key = get_menu_key(item)
        
        assert key == "index.md"


class TestGetMenuContent:
    """Test cases for get_menu_content function."""
    
    def test_get_menu_content_with_items(self):
        """Test getting menu content with multiple items."""
        from markcms import get_menu_content
        
        nav_items = [
            {"title": "Home", "file": "index.md"},
            {"title": "About", "file": "about.md"}
        ]
        
        menu = get_menu_content(nav_items, "about.md")
        
        assert "**About**" in menu  # Active item should be bold


class TestGetSitemapContent:
    """Test cases for get_sitemap_content function."""
    
    def test_get_sitemap_content_with_items(self):
        """Test getting sitemap content with multiple items."""
        from markcms import get_sitemap_content
        
        nav_items = [
            {"title": "Home", "file": "index.md"}
        ]
        
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


class TestIMAGE_EXTENSIONS:
    """Test cases for IMAGE_EXTENSIONS constant."""
    
    def test_image_extensions_includes_common_formats(self):
        """Test that common image extensions are included."""
        from markcms import IMAGE_EXTENSIONS
        
        assert '.jpg' in IMAGE_EXTENSIONS
        assert '.png' in IMAGE_EXTENSIONS


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
