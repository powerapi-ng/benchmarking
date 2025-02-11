import visualization
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import polars as pl

def correlation_perf_perf_hwpc_hwpc_cv_os(df1, df2, job):

    if job == "alone":
        df1_perf = df1.sql(f"SELECT * FROM self WHERE job = 'perf_{job}'")
        df2_perf = df2.sql(f"SELECT * FROM self WHERE job = 'perf_{job}'")
        df1_hwpc = df1.sql(f"SELECT * FROM self WHERE job = 'hwpc_{job}'")
        df2_hwpc = df2.sql(f"SELECT * FROM self WHERE job = 'hwpc_{job}'")
        title = f"Scatterplot of Ubuntu PERF coefficient of variation related to Debian, PKG domain, measurement tools isolated"
    else:
        df1_perf = df1.sql(f"SELECT * FROM self WHERE job = 'perf_with_hwpc'")
        df2_perf = df2.sql(f"SELECT * FROM self WHERE job = 'perf_with_hwpc'")
        df1_hwpc = df1.sql(f"SELECT * FROM self WHERE job = 'hwpc_with_perf'")
        df2_hwpc = df2.sql(f"SELECT * FROM self WHERE job = 'hwpc_with_perf'")
        title = f"Scatterplot of Ubuntu PERF coefficient of variation related to Debian, PKG domain, measurement tools running together"

    joined_perf = df1_perf.join(
            other=df2_perf, on=["node", "nb_ops_per_core", "nb_core", "alone"], how="left", validate="1:1", suffix="_debian"
            )
    joined_hwpc = df1_hwpc.join(
            other=df2_hwpc, on=["node", "nb_ops_per_core", "nb_core", "alone"], how="left", validate="1:1", suffix="_debian"
            )

    sns.set_theme(style="whitegrid")
    f, ax = plt.subplots(figsize=(12,8))
    sns.despine(f, left=True, bottom=True)
    plotted_df_perf = joined_perf.sql("SELECT * FROM self WHERE nb_ops_per_core = 25000 and processor_version != 'Gold 5320'").drop_nulls(subset=["pkg_coefficient_of_variation_debian", "pkg_coefficient_of_variation"]).drop_nans(subset=["pkg_coefficient_of_variation_debian", "pkg_coefficient_of_variation"])
    plotted_df_hwpc = joined_hwpc.sql("SELECT * FROM self WHERE nb_ops_per_core = 25000 and processor_version != 'Gold 5320'").drop_nulls(subset=["pkg_coefficient_of_variation_debian", "pkg_coefficient_of_variation"]).drop_nans(subset=["pkg_coefficient_of_variation_debian", "pkg_coefficient_of_variation"])
    
    max_perf_1 = plotted_df_perf["pkg_coefficient_of_variation"].max()
    max_perf_2 = plotted_df_perf["pkg_coefficient_of_variation_debian"].max()
    max_perf_both = max(max_perf_1, max_perf_2)
    max_hwpc_1 = plotted_df_hwpc["pkg_coefficient_of_variation"].max()
    max_hwpc_2 = plotted_df_hwpc["pkg_coefficient_of_variation_debian"].max()
    max_hwpc_both = max(max_hwpc_1, max_hwpc_2)

    corr = plotted_df_perf.select(pl.corr("pkg_coefficient_of_variation", "pkg_coefficient_of_variation_debian")).item()
    correlations = (
        plotted_df_perf.group_by("processor_detail")
        .agg(pl.corr("pkg_coefficient_of_variation", "pkg_coefficient_of_variation_debian").alias("corr"))
    )
    corr_dict = dict(zip(correlations["processor_detail"], correlations["corr"]))
    scatter = sns.scatterplot(data=plotted_df_perf,
                    x="pkg_coefficient_of_variation",
                    y="pkg_coefficient_of_variation_debian",
                    hue="node",
                    style="processor_vendor"
                    )
    sns.lineplot(x=[0, max_perf_both], y=[0, max_perf_both], color="red", linestyle="dashed", label="f(x) = x")
    plt.title(title)
    plt.xlabel("Coefficient of variation of PERF for PKG domain - Ubuntu2404 - Kernel 6.8")
    plt.ylabel("Coefficient of variation of HWPC for PKG domain - Debian11 - Kernel 5.10")
    plt.text(0.05, 0.95, f"Correlation: {corr:.2f}", transform=plt.gca().transAxes, 
             fontsize=12, verticalalignment='top', bbox=dict(boxstyle="round,pad=0.3", 
                                                             edgecolor='black', 
                                                             facecolor='white')
             )
    #handles, labels = scatter.get_legend_handles_labels()
    #new_labels = [f"{label} (corr: {corr_dict.get(label, 'N/A'):.2f})" for label in labels if label in corr_dict]
    #plt.legend(handles, new_labels, loc="lower right")
    plt.tight_layout()
    plt.show()

