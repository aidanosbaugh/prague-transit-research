import csv 
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

## DATA PATHS
DATA_DIR = Path(__file__).parent / "data"
INPUT_FILE = DATA_DIR / "tram_data.csv"

## LOAD DATA
df = pd.read_csv(INPUT_FILE)

## GRAPH DESIGN

sns.set_theme(style="whitegrid", context="paper")

fig, ax = plt.subplots(figsize=(9,6))

sns.boxplot(
    data=df,
    x="route",
    y="delay_seconds",
    order=["9","17","22"],
    width=0.55,
    showfliers=False,
    color="lightsteelblue",
    linewidth=1.2,
    ax=ax
)

## LABS AND TITLE

ax.set_title(
    "Distribution of Tram Delays on Lines 9,17,22",
    fontsize=15,
    weight="bold",
    pad=15
)

ax.set_xlabel("Tram Line", fontsize=12)
ax.set_ylabel("Delay(seconds)", fontsize=12)

## 0-DELAY REFERENCE LINE

ax.axhline(
    y=0,
    color="black",
    linestyle="--",
    linewidth=1,
    alpha=0.8
)

sns.despine()
plt.tight_layout()

## SAVE GRAPH
plt.savefig(
    DATA_DIR / "tram_delay_boxplot.png",
    dpi = 300,
    bbox_inches="tight"
)

plt.show()