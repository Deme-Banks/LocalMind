"""
Response Quality Scorer - evaluates AI response quality
"""

import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class QualityScore:
    """Response quality score"""
    overall: float  # 0.0 to 1.0
    coherence: float  # Logical flow and consistency
    relevance: float  # Relevance to prompt
    completeness: float  # How complete the answer is
    clarity: float  # How clear and understandable
    length_appropriateness: float  # Appropriate length for the question
    metrics: Dict[str, Any]  # Additional metrics


class ResponseQualityScorer:
    """Scores AI response quality"""
    
    def __init__(self):
        """Initialize quality scorer"""
        self.min_length = 10  # Minimum reasonable response length
        self.max_length_ratio = 10  # Max response should be 10x prompt length
    
    def score(
        self,
        response: str,
        prompt: str,
        context: Optional[List[str]] = None
    ) -> QualityScore:
        """
        Score response quality
        
        Args:
            response: AI-generated response
            prompt: Original user prompt
            context: Optional conversation context
            
        Returns:
            QualityScore object with various metrics
        """
        # Basic metrics
        response_length = len(response)
        prompt_length = len(prompt)
        
        # Calculate individual scores
        coherence = self._score_coherence(response)
        relevance = self._score_relevance(response, prompt, context)
        completeness = self._score_completeness(response, prompt)
        clarity = self._score_clarity(response)
        length_appropriateness = self._score_length_appropriateness(
            response_length, prompt_length
        )
        
        # Calculate overall score (weighted average)
        overall = (
            coherence * 0.25 +
            relevance * 0.30 +
            completeness * 0.20 +
            clarity * 0.15 +
            length_appropriateness * 0.10
        )
        
        # Additional metrics
        metrics = {
            "response_length": response_length,
            "prompt_length": prompt_length,
            "word_count": len(response.split()),
            "sentence_count": len(re.split(r'[.!?]+', response)),
            "has_code_blocks": bool(re.search(r'```', response)),
            "has_markdown": bool(re.search(r'[#*_`]', response)),
            "has_links": bool(re.search(r'http[s]?://', response)),
            "has_lists": bool(re.search(r'^\s*[-*+]\s', response, re.MULTILINE)),
        }
        
        return QualityScore(
            overall=round(overall, 3),
            coherence=round(coherence, 3),
            relevance=round(relevance, 3),
            completeness=round(completeness, 3),
            clarity=round(clarity, 3),
            length_appropriateness=round(length_appropriateness, 3),
            metrics=metrics
        )
    
    def _score_coherence(self, response: str) -> float:
        """Score response coherence (logical flow)"""
        if not response or len(response) < self.min_length:
            return 0.0
        
        # Check for repeated phrases (bad coherence)
        words = response.lower().split()
        if len(words) < 3:
            return 0.5
        
        # Check for sentence structure
        sentences = re.split(r'[.!?]+', response)
        valid_sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
        
        if len(valid_sentences) < 1:
            return 0.3
        
        # Check for transition words (good coherence)
        transition_words = [
            'however', 'therefore', 'furthermore', 'moreover', 'additionally',
            'consequently', 'thus', 'hence', 'meanwhile', 'subsequently'
        ]
        has_transitions = any(word in response.lower() for word in transition_words)
        
        # Base score
        score = 0.7
        
        # Bonus for transitions
        if has_transitions:
            score += 0.1
        
        # Penalty for too many repeated words
        word_freq = {}
        for word in words[:50]:  # Check first 50 words
            word_freq[word] = word_freq.get(word, 0) + 1
        
        max_repeats = max(word_freq.values()) if word_freq else 1
        if max_repeats > 5:
            score -= 0.2
        
        return min(1.0, max(0.0, score))
    
    def _score_relevance(self, response: str, prompt: str, context: Optional[List[str]] = None) -> float:
        """Score response relevance to prompt"""
        if not response or not prompt:
            return 0.0
        
        # Extract key terms from prompt
        prompt_lower = prompt.lower()
        response_lower = response.lower()
        
        # Simple keyword matching
        prompt_words = set(re.findall(r'\b\w{4,}\b', prompt_lower))  # Words 4+ chars
        response_words = set(re.findall(r'\b\w{4,}\b', response_lower))
        
        if not prompt_words:
            return 0.5  # Can't determine relevance
        
        # Calculate overlap
        overlap = len(prompt_words & response_words)
        relevance_ratio = overlap / len(prompt_words)
        
        # Base score
        score = min(1.0, relevance_ratio * 1.2)  # Allow slight over-relevance
        
        # Check for direct question answering
        question_words = ['what', 'how', 'why', 'when', 'where', 'who', 'which']
        is_question = any(prompt_lower.startswith(q) for q in question_words)
        
        if is_question:
            # Check if response seems to answer the question
            if any(word in response_lower[:100] for word in ['because', 'is', 'are', 'can', 'will']):
                score = min(1.0, score + 0.1)
        
        return min(1.0, max(0.0, score))
    
    def _score_completeness(self, response: str, prompt: str) -> float:
        """Score how complete the answer is"""
        if not response:
            return 0.0
        
        # Check for incomplete sentences
        incomplete_indicators = [
            '...', 'etc.', 'and so on', 'and more', 'see above'
        ]
        has_incomplete = any(indicator in response.lower() for indicator in incomplete_indicators)
        
        # Base score based on length
        response_length = len(response)
        if response_length < 20:
            base_score = 0.3
        elif response_length < 50:
            base_score = 0.5
        elif response_length < 200:
            base_score = 0.7
        else:
            base_score = 0.9
        
        # Penalty for incomplete indicators
        if has_incomplete:
            base_score -= 0.1
        
        # Check for question answering completeness
        question_words = ['what', 'how', 'why', 'when', 'where', 'who']
        is_question = any(prompt.lower().startswith(q) for q in question_words)
        
        if is_question:
            # Check if response has multiple sentences (more complete)
            sentences = re.split(r'[.!?]+', response)
            valid_sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
            
            if len(valid_sentences) >= 2:
                base_score = min(1.0, base_score + 0.1)
        
        return min(1.0, max(0.0, base_score))
    
    def _score_clarity(self, response: str) -> float:
        """Score response clarity"""
        if not response:
            return 0.0
        
        # Check for proper sentence structure
        sentences = re.split(r'[.!?]+', response)
        valid_sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
        
        if not valid_sentences:
            return 0.2
        
        # Base score
        score = 0.6
        
        # Check for very long sentences (less clear)
        avg_sentence_length = sum(len(s) for s in valid_sentences) / len(valid_sentences)
        if avg_sentence_length > 150:
            score -= 0.2
        elif avg_sentence_length < 30:
            score += 0.1
        
        # Check for proper capitalization
        properly_capitalized = sum(1 for s in valid_sentences if s and s[0].isupper())
        capitalization_ratio = properly_capitalized / len(valid_sentences) if valid_sentences else 0
        score += capitalization_ratio * 0.2
        
        # Check for spelling/grammar indicators
        common_errors = ['teh', 'adn', 'taht', 'recieve', 'seperate']
        has_errors = any(error in response.lower() for error in common_errors)
        if has_errors:
            score -= 0.1
        
        return min(1.0, max(0.0, score))
    
    def _score_length_appropriateness(self, response_length: int, prompt_length: int) -> float:
        """Score if response length is appropriate for the prompt"""
        if response_length < self.min_length:
            return 0.2
        
        if prompt_length == 0:
            return 0.7  # Can't determine appropriateness
        
        # Calculate ratio
        ratio = response_length / prompt_length if prompt_length > 0 else response_length / 100
        
        # Ideal ratio is between 0.5 and 5.0
        if 0.5 <= ratio <= 5.0:
            return 1.0
        elif 0.2 <= ratio < 0.5 or 5.0 < ratio <= 10.0:
            return 0.7
        elif ratio < 0.2:
            return 0.4  # Too short
        else:
            return 0.3  # Too long
    
    def compare_responses(
        self,
        responses: List[tuple[str, str]],  # List of (response, prompt) tuples
        context: Optional[List[str]] = None
    ) -> List[tuple[str, QualityScore]]:
        """
        Compare multiple responses and return scores
        
        Args:
            responses: List of (response, prompt) tuples
            context: Optional conversation context
            
        Returns:
            List of (response, QualityScore) tuples sorted by overall score
        """
        scored = []
        for response, prompt in responses:
            score = self.score(response, prompt, context)
            scored.append((response, score))
        
        # Sort by overall score (descending)
        scored.sort(key=lambda x: x[1].overall, reverse=True)
        return scored

