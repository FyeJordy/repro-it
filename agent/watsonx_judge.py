"""Optional watsonx.ai judge for right-reason verification."""

import os
import json
from typing import Dict, Any


def judge_failure_with_watsonx(bug_data: Dict[str, Any], test_code: str,
                                pytest_output: str, verbose: bool = False) -> Dict[str, Any]:
    """
    Use watsonx.ai/Granite to judge if test failure matches bug report.
    
    Falls back gracefully if credentials missing or API fails.
    
    Args:
        bug_data: Original bug report
        test_code: Generated test code
        pytest_output: Pytest execution output
        verbose: Enable diagnostic output
    
    Returns:
        dict with:
            - match (bool): Whether failure matches bug
            - confidence (float): 0.0-1.0
            - reasoning (str): Short explanation
            - provider (str): "watsonx.ai" or "unavailable"
    """
    
    # Check for required environment variables
    required_vars = ["WATSONX_API_KEY", "WATSONX_PROJECT_ID", "WATSONX_URL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        reason = f"Missing env vars: {', '.join(missing_vars)}"
        if verbose:
            print(f"[watsonx] {reason}")
        return {
            "match": None,
            "confidence": 0.0,
            "reasoning": reason,
            "provider": "unavailable"
        }
    
    try:
        # Import watsonx SDK (ibm-watsonx-ai 0.0.5 pattern)
        from ibm_watsonx_ai.foundation_models import Model
        from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
        
        if verbose:
            print("[watsonx] SDK imported successfully")
        
        # Get credentials from environment
        credentials = {
            "url": os.getenv("WATSONX_URL"),
            "apikey": os.getenv("WATSONX_API_KEY")
        }
        
        project_id = os.getenv("WATSONX_PROJECT_ID")
        model_id = os.getenv("WATSONX_MODEL_ID", "ibm/granite-8b-code-instruct")
        
        # Set generation parameters
        params = {
            GenParams.DECODING_METHOD: "greedy",
            GenParams.MAX_NEW_TOKENS: 200,
            GenParams.MIN_NEW_TOKENS: 1,
            GenParams.TEMPERATURE: 0.0,
        }
        
        # Initialize model
        model = Model(
            model_id=model_id,
            credentials=credentials,
            project_id=project_id,
            params=params
        )
        
        # Build judge prompt
        prompt = _build_judge_prompt(bug_data, test_code, pytest_output)
        
        if verbose:
            print(f"[watsonx] Calling model: {model_id}")
        
        # Call watsonx.ai
        response = model.generate_text(prompt=prompt)
        
        if verbose:
            print(f"[watsonx] Response received: {len(response)} chars")
        
        # Parse response
        result = _parse_judge_response(response)
        result["provider"] = "watsonx.ai"
        
        if verbose:
            print(f"[watsonx] Parsed result: match={result['match']}, confidence={result['confidence']}")
        
        return result
    
    except ImportError as e:
        reason = "ibm-watsonx-ai package not installed"
        if verbose:
            print(f"[watsonx] ImportError: {str(e)[:120]}")
        return {
            "match": None,
            "confidence": 0.0,
            "reasoning": reason,
            "provider": "unavailable"
        }
    
    except Exception as e:
        reason = f"{type(e).__name__}: {str(e)[:120]}"
        if verbose:
            print(f"[watsonx] API error: {reason}")
        return {
            "match": None,
            "confidence": 0.0,
            "reasoning": reason,
            "provider": "unavailable"
        }


def _build_judge_prompt(bug_data: Dict[str, Any], test_code: str, 
                        pytest_output: str) -> str:
    """Build prompt for watsonx.ai judge."""
    
    bug_title = bug_data.get("title", "")
    bug_desc = bug_data.get("description", "")
    
    prompt = f"""You are a test quality judge. Determine if a pytest failure correctly reproduces a bug.

Bug Report:
Title: {bug_title}
Description: {bug_desc}

Generated Test Code:
{test_code[:500]}

Pytest Output:
{pytest_output[:800]}

Reject if:
- ImportError, NameError, or ModuleNotFoundError
- Test contains TODO or "not yet implemented"
- Test contains "assert False" placeholder
- Failure is unrelated to bug description

Accept if:
- AssertionError with numeric comparison
- Failure matches bug scenario
- Test exercises the reported issue

Answer in JSON format:
{{"match": true/false, "confidence": 0.0-1.0, "reasoning": "brief explanation"}}

JSON:"""
    
    return prompt


def _parse_judge_response(response: str) -> Dict[str, Any]:
    """Parse watsonx.ai response into structured result."""
    
    try:
        # Try to extract JSON from response
        response = response.strip()
        
        # Find JSON object in response
        start = response.find('{')
        end = response.rfind('}') + 1
        
        if start >= 0 and end > start:
            json_str = response[start:end]
            result = json.loads(json_str)
            
            return {
                "match": result.get("match", False),
                "confidence": float(result.get("confidence", 0.5)),
                "reasoning": result.get("reasoning", "")[:200]
            }
    except Exception:
        pass
    
    # Fallback: parse text response
    response_lower = response.lower()
    
    if "reject" in response_lower or "false" in response_lower:
        match = False
    elif "accept" in response_lower or "true" in response_lower:
        match = True
    else:
        match = False
    
    return {
        "match": match,
        "confidence": 0.5,
        "reasoning": "Parsed from text response"
    }

# Made with Bob
