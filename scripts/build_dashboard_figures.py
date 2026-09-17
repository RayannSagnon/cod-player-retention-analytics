#!/usr/bin/env python3
"""
Build Power BI-equivalent portfolio dashboard PNGs for CoD Player Retention.

Metrics mirror sql/01-04 (D1/D7/D30, risk segments, mode mix, spender vs retention).
Regenerate:
  .venv/bin/python scripts/build_dashboard_figures.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

DISCLAIMER = (
    "Données SYNTHÉTIQUES: démonstration portfolio uniquement. "
    "Non affilié à Activision, Beenox, Microsoft Gaming ou Call of Duty."
)

# Dark BI-style palette
BG = "#0f1419"
PANEL = "#1a2332"
CARD = "#243044"
ACCENT = "#00bcd4"
ACCENT2 = "#7c4dff"
ACCENT3 = "#26a69a"
WARN = "#ff7043"
TEXT = "#e8eef7"
MUTED = "#8b9bb4"
GRID = "#2a3548"
BAR_D1 = "#42a5f5"
BAR_D7 = "#26c6da"
BAR_D30 = "#66bb6a"
RISK_COLORS = {
    "short_first_day": "#ff7043",
    "rough_first_kd": "#ffa726",
    "single_session_nonspender": "#42a5f5",
    "other": "#66bb6a",
}
MODE_COLORS = {
    "Warzone": "#7c4dff",
    "Multiplayer": "#26c6da",
    "Campaign": "#66bb6a",
}


def load_data():
    players = pd.read_csv(DATA / "players.csv", parse_dates=["install_date"])
    sessions = pd.read_csv(DATA / "sessions.csv", parse_dates=["session_date"])
    purchases = pd.read_csv(DATA / "purchases.csv", parse_dates=["purchase_date"])
    return players, sessions, purchases


def compute_player_retention(players: pd.DataFrame, sessions: pd.DataFrame) -> pd.DataFrame:
    """Per-player D1 / D7 / D30 flags matching sql/01 and sql/04."""
    s = sessions.copy()
    d1 = (
        s.loc[s["day_number"] == 1, "player_id"]
        .drop_duplicates()
        .to_frame()
        .assign(d1=1)
    )
    d7 = (
        s.loc[s["day_number"].between(1, 7), "player_id"]
        .drop_duplicates()
        .to_frame()
        .assign(d7=1)
    )
    d30 = (
        s.loc[s["day_number"].between(1, 30), "player_id"]
        .drop_duplicates()
        .to_frame()
        .assign(d30=1)
    )
    out = players.merge(d1, on="player_id", how="left")
    out = out.merge(d7, on="player_id", how="left")
    out = out.merge(d30, on="player_id", how="left")
    for c in ("d1", "d7", "d30"):
        out[c] = out[c].fillna(0).astype(int)
    return out


def compute_risk_segments(players: pd.DataFrame, sessions: pd.DataFrame) -> pd.DataFrame:
    """Risk segments matching sql/02_churn_risk_signals.sql (CASE order)."""
    day0 = sessions.loc[sessions["day_number"] == 0].copy()
    day0_agg = (
        day0.groupby("player_id")
        .agg(
            day0_minutes=("duration_min", "sum"),
            day0_sessions=("session_id", "count"),
            day0_kills=("kills", "sum"),
            day0_deaths=("deaths", "sum"),
        )
        .reset_index()
    )
    # AVG of per-session K/D as in SQL: AVG(kills/NULLIF(deaths,0))
    day0["kd"] = day0["kills"] / day0["deaths"].replace(0, np.nan)
    kd_avg = day0.groupby("player_id")["kd"].mean().reset_index(name="day0_kd")
    day0_agg = day0_agg.merge(kd_avg, on="player_id", how="left")

    retained = (
        sessions.loc[sessions["day_number"].between(1, 7), "player_id"]
        .drop_duplicates()
        .to_frame()
        .assign(retained_d7=1)
    )

    flags = players.merge(day0_agg, on="player_id", how="left")
    flags = flags.merge(retained, on="player_id", how="left")
    flags["day0_minutes"] = flags["day0_minutes"].fillna(0)
    flags["day0_sessions"] = flags["day0_sessions"].fillna(0)
    flags["day0_kd"] = flags["day0_kd"].fillna(0)
    flags["retained_d7"] = flags["retained_d7"].fillna(0).astype(int)

    def segment(row):
        if row["day0_minutes"] < 20:
            return "short_first_day"
        if row["day0_kd"] < 0.6:
            return "rough_first_kd"
        if row["spender"] == 0 and row["day0_sessions"] == 1:
            return "single_session_nonspender"
        return "other"

    flags["risk_segment"] = flags.apply(segment, axis=1)
    return flags


def compute_mode_mix(players: pd.DataFrame, sessions: pd.DataFrame) -> pd.DataFrame:
    """Mode mix % of minutes (day_number <= 7) for retained vs churned D7 (sql/03)."""
    labels = (
        sessions.loc[sessions["day_number"].between(1, 7), "player_id"]
        .drop_duplicates()
        .to_frame()
        .assign(retained_d7=1)
    )
    labels = players[["player_id"]].merge(labels, on="player_id", how="left")
    labels["retained_d7"] = labels["retained_d7"].fillna(0).astype(int)

    mode_share = (
        sessions.loc[sessions["day_number"] <= 7]
        .groupby(["player_id", "mode"], as_index=False)["duration_min"]
        .sum()
        .rename(columns={"duration_min": "minutes"})
    )
    m = labels.merge(mode_share, on="player_id", how="inner")
    tot = m.groupby("retained_d7")["minutes"].transform("sum")
    agg = m.groupby(["retained_d7", "mode"], as_index=False)["minutes"].sum()
    tot2 = agg.groupby("retained_d7")["minutes"].transform("sum")
    agg["pct_of_minutes"] = (100.0 * agg["minutes"] / tot2).round(1)
    return agg


def cohort_week(series: pd.Series) -> pd.Series:
    """Monday-start week like SQLite date(install_date, 'weekday 0', '-6 days')."""
    # pandas: week starting Monday
    return series.dt.to_period("W-SUN").apply(lambda p: p.start_time).dt.normalize()


def style_ax(ax, title: str | None = None):
    ax.set_facecolor(PANEL)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.yaxis.label.set_color(MUTED)
    ax.xaxis.label.set_color(MUTED)
    if title:
        ax.set_title(title, color=TEXT, fontsize=12, fontweight="bold", pad=10, loc="left")
    ax.grid(axis="y", color=GRID, linewidth=0.6, alpha=0.8)
    ax.set_axisbelow(True)


def add_disclaimer(fig):
    fig.text(
        0.5,
        0.012,
        DISCLAIMER,
        ha="center",
        va="bottom",
        color=WARN,
        fontsize=8,
        style="italic",
        wrap=True,
    )


def add_header(fig, title: str, subtitle: str):
    fig.text(0.04, 0.955, title, color=TEXT, fontsize=18, fontweight="bold", ha="left")
    fig.text(0.04, 0.915, subtitle, color=MUTED, fontsize=10, ha="left")
    # accent line under header
    fig.patches.append(
        mpatches.FancyBboxPatch(
            (0.04, 0.898),
            0.92,
            0.003,
            transform=fig.transFigure,
            boxstyle="round,pad=0",
            facecolor=ACCENT,
            edgecolor="none",
            zorder=0,
        )
    )


def draw_kpi_card(ax, label: str, value_pct: float, sub: str, color: str):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_facecolor(CARD)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    # left accent bar
    ax.add_patch(
        mpatches.FancyBboxPatch(
            (0, 0), 0.02, 1, boxstyle="square,pad=0", facecolor=color, edgecolor="none",
            transform=ax.transAxes, clip_on=False,
        )
    )
    ax.text(0.08, 0.72, label, color=MUTED, fontsize=11, fontweight="bold", transform=ax.transAxes)
    ax.text(
        0.08,
        0.32,
        f"{value_pct:.1f} %",
        color=TEXT,
        fontsize=28,
        fontweight="bold",
        transform=ax.transAxes,
    )
    ax.text(0.08, 0.10, sub, color=MUTED, fontsize=8, transform=ax.transAxes)


def build_page1(ret: pd.DataFrame, path: Path):
    n = len(ret)
    d1 = 100 * ret["d1"].mean()
    d7 = 100 * ret["d7"].mean()
    d30 = 100 * ret["d30"].mean()

    by_plat = (
        ret.groupby("platform")
        .agg(players=("player_id", "count"), d1=("d1", "mean"), d7=("d7", "mean"), d30=("d30", "mean"))
        .reset_index()
    )
    by_plat["d1"] *= 100
    by_plat["d7"] *= 100
    by_plat["d30"] *= 100
    # stable platform order
    order = ["PC", "PS5", "Xbox"]
    by_plat["platform"] = pd.Categorical(by_plat["platform"], categories=order, ordered=True)
    by_plat = by_plat.sort_values("platform")

    ret = ret.copy()
    ret["cohort_week"] = cohort_week(ret["install_date"])
    by_cohort = (
        ret.groupby("cohort_week")
        .agg(players=("player_id", "count"), d1=("d1", "mean"), d7=("d7", "mean"))
        .reset_index()
        .sort_values("cohort_week")
    )
    by_cohort["d1"] *= 100
    by_cohort["d7"] *= 100

    fig = plt.figure(figsize=(16.5, 9.2), dpi=100, facecolor=BG)
    gs = GridSpec(
        3, 3, figure=fig, height_ratios=[0.85, 2.2, 2.0],
        hspace=0.45, wspace=0.28,
        left=0.06, right=0.96, top=0.86, bottom=0.08,
    )

    add_header(
        fig,
        "Rétention joueurs: Vue d'ensemble",
        f"Case study CoD · {n:,} joueurs · D1 / D7 / D30 (session day_number)",
    )
    add_disclaimer(fig)

    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[0, 2])
    draw_kpi_card(ax1, "Rétention D1", d1, "≥1 session jour 1", BAR_D1)
    draw_kpi_card(ax2, "Rétention D7", d7, "≥1 session jours 1-7", BAR_D7)
    draw_kpi_card(ax3, "Rétention D30", d30, "≥1 session jours 1-30", BAR_D30)

    # Clustered bars by platform
    axb = fig.add_subplot(gs[1, :])
    style_ax(axb, "Rétention D1 / D7 / D30 par plateforme")
    x = np.arange(len(by_plat))
    w = 0.25
    b1 = axb.bar(x - w, by_plat["d1"], w, color=BAR_D1, label="D1", zorder=3)
    b2 = axb.bar(x, by_plat["d7"], w, color=BAR_D7, label="D7", zorder=3)
    b3 = axb.bar(x + w, by_plat["d30"], w, color=BAR_D30, label="D30", zorder=3)
    axb.set_xticks(x)
    axb.set_xticklabels(
        [f"{p}\n(n={int(n_)})" for p, n_ in zip(by_plat["platform"], by_plat["players"])],
        color=TEXT,
    )
    axb.set_ylabel("% rétention", color=MUTED)
    axb.set_ylim(0, 110)
    axb.legend(
        facecolor=CARD, edgecolor=GRID, labelcolor=TEXT, fontsize=9, loc="upper right",
        framealpha=0.95,
    )
    for bars in (b1, b2, b3):
        for bar in bars:
            h = bar.get_height()
            axb.text(
                bar.get_x() + bar.get_width() / 2,
                h + 1.5,
                f"{h:.1f}",
                ha="center",
                va="bottom",
                color=TEXT,
                fontsize=8,
            )

    # Cohort week line
    axc = fig.add_subplot(gs[2, :])
    style_ax(axc, "Tendance cohorte (semaine d'install): D1 & D7")
    weeks = by_cohort["cohort_week"]
    axc.plot(weeks, by_cohort["d1"], marker="o", color=BAR_D1, linewidth=2, label="D1", markersize=5)
    axc.plot(weeks, by_cohort["d7"], marker="o", color=BAR_D7, linewidth=2, label="D7", markersize=5)
    axc.fill_between(weeks, by_cohort["d7"], alpha=0.12, color=BAR_D7)
    axc.set_ylabel("% rétention", color=MUTED)
    axc.set_ylim(0, 100)
    axc.legend(
        facecolor=CARD, edgecolor=GRID, labelcolor=TEXT, fontsize=9, loc="lower right",
        framealpha=0.95,
    )
    axc.tick_params(axis="x", labelrotation=25)
    for label in axc.get_xticklabels():
        label.set_color(MUTED)

    fig.savefig(path, dpi=100, facecolor=BG, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    return {"d1": d1, "d7": d7, "d30": d30, "n": n, "by_platform": by_plat}


def build_page2(flags: pd.DataFrame, mode_mix: pd.DataFrame, ret: pd.DataFrame, path: Path):
    seg = (
        flags.groupby("risk_segment")
        .agg(players=("player_id", "count"), d7=("retained_d7", "mean"))
        .reset_index()
    )
    seg["d7"] = (seg["d7"] * 100).round(1)
    seg_order = ["short_first_day", "rough_first_kd", "single_session_nonspender", "other"]
    seg["risk_segment"] = pd.Categorical(seg["risk_segment"], categories=seg_order, ordered=True)
    seg = seg.sort_values("risk_segment")

    spender = (
        ret.groupby("spender")
        .agg(players=("player_id", "count"), d1=("d1", "mean"), d7=("d7", "mean"), d30=("d30", "mean"))
        .reset_index()
    )
    for c in ("d1", "d7", "d30"):
        spender[c] *= 100

    fig = plt.figure(figsize=(16.5, 9.2), dpi=100, facecolor=BG)
    gs = GridSpec(
        2, 2, figure=fig, height_ratios=[1.15, 1.0],
        hspace=0.38, wspace=0.28,
        left=0.07, right=0.96, top=0.86, bottom=0.08,
    )
    add_header(
        fig,
        "Signaux de risque & engagement",
        "Segments précoces vs D7 · Mix de modes (j≤7) · Spender vs rétention",
    )
    add_disclaimer(fig)

    # Risk segment bars
    axr = fig.add_subplot(gs[0, 0])
    style_ax(axr, "Rétention D7 par segment de risque")
    labels_fr = {
        "short_first_day": "1er jour court\n(<20 min)",
        "rough_first_kd": "1er K/D faible\n(<0,6)",
        "single_session_nonspender": "1 session,\nnon-spender",
        "other": "Autre",
    }
    y = np.arange(len(seg))
    colors = [RISK_COLORS[s] for s in seg["risk_segment"]]
    bars = axr.barh(y, seg["d7"], color=colors, height=0.65, zorder=3)
    # highlight short_first_day with edge
    for i, s in enumerate(seg["risk_segment"]):
        if s == "short_first_day":
            bars[i].set_edgecolor("#ffccbc")
            bars[i].set_linewidth(2)
    axr.set_yticks(y)
    axr.set_yticklabels(
        [f"{labels_fr[s]}\n(n={int(n_)})" for s, n_ in zip(seg["risk_segment"], seg["players"])],
        color=TEXT,
        fontsize=9,
    )
    axr.set_xlabel("% rétention D7", color=MUTED)
    axr.set_xlim(0, 100)
    global_d7 = 100 * flags["retained_d7"].mean()
    axr.axvline(global_d7, color=ACCENT, linestyle="--", linewidth=1.2, alpha=0.9, zorder=4)
    axr.text(
        global_d7 + 0.8,
        len(seg) - 0.35,
        f"Global {global_d7:.1f}%",
        color=ACCENT,
        fontsize=8,
        va="top",
    )
    for bar, val in zip(bars, seg["d7"]):
        axr.text(
            val + 0.8,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}%",
            va="center",
            color=TEXT,
            fontsize=9,
            fontweight="bold",
        )

    # Mode mix stacked 100%
    axm = fig.add_subplot(gs[0, 1])
    style_ax(axm, "Mix de modes: % des minutes (j≤7)")
    modes = ["Warzone", "Multiplayer", "Campaign"]
    status_labels = {0: "Churné D7", 1: "Retenu D7"}
    pivot = mode_mix.pivot(index="retained_d7", columns="mode", values="pct_of_minutes").fillna(0)
    for m in modes:
        if m not in pivot.columns:
            pivot[m] = 0
    pivot = pivot[modes]
    x = np.arange(len(pivot.index))
    bottom = np.zeros(len(pivot))
    for mode in modes:
        vals = pivot[mode].values
        axm.bar(x, vals, bottom=bottom, color=MODE_COLORS[mode], label=mode, width=0.55, zorder=3)
        for i, v in enumerate(vals):
            if v >= 8:
                axm.text(
                    x[i],
                    bottom[i] + v / 2,
                    f"{v:.1f}%",
                    ha="center",
                    va="center",
                    color=TEXT,
                    fontsize=8,
                    fontweight="bold",
                )
        bottom += vals
    axm.set_xticks(x)
    axm.set_xticklabels([status_labels[i] for i in pivot.index], color=TEXT)
    axm.set_ylabel("% des minutes", color=MUTED)
    axm.set_ylim(0, 100)
    axm.legend(
        facecolor=CARD, edgecolor=GRID, labelcolor=TEXT, fontsize=9, loc="upper right",
        framealpha=0.95,
    )

    # Spender vs retention
    axs = fig.add_subplot(gs[1, :])
    style_ax(axs, "Spender vs non-spender: D1 / D7 / D30")
    spender = spender.sort_values("spender")
    x = np.arange(len(spender))
    w = 0.25
    labels_sp = [
        f"Non-spender\n(n={int(spender.loc[spender.spender==0,'players'].iloc[0])})",
        f"Spender\n(n={int(spender.loc[spender.spender==1,'players'].iloc[0])})",
    ]
    b1 = axs.bar(x - w, spender["d1"], w, color=BAR_D1, label="D1", zorder=3)
    b2 = axs.bar(x, spender["d7"], w, color=BAR_D7, label="D7", zorder=3)
    b3 = axs.bar(x + w, spender["d30"], w, color=BAR_D30, label="D30", zorder=3)
    axs.set_xticks(x)
    axs.set_xticklabels(labels_sp, color=TEXT)
    axs.set_ylabel("% rétention", color=MUTED)
    axs.set_ylim(0, 115)
    axs.legend(
        facecolor=CARD, edgecolor=GRID, labelcolor=TEXT, fontsize=9, loc="upper left",
        framealpha=0.95,
    )
    for bars in (b1, b2, b3):
        for bar in bars:
            h = bar.get_height()
            axs.text(
                bar.get_x() + bar.get_width() / 2,
                h + 1.5,
                f"{h:.1f}",
                ha="center",
                va="bottom",
                color=TEXT,
                fontsize=9,
            )
    # annotate D7 lift
    d7_ns = float(spender.loc[spender.spender == 0, "d7"].iloc[0])
    d7_sp = float(spender.loc[spender.spender == 1, "d7"].iloc[0])
    axs.annotate(
        f"Lift D7 spenders : +{d7_sp - d7_ns:.1f} pp",
        xy=(1, d7_sp),
        xytext=(1.35, d7_sp + 8),
        color=ACCENT,
        fontsize=9,
        fontweight="bold",
        arrowprops=dict(arrowstyle="->", color=ACCENT, lw=1),
    )

    fig.savefig(path, dpi=100, facecolor=BG, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    return {"segments": seg, "spender": spender, "mode_mix": mode_mix}


def build_page3_optional(ret: pd.DataFrame, path: Path):
    """Optional spender lens close-up."""
    spender = (
        ret.groupby("spender")
        .agg(players=("player_id", "count"), d1=("d1", "mean"), d7=("d7", "mean"), d30=("d30", "mean"))
        .reset_index()
    )
    for c in ("d1", "d7", "d30"):
        spender[c] *= 100

    fig = plt.figure(figsize=(16.5, 6.8), dpi=100, facecolor=BG)
    gs = GridSpec(1, 3, figure=fig, wspace=0.3, left=0.06, right=0.96, top=0.78, bottom=0.12)
    add_header(
        fig,
        "Lentille spender: détail rétention",
        "Comparaison spenders vs non-spenders (même définitions SQL)",
    )
    add_disclaimer(fig)

    metrics = [("D1", "d1", BAR_D1), ("D7", "d7", BAR_D7), ("D30", "d30", BAR_D30)]
    for i, (name, col, color) in enumerate(metrics):
        ax = fig.add_subplot(gs[0, i])
        style_ax(ax, f"Rétention {name}")
        vals = [
            float(spender.loc[spender.spender == 0, col].iloc[0]),
            float(spender.loc[spender.spender == 1, col].iloc[0]),
        ]
        bars = ax.bar(
            ["Non-spender", "Spender"],
            vals,
            color=[MUTED, color],
            width=0.55,
            zorder=3,
        )
        ax.set_ylim(0, 110)
        ax.set_ylabel("%", color=MUTED)
        for bar, v in zip(bars, vals):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                v + 2,
                f"{v:.1f}%",
                ha="center",
                color=TEXT,
                fontsize=12,
                fontweight="bold",
            )
        delta = vals[1] - vals[0]
        ax.text(
            0.5,
            0.05,
            f"Δ = +{delta:.1f} pp",
            transform=ax.transAxes,
            ha="center",
            color=ACCENT,
            fontsize=10,
            fontweight="bold",
        )

    fig.savefig(path, dpi=100, facecolor=BG, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)


def main():
    players, sessions, purchases = load_data()
    ret = compute_player_retention(players, sessions)
    flags = compute_risk_segments(players, sessions)
    mode_mix = compute_mode_mix(players, sessions)

    p1 = OUT / "01_retention_overview.png"
    p2 = OUT / "02_risk_segments.png"
    p3 = OUT / "03_spender_lens.png"

    m1 = build_page1(ret, p1)
    m2 = build_page2(flags, mode_mix, ret, p2)
    build_page3_optional(ret, p3)

    # Metric check report
    print("=== PNG écrits ===")
    for p in (p1, p2, p3):
        print(f"  {p}  ({p.stat().st_size // 1024} KB)")

    print("\n=== Contrôle métriques (attendu ≈) ===")
    print(f"  D1   {m1['d1']:.1f}%  (attendu ~44.2%)")
    print(f"  D7   {m1['d7']:.1f}%  (attendu ~86.0%)")
    print(f"  D30  {m1['d30']:.1f}%  (attendu ~95.2%)")
    short = m2["segments"].loc[m2["segments"]["risk_segment"] == "short_first_day"].iloc[0]
    print(f"  short_first_day D7  {short['d7']:.1f}%  (attendu ~79.1%, n={int(short['players'])})")
    sp = m2["spender"]
    print(
        f"  spender D7  {float(sp.loc[sp.spender==1,'d7'].iloc[0]):.1f}%  "
        f"vs non-spender {float(sp.loc[sp.spender==0,'d7'].iloc[0]):.1f}%  "
        f"(attendu ~91.4% vs ~84.9%)"
    )
    print("\n=== Par plateforme ===")
    print(m1["by_platform"].to_string(index=False))
    print("\n=== Segments ===")
    print(m2["segments"].to_string(index=False))
    print("\n=== Mode mix ===")
    print(m2["mode_mix"].to_string(index=False))


if __name__ == "__main__":
    main()
