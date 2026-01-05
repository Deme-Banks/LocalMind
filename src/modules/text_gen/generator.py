"""
Text Generator Module
Specialized for creative writing, content generation, and text transformation
"""

import re
from typing import Dict, Any, Optional, List

from ..base import BaseModule, ModuleResponse


class TextGeneratorModule(BaseModule):
    """Module for text generation and creative writing"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.description = "Specialized assistant for creative writing, content generation, and text transformation"
        self.triggers = [
            "write", "story", "essay", "article", "blog", "poem", "letter",
            "email", "summary", "paraphrase", "rewrite", "translate",
            "creative", "fiction", "narrative", "prose"
        ]
    
    def get_info(self) -> Dict[str, Any]:
        """Get module information"""
        return {
            "name": "text_gen",
            "display_name": "Text Generator",
            "description": self.description,
            "version": self.version,
            "enabled": self.enabled,
            "commands": self.get_commands(),
            "tools": self.get_tools()
        }
    
    def can_handle(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if prompt is text generation-related"""
        prompt_lower = prompt.lower()
        
        # Check for text generation keywords
        for trigger in self.triggers:
            if trigger in prompt_lower:
                return True
        
        # Check for writing patterns
        writing_patterns = [
            r'write\s+(a|an|the)\s+\w+',  # "write a story"
            r'create\s+(a|an|the)\s+\w+',  # "create a poem"
            r'summarize',  # Summarization
            r'paraphrase',  # Paraphrasing
            r'translate\s+to',  # Translation
        ]
        
        for pattern in writing_patterns:
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
        """Process text generation prompt"""
        if not model_loader:
            return ModuleResponse(
                content="Error: Model loader not available",
                metadata={"module": "text_gen"},
                success=False,
                error="Model loader required"
            )
        
        # Enhance prompt for text generation
        enhanced_prompt = self._enhance_prompt(prompt, context)
        
        # Get model from context or use default
        model = kwargs.get("model") or (context.get("model") if context else None)
        temperature = kwargs.get("temperature", 0.8)  # Higher temperature for creativity
        
        try:
            # Generate response using model
            response = model_loader.generate(
                prompt=enhanced_prompt,
                model=model,
                temperature=temperature,
                system_prompt="You are a creative writing assistant."
            )
            
            return ModuleResponse(
                content=response.text,
                metadata={
                    "module": "text_gen",
                    "model": response.model,
                    "enhanced_prompt": enhanced_prompt != prompt
                },
                success=True
            )
        except Exception as e:
            return ModuleResponse(
                content="",
                metadata={"module": "text_gen"},
                success=False,
                error=str(e)
            )
    
    def _enhance_prompt(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Enhance prompt with writing-specific context"""
        enhanced = prompt
        
        # Add style/tone hints if present in context
        if context and context.get("style"):
            enhanced = f"Style: {context['style']}\n\n{enhanced}"
        
        # Add length requirements if mentioned
        if "short" in prompt.lower():
            enhanced = f"{enhanced}\n\nKeep it concise (under 200 words)."
        elif "long" in prompt.lower() or "detailed" in prompt.lower():
            enhanced = f"{enhanced}\n\nProvide a detailed response (500+ words)."
        
        return enhanced
    
    def get_commands(self) -> List[Dict[str, str]]:
        """Get text generation module commands"""
        return [
            {
                "trigger": "/write",
                "description": "Generate creative text",
                "example": "/write a short story about a robot"
            },
            {
                "trigger": "/summarize",
                "description": "Summarize text",
                "example": "/summarize this article: ..."
            },
            {
                "trigger": "/paraphrase",
                "description": "Paraphrase text",
                "example": "/paraphrase rewrite this in simpler terms"
            },
            {
                "trigger": "/translate",
                "description": "Translate text",
                "example": "/translate to Spanish: Hello"
            }
        ]
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get text generation module tools"""
        return [
            {
                "name": "creative_writing",
                "description": "Generate creative content",
                "parameters": ["genre", "length", "style", "topic"]
            },
            {
                "name": "text_summarization",
                "description": "Summarize long text",
                "parameters": ["text", "max_length"]
            },
            {
                "name": "text_paraphrasing",
                "description": "Paraphrase text",
                "parameters": ["text", "style"]
            },
            {
                "name": "translation",
                "description": "Translate text between languages",
                "parameters": ["text", "target_language", "source_language"]
            }
        ]

