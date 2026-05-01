from __future__ import annotations

import datetime as dt
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Auction(StrEnum):
    DAY_AHEAD = "DAY_AHEAD"
    IDA1 = "IDA1"
    IDA2 = "IDA2"
    IDA3 = "IDA3"


class DataStatus(StrEnum):
    ACTUAL = "ACTUAL"
    ESTIMATED = "ESTIMATED"
    MISSING = "MISSING"


class _FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class DataPoint(_FrozenModel):
    """A single timestamped observation. `value` is None when `status == MISSING`."""

    timestamp: dt.datetime
    value: float | None = None
    status: DataStatus = DataStatus.ACTUAL


class Series(_FrozenModel):
    """A homogeneous timeseries for a single (area, name) pair."""

    area: str
    name: str
    frequency: int = Field(description="Sampling period in minutes.")
    unit: str | None = None
    data: list[DataPoint]


class ReportReference(_FrozenModel):
    """A handle to a single upstream report, from a report-list endpoint."""

    id: str
    dpug_id: str
    report_name: str
    group: list[str]
    dynamic: bool
    resource_name: str
    publish_time: dt.datetime
    date: dt.date
    date_retention: dt.date
