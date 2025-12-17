"""
Tool Executor - executes tools/functions based on AI model requests
"""

from typing import Dict, Any, Optional, List
import logging
import json
import re

from .tool_registry import ToolRegistry, Tool

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Executes tools requested by AI models"""
    
    def __init__(self, tool_registry: ToolRegistry):
        """
        Initialize tool executor
        
        Args:
            tool_registry: Tool registry instance
        """
        self.tool_registry = tool_registry
    
    def parse_tool_calls(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse tool calls from AI response text
        
        Supports multiple formats:
        1. JSON format: {"tool": "name", "arguments": {...}}
        2. Function call format: tool_name(arg1="value", arg2="value")
        3. XML format: <tool name="name"><arg name="arg1">value</arg></tool>
        
        Args:
            text: AI response text
        
        Returns:
            List of parsed tool calls
        """
        tool_calls = []
        
        # Try JSON format
        json_pattern = r'\{"tool":\s*"([^"]+)",\s*"arguments":\s*(\{[^}]+\})\}'
        matches = re.finditer(json_pattern, text)
        for match in matches:
            tool_name = match.group(1)
            try:
                arguments = json.loads(match.group(2))
                tool_calls.append({
                    "tool": tool_name,
                    "arguments": arguments
                })
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON arguments for tool {tool_name}")
        
        # Try function call format: tool_name(arg1="value", arg2=123)
        func_pattern = r'(\w+)\s*\(([^)]+)\)'
        matches = re.finditer(func_pattern, text)
        for match in matches:
            tool_name = match.group(1)
            if tool_name in self.tool_registry.tools:
                args_str = match.group(2)
                arguments = self._parse_function_args(args_str)
                tool_calls.append({
                    "tool": tool_name,
                    "arguments": arguments
                })
        
        return tool_calls
    
    def _parse_function_args(self, args_str: str) -> Dict[str, Any]:
        """Parse function arguments from string"""
        arguments = {}
        
        # Simple parser for key="value" or key=123 format
        pattern = r'(\w+)\s*=\s*("([^"]+)"|(\d+\.?\d*)|(\w+))'
        matches = re.finditer(pattern, args_str)
        for match in matches:
            key = match.group(1)
            # Get value (string, number, or identifier)
            if match.group(3):  # String
                value = match.group(3)
            elif match.group(4):  # Number
                value = float(match.group(4)) if '.' in match.group(4) else int(match.group(4))
            else:  # Identifier
                value = match.group(5)
            arguments[key] = value
        
        return arguments
    
    def execute_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute a list of tool calls
        
        Args:
            tool_calls: List of tool call dictionaries
        
        Returns:
            List of execution results
        """
        results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call.get("tool")
            arguments = tool_call.get("arguments", {})
            
            if not tool_name:
                results.append({
                    "success": False,
                    "error": "Tool name not specified"
                })
                continue
            
            # Execute tool
            result = self.tool_registry.execute_tool(tool_name, arguments)
            result["tool"] = tool_name
            results.append(result)
        
        return results
    
    def format_tool_results(self, results: List[Dict[str, Any]]) -> str:
        """
        Format tool execution results for AI model
        
        Args:
            results: List of execution results
        
        Returns:
            Formatted string
        """
        formatted = []
        
        for result in results:
            tool_name = result.get("tool", "unknown")
            if result.get("success"):
                formatted.append(f"Tool {tool_name} executed successfully:")
                formatted.append(str(result.get("result", "")))
            else:
                formatted.append(f"Tool {tool_name} failed:")
                formatted.append(result.get("error", "Unknown error"))
            formatted.append("")  # Blank line
        
        return "\n".join(formatted)
    
    def process_with_tools(
        self,
        prompt: str,
        model_response: str,
        max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Process AI response and execute any tool calls
        
        Args:
            prompt: Original user prompt
            model_response: AI model response
            max_iterations: Maximum number of tool call iterations
        
        Returns:
            Dictionary with final response and tool execution history
        """
        history = []
        current_response = model_response
        iteration = 0
        
        while iteration < max_iterations:
            # Parse tool calls from response
            tool_calls = self.parse_tool_calls(current_response)
            
            if not tool_calls:
                # No more tool calls, return final response
                break
            
            # Execute tools
            results = self.execute_tool_calls(tool_calls)
            history.append({
                "iteration": iteration,
                "tool_calls": tool_calls,
                "results": results
            })
            
            # Format results for next iteration
            results_text = self.format_tool_results(results)
            current_response = f"{current_response}\n\nTool Results:\n{results_text}"
            
            iteration += 1
        
        return {
            "final_response": current_response,
            "tool_history": history,
            "iterations": iteration
        }

