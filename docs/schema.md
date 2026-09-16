# Data schema (synthetic)

> **Disclaimer:** All data is synthetic and generated for portfolio demonstration. Not affiliated with Activision, Beenox, or Call of Duty. No real player data.

## `players.csv`
| Column | Type | Description |
|--------|------|-------------|
| player_id | text | Unique player id (`P00001`…) |
| install_date | date | First install / acquisition date |
| platform | text | PC / PS5 / Xbox |
| region | text | NA-East / NA-West / EU / LATAM |
| skill_factor | float | Synthetic skill proxy (~0.2–2.0) |
| spender | 0/1 | Flag for higher monetization propensity |

## `sessions.csv`
| Column | Type | Description |
|--------|------|-------------|
| session_id | int | Unique session id |
| player_id | text | FK → players |
| session_date | date | Calendar date of session |
| day_number | int | Days since install (0 = install day) |
| mode | text | Warzone / Multiplayer / Campaign |
| duration_min | int | Session length (minutes) |
| kills | int | Kills in session |
| deaths | int | Deaths in session |
| won | 0/1 | Match/outcome win flag (simplified) |
| platform | text | Platform for the session |

## `purchases.csv`
| Column | Type | Description |
|--------|------|-------------|
| player_id | text | FK → players |
| purchase_date | date | Purchase date |
| amount_usd | float | Amount in USD |
| item_type | text | battle_pass / skin / bundle |
