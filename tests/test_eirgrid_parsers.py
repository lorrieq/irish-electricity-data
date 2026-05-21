import datetime as dt
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from irish_electricity_data.providers.eirgrid import (
    EirgridCo2Data,
    EirgridFuelMix,
    EirgridInterconnectorData,
    EirgridOutturnData,
    parse_co2,
    parse_frequency,
    parse_fuel_mix,
    parse_generation,
    parse_interconnector_flows,
    parse_outturn,
    parse_snsp,
)

UTC = ZoneInfo("UTC")


def test_parse_outturn_returns_structured_data():
    fixture_path = Path(__file__).parent / "fixtures" / "eirgrid" / "outturn_sample.json"
    payload = json.loads(fixture_path.read_text())

    result = parse_outturn(payload)

    assert isinstance(result, EirgridOutturnData)

    # Each variable has 4 rows in the fixture, 2 of which are null and get dropped.
    assert len(result.solar_ni) == 2
    # 09:00 IST in April is BST (UTC+1) → 08:00 UTC
    assert result.solar_ni[0].timestamp == dt.datetime(2026, 4, 24, 8, 0, tzinfo=UTC)
    assert result.solar_ni[0].value == 57
    assert result.solar_ni[1].timestamp == dt.datetime(2026, 4, 24, 8, 15, tzinfo=UTC)
    assert result.solar_ni[1].value == 65

    assert len(result.wind_ni) == 2
    assert result.wind_ni[0].value == 47

    assert len(result.demand_ni) == 2
    assert result.demand_ni[0].timestamp == dt.datetime(2026, 4, 24, 4, 30, tzinfo=UTC)
    assert result.demand_ni[0].value == 639

    # No all-island or ROI data in the fixture.
    assert result.solar_ie == []
    assert result.solar_roi == []
    assert result.wind_ie == []
    assert result.demand_ie == []


def test_parse_frequency():
    fixture_path = Path(__file__).parent / "fixtures" / "eirgrid" / "frequency_sample.json"
    payload = json.loads(fixture_path.read_text())

    result = parse_frequency(payload)

    # 4 rows in the fixture, 1 null dropped.
    assert len(result) == 3
    # 14-May-2026 09:00:00 Dublin IST (UTC+1) → 08:00:00 UTC
    assert result[0].timestamp == dt.datetime(2026, 5, 14, 8, 0, 0, tzinfo=UTC)
    assert result[0].value == 50.02
    assert result[1].value == 50.0
    assert result[2].value == 50.01


def test_parse_co2():
    fixture_path = Path(__file__).parent / "fixtures" / "eirgrid" / "co2_sample.json"
    payload = json.loads(fixture_path.read_text())

    result = parse_co2(payload)

    assert isinstance(result, EirgridCo2Data)

    # 3 ALL rows in the fixture, 1 null dropped → 2 points.
    assert len(result.co2_ie) == 2
    # 14-May-2026 00:00:00 Dublin IST (UTC+1) → 2026-05-13 23:00:00 UTC
    assert result.co2_ie[0].timestamp == dt.datetime(2026, 5, 13, 23, 0, 0, tzinfo=UTC)
    assert result.co2_ie[0].value == 657
    assert result.co2_ie[1].value == 693

    assert len(result.co2_roi) == 2
    assert result.co2_roi[0].value == 486

    assert result.co2_ni == []

    # 3 ALL intensity rows in the fixture, 1 null dropped → 2 points.
    assert len(result.co2_intensity_ie) == 2
    assert result.co2_intensity_ie[0].timestamp == dt.datetime(2026, 5, 13, 23, 0, 0, tzinfo=UTC)
    assert result.co2_intensity_ie[0].value == 188
    assert result.co2_intensity_ie[1].value == 184

    assert len(result.co2_intensity_ni) == 1
    assert result.co2_intensity_ni[0].value == 248

    assert len(result.co2_intensity_roi) == 1
    assert result.co2_intensity_roi[0].value == 179


def test_parse_snsp():
    fixture_path = Path(__file__).parent / "fixtures" / "eirgrid" / "snsp_sample.json"
    payload = json.loads(fixture_path.read_text())

    result = parse_snsp(payload)

    # 4 rows in the fixture, 1 null dropped.
    assert len(result) == 3
    # 14-May-2026 00:00:00 Dublin IST (UTC+1) → 2026-05-13 23:00:00 UTC
    assert result[0].timestamp == dt.datetime(2026, 5, 13, 23, 0, 0, tzinfo=UTC)
    assert result[0].value == 65.9455
    assert result[1].value == 62.3181
    assert result[2].value == 59.2893


def test_parse_generation():
    fixture_path = Path(__file__).parent / "fixtures" / "eirgrid" / "generation_sample.json"
    payload = json.loads(fixture_path.read_text())

    result = parse_generation(payload)

    # 4 rows in the fixture, 1 null dropped.
    assert len(result) == 3
    # 21-May-2026 00:00:00 Dublin IST (UTC+1) → 2026-05-20 23:00:00 UTC
    assert result[0].timestamp == dt.datetime(2026, 5, 20, 23, 0, 0, tzinfo=UTC)
    assert result[0].value == 3529
    assert result[1].value == 3612
    assert result[2].value == 3748


def test_parse_fuel_mix():
    fixture_path = Path(__file__).parent / "fixtures" / "eirgrid" / "fuel_mix_sample.json"
    payload = json.loads(fixture_path.read_text())

    result = parse_fuel_mix(payload)

    assert isinstance(result, EirgridFuelMix)

    # FUEL_NET_IMPORT is null in the fixture and gets dropped.
    assert result.net_import == []

    # 21-May-2026 00:00:00 Dublin IST (UTC+1) → 2026-05-20 23:00:00 UTC
    expected_ts = dt.datetime(2026, 5, 20, 23, 0, 0, tzinfo=UTC)

    assert len(result.coal) == 1
    assert result.coal[0].timestamp == expected_ts
    assert result.coal[0].value == 0

    assert len(result.gas) == 1
    assert result.gas[0].value == 40906.73

    assert len(result.other_fossil) == 1
    assert result.other_fossil[0].value == 1234.5

    assert len(result.renewable) == 1
    assert result.renewable[0].value == 56158.36


def test_parse_interconnector_flows():
    fixture_path = Path(__file__).parent / "fixtures" / "eirgrid" / "interconnection_sample.json"
    payload = json.loads(fixture_path.read_text())

    result = parse_interconnector_flows(payload)

    assert isinstance(result, EirgridInterconnectorData)

    # 25-Apr-2026 00:00:00 Dublin IST (UTC+1) → 2026-04-24 23:00:00 UTC
    expected_ts = dt.datetime(2026, 4, 24, 23, 0, tzinfo=UTC)

    assert len(result.ewic) == 1
    assert result.ewic[0].timestamp == expected_ts
    assert result.ewic[0].value == 3

    assert result.greenlink[0].value == 520
    assert result.moyle[0].value == 363
    assert result.net[0].value == 886
