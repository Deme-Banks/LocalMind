"""
A/B Testing - Compare responses from different models
"""

import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import logging

from .response_quality import ResponseQualityScorer, QualityScore
from .model_loader import ModelLoader

logger = logging.getLogger(__name__)


@dataclass
class ABTestResult:
    """Result of A/B test between models"""
    model_a: str
    model_b: str
    prompt: str
    response_a: str
    response_b: str
    score_a: QualityScore
    score_b: QualityScore
    winner: str  # 'a', 'b', or 'tie'
    performance_a: Dict[str, Any]  # Timing, tokens, etc.
    performance_b: Dict[str, Any]
    difference: float  # Score difference (a - b)


class ABTester:
    """A/B testing between models"""
    
    def __init__(self, model_loader: ModelLoader):
        """
        Initialize A/B tester
        
        Args:
            model_loader: Model loader instance
        """
        self.model_loader = model_loader
        self.quality_scorer = ResponseQualityScorer()
    
    async def test(
        self,
        prompt: str,
        model_a: str,
        model_b: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        context: Optional[List[str]] = None
    ) -> ABTestResult:
        """
        Run A/B test between two models
        
        Args:
            prompt: Test prompt
            model_a: First model to test
            model_b: Second model to test
            system_prompt: Optional system prompt
            temperature: Temperature setting
            context: Optional conversation context
            
        Returns:
            ABTestResult with comparison
        """
        # Generate responses from both models
        start_time_a = time.time()
        try:
            response_a_obj = await self._generate_response(
                prompt, model_a, system_prompt, temperature
            )
            response_a = response_a_obj.text
            time_a = time.time() - start_time_a
        except Exception as e:
            logger.error(f"Error generating response from {model_a}: {e}")
            response_a = f"Error: {str(e)}"
            time_a = 0.0
        
        start_time_b = time.time()
        try:
            response_b_obj = await self._generate_response(
                prompt, model_b, system_prompt, temperature
            )
            response_b = response_b_obj.text
            time_b = time.time() - start_time_b
        except Exception as e:
            logger.error(f"Error generating response from {model_b}: {e}")
            response_b = f"Error: {str(e)}"
            time_b = 0.0
        
        # Score both responses
        score_a = self.quality_scorer.score(response_a, prompt, context)
        score_b = self.quality_scorer.score(response_b, prompt, context)
        
        # Determine winner
        if score_a.overall > score_b.overall + 0.05:  # 5% threshold
            winner = 'a'
        elif score_b.overall > score_a.overall + 0.05:
            winner = 'b'
        else:
            winner = 'tie'
        
        # Performance metrics
        performance_a = {
            "response_time": round(time_a, 3),
            "tokens": len(response_a.split()) if response_a else 0,
            "characters": len(response_a) if response_a else 0
        }
        
        performance_b = {
            "response_time": round(time_b, 3),
            "tokens": len(response_b.split()) if response_b else 0,
            "characters": len(response_b) if response_b else 0
        }
        
        return ABTestResult(
            model_a=model_a,
            model_b=model_b,
            prompt=prompt,
            response_a=response_a,
            response_b=response_b,
            score_a=score_a,
            score_b=score_b,
            winner=winner,
            performance_a=performance_a,
            performance_b=performance_b,
            difference=round(score_a.overall - score_b.overall, 3)
        )
    
    async def _generate_response(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str],
        temperature: float
    ):
        """Generate response from a model"""
        # Determine backend
        backend_name, backend_type = None, None
        for name, backend in self.model_loader.backends.items():
            try:
                if model in backend.list_models():
                    backend_name = name
                    backend_type = backend.get_backend_info().get("type", name)
                    break
            except Exception:
                continue
        
        if not backend_name:
            raise RuntimeError(f"Model {model} not found")
        
        backend = self.model_loader.backends[backend_name]
        
        # Generate response
        if hasattr(backend, 'generate'):
            response = backend.generate(
                prompt=prompt,
                model=model,
                system_prompt=system_prompt,
                temperature=temperature
            )
            return response
        else:
            raise RuntimeError(f"Backend {backend_name} does not support generation")
    
    def batch_test(
        self,
        prompts: List[str],
        model_a: str,
        model_b: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Run batch A/B test on multiple prompts
        
        Args:
            prompts: List of test prompts
            model_a: First model
            model_b: Second model
            system_prompt: Optional system prompt
            temperature: Temperature setting
            
        Returns:
            Summary statistics
        """
        import asyncio
        
        results = []
        for prompt in prompts:
            try:
                result = asyncio.run(self.test(
                    prompt, model_a, model_b, system_prompt, temperature
                ))
                results.append(result)
            except Exception as e:
                logger.error(f"Error in batch test for prompt: {e}")
        
        # Calculate statistics
        wins_a = sum(1 for r in results if r.winner == 'a')
        wins_b = sum(1 for r in results if r.winner == 'b')
        ties = sum(1 for r in results if r.winner == 'tie')
        
        avg_score_a = sum(r.score_a.overall for r in results) / len(results) if results else 0
        avg_score_b = sum(r.score_b.overall for r in results) / len(results) if results else 0
        
        avg_time_a = sum(r.performance_a['response_time'] for r in results) / len(results) if results else 0
        avg_time_b = sum(r.performance_b['response_time'] for r in results) / len(results) if results else 0
        
        return {
            "total_tests": len(results),
            "wins_a": wins_a,
            "wins_b": wins_b,
            "ties": ties,
            "avg_score_a": round(avg_score_a, 3),
            "avg_score_b": round(avg_score_b, 3),
            "avg_time_a": round(avg_time_a, 3),
            "avg_time_b": round(avg_time_b, 3),
            "results": results
        }

