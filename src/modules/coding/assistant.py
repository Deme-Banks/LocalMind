"""
Coding Assistant Module
Provides specialized assistance for programming tasks
"""

import re
from typing import Dict, Any, Optional, List
from pathlib import Path

from ..base import BaseModule, ModuleResponse


class CodingAssistantModule(BaseModule):
    """Module for coding assistance"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.description = "Specialized assistant for programming, code generation, debugging, and code analysis"
        self.triggers = [
            "code", "programming", "function", "class", "debug", "error",
            "syntax", "algorithm", "implement", "refactor", "optimize",
            "python", "javascript", "java", "c++", "html", "css", "sql"
        ]
    
    def get_info(self) -> Dict[str, Any]:
        """Get module information"""
        return {
            "name": "coding",
            "display_name": "Coding Assistant",
            "description": self.description,
            "version": self.version,
            "enabled": self.enabled,
            "commands": self.get_commands(),
            "tools": self.get_tools()
        }
    
    def can_handle(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if prompt is coding-related"""
        prompt_lower = prompt.lower()
        
        # Check for coding keywords
        for trigger in self.triggers:
            if trigger in prompt_lower:
                return True
        
        # Check for code blocks
        if "```" in prompt or "```" in prompt:
            return True
        
        # Check for programming patterns
        code_patterns = [
            r'\bdef\s+\w+\s*\(',  # Python function
            r'\bfunction\s+\w+\s*\(',  # JavaScript function
            r'\bclass\s+\w+',  # Class definition
            r'import\s+\w+',  # Import statement
            r'#include',  # C/C++ include
            r'<\w+>',  # HTML tags
        ]
        
        for pattern in code_patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                return True
        
        return False
    
    def process(
        self,
        prompt: str,
        model_loader: Any = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> ModuleResponse:
        """Process coding-related prompt"""
        if not model_loader:
            return ModuleResponse(
                content="Error: Model loader not available",
                metadata={"module": "coding"},
                success=False,
                error="Model loader required"
            )
        
        # Enhance prompt for coding tasks
        enhanced_prompt = self._enhance_prompt(prompt, context)
        
        # Get model from context or use default
        model = kwargs.get("model") or (context.get("model") if context else None)
        temperature = kwargs.get("temperature", 0.3)  # Lower temperature for code
        
        try:
            # Generate response using model
            response = model_loader.generate(
                prompt=enhanced_prompt,
                model=model,
                temperature=temperature,
                system_prompt="You are an expert programming assistant. Provide clear, well-commented code. Explain your approach when helpful."
            )
            
            return ModuleResponse(
                content=response.text,
                metadata={
                    "module": "coding",
                    "model": response.model,
                    "enhanced_prompt": enhanced_prompt != prompt
                },
                success=True
            )
        except Exception as e:
            return ModuleResponse(
                content="",
                metadata={"module": "coding"},
                success=False,
                error=str(e)
            )
    
    def _enhance_prompt(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Enhance prompt with coding-specific context"""
        # Extract code blocks if present
        code_blocks = re.findall(r'```(?:\w+)?\n?(.*?)```', prompt, re.DOTALL)
        
        enhanced = prompt
        
        # Add context about previous code if available
        if context and context.get("messages"):
            # Look for code in recent messages
            recent_code = []
            for msg in context["messages"][-5:]:  # Last 5 messages
                content = msg.get("content", "")
                if "```" in content or any(keyword in content.lower() for keyword in ["def ", "function ", "class "]):
                    recent_code.append(content[:200])  # First 200 chars
            
            if recent_code:
                enhanced = f"Previous context:\n{chr(10).join(recent_code)}\n\n{enhanced}"
        
        return enhanced
    
    def get_commands(self) -> List[Dict[str, str]]:
        """Get coding module commands"""
        return [
            {
                "trigger": "/code",
                "description": "Generate code",
                "example": "/code write a Python function to sort a list"
            },
            {
                "trigger": "/debug",
                "description": "Debug code",
                "example": "/debug fix this error: ..."
            },
            {
                "trigger": "/explain",
                "description": "Explain code",
                "example": "/explain what does this code do?"
            },
            {
                "trigger": "/refactor",
                "description": "Refactor code",
                "example": "/refactor make this code more efficient"
            }
        ]
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get coding module tools"""
        return [
            {
                "name": "code_generation",
                "description": "Generate code based on requirements",
                "parameters": ["language", "requirements", "style"]
            },
            {
                "name": "code_analysis",
                "description": "Analyze and explain code",
                "parameters": ["code", "focus"]
            },
            {
                "name": "code_debugging",
                "description": "Debug and fix code errors",
                "parameters": ["code", "error_message"]
            }
        ]

