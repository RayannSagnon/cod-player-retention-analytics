#!/usr/bin/env python3
"""Generate synthetic player / session / purchase data for the CoD retention case study.
SYNTHETIC ONLY: not affiliated with Activision, Beenox, or Call of Duty.
"""
import csv, json, random
from datetime import datetime, timedelta, timezone
from pathlib import Path

random.seed(42)
OUT = Path(__file__).resolve().parents[1] / "data"
OUT.mkdir(exist_ok=True)

N_PLAYERS = 5000
START = datetime(2026, 1, 1)
PLATFORMS = ["PC", "PS5", "Xbox"]
MODES = ["Warzone", "Multiplayer", "Campaign"]
REGIONS = ["NA-East", "NA-West", "EU", "LATAM"]

def main():
    players = []
    for i in range(1, N_PLAYERS + 1):
        install = START + timedelta(days=random.randint(0, 90))
        skill = max(0.2, min(2.0, random.gauss(1.0, 0.35)))
        spend_propensity = max(0, random.gauss(0.15, 0.2))
        players.append({
            "player_id": f"P{i:05d}",
            "install_date": install.strftime("%Y-%m-%d"),
            "platform": random.choice(PLATFORMS),
            "region": random.choice(REGIONS),
            "skill_factor": round(skill, 3),
            "spender": 1 if random.random() < spend_propensity else 0,
        })

    sessions, purchases = [], []
    sid = 1
    for p in players:
        install = datetime.strptime(p["install_date"], "%Y-%m-%d")
        active_days = []
        # More realistic mobile/live-game style decay
        for day in range(0, 61):
            if day == 0:
                base = 0.95
            elif day == 1:
                base = 0.42 * (0.9 + 0.15 * p["skill_factor"])
            elif day <= 7:
                base = 0.22 * (0.85 + 0.2 * p["skill_factor"]) * (0.97 ** day)
            else:
                base = 0.08 * (0.85 + 0.25 * p["skill_factor"]) * (0.96 ** (day - 7))
            if p["spender"]:
                base += 0.06
            base = min(0.95, max(0.01, base))
            if random.random() < base:
                active_days.append(day)
            # early abandoners stop being sampled heavily
            if day == 3 and 0 not in active_days and 1 not in active_days:
                break
        for d in active_days:
            sess_date = install + timedelta(days=d)
            for _ in range(1 if random.random() < 0.7 else random.randint(2, 3)):
                mode = random.choices(MODES, weights=[0.55, 0.35, 0.10])[0]
                duration = max(5, int(random.gauss(45, 20)))
                kills = max(0, int(random.gauss(8 * p["skill_factor"], 4)))
                deaths = max(1, int(random.gauss(9 / p["skill_factor"], 3)))
                won = 1 if random.random() < (0.35 + 0.1 * (p["skill_factor"] - 1)) else 0
                sessions.append({
                    "session_id": sid,
                    "player_id": p["player_id"],
                    "session_date": sess_date.strftime("%Y-%m-%d"),
                    "day_number": d,
                    "mode": mode,
                    "duration_min": duration,
                    "kills": kills,
                    "deaths": deaths,
                    "won": won,
                    "platform": p["platform"],
                })
                sid += 1
                if p["spender"] and random.random() < 0.04:
                    purchases.append({
                        "player_id": p["player_id"],
                        "purchase_date": sess_date.strftime("%Y-%m-%d"),
                        "amount_usd": round(random.choice([5, 10, 20, 25]) * random.uniform(0.9, 1.1), 2),
                        "item_type": random.choice(["battle_pass", "skin", "bundle"]),
                    })

    def write(name, rows, fields):
        with open(OUT / name, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            if rows:
                w.writerows(rows)

    write("players.csv", players, list(players[0].keys()))
    write("sessions.csv", sessions, list(sessions[0].keys()))
    write("purchases.csv", purchases, ["player_id", "purchase_date", "amount_usd", "item_type"])
    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_players": len(players),
        "n_sessions": len(sessions),
        "n_purchases": len(purchases),
        "disclaimer": "SYNTHETIC data for portfolio demonstration only. Not affiliated with Activision, Beenox, or Call of Duty.",
    }
    (OUT / "meta.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))

if __name__ == "__main__":
    main()
