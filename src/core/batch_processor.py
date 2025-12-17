"""
Batch Processor - handles async request batching for API backends
"""

from typing import List, Dict, Any, Optional, Callable
import asyncio
import aiohttp
from dataclasses import dataclass
import logging
import time

logger = logging.getLogger(__name__)


@dataclass
class BatchRequest:
    """Represents a request in a batch"""
    id: str
    prompt: str
    model: str
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class BatchResponse:
    """Response from a batch request"""
    id: str
    text: str
    model: str
    metadata: Dict[str, Any]
    success: bool = True
    error: Optional[str] = None


class BatchProcessor:
    """Processes multiple requests in batches for efficiency"""
    
    def __init__(self, max_batch_size: int = 10, max_wait_time: float = 0.1):
        """
        Initialize batch processor
        
        Args:
            max_batch_size: Maximum number of requests per batch
            max_wait_time: Maximum time to wait before processing a batch (seconds)
        """
        self.max_batch_size = max_batch_size
        self.max_wait_time = max_wait_time
        self.pending_requests: List[BatchRequest] = []
        self.batch_lock = asyncio.Lock()
        self.batch_timer: Optional[asyncio.Task] = None
    
    async def add_request(
        self,
        request: BatchRequest,
        processor_func: Callable[[List[BatchRequest]], List[BatchResponse]]
    ) -> BatchResponse:
        """
        Add a request to the batch and process when ready
        
        Args:
            request: Batch request to add
            processor_func: Async function to process a batch of requests
        
        Returns:
            BatchResponse for this request
        """
        async with self.batch_lock:
            self.pending_requests.append(request)
            
            # If batch is full, process immediately
            if len(self.pending_requests) >= self.max_batch_size:
                return await self._process_batch(processor_func)
            
            # Otherwise, start/restart timer
            if self.batch_timer is None or self.batch_timer.done():
                self.batch_timer = asyncio.create_task(self._wait_and_process(processor_func))
            
            # Wait for this request to be processed
            return await self._wait_for_request(request.id, processor_func)
    
    async def _wait_and_process(self, processor_func: Callable):
        """Wait for max_wait_time then process batch"""
        await asyncio.sleep(self.max_wait_time)
        async with self.batch_lock:
            if self.pending_requests:
                await self._process_batch(processor_func)
    
    async def _process_batch(
        self,
        processor_func: Callable[[List[BatchRequest]], List[BatchResponse]]
    ) -> BatchResponse:
        """Process current batch of requests"""
        if not self.pending_requests:
            return None
        
        batch = self.pending_requests.copy()
        self.pending_requests.clear()
        
        # Cancel timer if running
        if self.batch_timer and not self.batch_timer.done():
            self.batch_timer.cancel()
        self.batch_timer = None
        
        # Process batch
        try:
            responses = await processor_func(batch)
            # Return first response (for single request case)
            return responses[0] if responses else None
        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            # Return error response for first request
            if batch:
                return BatchResponse(
                    id=batch[0].id,
                    text="",
                    model=batch[0].model,
                    metadata={},
                    success=False,
                    error=str(e)
                )
            return None
    
    async def _wait_for_request(
        self,
        request_id: str,
        processor_func: Callable
    ) -> BatchResponse:
        """Wait for a specific request to be processed"""
        # Simple implementation: process immediately if only one request
        # In a more sophisticated implementation, we'd use futures/events
        await asyncio.sleep(self.max_wait_time)
        async with self.batch_lock:
            if self.pending_requests:
                return await self._process_batch(processor_func)
        
        # Fallback: process single request
        request = next((r for r in self.pending_requests if r.id == request_id), None)
        if request:
            return await self._process_batch(processor_func)
        
        return BatchResponse(
            id=request_id,
            text="",
            model="",
            metadata={},
            success=False,
            error="Request not found in batch"
        )
    
    async def process_batch_async(
        self,
        requests: List[BatchRequest],
        processor_func: Callable[[List[BatchRequest]], List[BatchResponse]]
    ) -> List[BatchResponse]:
        """
        Process a batch of requests asynchronously
        
        Args:
            requests: List of batch requests
            processor_func: Async function to process requests
        
        Returns:
            List of batch responses
        """
        if not requests:
            return []
        
        # Process in parallel batches
        tasks = []
        for i in range(0, len(requests), self.max_batch_size):
            batch = requests[i:i + self.max_batch_size]
            tasks.append(processor_func(batch))
        
        # Wait for all batches
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten results
        responses = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch processing error: {result}")
                continue
            if isinstance(result, list):
                responses.extend(result)
            else:
                responses.append(result)
        
        return responses


class AsyncRequestBatcher:
    """Simpler async request batcher for API backends"""
    
    def __init__(self, batch_size: int = 5, batch_delay: float = 0.05):
        """
        Initialize async request batcher
        
        Args:
            batch_size: Number of requests to batch together
            batch_delay: Delay before processing batch (seconds)
        """
        self.batch_size = batch_size
        self.batch_delay = batch_delay
    
    async def batch_requests(
        self,
        requests: List[Dict[str, Any]],
        process_func: Callable[[List[Dict]], List[Any]]
    ) -> List[Any]:
        """
        Batch and process requests asynchronously
        
        Args:
            requests: List of request dictionaries
            process_func: Async function to process a batch
        
        Returns:
            List of responses
        """
        if not requests:
            return []
        
        # Split into batches
        batches = [
            requests[i:i + self.batch_size]
            for i in range(0, len(requests), self.batch_size)
        ]
        
        # Process batches concurrently
        tasks = [process_func(batch) for batch in batches]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten and handle errors
        responses = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch error: {result}")
                continue
            if isinstance(result, list):
                responses.extend(result)
            else:
                responses.append(result)
        
        return responses

