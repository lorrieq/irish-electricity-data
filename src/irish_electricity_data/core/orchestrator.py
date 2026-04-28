import datetime as dt
import random
import time
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass

import httpx

from .constants import (
    DEFAULT_BACKOFF_BASE_SECONDS,
    DEFAULT_BACKOFF_MAX_SECONDS,
    DEFAULT_MAX_RETRIES,
)
from .exceptions import ProviderRateLimited, ProviderTimeout


@dataclass(frozen=True)
class RetryPolicy:
    max_retries: int = DEFAULT_MAX_RETRIES
    base_seconds: float = DEFAULT_BACKOFF_BASE_SECONDS
    max_seconds: float = DEFAULT_BACKOFF_MAX_SECONDS
    jitter: float = 0.25


def _backoff_delay(attempt: int, policy: RetryPolicy) -> float:
    exp = min(policy.max_seconds, policy.base_seconds * (2**attempt))
    jittered = exp * (1.0 + random.uniform(-policy.jitter, policy.jitter))
    return max(0.0, jittered)


def with_retries[T](
    fn: Callable[[], T],
    *,
    policy: RetryPolicy | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Invoke `fn` with jittered exponential backoff on transient upstream failures.

    Retries on httpx transport errors, 429, and 5xx. Non-retryable errors propagate.
    """
    if policy is None:
        policy = RetryPolicy()
    last_exc: Exception | None = None
    for attempt in range(policy.max_retries + 1):
        try:
            return fn()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 429:
                last_exc = ProviderRateLimited(str(exc))
            elif 500 <= status < 600:
                last_exc = exc
            else:
                raise
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            last_exc = exc

        if attempt >= policy.max_retries:
            break
        sleep(_backoff_delay(attempt, policy))

    if isinstance(last_exc, ProviderRateLimited):
        raise last_exc
    raise ProviderTimeout("upstream exhausted retry budget") from last_exc


def month_chunks(start: dt.date, end: dt.date) -> Iterator[tuple[dt.date, dt.date]]:
    """Split `[start, end]` (inclusive) into calendar-month ranges.

    Used by the chunking engine so a multi-year user request becomes N manageable fetches.
    """
    if end < start:
        raise ValueError("end must be on or after start")

    cursor = start
    while cursor <= end:
        if cursor.month == 12:
            next_month = dt.date(cursor.year + 1, 1, 1)
        else:
            next_month = dt.date(cursor.year, cursor.month + 1, 1)
        chunk_end = min(end, next_month - dt.timedelta(days=1))
        yield cursor, chunk_end
        cursor = chunk_end + dt.timedelta(days=1)


def iter_chunks[T](
    start: dt.date,
    end: dt.date,
    fetch: Callable[[dt.date, dt.date], Iterable[T]],
) -> Iterator[T]:
    """Apply `fetch` to each monthly chunk and flatten the results."""
    for chunk_start, chunk_end in month_chunks(start, end):
        yield from fetch(chunk_start, chunk_end)
