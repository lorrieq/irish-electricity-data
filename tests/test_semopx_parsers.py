import datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

from irish_electricity_data.providers.semopx import parse_market_result
from irish_electricity_data.schema import MarketResult


def test_parse_market_result():
    fixture_path = Path(__file__).parent / "fixtures" / "semopx_market_result_day_ahead.csv"
    content = fixture_path.read_text()
    result = parse_market_result(content)

    assert isinstance(result, MarketResult)
    assert len(result.portfolios) > 0

    first = result.portfolios[0]
    assert first.participant == "AARHUS"
    assert first.unit_id == "AU_500145"
    assert first.order_type == "Linear order"
    assert first.user == "AARHUSR01API"
    assert len(first.positions) == 48
    assert first.positions[0].timestamp == dt.datetime(2026, 4, 19, 22, tzinfo=ZoneInfo("UTC"))
    assert first.positions[0].value == 2.0

    last = result.portfolios[-1]
    assert last.participant == "WFST"
    assert last.unit_id == "GU_404480"
    assert last.order_type == "Linear order"
    assert last.user == "WFST01API"
    assert len(last.positions) == 48
    assert last.positions[0].timestamp == dt.datetime(2026, 4, 19, 22, tzinfo=ZoneInfo("UTC"))
    assert last.positions[0].value == -1.3
