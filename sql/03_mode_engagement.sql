-- Mode mix for retained vs churned players (D7)
WITH labels AS (
  SELECT
    p.player_id,
    MAX(CASE WHEN s.day_number BETWEEN 1 AND 7 THEN 1 ELSE 0 END) AS retained_d7
  FROM players p
  LEFT JOIN sessions s ON p.player_id = s.player_id
  GROUP BY 1
),
mode_share AS (
  SELECT
    s.player_id,
    s.mode,
    SUM(s.duration_min) AS minutes
  FROM sessions s
  WHERE s.day_number <= 7
  GROUP BY 1, 2
)
SELECT
  l.retained_d7,
  m.mode,
  ROUND(100.0 * SUM(m.minutes) / SUM(SUM(m.minutes)) OVER (PARTITION BY l.retained_d7), 1) AS pct_of_minutes
FROM labels l
JOIN mode_share m ON l.player_id = m.player_id
GROUP BY 1, 2
ORDER BY 1, 3 DESC;
