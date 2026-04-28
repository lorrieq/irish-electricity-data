from __future__ import annotations

import httpx

from .constants import DEFAULT_TIMEOUT_SECONDS

_DEFAULT_USER_AGENT = "irish-electricity-data/0.1 (+https://github.com/)"


def build_client(
    *,
    base_url: str = "",
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    user_agent: str = _DEFAULT_USER_AGENT,
    http2: bool = True,
    headers: dict[str, str] | None = None,
) -> httpx.Client:
    """Return a configured httpx.Client with sensible defaults for SEM upstreams.

    Sync today; the same seam can grow an AsyncClient variant without churn at call sites.
    """
    merged_headers = {"User-Agent": user_agent, "Accept": "*/*"}
    if headers:
        merged_headers.update(headers)

    return httpx.Client(
        base_url=base_url,
        timeout=httpx.Timeout(timeout),
        http2=http2,
        headers=merged_headers,
        follow_redirects=True,
    )
