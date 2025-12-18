"""
Model Router - routes requests to the best model based on task type
"""

from typing import Dict, List, Optional, Tuple
import re
import logging

logger = logging.getLogger(__name__)


class ModelRouter:
    """Routes requests to appropriate models based on task type"""
    
    def __init__(self):
        """Initialize model router"""
        # Task detection patterns
        self.task_patterns = {
            'code': [
                r'\b(code|programming|function|class|variable|syntax|debug|fix|error|bug|implement|algorithm|script|python|javascript|java|c\+\+|html|css|sql|api|endpoint)\b',
                r'```[\s\S]*?```',  # Code blocks
                r'def\s+\w+\s*\(',  # Function definitions
                r'function\s+\w+\s*\(',  # JS functions
                r'class\s+\w+',  # Class definitions
                r'import\s+\w+',  # Imports
                r'#include',  # C/C++ includes
            ],
            'writing': [
                r'\b(write|essay|article|blog|story|narrative|poem|letter|email|draft|compose|creative|fiction|non-fiction)\b',
                r'\b(paragraph|sentence|grammar|spelling|punctuation|style|tone|voice)\b',
            ],
            'analysis': [
                r'\b(analyze|analysis|explain|interpret|evaluate|assess|compare|contrast|examine|study|research|investigate)\b',
                r'\b(why|how|what|when|where|reason|cause|effect|consequence|implication)\b',
                r'\b(data|statistics|trend|pattern|insight|conclusion|finding)\b',
            ],
            'translation': [
                r'\b(translate|translation|language|english|spanish|french|german|chinese|japanese|korean|portuguese|italian)\b',
                r'\b(in\s+\w+\s+language|to\s+\w+|from\s+\w+)\b',
            ],
            'math': [
                r'\b(calculate|solve|equation|formula|math|mathematics|algebra|geometry|calculus|derivative|integral|matrix)\b',
                r'\b(\d+\s*[\+\-\*/]\s*\d+|\d+\s*=\s*\d+)',  # Math expressions
                r'\b(square|root|power|exponent|logarithm|trigonometry|sin|cos|tan)\b',
            ],
            'question': [
                r'\?',  # Question mark
                r'\b(what|who|where|when|why|how|which|can|could|should|would|is|are|do|does|did)\b',
            ],
            'summarization': [
                r'\b(summarize|summary|summarise|brief|overview|synopsis|abstract|condense|shorten)\b',
                r'\b(in\s+summary|to\s+summarize|key\s+points|main\s+points)\b',
            ],
            'creative': [
                r'\b(creative|imagine|story|poem|song|joke|humor|funny|entertaining|artistic|original|unique)\b',
                r'\b(make\s+up|invent|create|design|brainstorm|idea|concept)\b',
            ],
            'fast': [
                r'\b(quick|fast|urgent|asap|immediately|quickly|speed|hurry)\b',
            ],
        }
        
        # Model recommendations by task
        self.task_models = {
            'code': [
                'codellama', 'deepseek-coder', 'gpt-4', 'claude-3-opus',
                'gpt-4-turbo', 'claude-3-5-sonnet', 'mistral-large'
            ],
            'writing': [
                'llama3', 'mistral', 'gpt-3.5-turbo', 'claude-3-sonnet',
                'gpt-4', 'claude-3-5-sonnet', 'gemini-pro'
            ],
            'analysis': [
                'gpt-4', 'claude-3-opus', 'claude-3-5-sonnet', 'llama3',
                'mistral-large', 'gpt-4-turbo', 'gemini-1.5-pro'
            ],
            'translation': [
                'gpt-3.5-turbo', 'claude-3-haiku', 'mistral', 'llama3',
                'gemini-pro', 'gpt-4o-mini'
            ],
            'math': [
                'gpt-4', 'claude-3-opus', 'gpt-4-turbo', 'claude-3-5-sonnet',
                'gemini-1.5-pro', 'mistral-large'
            ],
            'question': [
                'gpt-3.5-turbo', 'claude-3-haiku', 'llama3', 'mistral',
                'gpt-4o-mini', 'gemini-1.5-flash'
            ],
            'summarization': [
                'claude-3-haiku', 'gpt-3.5-turbo', 'mistral', 'llama3',
                'gemini-1.5-flash', 'gpt-4o-mini'
            ],
            'creative': [
                'gpt-4', 'claude-3-opus', 'mistral-large', 'llama3',
                'gpt-4-turbo', 'claude-3-5-sonnet'
            ],
            'fast': [
                'groq', 'gpt-3.5-turbo', 'claude-3-haiku', 'mistral-tiny',
                'gpt-4o-mini', 'gemini-1.5-flash'
            ],
        }
        
        # Default fallback models
        self.default_models = [
            'gpt-3.5-turbo', 'llama3', 'mistral', 'claude-3-haiku'
        ]
    
    def detect_task_type(self, prompt: str) -> Tuple[str, float]:
        """
        Detect task type from prompt
        
        Args:
            prompt: User prompt text
            
        Returns:
            Tuple of (task_type, confidence_score)
        """
        prompt_lower = prompt.lower()
        scores = {}
        
        # Score each task type
        for task_type, patterns in self.task_patterns.items():
            score = 0.0
            for pattern in patterns:
                matches = len(re.findall(pattern, prompt_lower, re.IGNORECASE))
                if matches > 0:
                    score += matches * 0.1  # Weight by number of matches
                    # Boost score for code blocks
                    if '```' in pattern:
                        score += 0.5
            
            if score > 0:
                scores[task_type] = score
        
        if not scores:
            return 'general', 0.0
        
        # Get task with highest score
        best_task = max(scores.items(), key=lambda x: x[1])
        confidence = min(best_task[1], 1.0)  # Cap at 1.0
        
        return best_task[0], confidence
    
    def route_to_model(
        self,
        prompt: str,
        available_models: List[str],
        task_type: Optional[str] = None
    ) -> Tuple[Optional[str], str, float]:
        """
        Route prompt to best model
        
        Args:
            prompt: User prompt
            available_models: List of available model names
            task_type: Optional explicit task type (if None, will detect)
            
        Returns:
            Tuple of (recommended_model, detected_task, confidence)
        """
        # Detect task if not provided
        if task_type is None:
            task_type, confidence = self.detect_task_type(prompt)
        else:
            confidence = 0.8  # Higher confidence if explicitly provided
        
        # Get recommended models for this task
        recommended_models = self.task_models.get(task_type, [])
        
        # Find first available recommended model
        for model in recommended_models:
            if model in available_models:
                return model, task_type, confidence
        
        # Fallback to default models
        for model in self.default_models:
            if model in available_models:
                return model, task_type, confidence
        
        # Last resort: use first available model
        if available_models:
            return available_models[0], task_type, confidence
        
        return None, task_type, confidence
    
    def get_task_recommendations(
        self,
        task_type: str,
        available_models: List[str]
    ) -> List[str]:
        """
        Get list of recommended models for a task type
        
        Args:
            task_type: Task type
            available_models: List of available model names
            
        Returns:
            List of recommended models (filtered to available ones)
        """
        recommended = self.task_models.get(task_type, [])
        return [m for m in recommended if m in available_models]
    
    def get_all_task_types(self) -> List[str]:
        """Get list of all supported task types"""
        return list(self.task_patterns.keys())
    
    def select_best_default_model(
        self,
        available_models: List[str],
        preferences: Optional[Dict[str, any]] = None
    ) -> Optional[str]:
        """
        Select the best default model based on availability and preferences
        
        Args:
            available_models: List of available model names
            preferences: Optional user preferences (favorites, usage history, etc.)
            
        Returns:
            Recommended default model name
        """
        if not available_models:
            return None
        
        # Priority order for default selection
        priority_models = [
            # Fast, free local models first
            'llama3', 'mistral', 'llama3.1',
            # Good general purpose API models
            'gpt-3.5-turbo', 'claude-3-haiku', 'gpt-4o-mini',
            # Premium models
            'gpt-4', 'claude-3-opus', 'claude-3-5-sonnet',
            # Fast API models
            'groq', 'gemini-1.5-flash'
        ]
        
        # Check user preferences first
        if preferences:
            favorites = preferences.get('favorites', [])
            for fav in favorites:
                if fav in available_models:
                    return fav
            
            most_used = preferences.get('most_used', [])
            for model in most_used:
                if model in available_models:
                    return model
        
        # Try priority models
        for model in priority_models:
            if model in available_models:
                return model
        
        # Fallback to first available
        return available_models[0]
    
    def suggest_model_for_context(
        self,
        conversation_history: List[str],
        available_models: List[str],
        current_model: Optional[str] = None
    ) -> Tuple[Optional[str], str]:
        """
        Suggest model based on conversation context
        
        Args:
            conversation_history: List of recent messages
            available_models: List of available model names
            current_model: Current selected model
            
        Returns:
            Tuple of (suggested_model, reason)
        """
        if not conversation_history:
            return None, "No context"
        
        # Analyze recent messages for task type
        recent_text = " ".join(conversation_history[-5:])  # Last 5 messages
        
        # Detect task from conversation
        task_type, confidence = self.detect_task_type(recent_text)
        
        # If we already have a good model for this task, keep it
        if current_model:
            recommendations = self.get_task_recommendations(task_type, available_models)
            if current_model in recommendations[:3]:  # Top 3 recommendations
                return current_model, f"Current model is good for {task_type}"
        
        # Otherwise, suggest best model for detected task
        recommended, _, _ = self.route_to_model(
            prompt=recent_text,
            available_models=available_models,
            task_type=task_type
        )
        
        if recommended and recommended != current_model:
            return recommended, f"Better for {task_type} tasks"
        
        return None, "Current model is appropriate"

