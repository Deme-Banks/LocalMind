"""
Ensemble - combines responses from multiple models
"""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class EnsembleProcessor:
    """Processes and combines responses from multiple models"""
    
    def __init__(self):
        """Initialize ensemble processor"""
        pass
    
    def combine_responses(
        self,
        responses: List[Dict[str, Any]],
        method: str = "majority_vote"
    ) -> Dict[str, Any]:
        """
        Combine responses from multiple models
        
        Args:
            responses: List of response dictionaries with 'model', 'response', 'metadata'
            method: Combination method ('majority_vote', 'longest', 'shortest', 'average', 'first', 'best')
            
        Returns:
            Combined response dictionary
        """
        if not responses:
            return {
                "response": "",
                "models_used": [],
                "method": method,
                "metadata": {}
            }
        
        if len(responses) == 1:
            return {
                "response": responses[0].get("response", ""),
                "models_used": [responses[0].get("model", "unknown")],
                "method": method,
                "metadata": responses[0].get("metadata", {})
            }
        
        if method == "majority_vote":
            return self._majority_vote(responses)
        elif method == "longest":
            return self._longest_response(responses)
        elif method == "shortest":
            return self._shortest_response(responses)
        elif method == "average":
            return self._average_response(responses)
        elif method == "first":
            return self._first_response(responses)
        elif method == "best":
            return self._best_response(responses)
        elif method == "concatenate":
            return self._concatenate_responses(responses)
        else:
            logger.warning(f"Unknown ensemble method: {method}, using majority_vote")
            return self._majority_vote(responses)
    
    def _majority_vote(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use majority voting - find most common response pattern"""
        # For text responses, we'll use the longest response that appears most similar
        # This is a simplified approach - in practice, you'd want semantic similarity
        
        # Group similar responses (simple length-based grouping)
        response_groups = {}
        for resp in responses:
            text = resp.get("response", "").strip()
            length_bucket = len(text) // 100  # Group by ~100 char buckets
            if length_bucket not in response_groups:
                response_groups[length_bucket] = []
            response_groups[length_bucket].append(resp)
        
        # Find the largest group
        largest_group = max(response_groups.values(), key=len)
        
        # Use the longest response from the largest group
        best_response = max(largest_group, key=lambda r: len(r.get("response", "")))
        
        return {
            "response": best_response.get("response", ""),
            "models_used": [r.get("model", "unknown") for r in responses],
            "method": "majority_vote",
            "metadata": {
                "consensus_count": len(largest_group),
                "total_models": len(responses),
                "selected_model": best_response.get("model", "unknown")
            }
        }
    
    def _longest_response(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use the longest response"""
        longest = max(responses, key=lambda r: len(r.get("response", "")))
        return {
            "response": longest.get("response", ""),
            "models_used": [r.get("model", "unknown") for r in responses],
            "method": "longest",
            "metadata": {
                "selected_model": longest.get("model", "unknown"),
                "response_length": len(longest.get("response", ""))
            }
        }
    
    def _shortest_response(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use the shortest response"""
        shortest = min(responses, key=lambda r: len(r.get("response", "")))
        return {
            "response": shortest.get("response", ""),
            "models_used": [r.get("model", "unknown") for r in responses],
            "method": "shortest",
            "metadata": {
                "selected_model": shortest.get("model", "unknown"),
                "response_length": len(shortest.get("response", ""))
            }
        }
    
    def _average_response(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine responses by averaging (concatenate with separators)"""
        response_texts = [r.get("response", "").strip() for r in responses]
        
        # Combine with clear separators
        combined = "\n\n---\n\n".join([
            f"**{r.get('model', 'Unknown')}:**\n{text}"
            for r, text in zip(responses, response_texts)
        ])
        
        return {
            "response": combined,
            "models_used": [r.get("model", "unknown") for r in responses],
            "method": "average",
            "metadata": {
                "combined_count": len(responses)
            }
        }
    
    def _first_response(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use the first response"""
        first = responses[0]
        return {
            "response": first.get("response", ""),
            "models_used": [r.get("model", "unknown") for r in responses],
            "method": "first",
            "metadata": {
                "selected_model": first.get("model", "unknown")
            }
        }
    
    def _best_response(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select best response based on metrics (fastest with good quality)"""
        # Score based on response time and length (faster + longer = better)
        scored = []
        for resp in responses:
            response_time = resp.get("response_time", 999)
            response_length = len(resp.get("response", ""))
            # Lower time is better, higher length is better
            # Score = length / (time + 1) to avoid division by zero
            score = response_length / (response_time + 1)
            scored.append((score, resp))
        
        # Get highest scoring response
        best = max(scored, key=lambda x: x[0])[1]
        
        return {
            "response": best.get("response", ""),
            "models_used": [r.get("model", "unknown") for r in responses],
            "method": "best",
            "metadata": {
                "selected_model": best.get("model", "unknown"),
                "score": max(scored, key=lambda x: x[0])[0]
            }
        }
    
    def _concatenate_responses(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Concatenate all responses"""
        response_texts = []
        for resp in responses:
            model = resp.get("model", "Unknown")
            text = resp.get("response", "").strip()
            response_texts.append(f"## {model}\n\n{text}")
        
        combined = "\n\n---\n\n".join(response_texts)
        
        return {
            "response": combined,
            "models_used": [r.get("model", "unknown") for r in responses],
            "method": "concatenate",
            "metadata": {
                "combined_count": len(responses)
            }
        }

