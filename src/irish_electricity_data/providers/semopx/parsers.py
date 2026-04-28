from __future__ import annotations

import datetime as dt
from typing import Any

from ...core.constants import TZ_UTC
from ...core.exceptions import ParseError
from ...schema.models import DataPoint, MarketResult, PortfolioPosition, ReportReference


def parse_report_list(items: list[dict[str, Any]]) -> list[ReportReference]:
    return [
        ReportReference(
            id=item["_id"],
            dpug_id=item["DPuG_ID"],
            report_name=item["ReportName"],
            group=item["Group"],
            dynamic=item["Dynamic"],
            resource_name=item["ResourceName"],
            publish_time=dt.datetime.fromisoformat(item["PublishTime"]),
            date=dt.datetime.fromisoformat(item["Date"]).date(),
            date_retention=dt.date.fromisoformat(item["DateRetention"]),
        )
        for item in items
    ]


def _split_lines(content: str) -> list[list[str]]:
    lines = content.replace("\r", "").split("\n")
    return [line.split(";") for line in lines if line != ""]


def _portfolio_slices(pieces: list[list[str]]) -> list[tuple[int, int]]:
    starts = [i for i, line in enumerate(pieces) if line and line[0] == "Portfolio"]
    slices: list[tuple[int, int]] = []
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(pieces)
        slices.append((start, end))
    return slices


def _parse_portfolio(block: list[list[str]]) -> PortfolioPosition:
    if len(block) < 4:
        raise ParseError("portfolio block must have at least 4 rows")

    participant = block[0][1]
    unit_id = block[0][2]
    order_type = block[1][0]
    user = block[1][1]

    timestamps = [dt.datetime.strptime(e, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=TZ_UTC) for e in block[2]]
    values = [float(e.replace(",", ".")) for e in block[3]]

    positions = [DataPoint(timestamp=t, value=v) for t, v in zip(timestamps, values, strict=False)]
    return PortfolioPosition(
        participant=participant,
        unit_id=unit_id,
        order_type=order_type,
        user=user,
        positions=positions,
    )


def _header_value(pieces: list[list[str]], key: str) -> str | None:
    for line in pieces:
        if line and line[0] == key and len(line) > 1:
            return line[1]
    return None


def _maybe_datetime(value: str | None) -> dt.datetime | None:
    if value is None:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_market_result(report_content: str) -> MarketResult:
    """Parse a SEMOpx market result CSV into a MarketResult with per-portfolio positions."""
    pieces = _split_lines(report_content)

    portfolios = [_parse_portfolio(pieces[s:e]) for s, e in _portfolio_slices(pieces)]

    return MarketResult(
        auction=_header_value(pieces, "Auction"),
        auction_name=_header_value(pieces, "Auction name"),
        auction_datetime=_maybe_datetime(_header_value(pieces, "Auction date time")),
        publication_datetime=_maybe_datetime(_header_value(pieces, "Publication date time")),
        portfolios=portfolios,
    )
