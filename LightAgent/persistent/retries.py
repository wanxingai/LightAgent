"""Explicit, bounded retry decisions for host backend adapters.

An exception's message is never used to infer whether side effects occurred.
Adapters may opt in only when they know the failed dispatch is safe to repeat.
Timeouts, authentication errors, and unknown outcomes remain host decisions.
"""
from dataclasses import dataclass
import math
import random
import time

from ..backends import BackendError


class BackendFailure(BackendError):
    def __init__(self, message, *, category='transient', retryable=False,
                 safe_to_retry=False, retry_after=None):
        if category not in ('transient', 'rate_limit', 'unavailable', 'authentication',
                            'permission', 'invalid_request', 'cancelled', 'timeout', 'unknown'):
            raise ValueError('unsupported backend failure category')
        if type(retryable) is not bool or type(safe_to_retry) is not bool:
            raise ValueError('retry signals must be boolean')
        if retry_after is not None and (type(retry_after) not in (int, float)
                                      or not math.isfinite(retry_after) or retry_after < 0):
            raise ValueError('retry_after must be finite and nonnegative')
        super().__init__(message)
        self.category = category
        self.retryable = retryable
        self.safe_to_retry = safe_to_retry
        self.retry_after = retry_after

    def to_dict(self):
        return {'category': self.category, 'retryable': self.retryable,
                'safe_to_retry': self.safe_to_retry, 'retry_after': self.retry_after}


def classify_failure(exc):
    if isinstance(exc, BackendFailure):
        return exc
    category = 'permission' if isinstance(exc, PermissionError) else 'timeout' if isinstance(exc, TimeoutError) else 'unknown'
    return BackendFailure(type(exc).__name__, category=category)


@dataclass(frozen=True)
class RetryPolicy:
    max_retries: int = 2
    base_delay: float = 1
    max_delay: float = 60
    jitter: float = .2

    def __post_init__(self):
        if type(self.max_retries) is not int or not 0 <= self.max_retries <= 100:
            raise ValueError('max_retries must be an integer from 0 to 100')
        for name in ('base_delay', 'max_delay', 'jitter'):
            value = getattr(self, name)
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError(name+' must be finite and nonnegative')
        if self.base_delay <= 0 or self.max_delay < self.base_delay or self.jitter > 1:
            raise ValueError('invalid retry delay or jitter bounds')

    def delay(self, exc, retry_number, *, random_value=None):
        """Return a bounded delay, or None when a host decision is required."""
        if type(retry_number) is not int or retry_number < 1:
            raise ValueError('retry_number starts at 1')
        failure = classify_failure(exc)
        if (retry_number > self.max_retries or not failure.retryable or not failure.safe_to_retry
                or failure.category not in ('transient', 'rate_limit', 'unavailable')):
            return None
        if failure.retry_after is not None and failure.retry_after > self.max_delay:
            return None  # Never violate the server's minimum wait to fit our bound.
        value = random.random() if random_value is None else random_value
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError('random_value must be between 0 and 1')
        base = min(self.max_delay, self.base_delay * 2**(retry_number-1))
        delay = min(self.max_delay, base * (1 + self.jitter * (2*value-1)))
        return max(failure.retry_after or 0, delay)


def next_retry(exc, retry_number, policy=None, *, now=None, random_value=None):
    delay = (policy or RetryPolicy()).delay(exc, retry_number, random_value=random_value)
    return None if delay is None else (time.time() if now is None else now) + delay
