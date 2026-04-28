import datetime as dt
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from irish_electricity_data.providers.eirgrid import parse_interconnector_flows, parse_outturn
from irish_electricity_data.schema import Series

UTC = ZoneInfo("UTC")


def test_parse_outturn_groups_by_region_and_variable():
    fixture_path = Path(__file__).parent / "fixtures" / "eirgrid_outturn_sample.json"
    payload = json.loads(fixture_path.read_text())

    result = parse_outturn(payload)

    assert all(isinstance(s, Series) for s in result)
    keys = {(s.area, s.name) for s in result}
    assert keys == {("NI", "Solar"), ("NI", "Wind"), ("NI", "Demand")}

    for s in result:
        assert s.frequency == 15
        assert s.unit == "MW"
        assert all(p.value is not None for p in s.data)

    # Each variable has 4 rows in the fixture, 2 of which are null and get dropped.
    solar = next(s for s in result if s.name == "Solar")
    assert len(solar.data) == 2
    # 09:00 IST in April is BST (UTC+1) → 08:00 UTC
    assert solar.data[0].timestamp == dt.datetime(2026, 4, 24, 8, 0, tzinfo=UTC)
    assert solar.data[0].value == 57
    assert solar.data[-1].timestamp == dt.datetime(2026, 4, 24, 8, 15, tzinfo=UTC)
    assert solar.data[-1].value == 65

    demand = next(s for s in result if s.name == "Demand")
    assert len(demand.data) == 2
    assert demand.data[0].timestamp == dt.datetime(2026, 4, 24, 4, 30, tzinfo=UTC)
    assert demand.data[0].value == 639


def test_parse_interconnector_flows():
    fixture_path = Path(__file__).parent / "fixtures" / "eirgrid_interconnection_sample.json"
    payload = json.loads(fixture_path.read_text())

    result = parse_interconnector_flows(payload)

    assert all(isinstance(s, Series) for s in result)
    assert all(s.frequency == 15 for s in result)
    assert all(s.unit == "MW" for s in result)

    by_name = {s.name: s for s in result}
    assert set(by_name) == {"EWIC", "GREENLINK", "MOYLE", "Net"}

    # 25-Apr-2026 00:00:00 Dublin IST (UTC+1) → 2026-04-24 23:00:00 UTC
    expected_ts = dt.datetime(2026, 4, 24, 23, 0, tzinfo=UTC)

    ewic = by_name["EWIC"]
    assert ewic.area == "ROI"
    assert len(ewic.data) == 1
    assert ewic.data[0].timestamp == expected_ts
    assert ewic.data[0].value == 3

    greenlink = by_name["GREENLINK"]
    assert greenlink.area == "ROI"
    assert greenlink.data[0].value == 520

    moyle = by_name["MOYLE"]
    assert moyle.area == "NI"
    assert moyle.data[0].value == 363

    net = by_name["Net"]
    assert net.area == "ALL"
    assert net.data[0].value == 886
