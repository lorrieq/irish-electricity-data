from __future__ import annotations

import datetime as dt
from enum import StrEnum

from ...core.constants import TZ_DUBLIN
from ...core.exceptions import ProviderError
from ...schema.models import DataPoint
from ..base import BaseProvider
from .models import EirgridCo2Data, EirgridInterconnectorData, EirgridOutturnData
from .parsers import parse_co2, parse_frequency, parse_interconnector_flows, parse_outturn, parse_snsp


def _to_ist(ts: dt.datetime) -> dt.datetime:
    if ts.tzinfo is None:
        return ts.replace(tzinfo=TZ_DUBLIN)
    return ts.astimezone(TZ_DUBLIN)


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

    def get_co2(
        self,
        start: dt.datetime,
        end: dt.datetime | None = None,
        *,
        region: Region | None = None,
    ) -> EirgridCo2Data:
        """Fetch 15-minute CO2 emission readings.

        When `region` is omitted, all three regions are fetched (one request each)
        and merged. Fields not covered by the request are empty lists.
        Naive datetimes are assumed to be Dublin local time.
        """
        start_date = _to_ist(start).date()
        end_date = _to_ist(end).date() if end is not None else start_date
        if end_date < start_date:
            raise ValueError("end must be on or after start")

        if region is None:
            merged = {}
            for r in Region:
                result = self.get_co2(start, end, region=r)
                for field in EirgridCo2Data.model_fields:
                    points = getattr(result, field)
                    if points:
                        merged[field] = points
            return EirgridCo2Data(**merged)

        params = {
            "region": region.value,
            "chartType": "co2",
            "dateRange": "day",
            "dateFrom": start_date.strftime("%d-%b-%Y"),
            "dateTo": end_date.strftime("%d-%b-%Y"),
            "areas": "co2emission,co2intensity",
        }
        payload = self._get_json("/api/chart/", params=params)
        if not isinstance(payload, dict):
            raise ProviderError("EirGrid CO2 response was not a JSON object")
        return parse_co2(payload)

    def get_frequency(
        self,
        start: dt.datetime,
        end: dt.datetime | None = None,
    ) -> list[DataPoint]:
        """Fetch 5-second grid frequency readings for the given time range.

        Naive datetimes are assumed to be Dublin local time.
        """
        start_ist = _to_ist(start)
        end_ist = _to_ist(end) if end is not None else start_ist
        if end_ist < start_ist:
            raise ValueError("end must be on or after start")

        params = {
            "region": "ALL",
            "chartType": "frequency",
            "dateRange": "hour",
            "dateFrom": start_ist.strftime("%d-%b-%Y %H:%M"),
            "dateTo": end_ist.strftime("%d-%b-%Y %H:%M"),
            "areas": "frequency",
        }
        payload = self._get_json("/api/chart/", params=params)
        if not isinstance(payload, dict):
            raise ProviderError("EirGrid frequency response was not a JSON object")
        return parse_frequency(payload)

    def get_interconnector_flows(
        self,
        start: dt.datetime,
        end: dt.datetime | None = None,
    ) -> EirgridInterconnectorData:
        """Fetch 15-minute interconnector flows for the given delivery-date range.

        Positive values indicate import into Ireland; negative values export.
        Naive datetimes are assumed to be Dublin local time.
        """
        start_date = _to_ist(start).date()
        end_date = _to_ist(end).date() if end is not None else start_date
        if end_date < start_date:
            raise ValueError("end must be on or after start")

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

    def get_outturn(
        self,
        start: dt.datetime,
        end: dt.datetime | None = None,
        *,
        variables: Variable | list[Variable] | None = None,
        region: Region | None = None,
    ) -> EirgridOutturnData:
        """Fetch 15-minute outturn for the given variables and delivery-date range.

        When `region` is omitted, all three regions are fetched (one request each)
        and merged. When `variables` is omitted, all available variables are fetched.
        Fields not covered by the request are empty lists.
        Naive datetimes are assumed to be Dublin local time.
        """
        start_date = _to_ist(start).date()
        end_date = _to_ist(end).date() if end is not None else start_date
        if end_date < start_date:
            raise ValueError("end must be on or after start")

        if region is None:
            merged = {}
            for r in Region:
                result = self.get_outturn(start, end, variables=variables, region=r)
                for field in EirgridOutturnData.model_fields:
                    points = getattr(result, field)
                    if points:
                        merged[field] = points
            return EirgridOutturnData(**merged)

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
        start: dt.datetime,
        end: dt.datetime | None = None,
        *,
        region: Region | None = None,
    ) -> EirgridOutturnData:
        return self.get_outturn(start, end, variables=Variable.DEMAND, region=region)

    def get_outturn_solar(
        self,
        start: dt.datetime,
        end: dt.datetime | None = None,
        *,
        region: Region | None = None,
    ) -> EirgridOutturnData:
        return self.get_outturn(start, end, variables=Variable.SOLAR, region=region)

    def get_outturn_wind(
        self,
        start: dt.datetime,
        end: dt.datetime | None = None,
        *,
        region: Region | None = None,
    ) -> EirgridOutturnData:
        return self.get_outturn(start, end, variables=Variable.WIND, region=region)

    def get_snsp(
        self,
        start: dt.datetime,
        end: dt.datetime | None = None,
    ) -> list[DataPoint]:
        """Fetch 30-minute SNSP (System Non-Synchronous Penetration) readings.

        Values are percentages. Only all-island data is available from this endpoint.
        Naive datetimes are assumed to be Dublin local time.
        """
        start_date = _to_ist(start).date()
        end_date = _to_ist(end).date() if end is not None else start_date
        if end_date < start_date:
            raise ValueError("end must be on or after start")

        params = {
            "region": "ALL",
            "chartType": "snsp",
            "dateRange": "day",
            "dateFrom": start_date.strftime("%d-%b-%Y"),
            "dateTo": end_date.strftime("%d-%b-%Y"),
            "areas": "SnspAll",
        }
        payload = self._get_json("/api/chart/", params=params)
        if not isinstance(payload, dict):
            raise ProviderError("EirGrid SNSP response was not a JSON object")
        return parse_snsp(payload)
