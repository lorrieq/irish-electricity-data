import datetime as dt
import logging
from pathlib import Path

import pytest

from irish_electricity_data.core.exceptions import ReportNotFoundError
from irish_electricity_data.schema import Auction
from irish_electricity_data.providers.semopx import SemopxProvider, parse_report_list
from irish_electricity_data.schema import ReportReference


@pytest.fixture
def report_list_sample():
    """Sample market data report from SEMOpx API"""
    return [
        {
            "_id": "69cbc5539620d92af21867b2",
            "DPuG_ID": "EA-004",
            "ReportName": "Bid/Ask Curves",
            "Group": ["Market Data"],
            "Dynamic": True,
            "ResourceName": "BidAskCurves_SEM-DA_20260401_20260331143256.xml",
            "PublishTime": "2026-03-31T14:32:56",
            "Date": "2026-04-01",
            "DateRetention": "2026-04-01",
        }
    ]


def test_parse_report_list(report_list_sample):
    """Test parsing of market data report list"""
    result = parse_report_list(report_list_sample)

    assert len(result) == 1
    report = result[0]

    assert isinstance(report, ReportReference)
    assert report.id == "69cbc5539620d92af21867b2"
    assert report.dpug_id == "EA-004"
    assert report.report_name == "Bid/Ask Curves"
    assert report.group == ["Market Data"]
    assert report.dynamic is True
    assert report.resource_name == "BidAskCurves_SEM-DA_20260401_20260331143256.xml"
    assert report.publish_time == dt.datetime(2026, 3, 31, 14, 32, 56)
    assert report.date == dt.date(2026, 4, 1)
    assert report.date_retention == dt.date(2026, 4, 1)


def _make_ref(resource_name: str, publish_time: dt.datetime, delivery_date: dt.date) -> ReportReference:
    return ReportReference(
        id="abc",
        dpug_id="EA-001",
        report_name="Market Results",
        group=["Market Data"],
        dynamic=False,
        resource_name=resource_name,
        publish_time=publish_time,
        date=delivery_date,
        date_retention=delivery_date,
    )


_DELIVERY = dt.date(2026, 4, 20)
_FIXTURE_CONTENT = (Path(__file__).parent / "fixtures" / "semopx_market_result_day_ahead.csv").read_text()


def test_get_market_result(monkeypatch):
    ref = _make_ref(
        "MarketResult_SEM-DA_PWR-MRC-D+1_20260420100000_20260420105503.csv",
        dt.datetime(2026, 4, 20, 10, 55, 3),
        _DELIVERY,
    )
    provider = SemopxProvider()
    monkeypatch.setattr(provider, "list_reports", lambda **kw: [ref])
    monkeypatch.setattr(provider, "fetch_report", lambda rn: _FIXTURE_CONTENT)

    result = provider.get_market_result(Auction.DAY_AHEAD, _DELIVERY)

    assert result.auction == "SEM-DA"
    assert len(result.portfolios) > 0


def test_get_market_result_not_found(monkeypatch):
    provider = SemopxProvider()
    monkeypatch.setattr(provider, "list_reports", lambda **kw: [])

    with pytest.raises(ReportNotFoundError):
        provider.get_market_result(Auction.DAY_AHEAD, _DELIVERY)


def test_get_market_result_multiple_warns(monkeypatch, caplog):
    ref_early = _make_ref(
        "MarketResult_SEM-DA_PWR-MRC-D+1_20260420100000_20260420105503.csv",
        dt.datetime(2026, 4, 20, 10, 55, 3),
        _DELIVERY,
    )
    ref_late = _make_ref(
        "MarketResult_SEM-DA_PWR-MRC-D+1_20260420100000_20260420120000.csv",
        dt.datetime(2026, 4, 20, 12, 0, 0),
        _DELIVERY,
    )
    fetched: list[str] = []
    provider = SemopxProvider()
    monkeypatch.setattr(provider, "list_reports", lambda **kw: [ref_early, ref_late])
    monkeypatch.setattr(provider, "fetch_report", lambda rn: fetched.append(rn) or _FIXTURE_CONTENT)

    with caplog.at_level(logging.WARNING):
        provider.get_market_result(Auction.DAY_AHEAD, _DELIVERY)

    assert "Multiple" in caplog.text
    assert fetched == [ref_late.resource_name]
