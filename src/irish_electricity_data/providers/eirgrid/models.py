from __future__ import annotations

from ...schema.models import DataPoint, _FrozenModel


class EirgridInterconnectorData(_FrozenModel):
    """15-minute interconnector flow readings.

    Fields are empty lists when not present in the response.
    """

    ewic: list[DataPoint] = []
    greenlink: list[DataPoint] = []
    moyle: list[DataPoint] = []
    net: list[DataPoint] = []


class EirgridCo2Data(_FrozenModel):
    """15-minute CO2 emission and intensity readings across IE/NI/ROI.

    Fields are empty lists when not requested or not present in the response.
    `_ie` fields correspond to the all-island (ALL) region.
    CO2 intensity (gCO2/kWh) is available per region.
    """

    co2_ie: list[DataPoint] = []
    co2_ni: list[DataPoint] = []
    co2_roi: list[DataPoint] = []
    co2_intensity_ie: list[DataPoint] = []
    co2_intensity_ni: list[DataPoint] = []
    co2_intensity_roi: list[DataPoint] = []


class EirgridFuelMix(_FrozenModel):
    """Fuel mix breakdown. Values in MWh per fuel type.

    Fields are empty lists when not present in the response.
    """

    coal: list[DataPoint] = []
    gas: list[DataPoint] = []
    net_import: list[DataPoint] = []
    other_fossil: list[DataPoint] = []
    renewable: list[DataPoint] = []


class EirgridOutturnData(_FrozenModel):
    """15-minute outturn actuals for wind, demand, and solar across IE/NI/ROI.

    Fields are empty lists when not requested or not present in the response.
    `_ie` fields correspond to the all-island (ALL) region.
    """

    wind_ie: list[DataPoint] = []
    wind_ni: list[DataPoint] = []
    wind_roi: list[DataPoint] = []
    demand_ie: list[DataPoint] = []
    demand_ni: list[DataPoint] = []
    demand_roi: list[DataPoint] = []
    solar_ie: list[DataPoint] = []
    solar_ni: list[DataPoint] = []
    solar_roi: list[DataPoint] = []
