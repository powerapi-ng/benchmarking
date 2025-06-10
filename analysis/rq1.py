import visualization
import re
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import polars as pl
import numpy as np

processor_palette= {
    "E5-2620 v4\nBroadwell-E": "#ff0000",
    "E5-2698 v4\nBroadwell-E": "#ff9000",
    "E5-2630L v4\nBroadwell-E": "#fff000",
    "E5-2630 v3\nHaswell-E": "#00ff00",
    "Gold 5220\nCascade Lake-SP": "#009900",
    "Gold 5218\nCascade Lake-SP": "#0000ff",
    "i7-9750H\nCoffee Lake": "#000099",
    "Silver 4314\nIce Lake-SP": "#ff00ff",
    "Gold 5320\nIce Lake-SP": "#990099",
    "Gold 6126\nSkylake-SP": "#ff0099",
    "Gold 6130\nSkylake-SP": "#9900ff",
    "E5-2620\nSandy Bridge-EP": "#FF7F50",
    "E5-2630\nSandy Bridge-EP": "#de3163",
    "E5-2630L\nSandy Bridge-EP": "#9fe2bf",
    "E5-2660\nSandy Bridge-EP": "#ccccff",
    "7301\nZen": "#c0c0c0",
    "7352\nZen 2": "#808000",
    "7452\nZen 2": "#00ffff",
    "7642\nZen 2": "#008080",
    "7742\nZen 2": "#800000",
}



def ratio_tool_perf(dataframe, other_tool="hwpc", other_tool_domain="energy_pkg", perf_domain="cores"):
    filtered_dataframe_other_tool = dataframe.sql(f"SELECT * FROM self WHERE task = '{other_tool}_and_perf'")
    filtered_dataframe_perf = dataframe.sql(f"SELECT * FROM self WHERE task = 'perf_and_{other_tool}'")
    joined_dataframe_perf_and_other = filtered_dataframe_perf.join(
            other=filtered_dataframe_other_tool,
            on=["node", "nb_core", "nb_ops_per_core", "iteration"],
            how="left",
            validate="1:1",
            suffix=f"_{other_tool}"
            )
    ratio_column_name = f"ratio_{other_tool_domain}_perf_{other_tool}"
    joined_dataframe_perf_and_other = joined_dataframe_perf_and_other.with_columns(
            (pl.col(perf_domain) / pl.col(f"{other_tool_domain}_{other_tool}")).alias(ratio_column_name)
            )
    sns.boxplot(
            data=joined_dataframe_perf_and_other, 
            x="processor_detail", 
            y=ratio_column_name
            )
    plt.title(f"Correlation of {other_tool} and perf over {other_tool_domain} domain")
    plt.xlabel(f"Processor Details")
    plt.ylabel(f"Ratio of perf/{other_tool} energy measurements for {other_tool_domain} domain")
    plt.legend()
    plt.tight_layout()

    plt.show()


def plotted_df_tools_cv(df, tool1="perf", tool2="hwpc", domain_tool1="pkg", domain_tool2="pkg", os="ubuntu2404"):

    df_tool1 = df.sql(f"SELECT * FROM self WHERE task = '{tool1}_and_{tool2}'")
    df_tool2 = df.sql(f"SELECT * FROM self WHERE task = '{tool2}_and_{tool1}'")
    joined = df_tool1.join(
            other=df_tool2, on=["node", "nb_ops_per_core", "nb_core", "iteration"], how="left", validate="1:1", suffix=f"_{tool2}"
            )
    domain_1 = f"energy_{domain_tool1}"
    domain_2 = f"energy_{domain_tool2}_{tool2}"
    plotted_df = joined.sql("SELECT * FROM self").drop_nulls(subset=[domain_1, domain_2]).drop_nans(subset=[domain_1, domain_2])
    
    max_tool1 = plotted_df[domain_1].max()
    max_tool2 = plotted_df[domain_2].max()
    max_both = max(max_tool1, max_tool2)

    corr = plotted_df.select(pl.corr(domain_2, domain_1)).item()
    correlations = (
        plotted_df.group_by("processor_detail")
        .agg(pl.corr(domain_2, domain_1).alias("corr"))
    )
    corr_dict = dict(zip(correlations["processor_detail"], correlations["corr"]))
    return (plotted_df, domain_1, domain_2, max_both, corr, corr_dict)


def plot_correlation_tools_cv(df):
    (perf_hwpc, domain_perf_hwpc_1, domain_perf_hwpc_2, max_both_perf_hwpc, corr_perf_hwpc, corr_dict_perf_hwpc) = plotted_df_tools_cv(df, tool1="perf", tool2="hwpc", domain_tool1="pkg", domain_tool2="pkg")
    (perf_codecarbon, domain_perf_codecarbon_1, domain_perf_codecarbon_2, max_both_perf_codecarbon, corr_perf_codecarbon, corr_dict_perf_codecarbon) = plotted_df_tools_cv(df, tool1="perf", tool2="codecarbon", domain_tool1="pkg", domain_tool2="cores")
    (perf_alumet, domain_perf_alumet_1, domain_perf_alumet_2, max_both_perf_alumet, corr_perf_alumet, corr_dict_perf_alumet) = plotted_df_tools_cv(df, tool1="perf", tool2="alumet", domain_tool1="pkg", domain_tool2="pkg")
    (perf_scaphandre, domain_perf_scaphandre_1, domain_perf_scaphandre_2, max_both_perf_scaphandre, corr_perf_scaphandre, corr_dict_perf_scaphandre) = plotted_df_tools_cv(df, tool1="perf", tool2="scaphandre", domain_tool1="pkg", domain_tool2="pkg")
    (perf_vjoule, domain_perf_vjoule_1, domain_perf_vjoule_2, max_both_perf_vjoule, corr_perf_vjoule, corr_dict_perf_vjoule) = plotted_df_tools_cv(df, tool1="perf", tool2="vjoule", domain_tool1="pkg", domain_tool2="cores")

    fig, axs = plt.subplots(figsize=(12, 8), nrows=2, ncols=3)
    fig.delaxes(axs[1, 2])

    sns.scatterplot(data=perf_hwpc,
                    x=domain_perf_hwpc_1,
                    y=domain_perf_hwpc_2,
                    hue="processor_detail",
                    palette=processor_palette,
                    ax=axs[0, 0]

                    )
    sns.lineplot(x=[0, max_both_perf_hwpc], y=[0, max_both_perf_hwpc], ax=axs[0, 0],color="red", linestyle="dashed", label="f(x) = x")
    axs[0, 0].set_title(f"Correlation of Perf and HWPC over PKG domain")
    axs[0, 0].set_xlabel(f"PERF for PKG domain")
    axs[0, 0].set_ylabel(f"HWPC for PKG domain")
    handles, labels = axs[0, 0].get_legend_handles_labels()
    new_labels = [f"{label} (corr: {corr_dict_perf_hwpc.get(label, 'N/A'):.2f})" for label in labels if label in corr_dict_perf_hwpc]
    #axs[0, 0].legend(handles, new_labels, loc="lower right", bbox_to_anchor=(1.5, -0.1))
    axs[0, 0].get_legend().remove()


    sns.scatterplot(data=perf_codecarbon,
                    x=domain_perf_codecarbon_1,
                    y=domain_perf_codecarbon_2,
                    hue="processor_detail",
                    palette=processor_palette,
                    ax=axs[0, 1]

                    )
    sns.lineplot(x=[0, max_both_perf_codecarbon], y=[0, max_both_perf_codecarbon], ax=axs[0, 1],color="red", linestyle="dashed", label="f(x) = x")
    axs[0, 1].set_title(f"Correlation of Perf and codecarbon over PKG domain")
    axs[0, 1].set_xlabel(f"PERF for PKG domain")
    axs[0, 1].set_ylabel(f"codecarbon for PKG domain")
    handles, labels = axs[0, 1].get_legend_handles_labels()
    new_labels = [f"{label} (corr: {corr_dict_perf_codecarbon.get(label, 'N/A'):.2f})" for label in labels if label in corr_dict_perf_codecarbon]
    #axs[0, 1].legend(handles, new_labels, loc="lower right", bbox_to_anchor=(1.5, -0.1))
    axs[0, 1].get_legend().remove()


    sns.scatterplot(data=perf_alumet,
                    x=domain_perf_alumet_1,
                    y=domain_perf_alumet_2,
                    hue="processor_detail",
                    palette=processor_palette,
                    ax=axs[0, 2]

                    )
    sns.lineplot(x=[0, max_both_perf_alumet], y=[0, max_both_perf_alumet], ax=axs[0, 2],color="red", linestyle="dashed", label="f(x) = x")
    axs[0, 2].set_title(f"Correlation of Perf and alumet over PKG domain")
    axs[0, 2].set_xlabel(f"PERF for PKG domain")
    axs[0, 2].set_ylabel(f"alumet for PKG domain")
    handles, labels = axs[0, 2].get_legend_handles_labels()
    new_labels = [f"{label} (corr: {corr_dict_perf_alumet.get(label, 'N/A'):.2f})" for label in labels if label in corr_dict_perf_alumet]
    axs[0, 2].legend(handles, new_labels, loc="lower right", bbox_to_anchor=(1.5, -0.1))
    axs[0, 2].get_legend().remove()


    sns.scatterplot(data=perf_scaphandre,
                    x=domain_perf_scaphandre_1,
                    y=domain_perf_scaphandre_2,
                    hue="processor_detail",
                    palette=processor_palette,
                    ax=axs[1, 0]

                    )
    sns.lineplot(x=[0, max_both_perf_scaphandre], y=[0, max_both_perf_scaphandre], ax=axs[1, 0],color="red", linestyle="dashed", label="f(x) = x")
    axs[1, 0].set_title(f"Correlation of Perf and scaphandre over PKG domain")
    axs[1, 0].set_xlabel(f"PERF for PKG domain")
    axs[1, 0].set_ylabel(f"scaphandre for PKG domain")
    handles, labels = axs[1, 0].get_legend_handles_labels()
    new_labels = [f"{label} (corr: {corr_dict_perf_scaphandre.get(label, 'N/A'):.2f})" for label in labels if label in corr_dict_perf_scaphandre]
    #axs[1, 0].legend(handles, new_labels, loc="lower right", bbox_to_anchor=(1.5, -0.1))
    axs[1, 0].get_legend().remove()


    sns.scatterplot(data=perf_vjoule,
                    x=domain_perf_vjoule_1,
                    y=domain_perf_vjoule_2,
                    hue="processor_detail",
                    palette=processor_palette,
                    ax=axs[1, 1]

                    )
    sns.lineplot(x=[0, max_both_perf_vjoule], y=[0, max_both_perf_vjoule], ax=axs[1, 1],color="red", linestyle="dashed", label="f(x) = x")
    axs[1, 1].set_title(f"Correlation of Perf and vjoule over PKG domain")
    axs[1, 1].set_xlabel(f"PERF for PKG domain")
    axs[1, 1].set_ylabel(f"vjoule for PKG domain")
    handles, labels = axs[1, 1].get_legend_handles_labels()
    #new_labels = [f"{label} (corr: {corr_dict_perf_vjoule.get(label, 'N/A'):.2f})" for label in labels if label in corr_dict_perf_vjoule]
    #axs[1, 1].legend(handles, new_labels, loc="lower right", bbox_to_anchor=(1.75, 0.2))
    axs[1, 1].legend(handles, labels, loc="lower right", bbox_to_anchor=(1.75, 0.2))

    plt.tight_layout()
    plt.subplots_adjust(hspace=0.4, wspace=0.40)
    plt.show()

def heatmap_tools_cv(dataframe, tools=["hwpc_and_perf", "codecarbon_and_perf", "alumet_and_perf", "scaphandre_and_perf", "vjoule_and_perf"], domain="pkg"):
    dataframe = dataframe.to_pandas()
    pivot_pkg = dataframe.pivot_table(columns="processor_detail", index="task", values=f"pkg_coefficient_of_variation", aggfunc="median")

    pivot_cores = dataframe.pivot_table(columns="processor_detail", index="task", values=f"cores_coefficient_of_variation", aggfunc="median")

    pivot = pd.concat([pivot_pkg, pivot_cores])
    custom_order = ["scaphandre_and_perf", "alumet_and_perf", "codecarbon_and_perf", "hwpc_and_perf", "vjoule_and_perf" ]
    pivot = pivot.reindex(custom_order)
    print("pivot reindexed", pivot)
    plt.figure(figsize=(12, 5))
    ax = sns.heatmap(
            data=pivot,
            annot=True,
            robust=True,
            linewidth=.5,
            cmap="bwr",
            fmt=".3f",
            annot_kws={"size": 12, "fontweight" : "light"},
            cbar_kws={'label': 'Coefficient of Variation'}
            )
    
    ax.set_yticklabels(["Scaphandre", "Alumet", "CodeCarbon", "HWPC Sensor", "vJoule"])
    values = {}
    for idx, text in enumerate(ax.texts):
        x, y = text.get_position()
        value = text.get_text()
        if not values.get(x):
            values[x] = [(value, idx)]
        else:
            values[x].append((value, idx))
    for col in values.keys():
        idx = values[col][values[col].index(min(values[col]))][1]
        ax.texts[idx].set_fontweight('heavy')
    title = f"Heatmap of median PKG/Cores domains measurements CV by processor and PowerMetter Software"
    safe_title = re.sub(r'[^\w\s-]', '', title)  # Remove invalid characters
    safe_title = safe_title.replace(" ", "_")
    safe_title = safe_title.replace("\n", "_")
    plt.title(title)
    plt.xlabel("Processor version and generation")
    plt.ylabel("PowerMetter Software")

    plt.tight_layout()
    plt.show()

def diff_tool_perf_ci(dataframe):
   hwpc = dataframe.sql("SELECT * FROM self WHERE task = 'hwpc_and_perf'")
   perf_hwpc = dataframe.sql("SELECT * FROM self WHERE task = 'perf_and_hwpc'")
   codecarbon = dataframe.sql("SELECT * FROM self WHERE task = 'codecarbon_and_perf'")
   perf_codecarbon = dataframe.sql("SELECT * FROM self WHERE task = 'perf_and_codecarbon'")
   alumet = dataframe.sql("SELECT * FROM self WHERE task = 'alumet_and_perf'")
   perf_alumet = dataframe.sql("SELECT * FROM self WHERE task = 'perf_and_alumet'")
   scaphandre = dataframe.sql("SELECT * FROM self WHERE task = 'scaphandre_and_perf'")
   perf_scaphandre = dataframe.sql("SELECT * FROM self WHERE task = 'perf_and_scaphandre'")
   vjoule = dataframe.sql("SELECT * FROM self WHERE task = 'vjoule_and_perf'")
   perf_vjoule = dataframe.sql("SELECT * FROM self WHERE task = 'perf_and_vjoule'")
   
   hwpc_joined_dataframe = hwpc.join(            other=perf_hwpc,             on=["node", "nb_core", "nb_ops_per_core", "iteration"],            how="left",            validate="1:1",            suffix="_perf_hwpc"            )
   hwpc_joined_dataframe = hwpc_joined_dataframe.with_columns((pl.col("energy_pkg") - pl.col("energy_pkg_perf_hwpc")).alias("diff_hwpc_perf"))
   codecarbon_joined_dataframe = codecarbon.join(            other=perf_codecarbon,             on=["node", "nb_core", "nb_ops_per_core", "iteration"],            how="left",            validate="1:1",            suffix="_perf_codecarbon"            )
   alumet_joined_dataframe = alumet.join(            other=perf_alumet,             on=["node", "nb_core", "nb_ops_per_core", "iteration"],            how="left",            validate="1:1",            suffix="_perf_alumet"            )
   scaphandre_joined_dataframe = scaphandre.join(            other=perf_scaphandre,             on=["node", "nb_core", "nb_ops_per_core", "iteration"],            how="left",            validate="1:1",            suffix="_perf_scaphandre"            )
   vjoule_joined_dataframe = vjoule.join(            other=perf_vjoule,             on=["node", "nb_core", "nb_ops_per_core", "iteration"],            how="left",            validate="1:1",            suffix="_perf_vjoule"            )


