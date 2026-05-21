from __future__ import annotations

import datetime as dt
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class Auction(StrEnum):
    DAY_AHEAD = "DAY_AHEAD"
    IDA1 = "IDA1"
    IDA2 = "IDA2"
    IDA3 = "IDA3"


class _FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class DataPoint(_FrozenModel):
    timestamp: dt.datetime
    value: float | None = None


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
