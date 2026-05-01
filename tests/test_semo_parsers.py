import datetime as dt
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from irish_electricity_data.providers.semo import (
    parse_auction_report,
    parse_daily_meter_data_report,
    parse_hrly_forecast_imbalance_report,
    parse_imbalance_price_report,
    parse_imbalance_price_supp_info_report,
    parse_imbalance_settlement_report,
    parse_lts_report,
    parse_physical_notifications_report,
    parse_series_chunk,
    parse_wind_forecast_report,
)
from irish_electricity_data.providers.semo import (
    AuctionResult,
    DailyMeterData,
    Forecast,
    HrlyForecastImbalance,
    ImbalancePriceReport,
    ImbalancePriceSuppInfo,
    ImbalanceSettlementReport,
    LTSReport,
    PhysicalNotification,
)
from irish_electricity_data.schema import Series


def test_parse_series_chunk():
    data = [
        ["Index prices", 30, "EUR"],
        ["2026-04-07T22:00:00Z", "2026-04-07T22:30:00Z"],
        [180, 156.61],
    ]

    result = parse_series_chunk("NI", data)

    assert isinstance(result, Series)
    assert result.area == "NI"
    assert result.name == "Index prices"
    assert result.frequency == 30
    assert result.unit == "EUR"
    assert len(result.data) == 2
    assert result.data[0].timestamp == dt.datetime(2026, 4, 7, 22, 0, tzinfo=dt.UTC)
    assert result.data[1].value == 156.61


def test_parse_auction_report():
    fixture_path = Path(__file__).parent / "fixtures" / "semo" / "auction_result_day_ahead.json"
    content = fixture_path.read_text()
    report_content = json.loads(content)
    result = parse_auction_report(report_content)

    assert isinstance(result, AuctionResult)
    assert len(result.series) > 0
    assert all(isinstance(series, Series) for series in result.series)


def test_parse_imbalance_price_report():
    fixture_path = Path(__file__).parent / "fixtures" / "semo" / "PUB_5MinImbalPrc.xml"
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
    fixture_path = Path(__file__).parent / "fixtures" / "semo" / "PUB_30MinAvgImbalPrc.xml"
    result = parse_imbalance_settlement_report(fixture_path.read_text())

    assert isinstance(result, ImbalanceSettlementReport)
    assert result.trade_date == dt.date(2026, 4, 23)
    assert result.start_time == dt.datetime(2026, 4, 23, 15, 0, tzinfo=ZoneInfo("UTC"))
    assert result.end_time == dt.datetime(2026, 4, 23, 15, 30, tzinfo=ZoneInfo("UTC"))
    assert result.publish_time == dt.datetime(2026, 4, 23, 16, 0, 3, tzinfo=ZoneInfo("UTC"))
    assert result.net_imbalance_volume == -50.273
    assert result.imbalance_settlement_price == -22.6


def test_parse_physical_notifications_report():
    fixture_path = Path(__file__).parent / "fixtures" / "semo" / "PUB_DailyFinalPhysicalNotifications.xml"
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


def test_parse_daily_meter_data_report():
    fixture_path = Path(__file__).parent / "fixtures" / "semo" / "PUB_DailyMeterDataD1.xml"
    result = parse_daily_meter_data_report(fixture_path.read_text())

    assert len(result) == 37
    assert all(isinstance(row, DailyMeterData) for row in result)

    first = result[0]
    assert first.resource_name == "I_ROIEWIC"
    assert first.start_time == dt.datetime(2025, 5, 21, 23, 0, tzinfo=dt.UTC)
    assert first.end_time == dt.datetime(2025, 5, 21, 23, 29, 59, tzinfo=dt.UTC)
    assert first.metered_mw == -1.32

    last = result[-1]
    assert last.start_time == dt.datetime(2025, 5, 22, 17, 0, tzinfo=dt.UTC)
    assert last.metered_mw == 176.7


def test_parse_imbalance_price_supp_info_report():
    fixture_path = Path(__file__).parent / "fixtures" / "semo" / "PUB_5MinImbalPrcSuppInfo.xml"
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


def test_parse_hrly_forecast_imbalance_report():
    fixture_path = Path(__file__).parent / "fixtures" / "semo" / "PUB_HrlyForecastImbalance.xml"
    result = parse_hrly_forecast_imbalance_report(fixture_path.read_text())

    assert len(result) == 2
    assert all(isinstance(row, HrlyForecastImbalance) for row in result)

    first = result[0]
    assert first.publish_time == dt.datetime(2025, 5, 26, 8, 0, 31, tzinfo=ZoneInfo("UTC"))
    assert first.start_time == dt.datetime(2025, 5, 26, 9, 0, tzinfo=ZoneInfo("UTC"))
    assert first.total_pn == 334.9
    assert first.net_interconnector_schedule == 1493.0
    assert first.tso_demand_forecast == 4990.0
    assert first.tso_renewable_forecast == 2630.566
    assert first.calculated_imbalance == 531.534

    second = result[1]
    assert second.start_time == dt.datetime(2025, 5, 26, 9, 30, tzinfo=ZoneInfo("UTC"))
    assert second.total_pn == 338.1
    assert second.calculated_imbalance == 268.8


def test_parse_wind_forecast_report():
    fixture_path = Path(__file__).parent / "fixtures" / "semo" / "PUB_15MinAggWindFcst.xml"
    result = parse_wind_forecast_report(fixture_path.read_text())

    assert isinstance(result, Forecast)
    assert len(result.data) == 5
    assert result.publish_time == dt.datetime(2025, 5, 25, 6, 14, 2, tzinfo=ZoneInfo("UTC"))

    first = result.data[0]
    assert first.timestamp == dt.datetime(2025, 5, 24, 22, tzinfo=ZoneInfo("UTC"))
    assert first.value == 3617.03


def test_parse_lts():
    fixture_path = Path(__file__).parent / "fixtures" / "semo" / "PUB_LTSDOperationalSchedule.xml"
    result = parse_lts_report(fixture_path.read_text())

    assert len(result) == 2
    assert all(isinstance(row, LTSReport) for row in result)
