"""Read file tool with safety checks."""

import os
from pathlib import Path


def read_file(file_path: str, repo_root: str) -> dict:
    """
    Read file contents with safety checks.
    
    Args:
        file_path: Path to file (relative or absolute)
        repo_root: Root directory to restrict reads to
    
    Returns:
        dict with keys:
            - ok (bool): Success status
            - content (str|None): File contents if successful
            - error (str|None): Error message if failed
    """
    try:
        # Resolve to absolute paths
        repo_root_abs = Path(repo_root).resolve()
        file_path_abs = Path(file_path).resolve()
        
        # Security check: ensure file is inside repo_root
        if not str(file_path_abs).startswith(str(repo_root_abs)):
            return {
                "ok": False,
                "content": None,
                "error": f"File path outside repo root: {file_path}"
            }
        
        # Check if file exists
        if not file_path_abs.exists():
            return {
                "ok": False,
                "content": None,
                "error": f"File not found: {file_path}"
            }
        
        # Check if it's a file (not directory)
        if not file_path_abs.is_file():
            return {
                "ok": False,
                "content": None,
                "error": f"Path is not a file: {file_path}"
            }
        
        # Read file content
        with open(file_path_abs, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "ok": True,
            "content": content,
            "error": None
        }
    
    except UnicodeDecodeError:
        return {
            "ok": False,
            "content": None,
            "error": f"Cannot read binary file: {file_path}"
        }
    except Exception as e:
        return {
            "ok": False,
            "content": None,
            "error": f"Error reading file: {str(e)}"
        }

# Made with Bob
