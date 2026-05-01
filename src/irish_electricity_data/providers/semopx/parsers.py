from __future__ import annotations

import datetime as dt
from typing import Any
from xml.etree import ElementTree as ET

from ...core.constants import TZ_UTC
from ...core.exceptions import ParseError
from ...schema.models import DataPoint, ReportReference, _FrozenModel


class PortfolioPosition(_FrozenModel):
    """A single participant/unit's cleared position timeseries from a market result."""

    participant: str
    unit_id: str
    order_type: str
    user: str
    positions: list[DataPoint]


class MarketResult(_FrozenModel):
    """Parsed SEMOpx market result: per-portfolio cleared positions."""

    auction: str | None = None
    auction_name: str | None = None
    auction_datetime: dt.datetime | None = None
    publication_datetime: dt.datetime | None = None
    portfolios: list[PortfolioPosition]


class InterconnectorFlow(_FrozenModel):
    interconnector: str
    direction: str
    timestamp: dt.datetime
    scheduled: float
    total_scheduled: float
    publish_time: dt.datetime


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


def parse_interconnector_flows(xml: str) -> list[InterconnectorFlow]:
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as exc:
        raise ParseError(f"Invalid XML: {exc}") from exc
    
    ns = {"ns": "http://amp.unicorn.eu/xsd/InterconnectorFlowCapacityDocument.xsd"}

    publish_time_elem = root.find("ns:CreationDateTime", namespaces=ns)
    publish_time = dt.datetime.fromisoformat(publish_time_elem.attrib["v"])

    rows = root.findall("ns:CapacityTimeSeries", namespaces=ns)
    if not rows:
        raise ParseError("Interconnector flows report has no <CapacityTimeSeries> elements")

    data = []
    for row in rows:
        period = row.find("ns:Period", ns)
        time_interval = period.find("ns:TimeInterval", ns).attrib["v"]
        start, end = [dt.datetime.fromisoformat(x) for x in time_interval.split("/")]
        end -= dt.timedelta(minutes=30)  # bring back to last period

        intervals = period.findall("ns:Interval", namespaces=ns)
        for interval in intervals:
            hour, minute = [int(x) for x in interval.find("ns:StartTime", ns).attrib["v"].split(":")]

            # StartTime is HH:MM, need to determine date, assume date of `end`
            # if timestamps is later than `end` subtract a day
            initial_timestamp = dt.datetime.combine(end.date(), dt.time(hour, minute), tzinfo=TZ_UTC)
            timestamp = initial_timestamp - dt.timedelta(days=1) if initial_timestamp > end else initial_timestamp

            data.append(InterconnectorFlow(
                interconnector=row.find("ns:Interconnector", ns).attrib["v"],
                direction=row.find("ns:InterconnectorDirection", ns).attrib["v"],
                timestamp=timestamp,
                scheduled=interval.find("ns:Scheduled", ns).attrib["v"],
                total_scheduled=interval.find("ns:TotalScheduled", ns).attrib["v"],
                publish_time=publish_time
            ))
    
    return data


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
