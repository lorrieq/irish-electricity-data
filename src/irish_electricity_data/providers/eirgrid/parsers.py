from __future__ import annotations

import datetime as dt
from collections import defaultdict
from typing import Any

from ...core.constants import TZ_DUBLIN, TZ_UTC
from ...schema.models import DataPoint
from .models import EirgridCo2Data, EirgridInterconnectorData, EirgridOutturnData

_OUTTURN_FIELD_NAME_TO_LABEL: dict[str, str] = {
    "SOLAR_ACTUAL": "Solar",
    "WIND_ACTUAL": "Wind",
    "SYSTEM_DEMAND": "Demand",
}

_OUTTURN_KEY_TO_FIELD: dict[tuple[str, str], str] = {
    ("ALL", "Wind"):   "wind_ie",
    ("NI",  "Wind"):   "wind_ni",
    ("ROI", "Wind"):   "wind_roi",
    ("ALL", "Demand"): "demand_ie",
    ("NI",  "Demand"): "demand_ni",
    ("ROI", "Demand"): "demand_roi",
    ("ALL", "Solar"):  "solar_ie",
    ("NI",  "Solar"):  "solar_ni",
    ("ROI", "Solar"):  "solar_roi",
}

_INTER_FIELD_TO_FIELD: dict[str, str] = {
    "INTER_EWIC": "ewic",
    "INTER_GRNLK": "greenlink",
    "INTER_MOYLE": "moyle",
    "INTER_NET": "net",
}


def _parse_effective_time(value: str) -> dt.datetime:
    """Parse a `"DD-MMM-YYYY HH:MM:SS"` Dublin-local timestamp into tz-aware UTC.

    DST fold on the October transition isn't disambiguated here — both occurrences
    of the duplicated hour will collide on UTC. Revisit when we add fold handling.
    """
    naive = dt.datetime.strptime(value, "%d-%b-%Y %H:%M:%S")
    return naive.replace(tzinfo=TZ_DUBLIN).astimezone(TZ_UTC)


def _parse_datapoints_by_region(payload: dict[str, Any], field_name: str) -> dict[str, list[DataPoint]]:
    region_points: dict[str, list[DataPoint]] = defaultdict(list)
    for row in payload.get("Rows", []):
        if row.get("FieldName") != field_name:
            continue

        value = row.get("Value")
        if value is None:
            continue

        region_points[row["Region"]].append(
            DataPoint(timestamp=_parse_effective_time(row["EffectiveTime"]), value=value)
        )

    for points in region_points.values():
        points.sort(key=lambda p: p.timestamp)

    return region_points


def parse_co2(payload: dict[str, Any]) -> EirgridCo2Data:
    """Parse a CO2 response into an EirgridCo2Data."""
    by_region = _parse_datapoints_by_region(payload, "CO2_EMISSIONS")
    return EirgridCo2Data(
        co2_ie=by_region.get("ALL", []),
        co2_ni=by_region.get("NI", []),
        co2_roi=by_region.get("ROI", []),
    )


def parse_frequency(payload: dict[str, Any]) -> list[DataPoint]:
    """Parse a frequency response."""
    return _parse_datapoints_by_region(payload, "SYS_FREQUENCY").get("ALL", [])


def parse_interconnector_flows(payload: dict[str, Any]) -> EirgridInterconnectorData:
    """Parse an interconnection response into an EirgridInterconnectorData.
    Rows with an unknown FieldName or null Value are dropped.
    """
    rows = payload.get("Rows", [])
    by_field: dict[str, list[DataPoint]] = defaultdict(list)

    for row in rows:
        field = _INTER_FIELD_TO_FIELD.get(row.get("FieldName"))
        if field is None:
            continue
        value = row.get("Value")
        if value is None:
            continue
        by_field[field].append(DataPoint(timestamp=_parse_effective_time(row["EffectiveTime"]), value=value))

    for points in by_field.values():
        points.sort(key=lambda p: p.timestamp)

    return EirgridInterconnectorData(**by_field)


def parse_outturn(payload: dict[str, Any]) -> EirgridOutturnData:
    """Parse an outturn response into an EirgridOutturnData. Rows with unknown
    FieldName, unknown (Region, variable) combinations, or null Value are dropped.
    """
    rows = payload.get("Rows", [])
    by_field: dict[str, list[DataPoint]] = defaultdict(list)

    for row in rows:
        label = _OUTTURN_FIELD_NAME_TO_LABEL.get(row.get("FieldName"))
        if label is None:
            continue
        value = row.get("Value")
        if value is None:
            continue
        field = _OUTTURN_KEY_TO_FIELD.get((row["Region"], label))
        if field is None:
            continue
        by_field[field].append(DataPoint(
            timestamp=_parse_effective_time(row["EffectiveTime"]),
            value=value,
        ))

    for points in by_field.values():
        points.sort(key=lambda p: p.timestamp)

    return EirgridOutturnData(**by_field)


def parse_snsp(payload: dict[str, Any]) -> list[DataPoint]:
    """Parse an SNSP response."""
    return _parse_datapoints_by_region(payload, "SNSP_ALL").get("ALL", [])
