# Changelog

All notable changes to this project will be documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Planned]

---

## [0.1.0] — 2026-04-28

Initial release.

### Added
- `SemoProvider` — SEMO static-reports client covering auction results (EA-001),
  5-minute imbalance prices (BM-025), 30-minute imbalance settlement (BM-026),
  imbalance price supplementary info / BOA rows (BM-027), and daily final physical
  notifications (BM-023)
- `SemopxProvider` — SEMOpx market-results client with report discovery and
  day-ahead / intraday result parsing
- `EirGridProvider` — EirGrid smart-grid dashboard client for 15-minute wind,
  solar, demand outturn and interconnector flows
- `MarketClient` — unified facade over all three providers with shared retry policy
- Typed Pydantic return models for all report types; timestamps normalised to
  tz-aware UTC at the parser boundary
- Per-call jittered exponential backoff via `RetryPolicy`

[0.1.0]: https://github.com/lorrieq/irish-electricity-data/releases/tag/v0.1.0
