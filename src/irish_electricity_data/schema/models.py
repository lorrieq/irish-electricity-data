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


class PortfolioPosition(_FrozenModel):
    """A single participant/unit's cleared position timeseries from a market result."""

    participant: str
    unit_id: str
    order_type: str
    user: str
    positions: list[DataPoint]


class AuctionResult(_FrozenModel):
    """Parsed SEMO auction report: prices, volumes, net positions across NI/ROI."""

    auction_date: dt.datetime | None = None
    delivery_date: dt.date | None = None
    publish_time: dt.datetime | None = None
    series: list[Series]


class MarketResult(_FrozenModel):
    """Parsed SEMOpx market result: per-portfolio cleared positions."""

    auction: str | None = None
    auction_name: str | None = None
    auction_datetime: dt.datetime | None = None
    publication_datetime: dt.datetime | None = None
    portfolios: list[PortfolioPosition]


class ImbalancePriceReport(_FrozenModel):
    """A single 5-minute imbalance-pricing period from SEMO (DPuG BM-025)."""

    trade_date: dt.date
    start_time: dt.datetime
    end_time: dt.datetime
    publish_time: dt.datetime
    net_imbalance_volume: float
    imbalance_price: float
    default_price_usage: bool
    asp_price_usage: bool
    total_unit_availability: float
    demand_control_volume: float
    pmea: float
    qpar: float
    administered_scarcity_price: float
    market_backup_price: float
    short_term_reserve_quantity: float
    operating_reserve_requirement: float


class ImbalanceSettlementReport(_FrozenModel):
    """A 30-minute imbalance settlement period from SEMO (DPuG BM-026).

    This is the settlement price — the volume-weighted average of the six 5-minute
    imbalance pricing periods in the half hour.
    """

    trade_date: dt.date
    start_time: dt.datetime
    end_time: dt.datetime
    publish_time: dt.datetime
    net_imbalance_volume: float
    imbalance_settlement_price: float


class ImbalancePriceSuppInfo(_FrozenModel):
    """A single BOA row from a 5-minute imbalance price supplementary info report.

    Each file covers one 5-minute period and contains one row per bid/offer acceptance
    that contributed to the imbalance price calculation.
    """

    trade_date: dt.date
    start_time: dt.datetime
    end_time: dt.datetime
    publish_time: dt.datetime
    participant_name: str
    resource_name: str
    pboa: float
    qboa: float
    rank: int
    so_flag: bool
    emergency_flag: bool
    non_marginal_flag: bool
    imbalance_price_flag: bool
    net_imbalance_volume_tag: float
    imbalance_price_tag: float
    price_average_reference_tag: float
    net_imbalance_volume: float
    non_energy_flags: int | None = None
    constraint_id: str | None = None


class PhysicalNotification(_FrozenModel):
    """A single row from a daily final physical notifications report (DPuG BM-023)."""

    resource_name: str
    start_time: dt.datetime
    start_mw: float
    end_time: dt.datetime
    end_mw: float
    under_test: bool
    publish_time: dt.datetime


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
