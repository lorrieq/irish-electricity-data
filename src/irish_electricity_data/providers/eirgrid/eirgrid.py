from __future__ import annotations

import datetime as dt
from enum import StrEnum

from ...core.constants import TZ_DUBLIN, TZ_UTC
from ...core.exceptions import ProviderError
from ...schema.models import DataPoint
from ..base import BaseProvider
from .models import EirgridCo2Data, EirgridFuelMix, EirgridInterconnectorData, EirgridOutturnData
from .parsers import parse_co2, parse_frequency, parse_fuel_mix, parse_generation, parse_interconnector_flows, parse_outturn, parse_snsp


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
    
    def _fetch_frequency(self, range_id: str, start: dt.datetime, end: dt.datetime) -> list[DataPoint]:
        if range_id == "hour":
            start_str = start.strftime("%d-%b-%Y %H:%M")
            end_str = end.strftime("%d-%b-%Y %H:%M")
        elif range_id == "day":
            start_str = start.strftime("%d-%b-%Y")
            end_str = end.strftime("%d-%b-%Y")
        else:
            raise ValueError("invalid range_id")

        params = {
            "region": "ALL",
            "chartType": "frequency",
            "dateRange": range_id,
            "dateFrom": start_str,
            "dateTo": end_str,
            "areas": "frequency",
        }
        payload = self._get_json("/api/chart/", params=params)
        if not isinstance(payload, dict):
            raise ProviderError("EirGrid frequency response was not a JSON object")
        return parse_frequency(payload)

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

        if start_ist.date() == end_ist.date() and start_ist.hour == end_ist.hour:
            points = self._fetch_frequency("hour", start_ist, end_ist)
        else:
            points = []
            current = start_ist.date()
            end_date = end_ist.date()
            while current <= end_date:
                points.extend(self._fetch_frequency("day", current, current))
                current += dt.timedelta(days=1)

        start_utc = start_ist.astimezone(TZ_UTC)
        end_utc = end_ist.astimezone(TZ_UTC)
        return [p for p in points if start_utc <= p.timestamp <= end_utc]

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

    def get_generation(
        self,
        start: dt.datetime,
        end: dt.datetime | None = None,
    ) -> list[DataPoint]:
        """Fetch 15-minute total generation actuals.

        Only all-island data is available from this endpoint.
        Naive datetimes are assumed to be Dublin local time.
        """
        start_date = _to_ist(start).date()
        end_date = _to_ist(end).date() if end is not None else start_date
        if end_date < start_date:
            raise ValueError("end must be on or after start")

        params = {
            "region": "ALL",
            "chartType": "generation",
            "dateRange": "day",
            "dateFrom": start_date.strftime("%d-%b-%Y"),
            "dateTo": end_date.strftime("%d-%b-%Y"),
            "areas": "generationactual",
        }
        payload = self._get_json("/api/chart/", params=params)
        if not isinstance(payload, dict):
            raise ProviderError("EirGrid generation response was not a JSON object")
        return parse_generation(payload)

    def get_fuel_mix(self) -> EirgridFuelMix:
        """Fetch the average fuel mix breakdown for today.

        Returns energy (MWh) per fuel type averaged over the current day.
        Only all-island data is available from this endpoint.
        """
        params = {
            "area": "fuelmix",
            "region": "ALL",
            "dateRange": "day",
        }
        payload = self._get_json("/api/average-fuel-mix/", params=params)
        if not isinstance(payload, dict):
            raise ProviderError("EirGrid fuel mix response was not a JSON object")
        return parse_fuel_mix(payload)

    def get_snsp(
        self,
        start: dt.datetime,
        end: dt.datetime | None = None,
    ) -> list[DataPoint]:
        """Fetch 30-minute SNSP (System Non-Synchronous Penetration) readings.

        Values are percentages. Only all-island data is available from this endpoint.
        Naive datetimes are assumed to be Dublin local time.
        """
        start_ist = _to_ist(start)
        end_ist = _to_ist(end) if end is not None else start_ist
        if end_ist < start_ist:
            raise ValueError("end must be on or after start")

        points: list[DataPoint] = []
        current = start_ist.date()
        end_date = end_ist.date()
        while current <= end_date:
            date_str = current.strftime("%d-%b-%Y")
            params = {
                "region": "ALL",
                "chartType": "snsp",
                "dateRange": "day",
                "dateFrom": date_str,
                "dateTo": date_str,
                "areas": "SnspAll",
            }
            payload = self._get_json("/api/chart/", params=params)
            if not isinstance(payload, dict):
                raise ProviderError("EirGrid SNSP response was not a JSON object")
            points.extend(parse_snsp(payload))
            current += dt.timedelta(days=1)

        start_utc = start_ist.astimezone(TZ_UTC)
        end_utc = end_ist.astimezone(TZ_UTC)
        return [p for p in points if start_utc <= p.timestamp <= end_utc]
