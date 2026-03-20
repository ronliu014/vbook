import time
from typing import Callable, TypeVar

T = TypeVar("T")

def with_retry(fn: Callable[[], T], max_retries: int = 3, base_delay: float = 1.0) -> T:
    last_error = None
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(base_delay * (2 ** attempt))
    raise last_error