from __future__ import annotations

import datetime as dt
from typing import Any
from xml.etree import ElementTree as ET

from ...core.constants import TZ_UTC
from ...core.exceptions import ParseError
from ...schema.models import (
    AuctionResult,
    DataPoint,
    ImbalancePriceReport,
    ImbalancePriceSuppInfo,
    ImbalanceSettlementReport,
    PhysicalNotification,
    ReportReference,
    Series,
)


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


_SeriesRow = list[list[Any]]


def extract_series_chunk(
    series_name: str,
    data: _SeriesRow,
    extra_match: str | None = None,
) -> _SeriesRow:
    """Locate a 3-line section in an auction report row: [header, timestamps, values]."""
    try:
        start_index = next(
            i for i, e in enumerate(data) if e[0] == series_name and (e[2] == extra_match if extra_match else True)
        )
    except StopIteration as exc:
        raise ParseError(f"series '{series_name}' not found in auction report") from exc
    return data[start_index : start_index + 3]


def parse_series_chunk(area: str, data: _SeriesRow) -> Series:
    """Parse a 3-row series chunk (header / timestamps / values) into a Series.

    Header row layout: [name, frequency, unit?]
    """
    header = data[0]
    series_name = header[0]
    frequency = header[1]
    unit = header[2] if len(header) > 2 else None

    timestamps = [dt.datetime.fromisoformat(x) for x in data[1]]
    values = data[2]

    points = [DataPoint(timestamp=t, value=v) for t, v in zip(timestamps, values, strict=False)]
    return Series(area=area, name=series_name, frequency=frequency, unit=unit, data=points)


_SERIES_TO_EXTRACT: list[tuple[str, str | None]] = [
    ("Index prices", "EUR"),
    ("Index prices", "GBP"),
    ("Index volumes", None),
    ("Net position", None),
]


def parse_auction_report(report_content: dict[str, Any]) -> AuctionResult:
    """Parse a SEMO auction report payload into an AuctionResult.

    Top-level payload keys: AuctionDate, PublishTime, rows (list of per-area row groups).
    """
    rows = report_content.get("rows")
    if not rows:
        raise ParseError("auction report missing 'rows'")

    auction_date = _maybe_datetime(report_content.get("AuctionDate"))
    publish_time = _maybe_datetime(report_content.get("PublishTime"))
    delivery_date = _maybe_date(report_content.get("Date"))

    series: list[Series] = []
    for area_rows in rows:
        area = area_rows[0][1].split("-")[0]
        for name, extra_match in _SERIES_TO_EXTRACT:
            chunk = extract_series_chunk(name, area_rows, extra_match=extra_match)
            series.append(parse_series_chunk(area, chunk))

    return AuctionResult(
        auction_date=auction_date,
        delivery_date=delivery_date,
        publish_time=publish_time,
        series=series,
    )


def _maybe_datetime(value: str | None) -> dt.datetime | None:
    if value is None:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _maybe_date(value: str | None) -> dt.date | None:
    if value is None:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _yn_to_bool(value: str) -> bool:
    if value == "Y":
        return True
    if value == "N":
        return False
    raise ParseError(f"expected 'Y' or 'N', got {value!r}")


def _parse_aware_utc(value: str) -> dt.datetime:
    """SEMO publishes naive ISO timestamps in UTC; make that explicit."""
    return dt.datetime.fromisoformat(value.replace("Z", "")).replace(tzinfo=TZ_UTC)


def parse_imbalance_price_report(xml: str) -> ImbalancePriceReport:
    """Parse a `PUB_5MinImbalPrc_*.xml` payload into an `ImbalancePriceReport`.

    Each file contains a single 5-minute imbalance-pricing period as attributes
    on a `<PUB_5MinImbalPrc>` element inside `<OutboundData>`.
    """
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as exc:
        raise ParseError(f"invalid XML: {exc}") from exc

    publish_time = _parse_aware_utc(root.attrib["PublishTime"])

    row = root.find("PUB_5MinImbalPrc")
    if row is None:
        raise ParseError("imbalance report missing <PUB_5MinImbalPrc> element")

    a = row.attrib
    return ImbalancePriceReport(
        trade_date=dt.date.fromisoformat(a["TradeDate"]),
        start_time=_parse_aware_utc(a["StartTime"]),
        end_time=_parse_aware_utc(a["EndTime"]),
        publish_time=publish_time,
        net_imbalance_volume=float(a["NetImbalanceVolume"]),
        imbalance_price=float(a["ImbalancePrice"]),
        default_price_usage=_yn_to_bool(a["DefaultPriceUsage"]),
        asp_price_usage=_yn_to_bool(a["ASPPriceUsage"]),
        total_unit_availability=float(a["TotalUnitAvailability"]),
        demand_control_volume=float(a["DemandControlVolume"]),
        pmea=float(a["PMEA"]),
        qpar=float(a["QPAR"]),
        administered_scarcity_price=float(a["AdministeredScarcityPrice"]),
        market_backup_price=float(a["MarketBackupPrice"]),
        short_term_reserve_quantity=float(a["ShortTermReserveQuantity"]),
        operating_reserve_requirement=float(a["OperatingReserveRequirement"]),
    )


def parse_imbalance_settlement_report(xml: str) -> ImbalanceSettlementReport:
    """Parse a `PUB_30MinAvgImbalPrc_*.xml` payload into an `ImbalanceSettlementReport`.

    Each file is one 30-minute settlement period with net imbalance volume and the
    volume-weighted settlement price, inside a `<PUB_30MinAvgImbalPrc>` element.
    """
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as exc:
        raise ParseError(f"invalid XML: {exc}") from exc

    publish_time = _parse_aware_utc(root.attrib["PublishTime"])

    row = root.find("PUB_30MinAvgImbalPrc")
    if row is None:
        raise ParseError("settlement report missing <PUB_30MinAvgImbalPrc> element")

    a = row.attrib
    return ImbalanceSettlementReport(
        trade_date=dt.date.fromisoformat(a["TradeDate"]),
        start_time=_parse_aware_utc(a["StartTime"]),
        end_time=_parse_aware_utc(a["EndTime"]),
        publish_time=publish_time,
        net_imbalance_volume=float(a["NetImbalanceVolume"]),
        imbalance_settlement_price=float(a["ImbalanceSettlementPrice"]),
    )


def parse_physical_notifications_report(xml: str) -> list[PhysicalNotification]:
    """Parse a `PUB_DailyFinalPhysicalNotifications_*.xml` payload into a list of rows.

    Each file covers one trade day; rows represent individual physical notification
    segments for each resource across one or more delivery dates.
    """
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as exc:
        raise ParseError(f"invalid XML: {exc}") from exc

    publish_time = _parse_aware_utc(root.attrib["PublishTime"])

    rows = root.findall("PUB_DailyFinalPhysicalNotifications")
    if not rows:
        raise ParseError("physical notifications report missing <PUB_DailyFinalPhysicalNotifications> elements")

    return [
        PhysicalNotification(
            resource_name=a["ResourceName"],
            start_time=_parse_aware_utc(a["StartTime"]),
            start_mw=float(a["StartMW"]),
            end_time=_parse_aware_utc(a["EndTime"]),
            end_mw=float(a["EndMW"]),
            under_test=_yn_to_bool(a["UnderTestFlag"]),
            publish_time=publish_time,
        )
        for row in rows
        for a in (row.attrib,)
    ]


def parse_imbalance_price_supp_info_report(xml: str) -> list[ImbalancePriceSuppInfo]:
    """Parse a `PUB_5MinImbalPrcSuppInfo_*.xml` payload into a list of BOA rows.

    Each file covers one 5-minute period; rows represent individual bid/offer
    acceptances. `NonEnergyFlags` and `ConstraintId` are absent on energy BOAs.
    """
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as exc:
        raise ParseError(f"invalid XML: {exc}") from exc

    publish_time = _parse_aware_utc(root.attrib["PublishTime"])

    rows = root.findall("PUB_5MinImbalPrcSuppInfo")
    if not rows:
        raise ParseError("supp info report missing <PUB_5MinImbalPrcSuppInfo> elements")

    result = []
    for row in rows:
        a = row.attrib
        result.append(
            ImbalancePriceSuppInfo(
                trade_date=dt.date.fromisoformat(a["TradeDate"]),
                start_time=_parse_aware_utc(a["StartTime"]),
                end_time=_parse_aware_utc(a["EndTime"]),
                publish_time=publish_time,
                participant_name=a["ParticipantName"],
                resource_name=a["ResourceName"],
                pboa=float(a["PBOA"]),
                qboa=float(a["QBOA"]),
                rank=int(a["Rank"]),
                so_flag=bool(int(a["SoFlag"])),
                emergency_flag=bool(int(a["EmergencyFlag"])),
                non_marginal_flag=bool(int(a["NonMarginalFlag"])),
                imbalance_price_flag=bool(int(a["ImbalancePriceFlag"])),
                net_imbalance_volume_tag=float(a["NetImbalanceVolumeTag"]),
                imbalance_price_tag=float(a["ImbalancePriceTag"]),
                price_average_reference_tag=float(a["PriceAverageReferenceTag"]),
                net_imbalance_volume=float(a["NetImbalanceVolume"]),
                non_energy_flags=int(a["NonEnergyFlags"]) if "NonEnergyFlags" in a else None,
                constraint_id=a.get("ConstraintId"),
            )
        )
    return result
