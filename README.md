# Call of Duty — Player Retention Analytics (Case Study)

**Portfolio case study** for product analytics / business intelligence roles (e.g. studio live-ops & player insights).

> **Synthetic data only.** Generated for demonstration. **Not affiliated with** Activision, Beenox, Microsoft Gaming, or *Call of Duty*. No real player telemetry.

## Why this exists

Studios running live games need analysts who can turn session data into **retention insights** and **product recommendations**. This project shows that loop end-to-end:

1. Define retention questions (D1 / D7 / D30)
2. Model a realistic synthetic dataset
3. SQL analysis
4. Dashboard (Power BI)
5. Three concrete product recommendations

Built by [Rayann Sagnon](https://rayannsagnon.com) — product-minded builder, Electrical Engineering & Systems @ University of Ottawa.

## Status

| Piece | Status |
|-------|--------|
| Synthetic dataset + generator | Done |
| Schema docs | Done |
| Starter SQL | Done |
| Power BI dashboard | To do (see `dashboard/`) |
| Product recommendations write-up | Template ready (`docs/product_recommendations_template.md`) |

## Dataset (quick facts)

See `data/meta.json` after generation. Default run:

- ~5,000 players
- ~100k+ sessions over ~60 days post-install
- Optional purchases for a spender segment

Regenerate:

```bash
python3 scripts/generate_synthetic_data.py
```

## Schema

See [`docs/schema.md`](docs/schema.md).

## SQL

| File | Question |
|------|----------|
| `sql/01_retention_cohort.sql` | D1/D7/D30 by cohort × platform |
| `sql/02_churn_risk_signals.sql` | Early risk segments vs D7 |
| `sql/03_mode_engagement.sql` | Mode mix retained vs churned |
| `sql/04_spender_vs_retention.sql` | Spender flag vs retention |

Load CSVs into SQLite / DuckDB / BigQuery / Power BI as you prefer. Some date functions are SQLite-oriented — adapt if needed.

### Quick SQLite load example

```bash
sqlite3 analysis.db <<'SQL'
.mode csv
.import data/players.csv players
.import data/sessions.csv sessions
.import data/purchases.csv purchases
SQL
sqlite3 analysis.db < sql/04_spender_vs_retention.sql
```

## Dashboard

See [`dashboard/README.md`](dashboard/README.md).

## Product recommendations

Draft in [`docs/product_recommendations_template.md`](docs/product_recommendations_template.md). Target: **3 actions**, each with evidence + success metric.

## Stack

Python 3 · CSV · SQL · Power BI (planned)

## License

MIT for code/docs. Dataset is synthetic fiction for education/portfolio use only.
