# Recommandations produit: Rétention joueurs CoD

> **Données synthétiques uniquement.** Analyse de démonstration portfolio. **Non affilié** à Activision, Beenox, Microsoft Gaming ou *Call of Duty*. Aucune télémétrie réelle. Les chiffres ci-dessous viennent du run SQL local (`sql/01`-`04` + agrégats globaux) sur 5 000 joueurs. Chaque recommandation est une **hypothèse à A/B tester**, pas une vérité terrain.

**Baseline globale :** D1 **44,2 %** · D7 **86,0 %** · D30 **95,2 %** (n = 5 000).

---

## Insight 1: Première journée trop courte = plus fort signal de churn D7

**Evidence :** Le segment `short_first_day` (moins de 20 min le jour d’install) regroupe **608** joueurs (**12,2 %** de la base) avec une rétention D7 de **79,1 %**, soit **−6,9 pp** vs le global (**86,0 %**). C’est l’écart le plus net parmi les quatre segments de risque (`rough_first_kd` 85,1 %, `single_session_nonspender` 87,5 %, `other` 88,7 %).

**Recommendation :** Tester un *onboarding live-ops* ciblé J0 pour les joueurs sous le seuil ~20 min : playlist « first match » plus courte, matchmaking protégé / bots allégés, et nudge in-game / push vers une 2ᵉ session le même jour (objectif : franchir ~25-30 min cumulées J0). Exclure les spenders déjà engagés pour ne pas polluer le signal.

**Success metric :** D7 du segment `short_first_day` (cible primaire) ; secondaire : % de joueurs J0 passant ≥ 20 min, et D1 du même segment. Succès si D7 segment ↑ d’au moins **+3 pp** vs contrôle sans dégrader le D7 global.

**Owner guess :** Live Ops (exécution) + Product (design onboarding)

---

## Insight 2: Les spenders retiennent mieux : monétisation précoce comme levier d’engagement (pas l’inverse)

**Evidence :** Spenders (**848** joueurs, **17,0 %**) : D1 **47,9 %**, D7 **91,4 %**, D30 **98,8 %**. Non-spenders (**4 152**) : D1 **43,5 %**, D7 **84,9 %**, D30 **94,4 %**. Lift D7 ≈ **+6,5 pp**. Attention : corrélation ≠ causation (le flag `spender` est une propension synthétique) : on ne « force » pas l’achat pour retenir.

**Recommendation :** A/B d’une offre *soft* J0-J2 (battle pass trial 3 jours / skin starter gratuit convertible) **uniquement** pour non-spenders avec ≥ 1 session J0, avec message centrée progression / identité, pas pression. Objectif : augmenter l’ancrage (raison de revenir) plutôt que le ARPDAU court terme.

**Success metric :** D7 des non-spenders exposés vs contrôle ; garde-fous : taux d’opt-out / plaintes, et D7 des spenders (ne doit pas baisser). Succès si D7 non-spenders ↑ **≥ +2 pp** avec conversion optionnelle en bonus, pas en KPI primaire.

**Owner guess :** Product (offre & UX) + Live Ops (ciblage / calendrier)

---

## Insight 3: Mix de modes : Warzone un peu plus présent chez les retenus

**Evidence :** Sur les minutes des 7 premiers jours, les joueurs **retenus D7** consacrent **55,2 %** à Warzone vs **51,7 %** chez les churnés ; Multiplayer **34,7 %** vs **37,4 %** ; Campaign **10,1 %** vs **10,9 %**. Écart Warzone ≈ **+3,5 pp**: signal **modeste**, à traiter comme piste d’expérience early-game, pas comme verdict « Warzone = rétention ».

**Recommendation :** Hypothèse à tester : pour les nouveaux joueurs dont la 1ʳᵉ session est Multiplayer ou Campaign et qui n’ont pas encore touché Warzone à J1, proposer un *soft redirect* (playlist découverte Warzone / duo avec ami / mode plus accessible) plutôt qu’un hard gate. Mesurer si l’exposition Warzone early augmente D7 **sans** cannibaliser la satisfaction Multiplayer.

**Success metric :** D7 des joueurs « première mode ≠ Warzone » exposés au redirect vs contrôle ; secondaire : part de minutes Warzone J0-J7 et taux de retour D1. Succès si D7 ↑ **≥ +2 pp** sur la cohorte ciblée, avec NPS / rate limit de plaintes stable.

**Owner guess :** Product (design modes / funnel) + Analytics (instrumentation & lecture A/B)

---

## What I would *not* do

- **Ne pas** sur-réagir aux écarts plateforme : PC / PS5 / Xbox sont quasi plats (D7 **86,1 / 86,7 / 85,3 %**) : une « initiative Xbox » isolée serait du bruit sur ces données.
- **Ne pas** traiter `single_session_nonspender` comme priorité #1 : D7 **87,5 %** (au-dessus du global) : le vrai levier early est `short_first_day`.
- **Ne pas** conclure que « faire payer » améliore la rétention : le lift spender est corrélationnel ; forcer la monétisation peut détruire la confiance.
- **Ne pas** scaler une reco Warzone sans A/B : +3,5 pp de mix minutes n’est pas une preuve causale.
- **Ne pas** présenter ces % comme des benchmarks industrie CoD : dataset **synthétique**, calibré pour démontrer une méthode d’analyse, pas la vérité live-ops.
