from __future__ import annotations

import datetime as dt

from ...schema.models import DataPoint, _FrozenModel


class AuctionResult(_FrozenModel):
    """Represents an auction result with prices, volumes and net positions across NI/ROI."""

    price_eur: list[DataPoint]
    price_gbp: list[DataPoint]
    ni_volumes: list[DataPoint]
    ni_net_position: list[DataPoint]
    roi_volumes: list[DataPoint]
    roi_net_position: list[DataPoint]


class ImbalancePriceReport(_FrozenModel):
    """Represents a 5-minute imbalance price period."""

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
    """Represents a 30-minute imbalance settlement period."""

    start_time: dt.datetime
    net_imbalance_volume: float
    imbalance_settlement_price: float


class ImbalancePriceSuppInfo(_FrozenModel):
    """Represents a bid/offer acceptance (BOA) from a 5-minute imbalance price supplementary info period."""

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
    """Represents an hourly forecast imbalance period."""

    publish_time: dt.datetime
    start_time: dt.datetime
    total_pn: float
    net_interconnector_schedule: float
    tso_demand_forecast: float
    tso_renewable_forecast_pd: float
    tso_renewable_forecast_npdr: float
    calculated_imbalance: float


class DailyMeterData(_FrozenModel):
    """Represents a 30-minute D1 metering interval."""

    resource_name: str
    start_time: dt.datetime
    metered_mw: float


class PhysicalNotification(_FrozenModel):
    """Represents a row of FPN data."""

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
    """Represents a row from the LTS operational schedule."""

    publish_time: dt.datetime
    resource_name: str
    start_time: dt.datetime
    scheduled_quantity: float
