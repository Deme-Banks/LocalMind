"""
Streaming Enhancer - improves streaming performance and adds visualization
"""

import time
from typing import AsyncIterator, Dict, Any, Optional
from collections import deque
import logging

logger = logging.getLogger(__name__)


class StreamingEnhancer:
    """Enhances streaming with performance metrics and visualization"""
    
    def __init__(self):
        """Initialize streaming enhancer"""
        self.metrics = {
            "tokens_per_second": 0.0,
            "average_latency": 0.0,
            "total_tokens": 0,
            "chunks_received": 0
        }
        self.latency_history = deque(maxlen=100)  # Keep last 100 latencies
    
    def enhance_stream(
        self, 
        stream: AsyncIterator[str],
        include_metrics: bool = True,
        chunk_size: int = 1
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Enhance a stream with metrics and metadata
        
        Args:
            stream: Original token stream
            include_metrics: Whether to include performance metrics
            chunk_size: Number of tokens per chunk
            
        Yields:
            Enhanced chunks with metadata
        """
        start_time = time.time()
        last_chunk_time = start_time
        token_count = 0
        chunk_buffer = []
        
        async for token in stream:
            current_time = time.time()
            chunk_latency = current_time - last_chunk_time
            self.latency_history.append(chunk_latency)
            
            token_count += 1
            chunk_buffer.append(token)
            
            # Calculate metrics
            elapsed = current_time - start_time
            if elapsed > 0:
                tokens_per_second = token_count / elapsed
                self.metrics["tokens_per_second"] = tokens_per_second
                self.metrics["total_tokens"] = token_count
                self.metrics["chunks_received"] += 1
            
            if len(self.latency_history) > 0:
                self.metrics["average_latency"] = sum(self.latency_history) / len(self.latency_history)
            
            # Yield chunk with metadata
            chunk_data = {
                "token": token,
                "chunk": "".join(chunk_buffer) if len(chunk_buffer) >= chunk_size else None,
                "timestamp": current_time
            }
            
            if include_metrics:
                chunk_data["metrics"] = {
                    "tokens_per_second": self.metrics["tokens_per_second"],
                    "total_tokens": token_count,
                    "elapsed_time": elapsed,
                    "average_latency": self.metrics["average_latency"]
                }
            
            # Clear buffer if chunk is complete
            if len(chunk_buffer) >= chunk_size:
                chunk_buffer = []
            
            yield chunk_data
            
            last_chunk_time = current_time
        
        # Final metrics
        total_time = time.time() - start_time
        final_metrics = {
            "tokens_per_second": token_count / total_time if total_time > 0 else 0,
            "total_tokens": token_count,
            "total_time": total_time,
            "average_latency": self.metrics["average_latency"]
        }
        
        yield {
            "done": True,
            "metrics": final_metrics
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current streaming metrics"""
        return self.metrics.copy()
    
    def reset_metrics(self):
        """Reset streaming metrics"""
        self.metrics = {
            "tokens_per_second": 0.0,
            "average_latency": 0.0,
            "total_tokens": 0,
            "chunks_received": 0
        }
        self.latency_history.clear()


class TokenVisualizer:
    """Visualizes token streaming"""
    
    @staticmethod
    def format_token_stream(tokens: list[str], highlight_new: bool = True) -> str:
        """
        Format tokens for visualization
        
        Args:
            tokens: List of tokens
            highlight_new: Whether to highlight newly added tokens
            
        Returns:
            Formatted HTML string
        """
        if not tokens:
            return ""
        
        if highlight_new:
            # Highlight the last token
            formatted = "".join(tokens[:-1]) + f'<span class="token-new">{tokens[-1]}</span>'
        else:
            formatted = "".join(tokens)
        
        return formatted
    
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Estimate token count (rough approximation)
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        # Rough approximation: ~4 characters per token
        return len(text) // 4
    
    @staticmethod
    def calculate_progress(current_tokens: int, estimated_total: Optional[int] = None) -> float:
        """
        Calculate streaming progress
        
        Args:
            current_tokens: Current token count
            estimated_total: Estimated total tokens (optional)
            
        Returns:
            Progress percentage (0-100)
        """
        if estimated_total and estimated_total > 0:
            return min(100.0, (current_tokens / estimated_total) * 100)
        return 0.0

