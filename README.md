# Penumbra

A backtest harness that answers, per asset lane (`smallcap`, `discovered`,
`crypto`), whether a sharp one-day vol-normalized drop in a volatile name predicts
a positive forward return net of the costs a real marketable order pays. Its end
state is a service that trades automatically; that service is gated on a lane
holding in validation.

- **What the product is:** the spec in
  [`andyvanosdale/penumbra-specs`](https://github.com/andyvanosdale/penumbra-specs)
  (`spec/00`–`spec/07`, `spec/DECISIONS.md`). The spec wins over anything here.
- **How the code is shaped and what is built versus owed:**
  [`docs/architecture.md`](docs/architecture.md).
- **Running, environment, store layout:** [`docs/`](docs/README.md).
- **What was tried and what happened:** [`research_log/`](research_log/). Every
  backtest is pre-registered there before it runs.

## Status

The code in `harness/`, `ingest/` and `experiments/` is the news-project harness
migrated unchanged from `waviisoft/penumbra`. It is the baseline the
implementation issues refactor to the spec; it does not yet implement the spec
(see `docs/architecture.md`, "Legacy baseline").

```bash
pip install -r requirements.txt
pytest -q
```
