"""
Summarize tram delay data and estimate the economic cost of delay.

Input : data/trams/tram_data_*.csv   (output of process_trams.py)
Output: data/trams/results/*.csv and *.png

Method (see paper, Sections 2.4 and 3.4):
    C_trip = VOT * T_add + VOR * sigma_T
    T_add   = mean lateness per observation (minutes; early running counted as 0)
    sigma_T = standard deviation of delay (minutes)
    VOR     = VOR_MULTIPLIER * VOT
"""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------------------------------------------------- PATHS
DATA_DIR = Path(__file__).parent / "data" / "trams"
OUT_DIR = DATA_DIR / "results"
OUT_DIR.mkdir(parents=True, exist_ok=True)
ROUTES = ["9", "17", "22"]

# ------------------------------------------------- COST PARAMETERS
# Set these from sourced values before reporting any cost figure.
VOT_CZK_PER_HOUR = None      # value of time (CZK/hour), e.g. from Czech appraisal guidance
VOR_MULTIPLIER = 1.4         # reliability premium implied by Dutch values in van Oort (2016)
TRIPS_PER_DAY = 2            # assumption for a representative commuter
DAYS_PER_YEAR = 220          # assumption for a representative commuter

sns.set_theme(style="whitegrid", context="paper")


# ----------------------------------------------------------- LOADING
def load_data():
    files = sorted(DATA_DIR.glob("tram_data_*.csv"))
    if not files:
        raise SystemExit(f"No tram CSV files found in {DATA_DIR}")
    frames = []
    for f in files:
        d = pd.read_csv(f)
        d["session"] = f.stem.replace("tram_data_", "")
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    df["route"] = df["route"].astype(str)
    df["delay_seconds"] = pd.to_numeric(df["delay_seconds"], errors="coerce")
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df["timestamp"] = df["timestamp"].dt.tz_convert("Europe/Prague")
    df = df.dropna(subset=["route", "delay_seconds", "timestamp"])
    df = df[df["route"].isin(ROUTES)].copy()
    df["delay_min"] = df["delay_seconds"] / 60.0
    return df


# ------------------------------------------------------- STATISTICS
def describe(x):
    x = pd.Series(x).dropna()
    return pd.Series({
        "n": len(x),
        "mean": x.mean(),
        "median": x.median(),
        "sd": x.std(ddof=1),
        "min": x.min(),
        "q25": x.quantile(0.25),
        "q75": x.quantile(0.75),
        "iqr": x.quantile(0.75) - x.quantile(0.25),
        "p90": x.quantile(0.90),
        "p95": x.quantile(0.95),
        "max": x.max(),
        "share_late_gt_1min": (x > 1).mean(),
        "share_late_gt_3min": (x > 3).mean(),
        "share_early_lt_0": (x < 0).mean(),
    })


def summary_by(df, by):
    return df.groupby(by)["delay_min"].apply(describe).unstack().round(3)


# ------------------------------------------------------------- COST
def cost_table(df):
    rows = []
    for route, g in list(df.groupby("route")) + [("All", df)]:
        t_add = g["delay_min"].clip(lower=0).mean()      # minutes
        sigma = g["delay_min"].std(ddof=1)               # minutes
        row = {"route": route, "T_add_min": t_add, "sigma_min": sigma}
        if VOT_CZK_PER_HOUR is not None:
            vot = VOT_CZK_PER_HOUR
            vor = VOR_MULTIPLIER * vot
            c_trip = vot * t_add / 60 + vor * sigma / 60
            row.update({
                "cost_trip_CZK": c_trip,
                "cost_year_CZK": c_trip * TRIPS_PER_DAY * DAYS_PER_YEAR,
            })
        rows.append(row)
    return pd.DataFrame(rows).round(3)


# ------------------------------------------------------------ PLOTS
def make_plots(df):
    # Histogram (1-minute bins), one panel per route
    fig, axes = plt.subplots(1, len(ROUTES), figsize=(12, 4), sharey=True)
    for ax, r in zip(axes, ROUTES):
        sns.histplot(df.loc[df.route == r, "delay_min"], binwidth=1,
                     color="steelblue", edgecolor="black", ax=ax)
        ax.axvline(0, color="black", linestyle="--", linewidth=1)
        ax.set_title(f"Line {r}")
        ax.set_xlabel("Delay (minutes)")
    axes[0].set_ylabel("Observations")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "fig1_histogram.png", dpi=300)
    plt.close(fig)

    # Boxplot, outliers SHOWN (tails drive the cost)
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.boxplot(data=df, x="route", y="delay_min", order=ROUTES,
                color="lightsteelblue", fliersize=2, ax=ax)
    ax.axhline(0, color="black", linestyle="--", linewidth=1)
    ax.set_xlabel("Tram line")
    ax.set_ylabel("Delay (minutes)")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "fig2_boxplot.png", dpi=300)
    plt.close(fig)

    # ECDF
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.ecdfplot(data=df, x="delay_min", hue="route", hue_order=ROUTES, ax=ax)
    ax.axvline(0, color="black", linestyle="--", linewidth=1)
    ax.set_xlabel("Delay (minutes)")
    ax.set_ylabel("Cumulative proportion")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "fig3_ecdf.png", dpi=300)
    plt.close(fig)


# ------------------------------------------------------------- MAIN
def main():
    df = load_data()
    print(f"Observations: {len(df):,} | sessions: {df['session'].nunique()}")

    by_route = summary_by(df, "route")
    overall = describe(df["delay_min"]).round(3).to_frame("All").T
    table = pd.concat([by_route, overall])
    table.to_csv(OUT_DIR / "table_descriptive_by_route.csv")
    print("\nDescriptive statistics (minutes):\n", table)

    # 30-minute bins within the collection window
    df["time_bin"] = df["timestamp"].dt.floor("30min").dt.strftime("%H:%M")
    by_time = summary_by(df, "time_bin")
    by_time.to_csv(OUT_DIR / "table_descriptive_by_time.csv")
    print("\nBy 30-minute period:\n", by_time[["n", "mean", "median", "sd"]])

    # Trip-level view: one value per vehicle run, reducing the dependence
    # between repeated 20-second snapshots of the same vehicle
    trips = (df.dropna(subset=["trip_id"])
               .groupby(["session", "trip_id", "route"])["delay_min"]
               .mean().reset_index())
    trip_table = pd.concat([summary_by(trips, "route"),
                            describe(trips["delay_min"]).round(3).to_frame("All").T])
    trip_table.to_csv(OUT_DIR / "table_descriptive_trip_level.csv")
    print("\nTrip-level (mean delay per trip):\n", trip_table[["n", "mean", "median", "sd"]])

    costs = cost_table(df)
    costs.to_csv(OUT_DIR / "table_cost.csv", index=False)
    print("\nCost table:\n", costs)
    if VOT_CZK_PER_HOUR is None:
        print("\nNOTE: set VOT_CZK_PER_HOUR to compute CZK values.")

    make_plots(df)
    print(f"\nResults saved to {OUT_DIR}")


if __name__ == "__main__":
    main()