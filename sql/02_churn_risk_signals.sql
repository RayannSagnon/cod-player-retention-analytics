-- Early signals associated with churn by D7
-- "Churned" here = no session on days 1-7 after install.

WITH flags AS (
  SELECT
    p.player_id,
    p.platform,
    p.spender,
    p.skill_factor,
    COALESCE(SUM(CASE WHEN s.day_number = 0 THEN s.duration_min END), 0) AS day0_minutes,
    COALESCE(SUM(CASE WHEN s.day_number = 0 THEN 1 END), 0) AS day0_sessions,
    COALESCE(AVG(CASE WHEN s.day_number = 0 THEN CAST(s.kills AS FLOAT) / NULLIF(s.deaths, 0) END), 0) AS day0_kd,
    MAX(CASE WHEN s.day_number BETWEEN 1 AND 7 THEN 1 ELSE 0 END) AS retained_d7
  FROM players p
  LEFT JOIN sessions s ON p.player_id = s.player_id
  GROUP BY 1, 2, 3, 4
)
SELECT
  CASE
    WHEN day0_minutes < 20 THEN 'short_first_day'
    WHEN day0_kd < 0.6 THEN 'rough_first_kd'
    WHEN spender = 0 AND day0_sessions = 1 THEN 'single_session_nonspender'
    ELSE 'other'
  END AS risk_segment,
  COUNT(*) AS players,
  ROUND(AVG(retained_d7) * 100, 1) AS d7_retention_pct
FROM flags
GROUP BY 1
ORDER BY d7_retention_pct ASC;
