"""Unit tests for Repro-It tools."""

import sys
import os
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.read_file import read_file
from tools.search_repo import search_repo
from tools.write_test import write_test
from tools.run_pytest import run_pytest


def test_read_file_success():
    """Test reading a valid file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("Hello, World!")
        
        result = read_file(str(test_file), tmpdir)
        assert result["ok"] is True
        assert result["content"] == "Hello, World!"
        assert result["error"] is None


def test_read_file_outside_repo():
    """Test that reading outside repo root is blocked."""
    with tempfile.TemporaryDirectory() as tmpdir:
        outside_file = Path(tmpdir).parent / "outside.txt"
        
        result = read_file(str(outside_file), tmpdir)
        assert result["ok"] is False
        assert "outside repo root" in result["error"].lower()


def test_read_file_not_found():
    """Test reading non-existent file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = read_file(str(Path(tmpdir) / "missing.txt"), tmpdir)
        assert result["ok"] is False
        assert "not found" in result["error"].lower()


def test_search_repo_finds_matches():
    """Test searching for text in repository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        (Path(tmpdir) / "file1.py").write_text("def hello():\n    return 'world'")
        (Path(tmpdir) / "file2.py").write_text("def goodbye():\n    return 'world'")
        
        result = search_repo("world", tmpdir)
        assert result["ok"] is True
        assert len(result["matches"]) == 2
        assert result["error"] is None


def test_search_repo_no_matches():
    """Test searching with no results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "file.py").write_text("def hello():\n    pass")
        
        result = search_repo("nonexistent", tmpdir)
        assert result["ok"] is True
        assert len(result["matches"]) == 0


def test_write_test_success():
    """Test writing a valid test file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_code = "def test_example():\n    assert True"
        
        result = write_test("tests/test_new.py", test_code, tmpdir)
        assert result["ok"] is True
        assert result["path"] is not None
        assert Path(result["path"]).exists()
        assert Path(result["path"]).read_text() == test_code


def test_write_test_invalid_filename():
    """Test that non-test filenames are rejected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = write_test("tests/invalid.py", "code", tmpdir)
        assert result["ok"] is False
        assert "must start with 'test_'" in result["error"]


def test_write_test_outside_tests_dir():
    """Test that writing outside tests/ is blocked."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = write_test("test_outside.py", "code", tmpdir)
        assert result["ok"] is False
        assert "must be in tests/" in result["error"].lower()


def test_run_pytest_success():
    """Test running pytest on a passing test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a simple passing test
        tests_dir = Path(tmpdir) / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_pass.py"
        test_file.write_text("def test_pass():\n    assert True")
        
        result = run_pytest("tests/test_pass.py", tmpdir)
        assert result["ok"] is True
        assert result["exit_code"] == 0


def test_run_pytest_failure():
    """Test running pytest on a failing test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a failing test
        tests_dir = Path(tmpdir) / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_fail.py"
        test_file.write_text("def test_fail():\n    assert False")
        
        result = run_pytest("tests/test_fail.py", tmpdir)
        assert result["ok"] is True
        assert result["exit_code"] != 0
        assert len(result["failure_messages"]) > 0


def test_run_pytest_file_not_found():
    """Test running pytest on non-existent file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = run_pytest("tests/missing.py", tmpdir)
        assert result["ok"] is False
        assert "not found" in result["error"].lower()

# Made with Bob
