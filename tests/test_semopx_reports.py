import datetime as dt
import pytest

from irish_electricity_data.sources.semopx._reports import (
    parse_report_list,
    ReportReference,
)


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
