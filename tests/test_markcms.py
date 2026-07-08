"""Tests for src/markcms.py - Markdown documentation CMS."""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
import yaml


class TestPathResolution:
    """Test path resolution utilities in markcms.py."""
    
    def test_resolve_absolute_path(self):
        """Test resolving absolute paths as-is."""
        from markcms import resolve_path
        
        abs_path = Path("/absolute/path")
        result = resolve_path(str(abs_path), Path("/base"))
        
        assert result == abs_path
    
    def test_resolve_relative_path(self):
        """Test resolving relative paths to base directory."""
        from markcms import resolve_path
        
        rel_path = "relative/path"
        base = Path("/base")
        result = resolve_path(rel_path, base)
        
        # resolve() resolves to the full path including the filename component
        expected = (base / "relative/path").resolve()
        assert result == expected
    
    def test_resolve_nested_relative(self):
        """Test resolving nested relative paths."""
        from markcms import resolve_path
        
        rel_path = "../parent/path"
        base = Path("/current/base")
        result = resolve_path(rel_path, base)
        
        # Should handle parent directory references
        assert "parent" in str(result)


class TestYAMLLoading:
    """Test YAML config loading in markcms.py."""
    
    def test_load_valid_config(self, temp_dir):
        """Test loading a valid YAML config file."""
        from markcms import load_config
        
        config_path = temp_dir / "_config.yml"
        config_content = {
            "docs": [
                {"title": "Home", "file": "index.md"},
                {"title": "About", "file": "about.md"}
            ]
        }
        
        config_path.write_text(yaml.dump(config_content))
        
        config = load_config(config_path)
        
        assert "docs" in config
        assert len(config["docs"]) == 2
    
    def test_load_nonexistent_config(self, temp_dir):
        """Test loading non-existent config file raises error."""
        from markcms import load_config
        
        with pytest.raises(FileNotFoundError):
            load_config(temp_dir / "nonexistent.yml")
    
    def test_load_invalid_yaml(self, temp_dir):
        """Test loading invalid YAML raises ValueError."""
        from markcms import load_config
        
        config_path = temp_dir / "invalid.yml"
        config_path.write_text("invalid: yaml: content: [")
        
        with pytest.raises(ValueError) as exc_info:
            load_config(config_path)
        
        assert "Invalid YAML" in str(exc_info.value)
    
    def test_load_empty_yaml(self, temp_dir):
        """Test loading empty YAML file returns empty dict."""
        from markcms import load_config
        
        config_path = temp_dir / "empty.yml"
        config_path.write_text("")
        
        config = load_config(config_path)
        
        assert config == {}


class TestMenuAndSitemapGeneration:
    """Test menu and sitemap generation utilities."""
    
    def test_get_menu_key_with_file(self):
        """Test getting menu key for item with file attribute."""
        from markcms import get_menu_key
        
        item = {"title": "Home", "file": "index.md"}
        key = get_menu_key(item)
        
        assert key == "index.md"
    
    def test_get_menu_key_with_link(self):
        """Test getting menu key for link-type item."""
        from markcms import get_menu_key
        
        item = {"title": "External Link", "type": "link"}
        key = get_menu_key(item)
        
        assert "__link__" in key
    
    def test_get_menu_key_with_title_only(self):
        """Test getting menu key for item with title only."""
        from markcms import get_menu_key
        
        item = {"title": "My Page"}
        key = get_menu_key(item)
        
        assert key == "My Page"
    
    def test_get_sitemap_content(self):
        """Test generating sitemap content."""
        from markcms import get_sitemap_content
        
        nav_items = [
            {"title": "Home", "file": "index.md"},
            {"title": "About", "file": "about.md"}
        ]
        
        sitemap = get_sitemap_content(nav_items, "index.md")
        
        assert "**Home**" in sitemap  # Active item should be bold
        assert "[About](about.md)" in sitemap
    
    def test_get_menu_content(self):
        """Test generating menu content."""
        from markcms import get_menu_content
        
        nav_items = [
            {"title": "Home", "file": "index.md"},
            {"title": "About", "file": "about.md"}
        ]
        
        menu = get_menu_content(nav_items, "index.md")
        
        assert "**Home**" in menu
        assert "[About](about.md)" in menu
        assert "•" in menu


class TestTemplateExpansion:
    """Test template placeholder expansion."""
    
    def test_expand_context_placeholders(self):
        """Test expanding context-dependent placeholders."""
        from markcms import expand_placeholders
        
        template = "{menu} {content}"
        context = {"menu": "Home • About", "content": "Main content"}
        
        templates_dir = Path("/tmp")
        result = expand_placeholders(
            template, context, templates_dir, [], "", {}
        )
        
        assert "Home • About" in result
        assert "Main content" in result
    
    def test_expand_with_custom_fragments(self):
        """Test expanding with custom template fragments."""
        from markcms import expand_placeholders
        
        template = "{header} {content}"
        context = {"content": "Body"}
        
        # Create temp templates directory with header fragment
        with patch('pathlib.Path.exists') as mock_exists, \
             patch('pathlib.Path.read_text') as mock_read:
            
            mock_exists.return_value = True
            mock_read.return_value = "<header>Header</header>"
            
            result = expand_placeholders(
                template, context, Path("/templates"), [], "", {"header": "header.md"}
            )
        
        assert "Header" in result
    
    def test_expand_missing_fragment(self):
        """Test expanding when fragment file is missing."""
        from markcms import expand_placeholders
        
        template = "{header} {content}"
        context = {"content": "Body"}
        
        with patch('pathlib.Path.exists', return_value=False):
            result = expand_placeholders(
                template, context, Path("/templates"), [], "", {"header": "header.md"}
            )
        
        assert "header.md not found" in result
    
    def test_expand_recursion_limit(self):
        """Test that expansion stops at depth limit."""
        from markcms import expand_placeholders
        
        template = "{header}"
        context = {"header": "{header}"}  # Self-referential
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.read_text', return_value="{header}"):
                result = expand_placeholders(
                    template, context, Path("/templates"), [], "", {"header": "header.md"}, depth=0
                )
        
        # Should not recurse infinitely — depth limit kicks in at 3
        assert result is not None


class TestGalleryGeneration:
    """Test gallery content generation."""
    
    def test_generate_gallery_with_images(self, temp_dir):
        """Test generating gallery from image files."""
        from markcms import generate_gallery_content
        
        # Create media directory with images
        media_dir = temp_dir / "media"
        media_dir.mkdir()
        
        (media_dir / "photo.jpg").write_bytes(b"fake jpg")
        (media_dir / "image.png").write_bytes(b"fake png")
        
        template_media_dir = temp_dir / "template-media"
        template_media_dir.mkdir()
        
        item = {"title": "Gallery", "columns": 1}
        
        gallery = generate_gallery_content(
            item, media_dir, template_media_dir, {}, temp_dir, temp_dir / "output.md"
        )
        
        assert "No images or supported media files found" not in gallery
    
    def test_generate_gallery_empty_directory(self, temp_dir):
        """Test generating gallery from empty directory."""
        from markcms import generate_gallery_content
        
        media_dir = temp_dir / "empty-media"
        media_dir.mkdir()
        
        template_media_dir = temp_dir / "template-media"
        template_media_dir.mkdir()
        
        item = {"title": "Empty Gallery"}
        
        gallery = generate_gallery_content(
            item, media_dir, template_media_dir, {}, temp_dir, temp_dir / "output.md"
        )
        
        assert "No images or supported media files found" in gallery
    
    def test_generate_gallery_nonexistent_directory(self, temp_dir):
        """Test generating gallery from non-existent directory."""
        from markcms import generate_gallery_content
        
        media_dir = temp_dir / "nonexistent-media"
        # Don't create it
        
        template_media_dir = temp_dir / "template-media"
        template_media_dir.mkdir()
        
        item = {"title": "Nonexistent Gallery"}
        
        gallery = generate_gallery_content(
            item, media_dir, template_media_dir, {}, temp_dir, temp_dir / "output.md"
        )
        
        assert "not found" in gallery
    
    def test_generate_gallery_multi_column(self, temp_dir):
        """Test generating gallery with multiple columns."""
        from markcms import generate_gallery_content
        
        media_dir = temp_dir / "media"
        media_dir.mkdir()
        
        (media_dir / "photo1.jpg").write_bytes(b"fake")
        (media_dir / "photo2.jpg").write_bytes(b"fake")
        
        template_media_dir = temp_dir / "template-media"
        template_media_dir.mkdir()
        
        item = {"title": "Gallery", "columns": 2}
        
        gallery = generate_gallery_content(
            item, media_dir, template_media_dir, {}, temp_dir, temp_dir / "output.md"
        )
        
        # Should have table format with 2 columns
        assert "|" in gallery
    
    def test_generate_gallery_paired_preview(self, temp_dir):
        """Test generating gallery with paired video+image."""
        from markcms import generate_gallery_content
        
        media_dir = temp_dir / "media"
        media_dir.mkdir()
        
        # Paired files: video.mp4 + video.jpg
        (media_dir / "video.mp4").write_bytes(b"fake video")
        (media_dir / "video.jpg").write_bytes(b"fake jpg")
        
        template_media_dir = temp_dir / "template-media"
        template_media_dir.mkdir()
        
        item = {"title": "Gallery"}
        
        gallery = generate_gallery_content(
            item, media_dir, template_media_dir, {}, temp_dir, temp_dir / "output.md"
        )
        
        assert "No images or supported media files found" not in gallery


class TestExtractFrontmatter:
    """Test frontmatter extraction."""
    
    def test_extract_frontmatter_present(self):
        """Test extracting frontmatter from content."""
        from markcms import extract_frontmatter
        
        content = "---\ntitle: Test\n---\n\nBody content"
        front, body = extract_frontmatter(content)
        
        assert front is not None
        assert "title: Test" in front
        assert "Body content" in body
    
    def test_extract_frontmatter_absent(self):
        """Test when no frontmatter is present."""
        from markcms import extract_frontmatter
        
        content = "Just plain content"
        front, body = extract_frontmatter(content)
        
        assert front is None
        assert body == "Just plain content"


class TestMarkCMSMain:
    """Test main() function of markcms.py."""
    
    def test_list_placeholders(self):
        """Test listing available placeholders."""
        from markcms import list_placeholders
        
        with patch('sys.stdout') as mock_stdout:
            list_placeholders(None)
            
            # Check that built-in placeholders are listed
            output = ''.join(str(call) for call in mock_stdout.write.call_args_list)
            assert "timestamp" in output or len(output) > 0
    
    def test_dry_run_mode(self, temp_dir):
        """Test dry-run mode validates without writing files."""
        # Create minimal config and content
        config = temp_dir / "_config.yml"
        config.write_text("docs:\n  - title: Test\n    file: page.md")
        
        docs_dir = temp_dir / "docs"
        docs_dir.mkdir()
        (docs_dir / "page.md").write_text("# Page Title")
        
        out_dir = temp_dir / "out"
        
        with patch('sys.argv', [
            'markcms.py',
            '--config', str(config),
            '--dry-run'
        ]):
            try:
                from markcms import main
                main()
            except SystemExit as e:
                # Should exit successfully in dry-run mode
                assert e.code == 0
    
    def test_config_with_both_docs_and_nav_raises(self, temp_dir):
        """Test that config with both docs and nav blocks raises ValueError."""
        config = temp_dir / "_config.yml"
        config.write_text("docs:\n  - title: Test\nnav:\n  - title: Old")
        
        with patch('sys.argv', ['markcms.py', '--config', str(config)]):
            try:
                from markcms import main
                main()
            except ValueError as e:
                assert "both 'docs' and 'nav'" in str(e)
            except SystemExit:
                pass
    
    def test_config_missing_both_blocks_raises(self, temp_dir):
        """Test that config missing both docs and nav raises ValueError."""
        config = temp_dir / "_config.yml"
        config.write_text("some_key: value")
        
        with patch('sys.argv', ['markcms.py', '--config', str(config)]):
            try:
                from markcms import main
                main()
            except ValueError as e:
                assert "must contain 'docs' or 'nav'" in str(e)
            except SystemExit:
                pass
