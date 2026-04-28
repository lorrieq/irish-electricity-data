from __future__ import annotations

from .core.orchestrator import RetryPolicy
from .providers.eirgrid import EirGridProvider
from .providers.semo import SemoProvider
from .providers.semopx import SemopxProvider


class MarketClient:
    """Facade over the per-market providers (SEMO, SEMOpx, EirGrid).

    Providers are lazily constructed so that importing the client is cheap and
    misconfigured providers don't fail until used.
    """

    def __init__(self, *, retry_policy: RetryPolicy | None = None) -> None:
        self._retry_policy = retry_policy or RetryPolicy()
        self._semo: SemoProvider | None = None
        self._semopx: SemopxProvider | None = None
        self._eirgrid: EirGridProvider | None = None

    @property
    def semo(self) -> SemoProvider:
        if self._semo is None:
            self._semo = SemoProvider(retry_policy=self._retry_policy)
        return self._semo

    @property
    def semopx(self) -> SemopxProvider:
        if self._semopx is None:
            self._semopx = SemopxProvider(retry_policy=self._retry_policy)
        return self._semopx

    @property
    def eirgrid(self) -> EirGridProvider:
        if self._eirgrid is None:
            self._eirgrid = EirGridProvider(retry_policy=self._retry_policy)
        return self._eirgrid

    def close(self) -> None:
        for provider in (self._semo, self._semopx, self._eirgrid):
            if provider is not None:
                provider.close()

    def __enter__(self) -> MarketClient:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
