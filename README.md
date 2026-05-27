# Irish Electricity Data

[![codecov](https://codecov.io/gh/lorrieq/irish-electricity-data/graph/badge.svg)](https://codecov.io/gh/lorrieq/irish-electricity-data)

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

### EirGrid — outturn wind production

```python
import datetime as dt
from irish_electricity_data import MarketClient

with MarketClient() as client:
    start, end = dt.datetime(2025, 1, 15, 10), dt.datetime(2025, 1, 15, 15)
    data = client.eirgrid.get_outturn_wind(start, end)
    print(data.wind_ie)
```

### SEMO — Imbalance settlement prices

```python
import datetime as dt
from irish_electricity_data import MarketClient

with MarketClient() as client:
    data = client.semo.get_settlement_prices(
        start=dt.datetime(2026, 5, 20),
        end=dt.datetime(2026, 5, 20, 10),
    )
```

### SEMOpx — Cleared positions per unit

```python
import datetime as dt
from irish_electricity_data import Auction, MarketClient

with MarketClient() as client:
    yesterday = dt.date.today() - dt.timedelta(days=1)
    result = client.semopx.get_market_result(Auction.DAY_AHEAD, yesterday)

    elem = result[0]
    print(elem.unit_id)
    print(elem.positions)

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
