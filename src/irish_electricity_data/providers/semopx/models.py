from __future__ import annotations

import datetime as dt

from ...schema.models import DataPoint, _FrozenModel


class PortfolioPosition(_FrozenModel):
    """Represents a single participant/unit cleared position timeseries within a market result."""

    participant: str
    unit_id: str
    order_type: str
    user: str
    positions: list[DataPoint]


class MarketResult(_FrozenModel):
    """Parsed SEMOpx auction market result containing per-portfolio cleared positions."""

    auction: str | None = None
    auction_name: str | None = None
    auction_datetime: dt.datetime | None = None
    publication_datetime: dt.datetime | None = None
    portfolios: list[PortfolioPosition]


class InterconnectorFlow(_FrozenModel):
    """Represents a single interconnector flow interval."""

    interconnector: str
    direction: str
    timestamp: dt.datetime
    scheduled: float
    total_scheduled: float
    publish_time: dt.datetime
