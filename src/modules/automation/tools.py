"""
Automation Tools Module
Provides automation and task execution capabilities
"""

import subprocess
import os
import re
from typing import Dict, Any, Optional, List
from pathlib import Path

from ..base import BaseModule, ModuleResponse


class AutomationToolsModule(BaseModule):
    """Module for automation and task execution"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.description = "Automation tools for executing tasks, running commands, and automating workflows"
        self.triggers = [
            "run", "execute", "command", "script", "automate", "task",
            "schedule", "workflow", "batch", "process"
        ]
        self.safe_mode = self.config.get("safe_mode", True)  # Only allow safe commands by default
    
    def get_info(self) -> Dict[str, Any]:
        """Get module information"""
        return {
            "name": "automation",
            "display_name": "Automation Tools",
            "description": self.description,
            "version": self.version,
            "enabled": self.enabled,
            "safe_mode": self.safe_mode,
            "commands": self.get_commands(),
            "tools": self.get_tools()
        }
    
    def can_handle(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if prompt is automation-related"""
        prompt_lower = prompt.lower()
        
        # Check for automation keywords
        for trigger in self.triggers:
            if trigger in prompt_lower:
                return True
        
        # Check for command patterns
        command_patterns = [
            r'run\s+(the\s+)?command',
            r'execute\s+(the\s+)?script',
            r'run\s+this\s+code',
            r'execute\s+this',
        ]
        
        for pattern in command_patterns:
            if re.search(pattern, prompt_lower):
                return True
        
        return False
    
    def process(
        self,
        prompt: str,
        model_loader: Any = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> ModuleResponse:
        """Process automation prompt"""
        # For now, this module primarily provides tools
        # Actual execution would require careful sandboxing
        
        if not model_loader:
            return ModuleResponse(
                content="Automation tools are available. Use /help automation to see available commands.",
                metadata={"module": "automation"},
                success=True
            )
        
        # Generate helpful response about automation
        try:
            response = model_loader.generate(
                prompt=f"User wants to automate: {prompt}\n\nProvide guidance on how to accomplish this task.",
                model=kwargs.get("model"),
                temperature=0.7,
                system_prompt="You are an automation assistant."
            )
            
            return ModuleResponse(
                content=response.text,
                metadata={
                    "module": "automation",
                    "model": response.model,
                    "safe_mode": self.safe_mode
                },
                success=True
            )
        except Exception as e:
            return ModuleResponse(
                content="",
                metadata={"module": "automation"},
                success=False,
                error=str(e)
            )
    
    def get_commands(self) -> List[Dict[str, str]]:
        """Get automation module commands"""
        return [
            {
                "trigger": "/run",
                "description": "Run a safe command",
                "example": "/run list files in current directory"
            },
            {
                "trigger": "/automate",
                "description": "Get automation guidance",
                "example": "/automate how to batch rename files"
            },
            {
                "trigger": "/task",
                "description": "Create a task workflow",
                "example": "/task create a workflow to backup files"
            }
        ]
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get automation module tools"""
        return [
            {
                "name": "command_execution",
                "description": "Execute safe system commands",
                "parameters": ["command", "working_directory"],
                "safe_commands_only": True
            },
            {
                "name": "file_operations",
                "description": "Perform file operations",
                "parameters": ["operation", "file_path"]
            },
            {
                "name": "workflow_creation",
                "description": "Create automation workflows",
                "parameters": ["steps", "conditions"]
            }
        ]

