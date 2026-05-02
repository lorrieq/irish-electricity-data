from __future__ import annotations

import datetime as dt

from ...schema.models import DataPoint, _FrozenModel


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
