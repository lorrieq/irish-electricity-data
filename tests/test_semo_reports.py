import datetime as dt

import pytest

from irish_electricity_data.providers.semo import parse_report_list
from irish_electricity_data.schema import ReportReference


@pytest.fixture
def report_list_sample():
    """Sample static-reports item as returned by the SEMO reports API."""
    return [
        {
            "_id": "69d78a379620d9261f4bbbfd",
            "DPuG_ID": "EA-001",
            "ReportName": "Market Results",
            "Group": ["Market Data"],
            "Dynamic": True,
            "ResourceName": "MarketResult_SEM-DA_PWR-MRC-D+1_20260409100000_20260409105502.csv",
            "Date": "2026-04-10T10:00:00",
            "DateRetention": "2026-04-09",
            "PublishTime": "2026-04-09T10:55:02",
        }
    ]


def test_parse_report_list(report_list_sample):
    result = parse_report_list(report_list_sample)

    assert len(result) == 1
    report = result[0]

    assert isinstance(report, ReportReference)
    assert report.id == "69d78a379620d9261f4bbbfd"
    assert report.dpug_id == "EA-001"
    assert report.report_name == "Market Results"
    assert report.group == ["Market Data"]
    assert report.dynamic is True
    assert report.resource_name == "MarketResult_SEM-DA_PWR-MRC-D+1_20260409100000_20260409105502.csv"
    assert report.publish_time == dt.datetime(2026, 4, 9, 10, 55, 2)
    assert report.date == dt.date(2026, 4, 10)
    assert report.date_retention == dt.date(2026, 4, 9)
