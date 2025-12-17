"""
Context Manager - handles context window management, summarization, and compression
"""

import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Represents a chat message"""
    role: str  # 'user' or 'assistant'
    content: str
    metadata: Optional[Dict[str, Any]] = None


class ContextManager:
    """Manages conversation context with window management and compression"""
    
    # Default context window sizes (in tokens, approximate)
    DEFAULT_CONTEXT_WINDOWS = {
        "gpt-3.5-turbo": 4096,
        "gpt-3.5-turbo-16k": 16384,
        "gpt-4": 8192,
        "gpt-4-turbo": 128000,
        "gpt-4o": 128000,
        "gpt-4o-mini": 128000,
        "claude-3-opus": 200000,
        "claude-3-sonnet": 200000,
        "claude-3-haiku": 200000,
        "claude-3-5-sonnet": 200000,
        "gemini-pro": 32768,
        "gemini-1.5-pro": 2000000,
        "gemini-1.5-flash": 1000000,
        "llama2": 4096,
        "llama3": 8192,
        "llama3.1": 128000,
        "mistral": 8192,
        "mixtral": 32768,
    }
    
    # Default to 4096 tokens if model not found
    DEFAULT_CONTEXT_WINDOW = 4096
    
    # Reserve tokens for system prompt and response
    RESERVED_TOKENS = 500
    
    def __init__(self, max_context_tokens: Optional[int] = None, 
                 summarization_threshold: float = 0.8,
                 compression_threshold: float = 0.9):
        """
        Initialize context manager
        
        Args:
            max_context_tokens: Maximum context window size (None = auto-detect from model)
            summarization_threshold: When to start summarization (0.8 = 80% of context used)
            compression_threshold: When to start compression (0.9 = 90% of context used)
        """
        self.max_context_tokens = max_context_tokens
        self.summarization_threshold = summarization_threshold
        self.compression_threshold = compression_threshold
        self.summaries: Dict[str, str] = {}  # Store summaries for compressed conversations
    
    def get_context_window(self, model: Optional[str] = None) -> int:
        """
        Get context window size for a model
        
        Args:
            model: Model name (e.g., "gpt-4", "llama3")
        
        Returns:
            Context window size in tokens
        """
        if self.max_context_tokens:
            return self.max_context_tokens
        
        if not model:
            return self.DEFAULT_CONTEXT_WINDOW
        
        # Try exact match first
        if model in self.DEFAULT_CONTEXT_WINDOWS:
            return self.DEFAULT_CONTEXT_WINDOWS[model]
        
        # Try partial match (e.g., "gpt-4-turbo-preview" matches "gpt-4-turbo")
        for model_key, window_size in self.DEFAULT_CONTEXT_WINDOWS.items():
            if model_key in model or model in model_key:
                return window_size
        
        # Default fallback
        return self.DEFAULT_CONTEXT_WINDOW
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text (rough approximation)
        
        Args:
            text: Text to estimate
        
        Returns:
            Estimated token count
        """
        # Rough approximation: 1 token ≈ 4 characters for English
        # This is a simple heuristic; actual tokenization varies by model
        return len(text) // 4
    
    def count_tokens(self, messages: List[Message]) -> int:
        """
        Count total tokens in messages
        
        Args:
            messages: List of messages
        
        Returns:
            Total token count
        """
        total = 0
        for msg in messages:
            # Add tokens for role and content
            total += self.estimate_tokens(f"{msg.role}: {msg.content}")
            # Add overhead for message structure (approximate)
            total += 4
        return total
    
    def build_context(self, messages: List[Message], model: Optional[str] = None,
                     system_prompt: Optional[str] = None) -> Tuple[List[Message], Dict[str, Any]]:
        """
        Build context from messages, applying compression/summarization if needed
        
        Args:
            messages: List of all messages in conversation
            model: Model name for context window detection
            system_prompt: Optional system prompt
        
        Returns:
            Tuple of (processed_messages, metadata)
        """
        context_window = self.get_context_window(model)
        available_tokens = context_window - self.RESERVED_TOKENS
        
        if system_prompt:
            available_tokens -= self.estimate_tokens(system_prompt)
        
        # Count current tokens
        current_tokens = self.count_tokens(messages)
        
        metadata = {
            "original_message_count": len(messages),
            "original_tokens": current_tokens,
            "context_window": context_window,
            "available_tokens": available_tokens,
            "compressed": False,
            "summarized": False
        }
        
        # If within limits, return as-is
        if current_tokens <= available_tokens:
            return messages, metadata
        
        # Need to compress/summarize
        logger.info(f"Context too large ({current_tokens} tokens, limit: {available_tokens}). Applying compression.")
        
        # Calculate how many messages we can keep
        # Keep recent messages (last N messages)
        # Compress/summarize older messages
        
        # Strategy: Keep recent messages, summarize older ones
        recent_messages = []
        old_messages = []
        
        # Start from the end and work backwards
        tokens_used = 0
        cutoff_index = len(messages)
        
        for i in range(len(messages) - 1, -1, -1):
            msg = messages[i]
            msg_tokens = self.estimate_tokens(f"{msg.role}: {msg.content}") + 4
            
            if tokens_used + msg_tokens <= available_tokens * self.compression_threshold:
                recent_messages.insert(0, msg)
                tokens_used += msg_tokens
            else:
                cutoff_index = i
                break
        
        # Get old messages to compress
        old_messages = messages[:cutoff_index]
        
        # Compress old messages
        if old_messages:
            compressed_summary = self.compress_messages(old_messages)
            summary_message = Message(
                role="system",
                content=f"[Previous conversation summary: {compressed_summary}]",
                metadata={"compressed": True, "original_count": len(old_messages)}
            )
            recent_messages.insert(0, summary_message)
            metadata["compressed"] = True
            metadata["compressed_message_count"] = len(old_messages)
            metadata["final_tokens"] = self.count_tokens(recent_messages)
        
        metadata["final_message_count"] = len(recent_messages)
        metadata["final_tokens"] = self.count_tokens(recent_messages)
        
        return recent_messages, metadata
    
    def compress_messages(self, messages: List[Message]) -> str:
        """
        Compress a list of messages into a summary
        
        Args:
            messages: List of messages to compress
        
        Returns:
            Compressed summary string
        """
        if not messages:
            return ""
        
        # Simple compression: extract key information
        # For better results, this could use an LLM to summarize, but for now we use heuristics
        
        user_messages = [msg.content for msg in messages if msg.role == "user"]
        assistant_messages = [msg.content for msg in messages if msg.role == "assistant"]
        
        # Create a summary
        summary_parts = []
        
        if user_messages:
            # Extract first and last user messages (often contain important context)
            if len(user_messages) > 2:
                summary_parts.append(f"User asked about: {user_messages[0][:200]}...")
                summary_parts.append(f"Last user message: {user_messages[-1][:200]}...")
            else:
                summary_parts.append(f"User messages: {'; '.join([m[:150] for m in user_messages])}")
        
        if assistant_messages:
            # Extract key points from assistant responses
            key_points = []
            for msg in assistant_messages[-3:]:  # Last 3 assistant messages
                # Extract sentences (simple heuristic)
                sentences = re.split(r'[.!?]\s+', msg)
                if sentences:
                    key_points.append(sentences[0][:100])  # First sentence of each
        
            if key_points:
                summary_parts.append(f"Key points discussed: {'; '.join(key_points)}")
        
        summary = " | ".join(summary_parts)
        
        # Limit summary length
        max_summary_tokens = 200
        if self.estimate_tokens(summary) > max_summary_tokens:
            summary = summary[:max_summary_tokens * 4] + "..."
        
        return summary
    
    def format_messages_for_backend(self, messages: List[Message], 
                                   backend_type: str = "ollama") -> Any:
        """
        Format messages for different backend types
        
        Args:
            messages: List of messages
            backend_type: Type of backend ("ollama", "openai", "anthropic", etc.)
        
        Returns:
            Formatted messages in backend-specific format
        """
        if backend_type in ["openai", "anthropic", "google", "mistral-ai", "cohere", "groq"]:
            # OpenAI-style format (list of dicts with role and content)
            formatted = []
            for msg in messages:
                if msg.role == "system":
                    # Some backends handle system messages differently
                    formatted.append({
                        "role": "system",
                        "content": msg.content
                    })
                else:
                    formatted.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            return formatted
        else:
            # Ollama-style format (single prompt string)
            # Build a conversation-style prompt
            lines = []
            for msg in messages:
                if msg.role == "system":
                    lines.append(f"System: {msg.content}")
                elif msg.role == "user":
                    lines.append(f"User: {msg.content}")
                elif msg.role == "assistant":
                    lines.append(f"Assistant: {msg.content}")
            
            lines.append("User:")  # Ready for next user input
            return "\n".join(lines)
    
    def get_conversation_history(self, conversation_messages: List[Dict[str, Any]]) -> List[Message]:
        """
        Convert conversation messages from storage format to Message objects
        
        Args:
            conversation_messages: List of message dicts from conversation manager
        
        Returns:
            List of Message objects
        """
        messages = []
        for msg_dict in conversation_messages:
            messages.append(Message(
                role=msg_dict.get("role", "user"),
                content=msg_dict.get("content", ""),
                metadata=msg_dict.get("metadata", {})
            ))
        return messages

