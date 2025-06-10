import matplotlib.pyplot as plt
import numpy as np
import re
import seaborn as sns
import polars as pl

palette = {
        "hwpc_with_perf": "#17becf",
        "perf_with_hwpc": "#ff7f0e",
    }

def plot_violinplot(dfs, x, y, hue, save=True, show=True):
    fig, axs = plt.subplots(nrows=1, ncols=2, sharey=True)
    plt.ylim(0, 1)

    sns.violinplot(ax=axs[0], data=dfs[0], x=x, y=y, hue=hue, inner="quart", gap=0.1)

    sns.violinplot(
        ax=axs[1], data=dfs[1], x=x, y=y, hue=hue, inner="quart", gap=0.1, cut=0.1
    )
    plt.title(f"{y} for {x} by {hue}")
    if show:
        plt.show()


def plot_boxplot(df, x, y, hue, prefix, save=True, show=True):
    plt.figure(figsize=(12, 6))
    plt.ylim(0, .1)
    df = df.sql("SELECT * FROM self WHERE nb_ops_per_core > 25")
    sns.boxplot(data=df, x=x, y=y, hue=hue)
   # sns.boxplot(
   #     data=df,
   #     x=x,
   #     y=y,
   #     hue=hue,
   # )

    title = f"{prefix} - HWPC Coefficient of Variation\n{y} for {x} by {hue}"
    safe_title = re.sub(r'[^\w\s-]', '', title)  # Remove invalid characters
    safe_title = safe_title.replace(" ", "_")
    safe_title = safe_title.replace("\n", "_")
    if save:
        plt.savefig(f'{safe_title}.png', dpi=600)
    if show:
        plt.show()

def plot_facet_grid_nb_ops_per_core_versions_domain_cv(df, domain, os, save=True, show=True):
    df = df.to_pandas()
    df = df.sort_values(by=["processor_vendor", "processor_generation"])
    g = sns.FacetGrid(
        df,
        col="nb_ops_per_core",  # Each grid is for a unique nb_ops_per_core value
        sharey=True,  # Share the y-axis across all grids
        margin_titles=True,
        aspect=2,  # Adjust the aspect ratio of the grid
        height=7,  # Set the height of each subplot
        palette=palette,
        col_wrap=3,
    )

    plt.ylim(0, 1)
    # Map the boxplot to each grid
    g.map(
        sns.boxplot,
        "processor_detail",  # X-axis
        f"{domain}_coefficient_of_variation",  # Y-axis
        "job",  # Hue for grouping
        palette=palette,
        showfliers=False,
    )
    g.set_axis_labels("Processor Detail", f"{domain} coefficient of variation")
    g.set_titles(col_template="Ops per Core: {col_name}")
    g.add_legend(title="Job")
    g.legend.set_bbox_to_anchor((0.85, 0.75))  # (x, y) coordinates relative to the first subplot
    g.legend.set_frame_on(True)
    # Rotate x-axis labels for better readability
    for ax in g.axes.flat:
        ax.tick_params(axis="x", rotation=90)
    title = f"Boxplots of {domain} measurements CV by nb_ops_per_core and processor versions - {os}"
    safe_title = re.sub(r'[^\w\s-]', '', title)  # Remove invalid characters
    safe_title = safe_title.replace(" ", "_")
    safe_title = safe_title.replace("\n", "_")
    plt.suptitle(title)
    plt.tight_layout()
    if save:
        plt.savefig(f'{safe_title}.png', dpi=600)
    if show:
        plt.show()

def plot_boxplots(dfs, x, y, hue, prefix, save=True, show=True):
    fig, axs = plt.subplots(nrows=1, ncols=2,figsize=(16,7) ,sharey=True)
    dfs[0] = dfs[0].sort(x)
    dfs[1] = dfs[1].sort(x)
    
    plt.ylim(0, 1)

    sns.boxplot(
        ax=axs[0],
        data=dfs[0],
        x=x,
        y=y,
        hue=hue,
        gap=0.1,
        palette=palette,
        showfliers=False,
    )
    axs[0].set_title("Debian11 - Kernel 5.10 - HWPC Coefficient of Variation")
    axs[0].set_xticklabels(axs[0].get_xticklabels(), rotation=90, ha="right")
    sns.boxplot(
        ax=axs[1],
        data=dfs[1],
        x=x,
        y=y,
        hue=hue,
        gap=0.1,
        palette=palette,
        showfliers=False,
    )
    axs[1].set_title("Ubuntu2404nfs - Kernel 6.8 - HWPC Coefficient of Variation")
    axs[1].set_xticklabels(axs[1].get_xticklabels(), rotation=90, ha="right")
    title = f"{prefix}\n{y} for {x} by {hue}"
    safe_title = re.sub(r'[^\w\s-]', '', title)  # Remove invalid characters
    safe_title = safe_title.replace(" ", "_")
    safe_title = safe_title.replace("\n", "_")
    plt.title(title)
    plt.tight_layout()
    if save:
        plt.savefig(f'{safe_title}.png', dpi=600)
    if show:
        plt.show()

def plot_os_degradation_nb_ops(joined_df, domain, tool, save=True, show=True):
    joined_df = joined_df.with_columns(
        (
            (
                pl.col(f"{domain}_coefficient_of_variation")
                - pl.col(f"{domain}_coefficient_of_variation_debian")
            ).alias(f"{domain}_diff")
        )
    )

    joined_df = joined_df.with_columns(
        (
            (
                pl.col(f"{domain}_coefficient_of_variation")
                / pl.col(f"{domain}_coefficient_of_variation_debian")
            ).alias(f"{domain}_ratio")
        )
    )


    aggregated = joined_df.group_by(["processor_detail", "nb_ops_per_core"]).agg(
        pl.col(f"{domain}_ratio").median().alias(f"{domain}_median_ratio"),
        pl.col(f"{domain}_diff").median().alias(f"{domain}_median_diff"),
        pl.col("processor_vendor").min().alias("processor_vendor"),
        pl.col("processor_generation").min().alias("processor_generation"),
    )

    df_pandas = aggregated.to_pandas()
    df_pandas = df_pandas.sort_values(by=["processor_vendor", "processor_generation"])

    plt.figure(figsize=(12, 5))
    ratio_cmap = sns.diverging_palette(220, 20, l=65, center="light", as_cmap=True)
    pivot_table = df_pandas.pivot(
        index="nb_ops_per_core",
        columns="processor_detail",
        values=f"{domain}_median_ratio",
    )

    sns.heatmap(
        pivot_table,
        annot=True,
        fmt=".2f",
        cmap=ratio_cmap,
        vmin=0,
        vmax=2,
    )
    title = f"Heatmap of median ratio of {domain} measurements CV (ubuntu/debian) by vendor\nfor {tool} tool"
    safe_title = re.sub(r'[^\w\s-]', '', title)  # Remove invalid characters
    safe_title = safe_title.replace(" ", "_")
    safe_title = safe_title.replace("\n", "_")
    plt.title(title)
    plt.xlabel("Processor version and generation")
    plt.ylabel("Number of operations per core")
    plt.tight_layout()
    if save:
        plt.savefig(f'{safe_title}.png', dpi=600)
    if show:
        plt.show()

    diff_cmap = sns.diverging_palette(220, 20, l=65, center="light", as_cmap=True)
    plt.figure(figsize=(15, 6))
    pivot_table = df_pandas.pivot(
        index="nb_ops_per_core",
        columns="processor_detail",
        values=f"{domain}_median_diff",
    )
    q1 = np.nanpercentile(pivot_table.values, 25)
    q3 = np.nanpercentile(pivot_table.values, 75)
    iqr = q3 - q1
    vmax = q3 + 1.5 * iqr
    sns.heatmap(
        pivot_table,
        annot=True,
        fmt=".2f",
        cmap=diff_cmap,
        vmin=-vmax,
        vmax=vmax,
    )
    plt.xlabel("Processor Details")
    plt.xticks(rotation=90, ha="right")
    plt.ylabel("Number of Operations Per Core")
    
    title = f"Heatmap of median diff for {domain} measurements CV (ubuntu - debian) by vendor\nfor {tool} tool"
    safe_title = re.sub(r'[^\w\s-]', '', title)  # Remove invalid characters
    safe_title = safe_title.replace(" ", "_")
    safe_title = safe_title.replace("\n", "_")
    plt.title(title)
    plt.tight_layout()
    if save:
        plt.savefig(f'{safe_title}.png', dpi=600)
    if show:
        plt.show()


def plot_os_degradation_percent_used(joined_df, domain, save=True, show=True):
    joined_df = joined_df.with_columns(
        (
            (
                pl.col(f"{domain}_coefficient_of_variation")
                - pl.col(f"{domain}_coefficient_of_variation_debian")
            ).alias(f"{domain}_diff")
        )
    )

    joined_df = joined_df.with_columns(
        (
            (
                pl.col(f"{domain}_coefficient_of_variation")
                / pl.col(f"{domain}_coefficient_of_variation_debian")
            ).alias(f"{domain}_ratio")
        )
    )

    aggregated = joined_df.group_by(["processor_detail", "percent_cores_used_category"]).agg(
        pl.col(f"{domain}_ratio").median().alias(f"{domain}_median_ratio"),
        pl.col(f"{domain}_diff").median().alias(f"{domain}_median_diff"),
    )

    df_pandas = aggregated.to_pandas()
    df_pandas = df_pandas.sort_values(by=["processor_detail"])

    plt.figure(figsize=(12, 5))
    ratio_cmap = sns.diverging_palette(220, 20, l=65, center="light", as_cmap=True)
    pivot_table = df_pandas.pivot(
        index="percent_cores_used_category",
        columns="processor_detail",
        values=f"{domain}_median_ratio",
    )

    sns.heatmap(
        pivot_table,
        annot=True,
        fmt=".2f",
        cmap=ratio_cmap,
        vmin=0,
        vmax=2,
    )
    title = f"Heatmap of median ratio of HWPC {domain} measurements CV (ubuntu/debian) by vendor"
    safe_title = re.sub(r'[^\w\s-]', '', title)  # Remove invalid characters
    safe_title = safe_title.replace(" ", "_")
    safe_title = safe_title.replace("\n", "_")
    plt.title(title)
    plt.tight_layout()
    if save:
        plt.savefig(f'{safe_title}.png', dpi=600)
    if show:
        plt.show()

    diff_cmap = sns.diverging_palette(220, 20, l=65, center="light", as_cmap=True)
    plt.figure(figsize=(15, 6))
    pivot_table = df_pandas.pivot(
        index="percent_cores_used_category",
        columns="processor_detail",
        values=f"{domain}_median_diff",
    )
    q1 = np.nanpercentile(pivot_table.values, 25)
    q3 = np.nanpercentile(pivot_table.values, 75)
    iqr = q3 - q1
    vmax = q3 + 1.5 * iqr
    sns.heatmap(
        pivot_table,
        annot=True,
        fmt=".2f",
        cmap=diff_cmap,
        vmin=-vmax,
        vmax=vmax,
    )
    plt.xlabel("Processor Details")
    plt.xticks(rotation=90, ha="right")
    plt.ylabel("Percent core used")

    title = f"Heatmap of median diff for HWPC {domain} measurements CV (ubuntu - debian) by vendor"
    safe_title = re.sub(r'[^\w\s-]', '', title)  # Remove invalid characters
    safe_title = safe_title.replace(" ", "_")
    safe_title = safe_title.replace("\n", "_")
    plt.title(title)
    plt.tight_layout()
    if save:
        plt.savefig(f'{safe_title}.png', dpi=600)
    if show:
        plt.show()

