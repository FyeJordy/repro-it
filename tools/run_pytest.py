"""Run pytest tool with result parsing."""

import subprocess
import re
from pathlib import Path


def run_pytest(test_file_path: str, repo_root: str) -> dict:
    """
    Run pytest on a specific test file.
    
    Args:
        test_file_path: Path to test file (relative or absolute)
        repo_root: Root directory to run pytest from
    
    Returns:
        dict with keys:
            - ok (bool): True if pytest ran (even if tests failed)
            - exit_code (int): Pytest exit code
            - stdout (str): Standard output
            - stderr (str): Standard error
            - failure_messages (list[str]): Extracted failure messages
            - error (str|None): Error message if pytest couldn't run
    """
    try:
        repo_root_path = Path(repo_root).resolve()
        
        if not repo_root_path.exists():
            return {
                "ok": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": "",
                "failure_messages": [],
                "error": f"Repository root not found: {repo_root}"
            }
        
        # Resolve test file path
        if Path(test_file_path).is_absolute():
            test_path = Path(test_file_path)
        else:
            test_path = repo_root_path / test_file_path
        
        if not test_path.exists():
            return {
                "ok": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": "",
                "failure_messages": [],
                "error": f"Test file not found: {test_file_path}"
            }
        
        # Run pytest with verbose output
        result = subprocess.run(
            ["python3", "-m", "pytest", str(test_path), "-v", "--tb=short"],
            cwd=repo_root_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Parse failure messages from output
        failure_messages = _parse_failures(result.stdout + result.stderr)
        
        return {
            "ok": True,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "failure_messages": failure_messages,
            "error": None
        }
    
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": "",
            "failure_messages": [],
            "error": "Pytest timeout after 30 seconds"
        }
    except FileNotFoundError:
        return {
            "ok": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": "",
            "failure_messages": [],
            "error": "pytest not found. Install with: pip install pytest"
        }
    except Exception as e:
        return {
            "ok": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": "",
            "failure_messages": [],
            "error": f"Error running pytest: {str(e)}"
        }


def _parse_failures(output: str) -> list:
    """
    Extract failure messages from pytest output.
    
    Looks for FAILED lines, assertion errors, and import errors.
    """
    failures = []
    lines = output.split('\n')
    
    for i, line in enumerate(lines):
        # Capture FAILED test lines
        if 'FAILED' in line and '::' in line:
            failures.append(line.strip())
        
        # Capture NameError (import failures)
        if 'NameError' in line:
            # Get context around NameError
            start = max(0, i - 1)
            end = min(len(lines), i + 2)
            context = '\n'.join(lines[start:end]).strip()
            if context and context not in failures:
                failures.append(context)
        
        # Capture AssertionError lines with context
        if 'AssertionError' in line:
            # Get a few lines of context
            start = max(0, i - 1)
            end = min(len(lines), i + 3)
            context = '\n'.join(lines[start:end]).strip()
            if context and context not in failures:
                failures.append(context)
        
        # Capture assertion comparison lines (Expected X, got Y)
        if 'Expected' in line and 'got' in line:
            failures.append(line.strip())
        
        # Capture ERROR lines
        if line.strip().startswith('ERROR') and '::' in line:
            failures.append(line.strip())
    
    # Limit to most relevant failures
    return failures[:10]

# Made with Bob
