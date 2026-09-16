# Power BI dashboard

Suggested pages (keep it tight):

1. **Retention overview** — D1/D7/D30 by platform + cohort
2. **Risk segments** — early signals vs D7 retention
3. **Mode mix** — retained vs churned (first 7 days)
4. **Spender lens** — retention by spender flag (+ optional revenue)

Import `data/*.csv` → Power Query → relationships:
- `players.player_id` 1→∞ `sessions.player_id`
- `players.player_id` 1→∞ `purchases.player_id`

Export 2–4 screenshots into `docs/screenshots/` for the README.
