from __future__ import annotations

import datetime as dt

from ...schema.models import DataPoint, Series, _FrozenModel


class AuctionResult(_FrozenModel):
    """Parsed SEMO auction report: prices, volumes, net positions across NI/ROI."""

    auction_date: dt.datetime | None = None
    delivery_date: dt.date | None = None
    publish_time: dt.datetime | None = None
    series: list[Series]


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


class HrlyForecastImbalance(_FrozenModel):
    """A single row from a hourly forecast imbalance report (PUB_HrlyForecastImbalance)."""

    publish_time: dt.datetime
    start_time: dt.datetime
    total_pn: float
    net_interconnector_schedule: float
    tso_demand_forecast: float
    tso_renewable_forecast: float
    calculated_imbalance: float


class DailyMeterData(_FrozenModel):
    """A single 30-minute metering interval from a D1 daily meter data report."""

    resource_name: str
    start_time: dt.datetime
    end_time: dt.datetime
    metered_mw: float


class PhysicalNotification(_FrozenModel):
    """A single row from a daily final physical notifications report (DPuG BM-023)."""

    resource_name: str
    start_time: dt.datetime
    start_mw: float
    end_time: dt.datetime
    end_mw: float
    under_test: bool
    publish_time: dt.datetime


class Forecast(_FrozenModel):
    name: str
    source: str
    publish_time: dt.datetime
    data: list[DataPoint]


class LTSReport(_FrozenModel):
    publish_time: dt.datetime
    resource_name: str
    start_time: dt.datetime
    scheduled_quantity: float
