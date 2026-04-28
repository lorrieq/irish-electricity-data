# Contributing

Contributions are welcome — bug reports, new providers, new report types, fixture updates, and documentation improvements all help.

## Development setup

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
git clone https://github.com/YOUR_FORK/irish-electricity-data.git
cd irish-electricity-data
uv sync
```

## Running tests and linting

```bash
uv run pytest -q          # run the test suite
uv run ruff check .       # lint
uv run ruff format .      # format
```

All tests must pass and `ruff check` must be clean before opening a PR.

## How the project is structured

```
src/irish_electricity_data/
├── client.py               # MarketClient facade
├── core/                   # Transport, retry, exceptions, constants
├── providers/
│   ├── eirgrid/            # EirGrid smart-grid dashboard
│   ├── semo/               # SEMO static reports
│   └── semopx/             # SEMOpx market data
└── schema/
    └── models.py           # All Pydantic return types
tests/
├── fixtures/               # Captured real (slimmed) API responses
└── test_*.py
```

New providers start as a single flat file (`providers/foo.py`) and only grow into a subpackage when the file becomes unwieldy.

## Adding a new report type

The most common contribution. The steps are the same for every report:

**1. Capture a fixture**

Fetch a real response from the upstream API and save it to `tests/fixtures/`.
Trim it down to be small but representative including any edge cases you can see in the data (nulls, negative values, optional fields, DST boundaries).

```bash
# Example — save a raw XML report from SEMO
uv run python -c "
from irish_electricity_data import MarketClient
with MarketClient() as c:
    print(c.semo.fetch_raw_report('PUB_YourReport_20250115.xml'))
" > tests/fixtures/semo_PUB_YourReport.xml
```

**2. Add a Pydantic model**

Add a frozen model to `src/irish_electricity_data/schema/models.py` and export it from `schema/__init__.py`. All timestamps must be `dt.datetime` (tz-aware UTC); use `dt.date` for calendar dates only.

**3. Write the parser**

Add a `parse_*` function to the relevant `providers/*/parsers.py`. Parsers receive raw text (XML or CSV) and return the model or a list of models. They must not make network requests.

**4. Wire up the provider method**

Add a `get_*` method to the provider class that calls a method to fetch the data/report and passes the result to your parser. Multi-report getters follow the pattern in the existing code: call `list_reports`, filter to the date range, fetch and flatten, sort by timestamp.

**5. Write the test**

Every parser must have a unit test backed by the fixture you captured in step 1.
Tests live in `tests/test_<provider>_parsers.py`. They must not hit the network.

```python
def test_parse_your_report():
    fixture = Path(__file__).parent / "fixtures" / "semo_PUB_YourReport.xml"
    result = parse_your_report(fixture.read_text())

    assert len(result) == <expected row count>
    first = result[0]
    assert first.some_field == <expected value>
    # Cover any optional or unusual fields explicitly
```

**6. Export**

Add the parser to `providers/*/\_\_init\_\_.py` and the model to the top-level
`src/irish_electricity_data/__init__.py`.

## Key conventions

- **No network in parsing tests.** Use a captured fixture. If an existing fixture is stale, recapture it and commit the updated file.
- **No caching in the library.** The client fetches on every call; persistence is the caller's concern.
- **Timestamps in, timestamps out.** Naive or local upstream times are converted to tz-aware UTC inside the parser. Nothing with `tzinfo=None` should appear in a returned model.
- **Fixtures over mocks.** Mocks can silently drift from reality; a real captured response catches upstream schema changes.

## Opening a pull request

- Keep the scope small — one report type, one bug fix, or one focused refactor per PR.
- Include the new or updated fixture file in the same commit as the parser and test.
- If you are unsure about the shape of a model or the right place to put something, open an issue first.
- Use of LLMs/AI to assist with development is permitted but the resulting code must follow conventions and code style.
