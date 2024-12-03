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


# Configuration constants
REDIS_CONFIG = {
    'socket_timeout': 5,
    'socket_connect_timeout': 5,
    'retry_on_timeout': True,
    'max_connections': 10
}

