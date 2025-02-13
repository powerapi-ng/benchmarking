import visualization
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import polars as pl

def correlation_perf_hwpc_cv(df, job, os):

    if job == "alone":
        df_perf = df.sql(f"SELECT * FROM self WHERE job = 'perf_{job}'")
        df_hwpc = df.sql(f"SELECT * FROM self WHERE job = 'hwpc_{job}'")
        title = f"Scatterplot of PERF coefficient of variation related to HWPC, PKG domain, measurement tools isolated\n{os}"
    else:
        df_perf = df.sql(f"SELECT * FROM self WHERE job = 'perf_with_hwpc'")
        df_hwpc = df.sql(f"SELECT * FROM self WHERE job = 'hwpc_with_perf'")
        title = f"Scatterplot of PERF coefficient of variation related to HWPC, PKG domain, measurement tools running together\n{os}"

    joined = df_hwpc.join(
            other=df_perf, on=["node", "nb_ops_per_core", "nb_core", "alone"], how="left", validate="1:1", suffix="_perf"
            )

    sns.set_theme(style="whitegrid")
    f, ax = plt.subplots(figsize=(12,8))
    sns.despine(f, left=True, bottom=True)
    plotted_df = joined.sql("SELECT * FROM self WHERE nb_ops_per_core = 25000 and processor_version != 'Gold 5320'").drop_nulls(subset=["pkg_coefficient_of_variation", "pkg_coefficient_of_variation_perf"]).drop_nans(subset=["pkg_coefficient_of_variation", "pkg_coefficient_of_variation_perf"])
    
    max_perf = plotted_df["pkg_coefficient_of_variation_perf"].max()
    max_hwpc = plotted_df["pkg_coefficient_of_variation"].max()
    max_both = max(max_perf, max_hwpc)

    corr = plotted_df.select(pl.corr("pkg_coefficient_of_variation_perf", "pkg_coefficient_of_variation")).item()
    correlations = (
        plotted_df.group_by("processor_detail")
        .agg(pl.corr("pkg_coefficient_of_variation_perf", "pkg_coefficient_of_variation").alias("corr"))
    )
    corr_dict = dict(zip(correlations["processor_detail"], correlations["corr"]))
    scatter = sns.scatterplot(data=plotted_df,
                    x="pkg_coefficient_of_variation_perf",
                    y="pkg_coefficient_of_variation",
                    hue="processor_detail",
                    style="processor_vendor"
                    )
    sns.lineplot(x=[0, max_both], y=[0, max_both], color="red", linestyle="dashed", label="f(x) = x")
    plt.title(title)
    plt.xlabel("Coefficient of variation of PERF for PKG domain")
    plt.ylabel("Coefficient of variation of HWPC for PKG domain")
    plt.text(0.05, 0.95, f"Correlation: {corr:.2f}", transform=plt.gca().transAxes, 
             fontsize=12, verticalalignment='top', bbox=dict(boxstyle="round,pad=0.3", 
                                                             edgecolor='black', 
                                                             facecolor='white')
             )
    handles, labels = scatter.get_legend_handles_labels()
    new_labels = [f"{label} (corr: {corr_dict.get(label, 'N/A'):.2f})" for label in labels if label in corr_dict]
    plt.legend(handles, new_labels, loc="lower right")
    plt.tight_layout()
    plt.show()

