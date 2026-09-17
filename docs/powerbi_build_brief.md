# Brief de construction Power BI: Rétention joueurs CoD

> **Données synthétiques uniquement.** Jeu de démonstration portfolio. **Non affilié** à Activision, Beenox, Microsoft Gaming ou *Call of Duty*. Aucune télémétrie réelle.

Ce brief te permet de construire un `.pbix` en **~2-3 h** dans Power BI Desktop, en **2 pages** (pas 4). Les ordres de grandeur ci-dessous viennent du run SQL local (`analysis.db`, 5 000 joueurs).

---

## 1. Import des données

1. Ouvre **Power BI Desktop** → *Obtenir des données* → **Texte/CSV**.
2. Importe dans cet ordre (depuis la racine du projet) :
   - `data/players.csv`
   - `data/sessions.csv`
   - `data/purchases.csv`
3. Dans Power Query, pour chaque table :
   - Promouvoir la 1ʳᵉ ligne en en-têtes (si pas déjà fait).
   - Types suggérés :
     - **players** : `install_date` → Date ; `skill_factor` → Décimal ; `spender` → Nombre entier
     - **sessions** : `session_date` → Date ; `day_number`, `duration_min`, `kills`, `deaths`, `won`, `session_id` → Entier
     - **purchases** : `purchase_date` → Date ; `amount_usd` → Décimal
4. *Fermer et appliquer*.

**Astuce Power Query (optionnel)**: colonne d’aide rétention côté joueur (fusionner ensuite ou créer en DAX) : tu peux aussi tout faire en mesures (recommandé pour garder le modèle simple).

---

## 2. Relations (modèle)

Dans *Vue modèle* :

| De | Vers | Cardinalité | Filtre croisé |
|----|------|-------------|---------------|
| `players[player_id]` | `sessions[player_id]` | **1 → ∞** | Unique (players filtre sessions) |
| `players[player_id]` | `purchases[player_id]` | **1 → ∞** | Unique |

Ne crée **pas** de relation directe sessions ↔ purchases. `players` est la table dimension.

---

## 3. Mesures DAX (simples)

Crée une table *Mesures* (vide) ou place-les dans `players`.

```dax
Players Count = DISTINCTCOUNT ( players[player_id] )

// Joueur retenu D1 / D7 / D30 = au moins 1 session avec day_number dans la fenêtre
Retained D1 =
VAR retained =
    CALCULATETABLE (
        VALUES ( sessions[player_id] ),
        sessions[day_number] = 1
    )
RETURN DIVIDE ( COUNTROWS ( retained ), [Players Count] )

Retained D7 =
VAR retained =
    CALCULATETABLE (
        VALUES ( sessions[player_id] ),
        sessions[day_number] >= 1,
        sessions[day_number] <= 7
    )
RETURN DIVIDE ( COUNTROWS ( retained ), [Players Count] )

Retained D30 =
VAR retained =
    CALCULATETABLE (
        VALUES ( sessions[player_id] ),
        sessions[day_number] >= 1,
        sessions[day_number] <= 30
    )
RETURN DIVIDE ( COUNTROWS ( retained ), [Players Count] )

D1 % = FORMAT ( [Retained D1], "0.0%" )
D7 % = FORMAT ( [Retained D7], "0.0%" )
D30 % = FORMAT ( [Retained D30], "0.0%" )
```

**Colonne calculée (Page 2: segments de risque)** sur `players` :

```dax
Risk Segment =
VAR day0_min =
    CALCULATE ( SUM ( sessions[duration_min] ), sessions[day_number] = 0 )
VAR day0_sessions =
    CALCULATE ( COUNTROWS ( sessions ), sessions[day_number] = 0 )
VAR day0_kd =
    CALCULATE (
        DIVIDE ( SUM ( sessions[kills] ), SUM ( sessions[deaths] ) ),
        sessions[day_number] = 0
    )
RETURN
    SWITCH (
        TRUE (),
        day0_min < 20, "short_first_day",
        day0_kd < 0.6, "rough_first_kd",
        players[spender] = 0 && day0_sessions = 1, "single_session_nonspender",
        "other"
    )
```

**Cohorte semaine (optionnel, Page 1)**: colonne sur `players` :

```dax
Cohort Week = players[install_date] - WEEKDAY ( players[install_date], 2 ) + 1
// ou en Power Query : Date.StartOfWeek([install_date], Day.Monday)
```

---

## 4. Page 1: Rétention

**Objectif :** vue exécutive D1 / D7 / D30 + plateforme (+ tendance cohorte optionnelle).

### Visuels suggérés

| # | Visuel | Contenu |
|---|--------|---------|
| 1 | **3 cartes** | `[Retained D1]`, `[Retained D7]`, `[Retained D30]` (format %) |
| 2 | **Barres groupées** | Axe : `platform` ; valeurs : D1 %, D7 %, D30 % |
| 3 | **Ligne** (optionnel) | Axe : `Cohort Week` ; valeur : D7 % (éventuellement D1 en 2ᵉ série) |

Filtres de page utiles : `platform`, plage `install_date`.

### Ordres de grandeur attendus (run SQL local)

| Métrique | Valeur |
|----------|--------|
| Joueurs | 5 000 |
| **D1 global** | **~44,2 %** |
| **D7 global** | **~86,0 %** |
| **D30 global** | **~95,2 %** |

**Par plateforme (global) :**

| Plateforme | Joueurs | D1 | D7 | D30 |
|------------|---------|----|----|-----|
| PC | 1 682 | 45,0 % | 86,1 % | 94,9 % |
| PS5 | 1 637 | 43,7 % | 86,7 % | 95,7 % |
| Xbox | 1 681 | 44,0 % | 85,3 % | 94,9 % |

Les écarts plateforme sont **faibles** (~1-2 pp sur D7) : le dashboard doit le montrer clairement (pas de « faux scoop »).

---

## 5. Page 2: Risques

**Objectif :** segments précoces vs D7, mix de modes, spender vs rétention.

### Visuels suggérés

| # | Visuel | Contenu |
|---|--------|---------|
| 1 | **Barres groupées / barres** | Axe : `Risk Segment` ; valeur : D7 % ; info-bulle : # joueurs |
| 2 | **Barres empilées à 100 %** | Légende : `mode` ; axe : retenu D7 (0/1) ; valeur : % des minutes (jours 0-7) |
| 3 | **Barres groupées** | Axe : `spender` (0/1) ; valeurs : D1 %, D7 %, D30 % |

### Résultats SQL de référence (à retrouver à ±0,5 pp)

**Segments de risque vs D7** (ordre du plus risqué) :

| Segment | Joueurs | D7 | Δ vs global (~86,0 %) |
|---------|---------|-----|------------------------|
| `short_first_day` | 608 | **79,1 %** | **−6,9 pp** |
| `rough_first_kd` | 1 598 | 85,1 % | −0,9 pp |
| `single_session_nonspender` | 1 542 | 87,5 % | +1,5 pp |
| `other` | 1 252 | 88,7 % | +2,6 pp |

**Mix de modes (% des minutes, jours ≤ 7)** :

| Statut D7 | Warzone | Multiplayer | Campaign |
|-----------|---------|-------------|----------|
| Churné (0) | 51,7 % | 37,4 % | 10,9 % |
| Retenu (1) | **55,2 %** | 34,7 % | 10,1 % |

→ Les retenus ont une part **Warzone** un peu plus élevée ; l’écart est **modeste** (à présenter comme signal, pas comme preuve causale).

**Spender vs rétention :**

| Spender | Joueurs | D1 | D7 | D30 |
|---------|---------|----|----|-----|
| 0 | 4 152 | 43,5 % | 84,9 % | 94,4 % |
| 1 | 848 | 47,9 % | **91,4 %** | 98,8 % |

→ Lift D7 spenders ≈ **+6,5 pp** vs non-spenders.

---

## 6. Checklist screenshots (portfolio)

Dossier cible : `docs/screenshots/` (déjà créé avec `.gitkeep`).

Exporter **2-4 PNG** (haute résolution, thème clair) :

1. `01_retention_overview.png`: Page 1 complète (cartes + barres plateforme)
2. `02_risk_segments.png`: barres segments de risque
3. `03_mode_mix.png`: mix modes retenus vs churnés *(optionnel)*
4. `04_spender_retention.png`: spender vs D1/D7/D30 *(optionnel)*

Ensuite, lier les images dans le `README.md` racine (section Dashboard).

---

## 7. Estimation temps

| Étape | Durée |
|-------|-------|
| Import + types + relations | ~30-40 min |
| Mesures DAX + colonne Risk Segment | ~40-50 min |
| Page 1 + Page 2 + mise en forme | ~45-60 min |
| Screenshots + lien README | ~15-20 min |
| **Total** | **~2-3 h** |

---

## 8. Livrable attendu

- Fichier local `dashboard/cod-retention.pbix` (**gitignoré** via `*.pbix`)
- 2-4 PNG dans `docs/screenshots/`
- Pas besoin de republier sur le service Power BI pour le portfolio (screenshots suffisent)
