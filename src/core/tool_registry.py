"""
Tool Registry - manages available tools/functions for AI models
"""

from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
import logging
import json
import inspect

logger = logging.getLogger(__name__)


@dataclass
class ToolParameter:
    """Parameter definition for a tool"""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None


@dataclass
class Tool:
    """Tool definition"""
    name: str
    description: str
    parameters: List[ToolParameter] = field(default_factory=list)
    function: Optional[Callable] = None
    module: Optional[str] = None  # Which module provides this tool
    safe: bool = True  # Whether tool is safe to execute
    requires_confirmation: bool = False  # Whether user confirmation is needed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary format (OpenAI function calling format)"""
        properties = {}
        required = []
        
        for param in self.parameters:
            properties[param.name] = {
                "type": param.type,
                "description": param.description
            }
            if param.required:
                required.append(param.name)
            if param.default is not None:
                properties[param.name]["default"] = param.default
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }
    
    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool with given arguments
        
        Args:
            arguments: Dictionary of parameter values
        
        Returns:
            Dictionary with execution result
        """
        if not self.function:
            return {
                "success": False,
                "error": "Tool function not defined"
            }
        
        try:
            # Validate arguments
            for param in self.parameters:
                if param.required and param.name not in arguments:
                    return {
                        "success": False,
                        "error": f"Missing required parameter: {param.name}"
                    }
            
            # Execute function
            result = self.function(**arguments)
            
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            logger.error(f"Error executing tool {self.name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class ToolRegistry:
    """Registry for managing tools/functions"""
    
    def __init__(self):
        """Initialize tool registry"""
        self.tools: Dict[str, Tool] = {}
        self._register_builtin_tools()
    
    def _register_builtin_tools(self):
        """Register built-in tools"""
        # Calculator tool
        self.register_tool(
            name="calculate",
            description="Perform mathematical calculations",
            parameters=[
                ToolParameter("expression", "string", "Mathematical expression to evaluate", True)
            ],
            function=self._calculate,
            safe=True
        )
        
        # Current time tool
        self.register_tool(
            name="get_current_time",
            description="Get the current date and time",
            parameters=[],
            function=self._get_current_time,
            safe=True
        )
        
        # File read tool (safe)
        self.register_tool(
            name="read_file",
            description="Read contents of a text file",
            parameters=[
                ToolParameter("file_path", "string", "Path to the file to read", True)
            ],
            function=self._read_file,
            safe=True,
            requires_confirmation=False
        )
    
    def register_tool(
        self,
        name: str,
        description: str,
        parameters: List[ToolParameter],
        function: Callable,
        module: Optional[str] = None,
        safe: bool = True,
        requires_confirmation: bool = False
    ) -> bool:
        """
        Register a tool
        
        Args:
            name: Tool name (must be unique)
            description: Tool description
            parameters: List of tool parameters
            function: Function to execute
            module: Module that provides this tool
            safe: Whether tool is safe to execute
            requires_confirmation: Whether user confirmation is needed
        
        Returns:
            True if registered successfully
        """
        if name in self.tools:
            logger.warning(f"Tool {name} already registered, overwriting")
        
        tool = Tool(
            name=name,
            description=description,
            parameters=parameters,
            function=function,
            module=module,
            safe=safe,
            requires_confirmation=requires_confirmation
        )
        
        self.tools[name] = tool
        logger.info(f"Registered tool: {name}")
        return True
    
    def unregister_tool(self, name: str) -> bool:
        """
        Unregister a tool
        
        Args:
            name: Tool name
        
        Returns:
            True if unregistered successfully
        """
        if name in self.tools:
            del self.tools[name]
            logger.info(f"Unregistered tool: {name}")
            return True
        return False
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """
        Get a tool by name
        
        Args:
            name: Tool name
        
        Returns:
            Tool instance or None
        """
        return self.tools.get(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all registered tools
        
        Returns:
            List of tool dictionaries
        """
        return [tool.to_dict() for tool in self.tools.values()]
    
    def get_tools_for_backend(self, backend_type: str) -> List[Dict[str, Any]]:
        """
        Get tools formatted for a specific backend
        
        Args:
            backend_type: Backend type (openai, anthropic, etc.)
        
        Returns:
            List of tools in backend-specific format
        """
        # For now, return OpenAI-compatible format
        return self.list_tools()
    
    def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool
        
        Args:
            name: Tool name
            arguments: Tool arguments
        
        Returns:
            Execution result
        """
        tool = self.get_tool(name)
        if not tool:
            return {
                "success": False,
                "error": f"Tool {name} not found"
            }
        
        if not tool.safe:
            logger.warning(f"Executing unsafe tool: {name}")
        
        return tool.execute(arguments)
    
    # Built-in tool implementations
    def _calculate(self, expression: str) -> str:
        """Calculate mathematical expression"""
        try:
            # Safe evaluation - only allow basic math operations
            allowed_chars = set("0123456789+-*/.() ")
            if not all(c in allowed_chars for c in expression):
                return "Error: Invalid characters in expression"
            
            result = eval(expression)  # Safe for math expressions only
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _get_current_time(self) -> str:
        """Get current time"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _read_file(self, file_path: str) -> str:
        """Read file contents (safe, limited)"""
        from pathlib import Path
        
        try:
            path = Path(file_path)
            
            # Security: prevent path traversal
            if ".." in str(path) or path.is_absolute():
                return "Error: Invalid file path"
            
            # Limit file size (1MB)
            if path.exists() and path.is_file():
                size = path.stat().st_size
                if size > 1024 * 1024:  # 1MB
                    return "Error: File too large (max 1MB)"
                
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Limit content length
                    if len(content) > 10000:
                        content = content[:10000] + "\n... (truncated)"
                    return content
            else:
                return "Error: File not found"
        except Exception as e:
            return f"Error: {str(e)}"

