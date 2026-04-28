import datetime as dt
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from irish_electricity_data.providers.semo import (
    parse_auction_report,
    parse_imbalance_price_report,
    parse_imbalance_price_supp_info_report,
    parse_imbalance_settlement_report,
    parse_physical_notifications_report,
    parse_series_chunk,
)
from irish_electricity_data.schema import (
    AuctionResult,
    ImbalancePriceReport,
    ImbalancePriceSuppInfo,
    ImbalanceSettlementReport,
    PhysicalNotification,
    Series,
)


def test_parse_series_chunk():
    data = [
        ["Index prices", 30, "EUR"],
        [
            "2026-04-07T22:00:00Z",
            "2026-04-07T22:30:00Z",
            "2026-04-07T23:00:00Z",
            "2026-04-07T23:30:00Z",
            "2026-04-08T00:00:00Z",
            "2026-04-08T00:30:00Z",
            "2026-04-08T01:00:00Z",
            "2026-04-08T01:30:00Z",
            "2026-04-08T02:00:00Z",
            "2026-04-08T02:30:00Z",
            "2026-04-08T03:00:00Z",
            "2026-04-08T03:30:00Z",
            "2026-04-08T04:00:00Z",
            "2026-04-08T04:30:00Z",
            "2026-04-08T05:00:00Z",
            "2026-04-08T05:30:00Z",
            "2026-04-08T06:00:00Z",
            "2026-04-08T06:30:00Z",
            "2026-04-08T07:00:00Z",
            "2026-04-08T07:30:00Z",
            "2026-04-08T08:00:00Z",
            "2026-04-08T08:30:00Z",
            "2026-04-08T09:00:00Z",
            "2026-04-08T09:30:00Z",
            "2026-04-08T10:00:00Z",
            "2026-04-08T10:30:00Z",
            "2026-04-08T11:00:00Z",
            "2026-04-08T11:30:00Z",
            "2026-04-08T12:00:00Z",
            "2026-04-08T12:30:00Z",
            "2026-04-08T13:00:00Z",
            "2026-04-08T13:30:00Z",
            "2026-04-08T14:00:00Z",
            "2026-04-08T14:30:00Z",
            "2026-04-08T15:00:00Z",
            "2026-04-08T15:30:00Z",
            "2026-04-08T16:00:00Z",
            "2026-04-08T16:30:00Z",
            "2026-04-08T17:00:00Z",
            "2026-04-08T17:30:00Z",
            "2026-04-08T18:00:00Z",
            "2026-04-08T18:30:00Z",
            "2026-04-08T19:00:00Z",
            "2026-04-08T19:30:00Z",
            "2026-04-08T20:00:00Z",
            "2026-04-08T20:30:00Z",
            "2026-04-08T21:00:00Z",
            "2026-04-08T21:30:00Z",
        ],
        [
            180,
            156.61,
            152.96,
            151.34,
            148.25,
            148.83,
            159.61,
            162.3,
            162.8,
            167.2,
            162.82,
            170,
            156.2,
            182.88,
            183.7,
            217.4,
            253.3,
            262.29,
            264.44,
            265.39,
            307.63,
            257.94,
            217.05,
            188.7,
            263.3,
            200,
            188,
            169.35,
            158.4,
            134.94,
            133.19,
            130.48,
            127.4,
            127.6,
            130.48,
            139.7,
            144,
            163.32,
            186.67,
            202.4,
            192.05,
            193.77,
            177.95,
            166.83,
            159.38,
            141.03,
            134.15,
            124.62,
        ],
    ]

    result = parse_series_chunk("NI", data)

    assert isinstance(result, Series)
    assert result.area == "NI"
    assert result.name == "Index prices"
    assert result.frequency == 30
    assert result.unit == "EUR"
    assert len(result.data) == 48
    assert result.data[0].timestamp == dt.datetime(2026, 4, 7, 22, 0, tzinfo=dt.UTC)
    assert result.data[1].value == 156.61


def test_parse_auction_report():
    fixture_path = Path(__file__).parent / "fixtures" / "semo_auction_result_day_ahead.json"
    content = fixture_path.read_text()
    report_content = json.loads(content)
    result = parse_auction_report(report_content)

    assert isinstance(result, AuctionResult)
    assert len(result.series) > 0
    assert all(isinstance(series, Series) for series in result.series)


def test_parse_imbalance_price_report():
    fixture_path = Path(__file__).parent / "fixtures" / "semo_5min_imbalance_price.xml"
    result = parse_imbalance_price_report(fixture_path.read_text())

    assert isinstance(result, ImbalancePriceReport)
    assert result.trade_date == dt.date(2026, 4, 23)
    assert result.start_time == dt.datetime(2026, 4, 23, 11, 15, tzinfo=ZoneInfo("UTC"))
    assert result.end_time == dt.datetime(2026, 4, 23, 11, 20, tzinfo=ZoneInfo("UTC"))
    assert result.publish_time == dt.datetime(2026, 4, 23, 11, 37, 40, tzinfo=ZoneInfo("UTC"))
    assert result.net_imbalance_volume == -9.073
    assert result.imbalance_price == 6.24
    assert result.default_price_usage is False
    assert result.asp_price_usage is False
    assert result.total_unit_availability == 11228.58
    assert result.demand_control_volume == 0
    assert result.pmea == -317.87
    assert result.qpar == 10
    assert result.administered_scarcity_price == -1000
    assert result.market_backup_price == 83.77
    assert result.short_term_reserve_quantity == 5341.616
    assert result.operating_reserve_requirement == 475.62


def test_parse_imbalance_settlement_report():
    fixture_path = Path(__file__).parent / "fixtures" / "semo_30min_imbalance_settlement.xml"
    result = parse_imbalance_settlement_report(fixture_path.read_text())

    assert isinstance(result, ImbalanceSettlementReport)
    assert result.trade_date == dt.date(2026, 4, 23)
    assert result.start_time == dt.datetime(2026, 4, 23, 15, 0, tzinfo=ZoneInfo("UTC"))
    assert result.end_time == dt.datetime(2026, 4, 23, 15, 30, tzinfo=ZoneInfo("UTC"))
    assert result.publish_time == dt.datetime(2026, 4, 23, 16, 0, 3, tzinfo=ZoneInfo("UTC"))
    assert result.net_imbalance_volume == -50.273
    assert result.imbalance_settlement_price == -22.6


def test_parse_physical_notifications_report():
    fixture_path = Path(__file__).parent / "fixtures" / "semo_PUB_DailyFinalPhysicalNotifications.xml"
    result = parse_physical_notifications_report(fixture_path.read_text())

    assert len(result) == 26
    assert all(isinstance(row, PhysicalNotification) for row in result)

    first = result[0]
    assert first.resource_name == "GU_503960"
    assert first.start_time == dt.datetime(2026, 4, 27, 16, 31, tzinfo=ZoneInfo("UTC"))
    assert first.start_mw == 0.0
    assert first.end_time == dt.datetime(2026, 4, 27, 17, 0, tzinfo=ZoneInfo("UTC"))
    assert first.end_mw == 0.0
    assert first.under_test is False
    assert first.publish_time == dt.datetime(2026, 4, 28, 9, 15, 3, tzinfo=ZoneInfo("UTC"))

    # Negative MW values (exports)
    neg_row = result[11]  # ROW=5530: StartMW=0, EndMW=-12.5
    assert neg_row.start_mw == 0.0
    assert neg_row.end_mw == -12.5


def test_parse_imbalance_price_supp_info_report():
    fixture_path = Path(__file__).parent / "fixtures" / "semo_PUB_5MinImbalPrcSuppInfo.xml"
    result = parse_imbalance_price_supp_info_report(fixture_path.read_text())

    assert len(result) == 22
    assert all(isinstance(row, ImbalancePriceSuppInfo) for row in result)

    first = result[0]
    assert first.trade_date == dt.date(2026, 4, 27)
    assert first.start_time == dt.datetime(2026, 4, 27, 7, 20, tzinfo=ZoneInfo("UTC"))
    assert first.end_time == dt.datetime(2026, 4, 27, 7, 25, tzinfo=ZoneInfo("UTC"))
    assert first.publish_time == dt.datetime(2026, 4, 27, 7, 42, 47, tzinfo=ZoneInfo("UTC"))
    assert first.participant_name == "PT_400024"
    assert first.resource_name == "GU_400121"
    assert first.pboa == 102.48
    assert first.qboa == 0.425
    assert first.rank == 14
    assert first.so_flag is True
    assert first.emergency_flag is True
    assert first.non_marginal_flag is False
    assert first.imbalance_price_flag is False
    assert first.net_imbalance_volume_tag == 1.0
    assert first.net_imbalance_volume == 3.555
    assert first.non_energy_flags is None
    assert first.constraint_id is None

    # Row 17 (index 16) has optional non-energy fields
    non_energy_row = result[16]
    assert non_energy_row.non_energy_flags == 0
    assert non_energy_row.constraint_id == "S_SEC_NI"
