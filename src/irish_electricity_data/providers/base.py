from __future__ import annotations

from enum import StrEnum
from typing import Any, ClassVar

import httpx

from ..core.orchestrator import RetryPolicy, with_retries
from ..core.transport import build_client


class ProviderCapability(StrEnum):
    AUCTION_RESULTS = "AUCTION_RESULTS"
    MARKET_RESULTS = "MARKET_RESULTS"
    GENERATION = "GENERATION"
    DEMAND = "DEMAND"
    WIND = "WIND"
    SOLAR = "SOLAR"
    INTERCONNECTOR = "INTERCONNECTOR"


class BaseProvider:
    """Abstract provider. Subclasses declare `name`, `base_url`, and `capabilities`.

    Provides retry-wrapped primitives for GETting JSON or raw bytes.
    """

    name: ClassVar[str] = ""
    base_url: ClassVar[str] = ""
    capabilities: ClassVar[frozenset[ProviderCapability]] = frozenset()

    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        if not self.name or not self.base_url:
            raise TypeError(f"{type(self).__name__} must set `name` and `base_url`.")
        self._owns_client = client is None
        self._client = client or build_client(base_url=self.base_url)
        self._retry = retry_policy or RetryPolicy()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> BaseProvider:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def supports(self, capability: ProviderCapability) -> bool:
        return capability in self.capabilities

    def _get_bytes(self, path: str, *, params: Any | None = None) -> bytes:
        def call() -> bytes:
            response = self._client.get(path, params=params)
            response.raise_for_status()
            return response.content

        return with_retries(call, policy=self._retry)

    def _get_json(self, path: str, *, params: Any | None = None) -> dict | list:
        import json

        return json.loads(self._get_bytes(path, params=params))

    def _get_text(self, path: str, *, params: Any | None = None) -> str:
        return self._get_bytes(path, params=params).decode("utf-8")
