"""Search repository for text patterns."""

import os
import subprocess
import shutil
from pathlib import Path


def search_repo(query: str, repo_root: str) -> dict:
    """
    Search for text patterns in repository files.
    
    Prefers ripgrep if available, falls back to Python search.
    Skips .git, __pycache__, node_modules, and binary files.
    
    Args:
        query: Text pattern to search for
        repo_root: Root directory to search in
    
    Returns:
        dict with keys:
            - ok (bool): Success status
            - matches (list): List of match dicts with file_path, line_number, line_content
            - error (str|None): Error message if failed
    """
    try:
        repo_root_path = Path(repo_root).resolve()
        
        if not repo_root_path.exists():
            return {
                "ok": False,
                "matches": [],
                "error": f"Repository root not found: {repo_root}"
            }
        
        # Try ripgrep first
        if shutil.which("rg"):
            return _search_with_ripgrep(query, repo_root_path)
        else:
            return _search_with_python(query, repo_root_path)
    
    except Exception as e:
        return {
            "ok": False,
            "matches": [],
            "error": f"Search error: {str(e)}"
        }


def _search_with_ripgrep(query: str, repo_root: Path) -> dict:
    """Search using ripgrep command."""
    try:
        result = subprocess.run(
            ["rg", "--line-number", "--no-heading", "--max-count", "30", query],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        matches = []
        for line in result.stdout.splitlines()[:30]:
            if ":" in line:
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    matches.append({
                        "file_path": parts[0],
                        "line_number": int(parts[1]),
                        "line_content": parts[2]
                    })
        
        return {
            "ok": True,
            "matches": matches,
            "error": None
        }
    
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "matches": [],
            "error": "Search timeout"
        }
    except Exception as e:
        return {
            "ok": False,
            "matches": [],
            "error": f"Ripgrep error: {str(e)}"
        }


def _search_with_python(query: str, repo_root: Path) -> dict:
    """Fallback search using Python."""
    matches = []
    skip_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv"}
    skip_extensions = {".pyc", ".so", ".dylib", ".dll", ".exe", ".bin"}
    
    try:
        for root, dirs, files in os.walk(repo_root):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            for file in files:
                # Skip binary files
                if any(file.endswith(ext) for ext in skip_extensions):
                    continue
                
                file_path = Path(root) / file
                rel_path = file_path.relative_to(repo_root)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, 1):
                            if query in line:
                                matches.append({
                                    "file_path": str(rel_path),
                                    "line_number": line_num,
                                    "line_content": line.rstrip()
                                })
                                
                                if len(matches) >= 30:
                                    return {
                                        "ok": True,
                                        "matches": matches,
                                        "error": None
                                    }
                except (UnicodeDecodeError, PermissionError):
                    # Skip files we can't read
                    continue
        
        return {
            "ok": True,
            "matches": matches,
            "error": None
        }
    
    except Exception as e:
        return {
            "ok": False,
            "matches": [],
            "error": f"Python search error: {str(e)}"
        }

# Made with Bob
