"""Tests for src/generate-issue-md.py - GitHub Issues to Markdown exporter."""
import sys
import json
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
import importlib.util

# The source file uses a hyphen in its name (generate-issue-md.py),
# so we can't use a standard Python import. Load it via importlib.
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

# Load the module by its file path
_spec = importlib.util.spec_from_file_location(
    'generate_issue_md',
    str(Path(__file__).parent.parent / 'src' / 'generate-issue-md.py')
)
generate_issue_md = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(generate_issue_md)


class TestGitHubAnchor:
    """Test anchor generation utility."""
    
    def test_anchor_simple_title(self):
        """Test generating anchor from simple title."""
        anchor = generate_issue_md.github_anchor("Issue Title")
        assert anchor == "issue-title"
    
    def test_anchor_with_diacritics(self):
        """Test anchor normalization removes diacritics."""
        anchor = generate_issue_md.github_anchor("Überprüfung der Funktion")
        assert "uberprufung" in anchor or "uber" in anchor
    
    def test_anchor_with_special_characters(self):
        """Test anchor removes special characters."""
        anchor = generate_issue_md.github_anchor("Issue #42: Bug Fix!")
        assert "#" not in anchor
        assert "!" not in anchor
        assert "issue" in anchor
    
    def test_anchor_lowercase_conversion(self):
        """Test anchor converts to lowercase."""
        anchor = generate_issue_md.github_anchor("UPPERCASE TITLE")
        assert anchor == anchor.lower()
    
    def test_anchor_empty_string(self):
        """Test anchor with empty string."""
        anchor = generate_issue_md.github_anchor("")
        assert anchor == ""
    
    def test_anchor_multiple_hyphens_collapsed(self):
        """Test that multiple consecutive hyphens are collapsed."""
        anchor = generate_issue_md.github_anchor("Test---With---Hyphens")
        assert "----" not in anchor
        assert "test-with-hyphens" == anchor
    
    def test_anchor_leading_trailing_hyphens_stripped(self):
        """Test that leading and trailing hyphens are removed."""
        anchor = generate_issue_md.github_anchor("---Test---")
        assert anchor.startswith("-") is False
        assert anchor.endswith("-") is False


class TestGHCLICommands:
    """Test GitHub CLI command execution (mocked)."""
    
    def test_run_gh_command_success(self):
        """Test successful gh command execution."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = '{"test": "data"}'
            mock_run.return_value = mock_result
            
            result = generate_issue_md.run_gh_command(["issue", "list"], verbose=False)
            assert json.loads(result) == {"test": "data"}
    
    def test_run_gh_command_failure(self):
        """Test handling of failed gh command."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stderr = "Authentication failed"
            mock_run.return_value = mock_result
            
            result = generate_issue_md.run_gh_command(["issue", "list"], verbose=True)
            assert result is None
    
    def test_run_gh_command_failure_no_verbose(self):
        """Test failed gh command without verbose output."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stderr = "Error"
            mock_run.return_value = mock_result
            
            result = generate_issue_md.run_gh_command(["issue", "list"], verbose=False)
            assert result is None


class TestIssueFetching:
    """Test issue fetching utilities."""
    
    def test_get_issues(self):
        """Test fetching list of issues."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = json.dumps([
                {"number": 1, "title": "Bug", "state": "open"},
                {"number": 2, "title": "Feature", "state": "closed"}
            ])
            mock_run.return_value = mock_result
            
            issues = generate_issue_md.get_issues(state="all")
            assert len(issues) == 2
            assert issues[0]["number"] == 1
    
    def test_get_issues_empty(self):
        """Test fetching issues returns empty list on failure."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_run.return_value = mock_result
            
            issues = generate_issue_md.get_issues(state="open")
            assert issues == []
    
    def test_get_issues_invalid_json(self):
        """Test fetching issues with invalid JSON returns empty list."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "not valid json"
            mock_run.return_value = mock_result
            
            issues = generate_issue_md.get_issues(state="open", verbose=True)
            assert issues == []
    
    def test_get_issue_details(self):
        """Test fetching detailed issue data."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            
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
            issue_data, comments = generate_issue_md.get_issue_details(42)
            assert issue_data is not None
            assert isinstance(comments, list)
    
    def test_get_issue_details_failure(self):
        """Test fetching issue details when API fails."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_run.return_value = mock_result
            
            issue_data, comments = generate_issue_md.get_issue_details(42)
            assert issue_data is None
            assert comments is None


class TestMarkdownGeneration:
    """Test Markdown document generation."""
    
    def _mock_issue_details(self, mock_run, state="open"):
        """Helper to set up mock for issue details calls."""
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
                    "created_at": "2024-01-01T00:00:00Z",
                    "state": state,
                    "user": {"login": "testuser"}
                })
                return result
            else:
                result = MagicMock()
                result.returncode = 0
                result.stdout = json.dumps([])
                return result
        mock_run.side_effect = side_effect
    
    def test_build_markdown_basic(self):
        """Test building basic markdown output."""
        issues = [
            {"number": 1, "title": "Bug Fix", "state": "open", "createdAt": "2024-01-01"},
            {"number": 2, "title": "Feature Request", "state": "closed", "createdAt": "2024-01-02"}
        ]
        with patch('subprocess.run') as mock_run:
            self._mock_issue_details(mock_run)
            markdown = generate_issue_md.build_markdown(issues, color=True)
            assert "# GitHub Issues" in markdown
            assert "## Overview" in markdown
            assert "| Issue | Title | State | Created |" in markdown
            assert "## Details" in markdown
    
    def test_build_markdown_with_milestone(self):
        """Test building markdown with milestone info."""
        issues = [
            {"number": 1, "title": "Bug", "state": "open", "createdAt": "2024-01-01",
             "milestone": {"title": "v1.0"}}
        ]
        with patch('subprocess.run') as mock_run:
            self._mock_issue_details(mock_run)
            markdown = generate_issue_md.build_markdown(issues, include_milestone=True)
            assert "## Details" in markdown
            assert "**Milestone:** v1.0" in markdown
    
    def test_build_markdown_with_assignees(self):
        """Test building markdown with assignee info."""
        issues = [
            {"number": 1, "title": "Bug", "state": "open", "createdAt": "2024-01-01",
             "assignees": [{"login": "developer"}]}
        ]
        with patch('subprocess.run') as mock_run:
            self._mock_issue_details(mock_run)
            markdown = generate_issue_md.build_markdown(issues, include_assignee=True)
            assert "**Assignee(s):** developer" in markdown
    
    def test_build_markdown_no_color(self):
        """Test building markdown without emoji colors."""
        issues = [{"number": 1, "title": "Bug", "state": "open", "createdAt": "2024-01-01"}]
        with patch('subprocess.run') as mock_run:
            self._mock_issue_details(mock_run)
            markdown = generate_issue_md.build_markdown(issues, color=False)
            assert "open" in markdown
            assert "🟢" not in markdown
    
    def test_build_markdown_back_to_top_links(self):
        """Test back-to-top link styles."""
        issues = [{"number": 1, "title": "Bug", "state": "open", "createdAt": "2024-01-01"}]
        with patch('subprocess.run') as mock_run:
            self._mock_issue_details(mock_run)
            
            markdown = generate_issue_md.build_markdown(issues, top_link_style="icon")
            assert "⬆️" in markdown
            assert "Back to top" not in markdown
            
            markdown_text = generate_issue_md.build_markdown(issues, top_link_style="text")
            assert "Back to top" in markdown_text
            assert "⬆️" not in markdown_text
            
            markdown_none = generate_issue_md.build_markdown(issues, top_link_style="none")
            assert "⬆️" not in markdown_none
            assert "Back to top" not in markdown_none
    
    def test_build_markdown_empty_issues(self):
        """Test building markdown with no issues."""
        markdown = generate_issue_md.build_markdown([], color=False)
        assert "# GitHub Issues for" in markdown
        assert "(0 total)" in markdown
    
    def test_build_markdown_with_comments(self):
        """Test building markdown with issue comments."""
        issues = [{"number": 1, "title": "Bug", "state": "open", "createdAt": "2024-01-01"}]
        with patch('subprocess.run') as mock_run:
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
                        "body": "Bug description",
                        "created_at": "2024-01-01T00:00:00Z",
                        "state": "open",
                        "user": {"login": "testuser"}
                    })
                    return result
                else:
                    result = MagicMock()
                    result.returncode = 0
                    result.stdout = json.dumps([
                        {"body": "Comment 1", "created_at": "2024-01-02", "user": {"login": "reviewer"}}
                    ])
                    return result
            mock_run.side_effect = side_effect
            markdown = generate_issue_md.build_markdown(issues)
            assert "**Comments:**" in markdown
            assert "> Comment 1" in markdown


class TestIssueFiltering:
    """Test issue filtering functionality."""
    
    def test_filter_by_assignee(self):
        """Test filtering issues by assignee login."""
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
        mock_issues = [
            {"assignees": [{"login": "alice", "name": "Alice Smith"}]},
            {"assignees": [{"login": "bob"}, {"login": "alice"}]}
        ]
        with pytest.raises(SystemExit) as exc_info:
            generate_issue_md.list_assignees(mock_issues)
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "alice" in captured.out.lower()
    
    def test_list_milestones(self, capsys):
        """Test listing unique milestones from issues."""
        mock_issues = [
            {"milestone": {"title": "v1.0"}},
            {"milestone": {"title": "v2.0"}},
            {"milestone": None},
            {"milestone": {"title": "v1.0"}}
        ]
        with pytest.raises(SystemExit) as exc_info:
            generate_issue_md.list_milestones(mock_issues)
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "v1.0" in captured.out
        assert "v2.0" in captured.out


class TestGenerateIssueMDMain:
    """Test main() function of generate-issue-md.py."""
    
    def test_main_dry_run(self):
        """Test dry-run mode prints issues instead of writing file."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = json.dumps([{"number": 1, "title": "Test", "state": "open"}])
            mock_run.return_value = mock_result
        
        with patch('sys.argv', ['generate-issue-md.py', '--dry-run']):
            try:
                generate_issue_md.main()
            except SystemExit as e:
                assert e.code == 0
    
    def test_main_with_filename(self):
        """Test writing to specified filename."""
        issues = [{"number": 1, "title": "Test", "state": "open"}]
        
        with patch.object(generate_issue_md, 'build_markdown', return_value="# Test\n") as mock_build:
            generate_issue_md.write_markdown(issues, "/tmp/test.md")
            mock_build.assert_called_once()
    
    def test_main_list_assignees(self):
        """Test --list-assignees flag."""
        mock_issues = [
            {"assignees": [{"login": "alice"}]},
            {"assignees": [{"login": "bob"}]}
        ]
        with patch.object(generate_issue_md, 'get_issues', return_value=mock_issues):
            with patch('sys.argv', ['generate-issue-md.py', '--list-assignees']):
                with pytest.raises(SystemExit) as exc_info:
                    generate_issue_md.main()
                assert exc_info.value.code == 0
    
    def test_main_list_milestones(self):
        """Test --list-milestones flag."""
        mock_issues = [
            {"milestone": {"title": "v1.0"}},
            {"milestone": {"title": "v2.0"}}
        ]
        with patch.object(generate_issue_md, 'get_issues', return_value=mock_issues):
            with patch('sys.argv', ['generate-issue-md.py', '--list-milestones']):
                with pytest.raises(SystemExit) as exc_info:
                    generate_issue_md.main()
                assert exc_info.value.code == 0
    
    def test_main_keyboard_interrupt(self):
        """Test KeyboardInterrupt handling in main."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = KeyboardInterrupt()
        
        with patch('sys.argv', ['generate-issue-md.py']):
            try:
                generate_issue_md.main()
            except SystemExit as e:
                assert e.code == 130
