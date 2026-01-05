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
    details: Dict[str, Any] = None,
    troubleshooting: str = None
) -> Dict[str, Any]:
    """
    Create an error response with enhanced context
    
    Args:
        message: Error message
        status_code: HTTP status code
        error_type: Optional error type
        details: Optional additional details
        troubleshooting: Optional troubleshooting tips
        
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
    if troubleshooting:
        response["troubleshooting"] = troubleshooting
    
    # Add common troubleshooting tips based on error type
    if not troubleshooting:
        if error_type == "not_found":
            response["troubleshooting"] = "Check that the resource exists and you have access to it."
        elif error_type == "validation":
            response["troubleshooting"] = "Verify all required fields are provided and have valid values."
        elif error_type == "rate_limit":
            response["troubleshooting"] = "Wait a moment and try again, or check your API rate limits."
        elif status_code == 500:
            response["troubleshooting"] = "Check server logs for more details. If the issue persists, try restarting the server."
    
    return response


def get_project_root() -> Path:
    """Get project root directory"""
    return Path(__file__).parent.parent.parent.parent
