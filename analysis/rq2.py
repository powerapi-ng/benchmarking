import visualization
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import polars as pl
import re


def boxplots_perf_hwpc_cv_processor(df, x, y, hue, prefix, save=True, show=True):
    plt.figure(figsize=(12, 6))
    df = df.sql("SELECT * FROM self WHERE nb_ops_per_core = 25000")
    sns.boxplot(
        data=df,
        x=x,
        y=y,
        hue=hue,
        showfliers=False
    )

    title = f"{prefix} - PKG Coefficient of Variation by {hue} and {x}"
    plt.title(title)
    plt.xticks(rotation=90, ha="right")
    plt.xlabel("Processor version and generation")
    plt.ylabel("PKG Coefficient of Variation")
    safe_title = re.sub(r'[^\w\s-]', '', title)  # Remove invalid characters
    safe_title = safe_title.replace(" ", "_")
    safe_title = safe_title.replace("\n", "_")
    plt.tight_layout()
    if save:
        plt.savefig(f'{safe_title}.png', dpi=500)
    if show:
        plt.show()

