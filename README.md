# Irish Electricity Data

Typed, synchronous Python client for Irish electricity market data. Covers a number of different sources, the EirGrid smartgrid dashboard, SEMO and SEMOpx reports and returns normalised Pydantic models with tz-aware UTC timestamps throughout.

## Data sources

| Provider | Upstream |
|----------|----------|
| `EirGridProvider` | smartgriddashboard.com |
| `SemoProvider` | reports.sem-o.com |
| `SemopxProvider` | reports.semopx.com |

<details>
<summary><strong>EirGridProvider</strong></summary>

| Method | Description | Resolution |
|--------|-------------|------------|
| `get_co2` | CO2 emissions by region | 15 min |
| `get_frequency` | Grid frequency | 5 sec |
| `get_interconnector_flows` | EWIC, Greenlink, and Moyle flows (positive = import) | 15 min |
| `get_outturn` | Wind, solar, and demand actuals (filterable by variable and region) | 15 min |
| `get_outturn_demand` | Demand outturn shortcut | 15 min |
| `get_outturn_solar` | Solar outturn shortcut | 15 min |
| `get_outturn_wind` | Wind outturn shortcut | 15 min |
| `get_snsp` | System Non-Synchronous Penetration, all-island | 30 min |

</details>

<details>
<summary><strong>SemoProvider</strong></summary>

| Method | Description | Resolution |
|--------|-------------|------------|
| `get_5min_imbalance_prices` | Imbalance prices | 5 min |
| `get_auction_results` | Ex-ante auction results - prices/volumes/net position data | daily |
| `get_fpns` | Final physical notifications by trade date | 30 min |
| `get_imbalance_forecast` | Hourly forecast imbalance | hourly |
| `get_imbalance_price_supporting_info` | Supporting detail behind imbalance prices | 5 min |
| `get_lts_schedule` | LTS operational schedule | 30 min |
| `get_metered_generation` | D1 daily metered generation per unit | 30 min |
| `get_settlement_prices` | 30-minute average imbalance settlement prices | 30 min |
| `get_wind_forecast` | Aggregated wind generation forecast | 15 min |

</details>

<details>
<summary><strong>SemopxProvider</strong></summary>

| Method | Description |
|--------|-------------|
| `get_market_result` | Market result for a given auction (DA, IDA1, IDA2, IDA3) and delivery date — includes per-portfolio volumes and prices |

</details>

## Installation

Requires Python 3.12+.

```bash
pip install irish-electricity-data
```

## Quick start

All providers are available through a single `MarketClient` object or they can be instantiated directly. Use it as a context manager to ensure the underlying HTTP connection is closed cleanly.

### EirGrid — wind outturn

```python
import datetime as dt
from irish_electricity_data import MarketClient

with MarketClient() as client:
    series = client.eirgrid.get_outturn_wind(dt.date(2025, 1, 15))
    for point in series.data:
        print(point.timestamp, point.value)
```

### SEMO — 5-minute imbalance prices

```python
import datetime as dt
from irish_electricity_data import MarketClient

with MarketClient() as client:
    prices = client.semo.get_imbalance_prices(
        start=dt.datetime(2025, 1, 15, 0, 0, tzinfo=dt.timezone.utc),
        end=dt.datetime(2025, 1, 15, 23, 55, tzinfo=dt.timezone.utc),
    )
    for p in prices:
        print(p.start_time, p.imbalance_price)
```

### SEMOpx — day-ahead market results

```python
import datetime as dt
from irish_electricity_data import Auction, MarketClient

with MarketClient() as client:
    result = client.semopx.get_market_result(Auction.DAY_AHEAD, dt.date(2025, 1, 15))
    for portfolio in result.portfolios:
        print(portfolio.participant, portfolio.unit_id)
```

## Design

- **Typed**: every method returns a Pydantic model or a list of models; no raw dicts or untyped tuples leak out of the library.
- **Synchronous**: built on `httpx` with HTTP/2. Async support is not planned.
- **No caching**: the library is a thin, faithful transport layer. Caching,
  persistence, and scheduling are the caller's responsibility.
- **Timestamps are UTC**: upstream local or naive times are normalised at the parser boundary.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
