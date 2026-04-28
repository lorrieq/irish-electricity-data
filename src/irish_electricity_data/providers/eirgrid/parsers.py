from __future__ import annotations

import datetime as dt
from collections import defaultdict
from typing import Any

from ...core.constants import TZ_DUBLIN, TZ_UTC
from ...schema.models import DataPoint, Series

_FIELD_NAME_TO_LABEL: dict[str, str] = {
    "SOLAR_ACTUAL": "Solar",
    "WIND_ACTUAL": "Wind",
    "SYSTEM_DEMAND": "Demand",
}

_INTER_FIELD_TO_NAME: dict[str, str] = {
    "INTER_EWIC": "EWIC",
    "INTER_GRNLK": "GREENLINK",
    "INTER_MOYLE": "MOYLE",
    "INTER_NET": "Net",
}


def _parse_effective_time(value: str) -> dt.datetime:
    """Parse a `"DD-MMM-YYYY HH:MM:SS"` Dublin-local timestamp into tz-aware UTC.

    DST fold on the October transition isn't disambiguated here — both occurrences
    of the duplicated hour will collide on UTC. Revisit when we add fold handling.
    """
    naive = dt.datetime.strptime(value, "%d-%b-%Y %H:%M:%S")
    return naive.replace(tzinfo=TZ_DUBLIN).astimezone(TZ_UTC)


def parse_outturn(payload: dict[str, Any]) -> list[Series]:
    """Parse an EirGrid chart-API response into one Series per (Region, variable).

    Rows are grouped by `(Region, FieldName)` and sorted by timestamp. Rows with
    unknown FieldNames or a null `Value` are dropped.
    """
    rows = payload.get("Rows", [])
    by_key: dict[tuple[str, str], list[DataPoint]] = defaultdict(list)

    for row in rows:
        field = row.get("FieldName")
        name = _FIELD_NAME_TO_LABEL.get(field)
        if name is None:
            continue

        value = row.get("Value")
        if value is None:
            continue

        point = DataPoint(
            timestamp=_parse_effective_time(row["EffectiveTime"]),
            value=value,
        )
        by_key[(row["Region"], name)].append(point)

    series: list[Series] = []
    for (region, name), points in sorted(by_key.items()):
        points.sort(key=lambda p: p.timestamp)
        series.append(Series(area=region, name=name, frequency=15, unit="MW", data=points))
    return series


def parse_interconnector_flows(payload: dict[str, Any]) -> list[Series]:
    """Parse an EirGrid interconnection API response into one Series per (Region, name).

    Known FieldNames: INTER_EWIC → EWIC (ROI), INTER_GRNLK → GREENLINK (ROI),
    INTER_MOYLE → MOYLE (NI), INTER_NET → Net (ALL). Unknown fields are dropped.
    Rows with a null Value are dropped.
    """
    rows = payload.get("Rows", [])
    by_key: dict[tuple[str, str], list[DataPoint]] = defaultdict(list)

    for row in rows:
        name = _INTER_FIELD_TO_NAME.get(row.get("FieldName"))
        if name is None:
            continue
        value = row.get("Value")
        if value is None:
            continue
        point = DataPoint(
            timestamp=_parse_effective_time(row["EffectiveTime"]),
            value=value,
        )
        by_key[(row["Region"], name)].append(point)

    series: list[Series] = []
    for (region, name), points in sorted(by_key.items()):
        points.sort(key=lambda p: p.timestamp)
        series.append(Series(area=region, name=name, frequency=15, unit="MW", data=points))
    return series
