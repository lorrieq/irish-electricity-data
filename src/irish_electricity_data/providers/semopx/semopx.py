from __future__ import annotations

import datetime as dt
import logging
from typing import Any

from ...core.exceptions import ProviderError, ReportNotFoundError
from ...schema.models import Auction, ReportReference
from ..base import BaseProvider
from .models import MarketResult
from .parsers import parse_market_result, parse_report_list

_log = logging.getLogger(__name__)

_SEMOPX_AUCTION_ID: dict[Auction, str] = {
    Auction.DAY_AHEAD: "SEM-DA",
    Auction.IDA1: "SEM-IDA1",
    Auction.IDA2: "SEM-IDA2",
    Auction.IDA3: "SEM-IDA3",
}


class SemopxProvider(BaseProvider):
    """SEMOpx market-reports provider (reports.semopx.com).

    Exposes paginated report discovery and high-level market-result parsing.
    """

    name = "semopx"
    base_url = "https://reports.semopx.com"

    def list_reports(
        self,
        *,
        date_from: dt.date | None = None,
        date_to: dt.date | None = None,
        search_name: str | None = None,
    ) -> list[ReportReference]:
        base_params: dict[str, Any] = {"group": "Market Data"}
        if date_from is not None:
            base_params["date_from"] = date_from.strftime("%Y-%m-%d")
        if date_to is not None:
            base_params["date_to"] = date_to.strftime("%Y-%m-%d")
        if search_name is not None:
            base_params["name"] = search_name

        first = self._get_json(
            "/api/v1/documents/static-reports",
            params={**base_params, "page": 1},
        )
        if not isinstance(first, dict) or "items" not in first:
            raise ProviderError("SEMOpx report list response missing 'items'")

        items = list(first["items"])
        total_pages = first.get("pagination", {}).get("totalPages", 1)
        for page in range(2, total_pages + 1):
            payload = self._get_json(
                "/api/v1/documents/static-reports",
                params={**base_params, "page": page},
            )
            if isinstance(payload, dict) and "items" in payload:
                items.extend(payload["items"])

        return parse_report_list(items)

    def fetch_report(self, resource_name: str) -> str:
        return self._get_text(f"/documents/{resource_name}")

    def get_market_result(self, auction: Auction, delivery_date: dt.date) -> MarketResult:
        auction_id = _SEMOPX_AUCTION_ID[auction]
        prefix = f"MarketResult_{auction_id}_"
        refs = self.list_reports(
            date_from=delivery_date, date_to=delivery_date + dt.timedelta(days=1), search_name=prefix
        )
        matches = [r for r in refs if r.resource_name.startswith(prefix) and r.date == delivery_date]

        if not matches:
            raise ReportNotFoundError(f"No market result report for {auction!r} on {delivery_date}")

        if len(matches) > 1:
            _log.warning(
                "Multiple market result reports for %s %s; using latest publish_time",
                auction,
                delivery_date,
            )
        ref = max(matches, key=lambda r: r.publish_time)
        return parse_market_result(self.fetch_report(ref.resource_name))
