"""
File Processor Module
Handles file operations, reading, writing, and processing files
"""

import re
from typing import Dict, Any, Optional, List
from pathlib import Path

from ..base import BaseModule, ModuleResponse


class FileProcessorModule(BaseModule):
    """Module for file processing operations"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.description = "File processing: read, write, analyze, and transform files"
        self.triggers = [
            "file", "read", "write", "save", "load", "process", "analyze",
            "parse", "extract", "convert", "format", "csv", "json", "xml"
        ]
        self.allowed_paths = self.config.get("allowed_paths", [])
        self.max_file_size = self.config.get("max_file_size", 10 * 1024 * 1024)  # 10MB default
    
    def get_info(self) -> Dict[str, Any]:
        """Get module information"""
        return {
            "name": "file_processor",
            "display_name": "File Processor",
            "description": self.description,
            "version": self.version,
            "enabled": self.enabled,
            "commands": self.get_commands(),
            "tools": self.get_tools()
        }
    
    def can_handle(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if prompt is file-related"""
        prompt_lower = prompt.lower()
        
        # Check for file keywords
        for trigger in self.triggers:
            if trigger in prompt_lower:
                return True
        
        # Check for file path patterns
        file_patterns = [
            r'\.(txt|csv|json|xml|yaml|yml|md|py|js|html|css)\b',  # File extensions
            r'read\s+(the\s+)?file',
            r'write\s+(to\s+)?(the\s+)?file',
            r'process\s+(the\s+)?file',
            r'analyze\s+(the\s+)?file',
        ]
        
        for pattern in file_patterns:
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
        """Process file-related prompt"""
        if not model_loader:
            return ModuleResponse(
                content="Error: Model loader not available",
                metadata={"module": "file_processor"},
                success=False,
                error="Model loader required"
            )
        
        # Extract file path if mentioned
        file_path = self._extract_file_path(prompt)
        
        # Enhance prompt
        enhanced_prompt = self._enhance_prompt(prompt, file_path, context)
        
        # Get model from context or use default
        model = kwargs.get("model") or (context.get("model") if context else None)
        temperature = kwargs.get("temperature", 0.5)  # Lower temperature for file operations
        
        try:
            # Generate response using model
            response = model_loader.generate(
                prompt=enhanced_prompt,
                model=model,
                temperature=temperature,
                system_prompt="You are a file processing assistant. Help users read, write, analyze, and transform files safely and efficiently."
            )
            
            return ModuleResponse(
                content=response.text,
                metadata={
                    "module": "file_processor",
                    "model": response.model,
                    "file_path": file_path,
                    "enhanced_prompt": enhanced_prompt != prompt
                },
                success=True
            )
        except Exception as e:
            return ModuleResponse(
                content="",
                metadata={"module": "file_processor"},
                success=False,
                error=str(e)
            )
    
    def _extract_file_path(self, prompt: str) -> Optional[str]:
        """Extract file path from prompt"""
        # Look for file paths (simple pattern)
        path_patterns = [
            r'["\']([^"\']+\.\w{2,4})["\']',  # Quoted paths
            r'(\S+\.(txt|csv|json|xml|yaml|yml|md|py|js|html|css))',  # Unquoted paths
        ]
        
        for pattern in path_patterns:
            match = re.search(pattern, prompt)
            if match:
                return match.group(1)
        
        return None
    
    def _enhance_prompt(self, prompt: str, file_path: Optional[str], context: Optional[Dict[str, Any]] = None) -> str:
        """Enhance prompt with file context"""
        enhanced = prompt
        
        # If file path found, add context
        if file_path:
            try:
                path = Path(file_path)
                if path.exists() and path.is_file():
                    # Check file size
                    size = path.stat().st_size
                    if size <= self.max_file_size:
                        # Read file content (for small files)
                        try:
                            with open(path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                # Limit content length
                                if len(content) > 5000:
                                    content = content[:5000] + "\n... (truncated)"
                                enhanced = f"File: {file_path}\nContent:\n{content}\n\n{prompt}"
                        except Exception:
                            enhanced = f"File: {file_path} (exists, {size} bytes)\n\n{prompt}"
                    else:
                        enhanced = f"File: {file_path} (too large: {size} bytes, max: {self.max_file_size})\n\n{prompt}"
                else:
                    enhanced = f"File: {file_path} (not found or not a file)\n\n{prompt}"
            except Exception:
                pass
        
        return enhanced
    
    def get_commands(self) -> List[Dict[str, str]]:
        """Get file processor module commands"""
        return [
            {
                "trigger": "/read",
                "description": "Read a file",
                "example": "/read file.txt"
            },
            {
                "trigger": "/write",
                "description": "Write to a file",
                "example": "/write save this to output.txt"
            },
            {
                "trigger": "/analyze",
                "description": "Analyze a file",
                "example": "/analyze what's in data.csv"
            },
            {
                "trigger": "/convert",
                "description": "Convert file format",
                "example": "/convert csv to json"
            }
        ]
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get file processor module tools"""
        return [
            {
                "name": "file_read",
                "description": "Read file contents",
                "parameters": ["file_path", "encoding"]
            },
            {
                "name": "file_write",
                "description": "Write to file",
                "parameters": ["file_path", "content", "encoding"]
            },
            {
                "name": "file_analyze",
                "description": "Analyze file structure and content",
                "parameters": ["file_path", "analysis_type"]
            },
            {
                "name": "file_convert",
                "description": "Convert between file formats",
                "parameters": ["file_path", "source_format", "target_format"]
            }
        ]

