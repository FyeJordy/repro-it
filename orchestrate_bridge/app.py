#!/usr/bin/env python3
"""
Orchestrate Bridge for Repro-It

Flask-based HTTP server that exposes Repro-It functionality via REST API.
This bridge is OPTIONAL - the main demo works without it.

Security:
- Path validation to prevent directory traversal
- No hardcoded secrets
- Never prints environment variable values
- 120-second timeout on subprocess execution
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from flask import Flask, request, jsonify

# Import bug text converter
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.bug_text_to_json import convert_text_to_bug_json

app = Flask(__name__)

# Project root is parent of orchestrate_bridge directory
PROJECT_ROOT = Path(__file__).parent.parent.resolve()


def validate_path(path_str: str) -> Tuple[bool, str]:
    """
    Validate that a path is safe to use.
    
    Returns:
        (is_valid, error_message)
    """
    if not path_str:
        return False, "Path cannot be empty"
    
    # Reject absolute paths
    if path_str.startswith('/'):
        return False, "Absolute paths are not allowed"
    
    # Reject paths containing ..
    if '..' in path_str:
        return False, "Path traversal (..) is not allowed"
    
    # Resolve the path and ensure it's within project root
    try:
        full_path = (PROJECT_ROOT / path_str).resolve()
        if not str(full_path).startswith(str(PROJECT_ROOT)):
            return False, "Path must be within project root"
    except Exception as e:
        return False, f"Invalid path: {str(e)}"
    
    return True, ""


def parse_repro_output(stdout: str) -> Tuple[Optional[str], str]:
    """
    Parse stdout to extract judge_provider and failure_summary.
    
    Returns:
        (judge_provider, failure_summary)
    """
    judge_provider = None
    failure_summary = ""
    
    # Look for judge provider in output
    # Match "watsonx.ai" or "deterministic"
    judge_match = re.search(r'Judge provider:\s*([\w.]+)', stdout)
    if judge_match:
        judge_provider = judge_match.group(1)
    
    # Look for failure summary
    # Common patterns in repro_it.py output
    if "FAILURE" in stdout:
        # Extract lines after FAILURE
        lines = stdout.split('\n')
        for i, line in enumerate(lines):
            if "FAILURE" in line and i + 1 < len(lines):
                failure_summary = lines[i + 1].strip()
                break
    
    if not failure_summary and "Error" in stdout:
        # Extract first error line
        for line in stdout.split('\n'):
            if "Error" in line:
                failure_summary = line.strip()
                break
    
    return judge_provider, failure_summary


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"ok": True})


@app.route('/run-repro', methods=['POST'])
def run_repro():
    """
    Run Repro-It with specified bug and repo paths.
    
    Request JSON:
        {
            "bug_path": "bugs/discount_double_gift_card.json",  # optional
            "repo_path": "demo_repo"  # optional
        }
    
    Response JSON:
        {
            "ok": bool,
            "exit_code": int,
            "success": bool,
            "judge_provider": str | null,
            "failure_summary": str,
            "stdout": str,
            "stderr": str
        }
    """
    try:
        data = request.get_json() or {}
        
        # Default paths
        bug_path = data.get('bug_path', 'bugs/discount_double_gift_card.json')
        repo_path = data.get('repo_path', 'demo_repo')
        
        # Validate paths
        is_valid, error = validate_path(bug_path)
        if not is_valid:
            app.logger.error(f"Invalid bug_path: {error}")
            return jsonify({
                "ok": False,
                "exit_code": -1,
                "success": False,
                "judge_provider": None,
                "failure_summary": f"Invalid bug_path: {error}",
                "stdout": "",
                "stderr": ""
            }), 400
        
        is_valid, error = validate_path(repo_path)
        if not is_valid:
            app.logger.error(f"Invalid repo_path: {error}")
            return jsonify({
                "ok": False,
                "exit_code": -1,
                "success": False,
                "judge_provider": None,
                "failure_summary": f"Invalid repo_path: {error}",
                "stdout": "",
                "stderr": ""
            }), 400
        
        # Log request (but not sensitive data)
        app.logger.info(f"Running repro_it.py with bug_path={bug_path}, repo_path={repo_path}")
        
        # Build command
        cmd = [
            sys.executable,
            'repro_it.py',
            '--bug', bug_path,
            '--repo', repo_path,
            '--verbose'
        ]
        
        # Execute subprocess with timeout
        try:
            result = subprocess.run(
                cmd,
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                timeout=120
            )
            
            exit_code = result.returncode
            stdout = result.stdout
            stderr = result.stderr
            success = exit_code == 0
            
            # Parse output
            judge_provider, failure_summary = parse_repro_output(stdout)
            
            app.logger.info(f"Command completed with exit_code={exit_code}")
            
            return jsonify({
                "ok": True,
                "exit_code": exit_code,
                "success": success,
                "judge_provider": judge_provider,
                "failure_summary": failure_summary,
                "stdout": stdout,
                "stderr": stderr
            })
            
        except subprocess.TimeoutExpired:
            app.logger.error("Command timed out after 120 seconds")
            return jsonify({
                "ok": False,
                "exit_code": -1,
                "success": False,
                "judge_provider": None,
                "failure_summary": "Command timed out after 120 seconds",
                "stdout": "",
                "stderr": "Timeout"
            }), 500
            
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            "ok": False,
            "exit_code": -1,
            "success": False,
            "judge_provider": None,
            "failure_summary": f"Server error: {str(e)}",
            "stdout": "",
            "stderr": str(e)
        }), 500


@app.route('/run-repro-from-text', methods=['POST'])
def run_repro_from_text():
    """
    Run Repro-It from plain-text bug report.
    
    Request JSON:
        {
            "text": "required non-empty plain text bug report",
            "bug_id": "optional default BUG-orch-001",
            "severity": "optional default medium",
            "repo_path": "optional default demo_repo"
        }
    
    Response JSON:
        {
            "ok": bool,
            "exit_code": int,
            "success": bool,
            "judge_provider": str | null,
            "failure_summary": str,
            "converted_bug": dict,
            "stdout": str,
            "stderr": str
        }
    """
    try:
        data = request.get_json() or {}
        
        # Validate required text field
        text = data.get('text', '').strip()
        if not text:
            app.logger.error("Missing or empty 'text' field")
            return jsonify({
                "ok": False,
                "exit_code": -1,
                "success": False,
                "judge_provider": None,
                "failure_summary": "Missing or empty 'text' field",
                "converted_bug": {},
                "stdout": "",
                "stderr": ""
            }), 400
        
        # Get optional parameters
        bug_id = data.get('bug_id', 'BUG-orch-001')
        severity = data.get('severity', 'medium')
        repo_path = data.get('repo_path', 'demo_repo')
        
        # Validate repo_path
        is_valid, error = validate_path(repo_path)
        if not is_valid:
            app.logger.error(f"Invalid repo_path: {error}")
            return jsonify({
                "ok": False,
                "exit_code": -1,
                "success": False,
                "judge_provider": None,
                "failure_summary": f"Invalid repo_path: {error}",
                "converted_bug": {},
                "stdout": "",
                "stderr": ""
            }), 400
        
        # Convert text to bug JSON
        app.logger.info(f"Converting plain text to bug JSON (bug_id={bug_id})")
        bug_dict = convert_text_to_bug_json(text, bug_id=bug_id, reporter="orchestrate", severity=severity)
        
        # Write bug JSON to file
        bug_path = 'bugs/from_orchestrate.json'
        full_bug_path = PROJECT_ROOT / bug_path
        full_bug_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_bug_path, 'w', encoding='utf-8') as f:
            json.dump(bug_dict, f, indent=2)
            f.write('\n')
        
        app.logger.info(f"Bug JSON written to {bug_path}")
        
        # Build command
        cmd = [
            sys.executable,
            'repro_it.py',
            '--bug', bug_path,
            '--repo', repo_path,
            '--verbose'
        ]
        
        # Execute subprocess with timeout
        try:
            result = subprocess.run(
                cmd,
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                timeout=120
            )
            
            exit_code = result.returncode
            stdout = result.stdout
            stderr = result.stderr
            success = exit_code == 0
            
            # Parse output
            judge_provider, failure_summary = parse_repro_output(stdout)
            
            app.logger.info(f"Command completed with exit_code={exit_code}")
            
            return jsonify({
                "ok": True,
                "exit_code": exit_code,
                "success": success,
                "judge_provider": judge_provider,
                "failure_summary": failure_summary,
                "converted_bug": bug_dict,
                "stdout": stdout,
                "stderr": stderr
            })
            
        except subprocess.TimeoutExpired:
            app.logger.error("Command timed out after 120 seconds")
            return jsonify({
                "ok": False,
                "exit_code": -1,
                "success": False,
                "judge_provider": None,
                "failure_summary": "Command timed out after 120 seconds",
                "converted_bug": bug_dict,
                "stdout": "",
                "stderr": "Timeout"
            }), 500
            
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            "ok": False,
            "exit_code": -1,
            "success": False,
            "judge_provider": None,
            "failure_summary": f"Server error: {str(e)}",
            "converted_bug": {},
            "stdout": "",
            "stderr": str(e)
        }), 500


if __name__ == '__main__':
    port = int(os.getenv("PORT", "5001"))
    print(f"Starting Orchestrate Bridge on port {port}")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Health check: http://localhost:{port}/health")
    print(f"Run repro: POST http://localhost:{port}/run-repro")
    print(f"Run repro from text: POST http://localhost:{port}/run-repro-from-text")
    app.run(host='0.0.0.0', port=port, debug=False)

# Made with Bob
