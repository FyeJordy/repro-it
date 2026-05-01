"""Write test file tool with safety checks."""

import os
from pathlib import Path


def write_test(file_path: str, test_code: str, repo_root: str) -> dict:
    """
    Write test file with safety checks.
    
    Only writes to files inside repo_root/tests/ directory.
    Filename must start with 'test_'.
    Creates parent directories if needed.
    
    Args:
        file_path: Path to test file (relative to repo_root)
        test_code: Test code content to write
        repo_root: Root directory of repository
    
    Returns:
        dict with keys:
            - ok (bool): Success status
            - path (str|None): Absolute path to written file if successful
            - error (str|None): Error message if failed
    """
    try:
        repo_root_abs = Path(repo_root).resolve()
        
        # Handle both absolute and relative paths
        if Path(file_path).is_absolute():
            file_path_abs = Path(file_path).resolve()
        else:
            file_path_abs = (repo_root_abs / file_path).resolve()
        
        # Security check: ensure file is inside repo_root
        if not str(file_path_abs).startswith(str(repo_root_abs)):
            return {
                "ok": False,
                "path": None,
                "error": f"File path outside repo root: {file_path}"
            }
        
        # Check if path is inside tests/ directory
        try:
            rel_path = file_path_abs.relative_to(repo_root_abs)
            parts = rel_path.parts
            if not parts or parts[0] != "tests":
                return {
                    "ok": False,
                    "path": None,
                    "error": f"Test files must be in tests/ directory: {file_path}"
                }
        except ValueError:
            return {
                "ok": False,
                "path": None,
                "error": f"Invalid path: {file_path}"
            }
        
        # Check filename starts with test_
        filename = file_path_abs.name
        if not filename.startswith("test_"):
            return {
                "ok": False,
                "path": None,
                "error": f"Test filename must start with 'test_': {filename}"
            }
        
        # Check if file exists and is not a test file (safety check)
        if file_path_abs.exists() and not filename.startswith("test_"):
            return {
                "ok": False,
                "path": None,
                "error": f"Refusing to overwrite non-test file: {file_path}"
            }
        
        # Create parent directories if needed
        file_path_abs.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the test file
        with open(file_path_abs, 'w', encoding='utf-8') as f:
            f.write(test_code)
        
        return {
            "ok": True,
            "path": str(file_path_abs),
            "error": None
        }
    
    except Exception as e:
        return {
            "ok": False,
            "path": None,
            "error": f"Error writing test file: {str(e)}"
        }

# Made with Bob
