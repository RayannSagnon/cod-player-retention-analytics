SELECT
  spender,
  COUNT(*) AS players,
  ROUND(AVG(CASE WHEN d1 = 1 THEN 1.0 ELSE 0 END) * 100, 1) AS d1_pct,
  ROUND(AVG(CASE WHEN d7 = 1 THEN 1.0 ELSE 0 END) * 100, 1) AS d7_pct,
  ROUND(AVG(CASE WHEN d30 = 1 THEN 1.0 ELSE 0 END) * 100, 1) AS d30_pct
FROM (
  SELECT
    p.player_id,
    p.spender,
    MAX(CASE WHEN s.day_number = 1 THEN 1 ELSE 0 END) AS d1,
    MAX(CASE WHEN s.day_number BETWEEN 1 AND 7 THEN 1 ELSE 0 END) AS d7,
    MAX(CASE WHEN s.day_number BETWEEN 1 AND 30 THEN 1 ELSE 0 END) AS d30
  FROM players p
  LEFT JOIN sessions s ON p.player_id = s.player_id
  GROUP BY 1, 2
)
GROUP BY spender;
