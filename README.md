# Dashboard: Rétention joueurs CoD

> **Données synthétiques uniquement.** Non affilié à Activision, Beenox, Microsoft Gaming ou *Call of Duty*.

## Visuels portfolio (Python / matplotlib)

Power BI Desktop n’est **pas disponible** sur la machine de build (Linux) ni sur le laptop Windows actuel. Les captures portfolio sont donc générées avec **pandas + matplotlib**: mêmes métriques que l’analyse SQL (`sql/01`-`04`), layout type BI (cartes + graphiques, thème sombre).

### Régénérer les PNG

```bash
python3 -m venv .venv
.venv/bin/pip install pandas matplotlib
.venv/bin/python scripts/build_dashboard_figures.py
```

Sortie : `docs/screenshots/01_retention_overview.png`, `02_risk_segments.png`, `03_spender_lens.png`.

### Pages

1. **Rétention**: cartes D1/D7/D30 ; barres groupées par plateforme ; tendance cohorte (semaine d’install)
2. **Risques**: segments early-risk vs D7 (highlight `short_first_day`) ; mix de modes retenus vs churnés ; spender vs rétention
3. **Lentille spender** *(optionnel)*: détail D1/D7/D30 spender vs non-spender

## Power BI plus tard

Si tu installes Power BI Desktop, suis le brief 2 pages : [`docs/powerbi_build_brief.md`](../docs/powerbi_build_brief.md) (import CSV, relations, mesures DAX, checklist screenshots). Le fichier `.pbix` reste gitignoré (`*.pbix`).

## Import & modèle (référence PBI)

- `players.player_id` **1→∞** `sessions.player_id`
- `players.player_id` **1→∞** `purchases.player_id`
