from __future__ import annotations

import datetime as dt
from enum import StrEnum

from ...core.exceptions import ProviderError
from ...schema.models import Series
from ..base import BaseProvider, ProviderCapability
from .parsers import parse_interconnector_flows, parse_outturn


class Variable(StrEnum):
    """The outturn variables the EirGrid chart API exposes via the `areas` param."""

    SOLAR = "solaractual"
    WIND = "windactual"
    DEMAND = "demandactual"


class Region(StrEnum):
    ALL = "ALL"
    ROI = "ROI"
    NI = "NI"


class Interconnector(StrEnum):
    EWIC = "EWIC"
    GREENLINK = "GREENLINK"
    MOYLE = "MOYLE"


class EirGridProvider(BaseProvider):
    """EirGrid smartgriddashboard provider.

    Hits the same unofficial chart endpoint the dashboard uses. Returns 15-minute
    outturn (actuals) only; forecast flows are not wired up.
    """

    name = "eirgrid"
    base_url = "https://www.smartgriddashboard.com"
    capabilities = frozenset(
        {
            ProviderCapability.GENERATION,
            ProviderCapability.DEMAND,
            ProviderCapability.WIND,
            ProviderCapability.SOLAR,
            ProviderCapability.INTERCONNECTOR,
        }
    )

    def get_outturn(
        self,
        start_date: dt.date,
        end_date: dt.date | None = None,
        *,
        variables: Variable | list[Variable] | None = None,
        region: Region = Region.ALL,
    ) -> list[Series]:
        """Fetch 15-minute outturn for the given variables and delivery-date range.

        When `variables` is omitted, all available variables are fetched. Returns
        one `Series` per (Region, variable) in the response.
        """
        if end_date is None:
            end_date = start_date
        if end_date < start_date:
            raise ValueError("end_date must be on or after start_date")

        if variables is None:
            variables = list(Variable)
        elif isinstance(variables, Variable):
            variables = [variables]

        params = {
            "region": region.value,
            "chartType": "default",
            "dateRange": "day",
            "dateFrom": start_date.strftime("%d-%b-%Y"),
            "dateTo": end_date.strftime("%d-%b-%Y"),
            "areas": ",".join(v.value for v in variables),
        }
        payload = self._get_json("/api/chart/", params=params)
        if not isinstance(payload, dict):
            raise ProviderError("EirGrid outturn response was not a JSON object")
        return parse_outturn(payload)

    def get_outturn_demand(
        self,
        start_date: dt.date,
        end_date: dt.date | None = None,
        *,
        region: Region = Region.ALL,
    ) -> Series:
        return self.get_outturn(start_date, end_date, variables=Variable.DEMAND, region=region)

    def get_outturn_solar(
        self,
        start_date: dt.date,
        end_date: dt.date | None = None,
        *,
        region: Region = Region.ALL,
    ) -> Series:
        return self.get_outturn(start_date, end_date, variables=Variable.SOLAR, region=region)

    def get_outturn_wind(
        self,
        start_date: dt.date,
        end_date: dt.date | None = None,
        *,
        region: Region = Region.ALL,
    ) -> Series:
        return self.get_outturn(start_date, end_date, variables=Variable.WIND, region=region)

    def get_interconnector_flows(
        self,
        start_date: dt.date,
        end_date: dt.date | None = None,
    ) -> list[Series]:
        """Fetch 15-minute interconnector flows for the given delivery-date range.

        Returns one `Series` per (Region, interconnector/net) in the response.
        Positive values indicate import into Ireland; negative values export.
        """
        if end_date is None:
            end_date = start_date
        if end_date < start_date:
            raise ValueError("end_date must be on or after start_date")

        params = {
            "region": "ALL",
            "chartType": "interconnection",
            "dateRange": "day",
            "dateFrom": start_date.strftime("%d-%b-%Y"),
            "dateTo": end_date.strftime("%d-%b-%Y"),
            "areas": "interconnection",
        }
        payload = self._get_json("/api/chart/", params=params)
        if not isinstance(payload, dict):
            raise ProviderError("EirGrid interconnection response was not a JSON object")
        return parse_interconnector_flows(payload)
