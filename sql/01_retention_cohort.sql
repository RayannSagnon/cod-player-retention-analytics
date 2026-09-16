-- D1 / D7 / D30 retention by install cohort (week)
-- Load CSVs into SQLite or your warehouse, then run.

WITH player_days AS (
  SELECT
    p.player_id,
    p.install_date,
    p.platform,
    p.spender,
    MAX(CASE WHEN s.day_number = 0 THEN 1 ELSE 0 END) AS d0,
    MAX(CASE WHEN s.day_number BETWEEN 1 AND 1 THEN 1 ELSE 0 END) AS d1,
    MAX(CASE WHEN s.day_number BETWEEN 1 AND 7 THEN 1 ELSE 0 END) AS d7,
    MAX(CASE WHEN s.day_number BETWEEN 1 AND 30 THEN 1 ELSE 0 END) AS d30
  FROM players p
  LEFT JOIN sessions s ON p.player_id = s.player_id
  GROUP BY 1, 2, 3, 4
)
SELECT
  date(install_date, 'weekday 0', '-6 days') AS cohort_week, -- SQLite; adapt for other engines
  platform,
  COUNT(*) AS players,
  ROUND(AVG(d1) * 100, 1) AS d1_retention_pct,
  ROUND(AVG(d7) * 100, 1) AS d7_retention_pct,
  ROUND(AVG(d30) * 100, 1) AS d30_retention_pct
FROM player_days
GROUP BY 1, 2
ORDER BY 1, 2;
