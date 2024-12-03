from functools import lru_cache
from typing import Tuple, Optional
import time
import redis
import logging
from concurrent.futures import ThreadPoolExecutor
from model import call_groq_api

@lru_cache(maxsize=128)
def get_redis_data(r: redis.Redis, pattern: str, batch_size: int = 100) -> list:
    """Efficiently retrieve Redis data using pipelining"""
    results = []
    cursor = "0"
    
    while cursor != 0:
        try:
            cursor, keys = r.scan(cursor=cursor, match=pattern, count=batch_size)
            if not keys:
                continue
                
            with r.pipeline(transaction=False) as pipe:
                for key in keys:
                    pipe.get(key)
                values = pipe.execute()
                
                results.extend(
                    (key.decode('utf-8'), value.decode('utf-8'))
                    for key, value in zip(keys, values)
                    if value is not None
                )
                
        except redis.RedisError as e:
            logging.error(f"Redis error during scan/get: {e}")
            break
            
    return results

class Timer:
    """Precise timing context manager"""
    __slots__ = ('start', 'duration_ms')
    
    def __init__(self):
        self.duration_ms = 0
        self.start = 0

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.duration_ms = round((time.perf_counter() - self.start) * 1000, 2)

async def get_relative_info(
    question: str,
    r: redis.Redis,
    personality: str,
    max_retries: int = 3,
    batch_size: int = 100
) -> Tuple[str, float, float]:
    """
    Optimized function to retrieve relevant information from Redis based on question category.
    
    Args:
        question: User's question
        r: Redis client instance
        personality: Chatbot personality prefix
        max_retries: Maximum number of Redis operation retries
        batch_size: Number of keys to process in each batch
    
    Returns:
        Tuple containing:
        - Retrieved information string
        - Category identification time (ms)
        - Data retrieval time (ms)
    """
    # Input validation
    if not all([question, r, personality]):
        logging.warning("Missing required parameters")
        return "", 0, 0

    # Category identification with timing
    with Timer() as cit_timer:
        try:
            category = categorize_question(question)
        except Exception as e:
            logging.error(f"Category identification failed: {e}")
            return "", 0, 0

    if category == "no":
        return "", cit_timer.duration_ms, 0

    # Data retrieval with timing
    with Timer() as drt_timer:
        pattern = f"{personality}:{category}:*"
        retry_count = 0
        results = []

        while retry_count < max_retries:
            try:
                results = get_redis_data(r, pattern, batch_size)
                break
            except redis.RedisError as e:
                retry_count += 1
                if retry_count == max_retries:
                    logging.error(f"Max retries reached. Redis error: {e}")
                    return "", cit_timer.duration_ms, 0
                time.sleep(0.1 * retry_count)  # Exponential backoff

        # Format results efficiently
        response = "\n".join(f"{key} - {value}" for key, value in results)

    return response, cit_timer.duration_ms, drt_timer.duration_ms

# Configuration constants
REDIS_CONFIG = {
    'socket_timeout': 5,
    'socket_connect_timeout': 5,
    'retry_on_timeout': True,
    'max_connections': 10
}

_all_ = [
    "get_relative_info"
]
