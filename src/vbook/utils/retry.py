import time
from typing import Callable, TypeVar
from .logger import get_logger

logger = get_logger(__name__)
T = TypeVar("T")

def with_retry(fn: Callable[[], T], max_retries: int = 3, base_delay: float = 1.0) -> T:
    last_error = None
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = base_delay * (2 ** attempt)
                logger.warning(
                    "第 %d/%d 次重试失败: %s，%.1fs 后重试",
                    attempt + 1, max_retries, e, wait
                )
                time.sleep(wait)
    raise last_error