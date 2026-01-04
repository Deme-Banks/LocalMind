"""
Base utilities for routes
"""

from typing import Dict, Any, Tuple
from pathlib import Path


def success_response(data: Dict[str, Any] = None, message: str = None) -> Dict[str, Any]:
    """
    Create a success response
    
    Args:
        data: Response data
        message: Optional success message
        
    Returns:
        Success response dictionary
    """
    response = {"status": "ok"}
    if data is not None:
        response.update(data)
    if message:
        response["message"] = message
    return response


def error_response(
    message: str,
    status_code: int = 500,
    error_type: str = None,
    details: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Create an error response
    
    Args:
        message: Error message
        status_code: HTTP status code
        error_type: Optional error type
        details: Optional additional details
        
    Returns:
        Error response dictionary
    """
    response = {
        "status": "error",
        "message": message
    }
    if error_type:
        response["error_type"] = error_type
    if details:
        response["details"] = details
    return response


def get_project_root() -> Path:
    """Get project root directory"""
    return Path(__file__).parent.parent.parent.parent
