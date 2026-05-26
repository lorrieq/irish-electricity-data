import datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

from irish_electricity_data.providers.semopx import (
    InterconnectorFlow,
    PortfolioPosition,
    parse_interconnector_flows,
    parse_market_result,
)


def test_parse_market_result():
    fixture_path = Path(__file__).parent / "fixtures" / "semopx" / "market_result_day_ahead.csv"
    content = fixture_path.read_text()
    result = parse_market_result(content)

    assert isinstance(result, list)
    assert len(result) > 0

    first = result[0]
    assert isinstance(first, PortfolioPosition)
    assert first.participant == "AARHUS"
    assert first.unit_id == "AU_500145"
    assert first.order_type == "Linear order"
    assert first.user == "AARHUSR01API"
    assert len(first.positions) == 48
    assert first.positions[0].timestamp == dt.datetime(2026, 4, 19, 22, tzinfo=ZoneInfo("UTC"))
    assert first.positions[0].value == 2.0

    last = result[-1]
    assert last.participant == "WFST"
    assert last.unit_id == "GU_404480"
    assert last.order_type == "Linear order"
    assert last.user == "WFST01API"
    assert len(last.positions) == 48
    assert last.positions[0].timestamp == dt.datetime(2026, 4, 19, 22, tzinfo=ZoneInfo("UTC"))
    assert last.positions[0].value == -1.3


def test_parse_interconnector_flows():
    fixture_path = Path(__file__).parent / "fixtures" / "semopx" / "IDA1_InterconnectorFlows.xml"
    content = fixture_path.read_text()
    result = parse_interconnector_flows(content)

    assert isinstance(result, list)
    assert all(isinstance(flow, InterconnectorFlow) for flow in result)

    first = result[0]
    assert first.interconnector == "GREENLINK"
    assert first.direction == "GB2-IE2"
    assert first.timestamp == dt.datetime(2026, 4, 30, 22, tzinfo=ZoneInfo("UTC"))
    assert first.scheduled == 513
    assert first.total_scheduled == 513

    last = result[-1]
    assert last.interconnector == "EWIC"
    assert last.direction == "IE-GB"
    assert last.timestamp == dt.datetime(2026, 5, 1, 21, 30, tzinfo=ZoneInfo("UTC"))
    assert last.scheduled == 0
    assert last.total_scheduled == 0
