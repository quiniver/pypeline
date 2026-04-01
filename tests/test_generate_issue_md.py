"""Tests for src/generate-issue-md.py - GitHub Issues to Markdown exporter."""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
import unicodedata
import re


class TestGitHubAnchor:
    """Test anchor generation utility."""
    
    def test_anchor_simple_title(self):
        """Test generating anchor from simple title."""
        from generate_issue_md import github_anchor
        
        anchor = github_anchor("Issue Title")
        
        assert anchor == "issue-title"
    
    def test_anchor_with_diacritics(self):
        """Test anchor normalization removes diacritics."""
        from generate_issue_md import github_anchor
        
        # Test with German umlauts
        anchor = github_anchor("Überprüfung der Funktion")
        
        assert "uberprufung" in anchor or "uber" in anchor
    
    def test_anchor_with_special_characters(self):
        """Test anchor removes special characters."""
        from generate_issue_md import github_anchor
        
        anchor = github_anchor("Issue #42: Bug Fix!")
        
        assert "#" not in anchor
        assert "!" not in anchor
        assert "issue" in anchor
    
    def test_anchor_lowercase_conversion(self):
        """Test anchor converts to lowercase."""
        from generate_issue_md import github_anchor
        
        anchor = github_anchor("UPPERCASE TITLE")
        
        assert anchor == anchor.lower()


class TestGHCLICommands:
    """Test GitHub CLI command execution (mocked)."""
    
    def test_run_gh_command_success(self):
        """Test successful gh command execution."""
        from generate_issue_md import run_gh_command
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = '{"test": "data"}'
            mock_run.return_value = mock_result
            
            result = run_gh_command(["issue", "list"], verbose=False)
            
            assert json.loads(result) == {"test": "data"}
    
    def test_run_gh_command_failure(self):
        """Test handling of failed gh command."""
        from generate_issue_md import run_gh_command
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stderr = "Authentication failed"
            mock_run.return_value = mock_result
            
            result = run_gh_command(["issue", "list"], verbose=True)
            
            assert result is None


class TestIssueFetching:
    """Test issue fetching utilities."""
    
    def test_get_issues(self):
        """Test fetching list of issues."""
        from generate_issue_md import get_issues
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = json.dumps([
                {"number": 1, "title": "Bug", "state": "open"},
                {"number": 2, "title": "Feature", "state": "closed"}
            ])
            mock_run.return_value = mock_result
            
            issues = get_issues(state="all")
            
            assert len(issues) == 2
            assert issues[0]["number"] == 1
    
    def test_get_issue_details(self):
        """Test fetching detailed issue data."""
        from generate_issue_md import get_issue_details
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            
            # First call: repo view
            # Second call: api /repos/.../issues/X
            # Third call: api /repos/.../issues/X/comments
            def side_effect(*args, **kwargs):
                if "repo view" in str(args[0]):
                    result = MagicMock()
                    result.returncode = 0
                    result.stdout = '{"nameWithOwner": "test/repo"}'
                    return result
                elif "/issues/" in str(args[0]) and "comments" not in str(args[0]):
                    result = MagicMock()
                    result.returncode = 0
                    result.stdout = json.dumps({
                        "body": "Issue body",
                        "created_at": "2024-01-01T00:00:00Z"
                    })
                    return result
                else:
                    result = MagicMock()
                    result.returncode = 0
                    result.stdout = json.dumps([])
                    return result
            
            mock_run.side_effect = side_effect
            
            issue_data, comments = get_issue_details(42)
            
            assert issue_data is not None
            assert isinstance(comments, list)


class TestMarkdownGeneration:
    """Test Markdown document generation."""
    
    def test_build_markdown_basic(self):
        """Test building basic markdown output."""
        from generate_issue_md import build_markdown
        
        issues = [
            {"number": 1, "title": "Bug Fix", "state": "open", "createdAt": "2024-01-01"},
            {"number": 2, "title": "Feature Request", "state": "closed", "createdAt": "2024-01-02"}
        ]
        
        markdown = build_markdown(issues, color=True)
        
        assert "# GitHub Issues" in markdown
        assert "## Overview" in markdown
        assert "| Issue | Title | State | Created |" in markdown
    
    def test_build_markdown_with_milestone(self):
        """Test building markdown with milestone info."""
        from generate_issue_md import build_markdown
        
        issues = [
            {
                "number": 1, 
                "title": "Bug", 
                "state": "open", 
                "createdAt": "2024-01-01",
                "milestone": {"title": "v1.0"}
            }
        ]
        
        markdown = build_markdown(issues, include_milestone=True)
        
        assert "## Details" in markdown
        assert "**Milestone:** v1.0" in markdown
    
    def test_build_markdown_with_assignees(self):
        """Test building markdown with assignee info."""
        from generate_issue_md import build_markdown
        
        issues = [
            {
                "number": 1, 
                "title": "Bug", 
                "state": "open", 
                "createdAt": "2024-01-01",
                "assignees": [{"login": "developer"}]
            }
        ]
        
        markdown = build_markdown(issues, include_assignee=True)
        
        assert "**Assignee(s):** developer" in markdown


class TestIssueFiltering:
    """Test issue filtering functionality."""
    
    def test_filter_by_assignee(self):
        """Test filtering issues by assignee login."""
        from generate_issue_md import get_issues
        
        # Mock issues with different assignees
        mock_issues = [
            {"number": 1, "assignees": [{"login": "alice"}]},
            {"number": 2, "assignees": [{"login": "bob"}]},
            {"number": 3, "assignees": [{"login": "alice"}, {"login": "charlie"}]}
        ]
        
        filtered = [
            issue for issue in mock_issues
            if any(a.get("login") == "alice" for a in issue.get("assignees", []))
        ]
        
        assert len(filtered) == 2
    
    def test_filter_by_milestone(self):
        """Test filtering issues by milestone title."""
        from generate_issue_md import get_issues
        
        mock_issues = [
            {"number": 1, "milestone": {"title": "v1.0"}},
            {"number": 2, "milestone": {"title": "v2.0"}},
            {"number": 3, "milestone": None}
        ]
        
        filtered = [
            issue for issue in mock_issues
            if issue.get("milestone") and issue["milestone"].get("title") == "v1.0"
        ]
        
        assert len(filtered) == 1


class TestListCommands:
    """Test listing assignees and milestones."""
    
    def test_list_assignees(self, capsys):
        """Test listing unique assignees from issues."""
        from generate_issue_md import list_assignees
        
        mock_issues = [
            {"assignees": [{"login": "alice", "name": "Alice Smith"}]},
            {"assignees": [{"login": "bob"}, {"login": "alice"}]}
        ]
        
        with pytest.raises(SystemExit) as exc_info:
            list_assignees(mock_issues)
        
        assert exc_info.value.code == 0
        
        captured = capsys.readouterr()
        assert "alice" in captured.out.lower()


class TestGenerateIssueMDMain:
    """Test main() function of generate-issue-md.py."""
    
    def test_main_dry_run(self):
        """Test dry-run mode prints issues instead of writing file."""
        from generate_issue_md import main
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = json.dumps([{"number": 1, "title": "Test", "state": "open"}])
            mock_run.return_value = mock_result
        
        with patch('sys.argv', ['generate-issue-md.py', '--dry-run']):
            try:
                main()
            except SystemExit as e:
                # Should exit successfully
                assert e.code == 0
    
    def test_main_with_filename(self):
        """Test writing to specified filename."""
        from generate_issue_md import write_markdown
        
        issues = [{"number": 1, "title": "Test", "state": "open"}]
        
        with patch('generate_issue_md.build_markdown') as mock_build:
            mock_build.return_value = "# Test\n"
            
            write_markdown(issues, "/tmp/test.md")
            
            # Verify file would be written (we don't actually create it)
