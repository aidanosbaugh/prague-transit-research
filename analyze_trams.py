
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

## DATA PATHS
DATA_DIR = Path(__file__).parent / "data" / "trams"
INPUT_FILES = sorted(DATA_DIR.glob("tram_data_*.csv"))

## GRAPH DESIGN
sns.set_theme(style="whitegrid", context="paper")

## CHECK FOR FILES
if not INPUT_FILES:
    print(f"No CSV files found in {DATA_DIR}")
else:
    for INPUT_FILE in INPUT_FILES:

        print(f"\nAnalyzing: {INPUT_FILE.name}")

        ## LOAD DATA
        df = pd.read_csv(INPUT_FILE)

        if df.empty:
            print("Skipping empty file.")
            continue

        ## CLEAN DATA
        df["route"] = df["route"].astype(str)
        df["delay_seconds"] = pd.to_numeric(
            df["delay_seconds"], errors="coerce"
        )
        df = df.dropna(subset=["route", "delay_seconds"])

        if df.empty:
            print("No valid delay data. Skipping file.")
            continue

        ## CREATE GRAPH
        fig, ax = plt.subplots(figsize=(9, 6))

        sns.boxplot(
            data=df,
            x="route",
            y="delay_seconds",
            order=["9", "17", "22"],
            width=0.55,
            showfliers=False,
            color="lightsteelblue",
            linewidth=1.2,
            ax=ax
        )

        ## LABELS AND TITLE
        ax.set_title(
            f"Distribution of Tram Delays\n{INPUT_FILE.stem}",
            fontsize=14,
            weight="bold",
            pad=15
        )

        ax.set_xlabel("Tram Line", fontsize=12)
        ax.set_ylabel("Delay (seconds)", fontsize=12)

        ## ZERO-DELAY REFERENCE LINE
        ax.axhline(
            y=0,
            color="black",
            linestyle="--",
            linewidth=1,
            alpha=0.8
        )

        sns.despine()
        plt.tight_layout()

        ## SAVE SEPARATE GRAPH FOR EACH CSV
        OUTPUT_FILE = DATA_DIR / f"{INPUT_FILE.stem}_boxplot.png"

        plt.savefig(
            OUTPUT_FILE,
            dpi=300,
            bbox_inches="tight"
        )

        print(f"Graph saved to: {OUTPUT_FILE.name}")

        plt.close(fig)

    print("\nAll files processed.")
