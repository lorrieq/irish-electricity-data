from __future__ import annotations

import datetime as dt
from enum import StrEnum
from typing import Any

from ...core.constants import TZ_UTC
from ...core.exceptions import ProviderError
from ...schema.models import (
    Auction,
    AuctionResult,
    ImbalancePriceReport,
    ImbalancePriceSuppInfo,
    ImbalanceSettlementReport,
    PhysicalNotification,
    ReportReference,
)
from ..base import BaseProvider, ProviderCapability
from .parsers import (
    parse_auction_report,
    parse_imbalance_price_report,
    parse_imbalance_price_supp_info_report,
    parse_imbalance_settlement_report,
    parse_physical_notifications_report,
    parse_report_list,
)

_RESOURCE_NAME_BY_AUCTION: dict[Auction, str] = {
    Auction.DAY_AHEAD: "MarketResult_SEM-DA_PWR-MRC-D",
    Auction.IDA1: "MarketResult_SEM-IDA1_PWR-SEM-GB-D",
    Auction.IDA2: "MarketResult_SEM-IDA2_PWR-SEM-GB-D_",
    Auction.IDA3: "MarketResult_SEM-IDA3_PWR-SEM-D_",
}


def resource_name_for_auction(auction: Auction) -> str:
    return _RESOURCE_NAME_BY_AUCTION[auction]


def _datetime_from_resource_name(resource_name: str) -> dt.datetime | None:
    """Extract the period datetime from a resource name like PUB_5MinImbalPrc_202604271030.xml."""
    stem = resource_name.rsplit(".", 1)[0]
    timestamp_str = stem.rsplit("_", 1)[-1]
    try:
        return dt.datetime.strptime(timestamp_str, "%Y%m%d%H%M").replace(tzinfo=TZ_UTC)
    except ValueError:
        return None


class _DPuG(StrEnum):
    PHYSICAL_NOTIFICATIONS = "BM-023"
    IMBALANCE_PRICE = "BM-025"
    IMBALANCE_SETTLEMENT = "BM-026"
    IMBALANCE_PRICE_SUPP_INFO = "BM-027"


class SemoProvider(BaseProvider):
    """SEMO static-reports provider (reports.sem-o.com)."""

    name = "semo"
    base_url = "https://reports.sem-o.com"
    capabilities = frozenset({ProviderCapability.AUCTION_RESULTS})

    def list_reports(
        self,
        params: Any,
        *,
        page_size: int = 500,
    ) -> list[ReportReference]:
        """Query `/api/v1/documents/static-reports`, transparently paginating.

        `params` is any httpx-compatible params value (dict or list of tuples).
        Use a list of tuples when sending multi-valued filters like `group[]`.
        """
        base = list(params.items()) if isinstance(params, dict) else list(params)
        base.append(("page_size", page_size))

        items: list[dict[str, Any]] = []
        page = 1
        while True:
            payload = self._get_json(
                "/api/v1/documents/static-reports",
                params=[*base, ("page", page)],
            )
            if not isinstance(payload, dict) or "items" not in payload:
                raise ProviderError("SEMO report list response missing 'items'")
            items.extend(payload["items"])
            total_pages = payload.get("pagination", {}).get("totalPages", 1)
            if page >= total_pages:
                break
            page += 1
        return parse_report_list(items)

    def fetch_report(self, report_id: str) -> dict[str, Any]:
        """Fetch a parsed JSON report payload by report id (auction-style reports)."""
        payload = self._get_json(f"/api/v1/documents/{report_id}")
        if not isinstance(payload, dict):
            raise ProviderError(f"SEMO report {report_id} returned unexpected type")
        return payload

    def fetch_raw_report(self, resource_name: str) -> str:
        """Fetch the raw text body of a report (XML, CSV, etc) by resource name."""
        return self._get_text(f"/documents/{resource_name}")

    def get_auction_result(self, report_id: str) -> AuctionResult:
        """Fetch and parse a single auction report by report id."""
        return parse_auction_report(self.fetch_report(report_id))

    def get_auction_results(
        self,
        auction: Auction,
        start_date: dt.date,
        end_date: dt.date | None = None,
    ) -> list[AuctionResult]:
        """Get auction results by delivery date, inclusive on both ends.

        Pads `date_to` by +1 day at the API layer to cover the 10:00-UTC filter
        quirk, then client-side filters and de-duplicates to the latest
        `publish_time` per delivery date.
        """
        if end_date is None:
            end_date = start_date
        if end_date < start_date:
            raise ValueError("end_date must be on or after start_date")

        refs = self.list_reports(
            [
                ("DPuG_ID", "EA-001"),
                ("order_by", "DESC"),
                ("sort_by", "Date"),
                ("ExcludeDelayedPublication", 0),
                ("ResourceName", resource_name_for_auction(auction)),
                ("date_from", start_date.strftime("%Y-%m-%d")),
                ("date_to", (end_date + dt.timedelta(days=1)).strftime("%Y-%m-%d")),
            ]
        )
        latest = _latest_by_delivery_date(refs, start_date, end_date)
        return [self.get_auction_result(ref.id) for ref in sorted(latest.values(), key=lambda r: r.date)]

    def get_physical_notifications_report(self, resource_name: str) -> list[PhysicalNotification]:
        """Fetch and parse a single daily final physical notifications report."""
        return parse_physical_notifications_report(self.fetch_raw_report(resource_name))

    def get_physical_notifications(
        self,
        start_date: dt.date,
        end_date: dt.date | None = None,
    ) -> list[PhysicalNotification]:
        """Get physical notifications by trade date, inclusive on both ends, sorted by start_time.

        Deduplicates to the latest-published report per trade date before fetching.
        """
        if end_date is None:
            end_date = start_date
        if end_date < start_date:
            raise ValueError("end_date must be on or after start_date")

        refs = self.list_reports(
            [
                ("DPuG_ID", _DPuG.PHYSICAL_NOTIFICATIONS),
                ("sort_by", "PublishTime"),
                ("order_by", "DESC"),
                ("date_from", start_date.strftime("%Y-%m-%d")),
                ("date_to", end_date.strftime("%Y-%m-%d")),
            ]
        )
        latest = _latest_by_delivery_date(refs, start_date, end_date)
        rows = [
            row
            for ref in sorted(latest.values(), key=lambda r: r.date)
            for row in self.get_physical_notifications_report(ref.resource_name)
        ]
        rows.sort(key=lambda r: r.start_time)
        return rows

    def get_imbalance_price_report(self, resource_name: str) -> ImbalancePriceReport:
        """Fetch and parse a single 5-minute imbalance price report."""
        return parse_imbalance_price_report(self.fetch_raw_report(resource_name))

    def get_imbalance_prices(
        self,
        start: dt.datetime,
        end: dt.datetime | None = None,
    ) -> list[ImbalancePriceReport]:
        """Get every 5-minute imbalance price within the datetime range, sorted."""
        if end is None:
            end = start
        if end < start:
            raise ValueError("end must be on or after start")

        refs = self.list_reports(
            [
                ("DPuG_ID", _DPuG.IMBALANCE_PRICE),
                ("sort_by", "PublishTime"),
                ("order_by", "DESC"),
                ("date_from", start.date().strftime("%Y-%m-%d")),
                ("date_to", end.date().strftime("%Y-%m-%d")),
            ]
        )
        refs = [
            r for r in refs if (t := _datetime_from_resource_name(r.resource_name)) is not None and start <= t <= end
        ]
        reports = [self.get_imbalance_price_report(r.resource_name) for r in refs]
        reports.sort(key=lambda r: r.start_time)
        return reports

    def get_imbalance_price_supp_info_report(self, resource_name: str) -> list[ImbalancePriceSuppInfo]:
        """Fetch and parse a single 5-minute imbalance price supplementary info report."""
        return parse_imbalance_price_supp_info_report(self.fetch_raw_report(resource_name))

    def get_imbalance_price_supp_infos(
        self,
        start: dt.datetime,
        end: dt.datetime | None = None,
    ) -> list[ImbalancePriceSuppInfo]:
        """Get every 5-minute imbalance price supp info within the datetime range, sorted."""
        if end is None:
            end = start
        if end < start:
            raise ValueError("end must be on or after start")

        refs = self.list_reports(
            [
                ("DPuG_ID", _DPuG.IMBALANCE_PRICE_SUPP_INFO),
                ("sort_by", "PublishTime"),
                ("order_by", "DESC"),
                ("date_from", start.date().strftime("%Y-%m-%d")),
                ("date_to", end.date().strftime("%Y-%m-%d")),
            ]
        )
        refs = [
            r for r in refs if (t := _datetime_from_resource_name(r.resource_name)) is not None and start <= t <= end
        ]
        rows = [row for r in refs for row in self.get_imbalance_price_supp_info_report(r.resource_name)]
        rows.sort(key=lambda r: r.start_time)
        return rows

    def get_imbalance_settlement_report(self, resource_name: str) -> ImbalanceSettlementReport:
        """Fetch and parse a single 30-minute imbalance settlement report."""
        return parse_imbalance_settlement_report(self.fetch_raw_report(resource_name))

    def get_imbalance_settlements(
        self,
        start: dt.datetime,
        end: dt.datetime | None = None,
    ) -> list[ImbalanceSettlementReport]:
        """Get every 30-minute imbalance settlement within the datetime range, sorted."""
        if end is None:
            end = start
        if end < start:
            raise ValueError("end must be on or after start")

        refs = self.list_reports(
            [
                ("DPuG_ID", _DPuG.IMBALANCE_SETTLEMENT),
                ("sort_by", "PublishTime"),
                ("order_by", "DESC"),
                ("date_from", start.date().strftime("%Y-%m-%d")),
                ("date_to", end.date().strftime("%Y-%m-%d")),
            ]
        )
        refs = [
            r for r in refs if (t := _datetime_from_resource_name(r.resource_name)) is not None and start <= t <= end
        ]
        reports = [self.get_imbalance_settlement_report(r.resource_name) for r in refs]
        reports.sort(key=lambda r: r.start_time)
        return reports


def _latest_by_delivery_date(
    refs: list[ReportReference],
    start_date: dt.date,
    end_date: dt.date,
) -> dict[dt.date, ReportReference]:
    """Pick the latest-published ReportReference per delivery date within [start, end]."""
    picks: dict[dt.date, ReportReference] = {}
    for ref in refs:
        if not (start_date <= ref.date <= end_date):
            continue
        existing = picks.get(ref.date)
        if existing is None or ref.publish_time > existing.publish_time:
            picks[ref.date] = ref
    return picks
