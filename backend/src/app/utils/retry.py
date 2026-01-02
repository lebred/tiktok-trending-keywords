"""
Retry utility for handling transient failures.
"""

import asyncio
import logging
from typing import Callable, TypeVar, Optional
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


async def retry_async(
    func: Callable[..., T],
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    *args,
    **kwargs
) -> T:
    """
    Retry an async function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts (seconds)
        backoff: Multiplier for delay after each attempt
        exceptions: Tuple of exceptions to catch and retry
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func
        
    Returns:
        Result of func
        
    Raises:
        Last exception if all attempts fail
    """
    last_exception = None
    current_delay = delay
    
    for attempt in range(1, max_attempts + 1):
        try:
            return await func(*args, **kwargs)
        except exceptions as e:
            last_exception = e
            if attempt < max_attempts:
                logger.warning(
                    f"Attempt {attempt}/{max_attempts} failed: {e}. "
                    f"Retrying in {current_delay:.2f}s..."
                )
                await asyncio.sleep(current_delay)
                current_delay *= backoff
            else:
                logger.error(f"All {max_attempts} attempts failed. Last error: {e}")
    
    raise last_exception


def retry_sync(
    func: Callable[..., T],
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    *args,
    **kwargs
) -> T:
    """
    Retry a synchronous function with exponential backoff.
    
    Args:
        func: Function to retry
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts (seconds)
        backoff: Multiplier for delay after each attempt
        exceptions: Tuple of exceptions to catch and retry
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func
        
    Returns:
        Result of func
        
    Raises:
        Last exception if all attempts fail
    """
    import time
    
    last_exception = None
    current_delay = delay
    
    for attempt in range(1, max_attempts + 1):
        try:
            return func(*args, **kwargs)
        except exceptions as e:
            last_exception = e
            if attempt < max_attempts:
                logger.warning(
                    f"Attempt {attempt}/{max_attempts} failed: {e}. "
                    f"Retrying in {current_delay:.2f}s..."
                )
                time.sleep(current_delay)
                current_delay *= backoff
            else:
                logger.error(f"All {max_attempts} attempts failed. Last error: {e}")
    
    raise last_exception

