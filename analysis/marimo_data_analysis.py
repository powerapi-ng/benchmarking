# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "altair==6.0.0",
#     "matplot2tikz==0.5.1",
#     "matplotlib==3.10.7",
#     "mplcyberpunk==0.7.6",
#     "numpy==2.3.5",
#     "polars==1.34.0",
#     "pyarrow",
#     "ruff==0.14.4",
#     "seaborn==0.13.2",
#     "tikzplotlib==0.10.1",
#     "tqdm==4.67.1",
#     "vegafusion==2.0.3",
#     "vl-convert-python==1.8.0",
# ]
# ///

import marimo

__generated_with = "0.17.2"
app = marimo.App(width="full")


@app.cell
def _():
    # IMPORTS
    import os # open files
    import sys 
    import argparse 
    import random 
    import polars as pl # Dataframes for data manipulation
    import pandas as pd
    import numpy as np # Statistics
    import gc 
    import math



    import schemas # Dataframes schemas
    import load # Lib for data loading

    import matplotlib.pyplot as plt # Viz package 1
    import matplotlib.patheffects as path_effects
    from matplotlib.colors import LogNorm
    import matplotlib.ticker as ticker
    import seaborn as sns # Viz package  2
    plt.style.use("seaborn-v0_8-paper")


    from pprint import pprint # Pretty print for data structures
    import re # regex
    import marimo as mo
    import test_file_load

    import json
    from pathlib import Path
    return Path, json, load, math, mo, np, pd, pl, plt, re, sns, test_file_load


@app.cell
def _(mo):
    mo.md(r"""# Vendor generation map with informations about processors""")
    return


@app.cell(hide_code=True)
def vendor_generation_map_1():
    vendor_generation_map = {
        "E5-2620 v4": {
            "architecture": "Broadwell-E",
            "vendor": "Intel",
            "generation": 6,
            "launch_date": "2016 Q1",
            "numa_nodes_number": "2",
            "numa_nodes_first_cpus": [0, 1],
        },
        "E5-2630L v4": {
            "architecture": "Broadwell-E",
            "vendor": "Intel",
            "generation": 6,
            "launch_date": "2016 Q1",
            "numa_nodes_number": "2",
            "numa_nodes_first_cpus": [0, 1],
        },
        "E5-2698 v4": {
            "architecture": "Broadwell-E",
            "vendor": "Intel",
            "generation": 6,
            "launch_date": "2016 Q1",
            "numa_nodes_number": "2",
            "numa_nodes_first_cpus": [0, 1],
        },
        "E5-2630 v3": {
            "architecture": "Haswell-E",
            "vendor": "Intel",
            "generation": 5,
            "launch_date": "2014 Q3",
            "numa_nodes_number": "2",
            "numa_nodes_first_cpus": [0, 1],
        },
        "Gold 5220": {
            "architecture": "Cascade Lake-SP",
            "vendor": "Intel",
            "generation": 10,
            "launch_date": "2019 Q2",
            "numa_nodes_number": "1",
            "numa_nodes_first_cpus": [0],
        },
        "Gold 5218": {
            "architecture": "Cascade Lake-SP",
            "vendor": "Intel",
            "generation": 10,
            "launch_date": "2019 Q2",
            "numa_nodes_number": "2",
            "numa_nodes_first_cpus": [0, 1],
        },
        "i7-9750H": {
            "architecture": "Coffee Lake",
            "vendor": "Intel",
            "generation": 9,
            "launch_date": "2019 Q2",
            "numa_nodes_number": "2",
            "numa_nodes_first_cpus": [0, 1],
        },
        "Silver 4314": {
            "architecture": "Ice Lake-SP",
            "vendor": "Intel",
            "generation": 10,
            "launch_date": "2021 Q2",
            "numa_nodes_number": "2",
            "numa_nodes_first_cpus": [0, 1],
        },
        "Gold 5320": {
            "architecture": "Ice Lake-SP",
            "vendor": "Intel",
            "generation": 10,
            "launch_date": "2021 Q2",
            "numa_nodes_number": "2",
            "numa_nodes_first_cpus": [0, 1],
        },
        "Gold 6126": {
            "architecture": "Skylake-SP",
            "vendor": "Intel",
            "generation": 6,
            "launch_date": "2017 Q3",
            "numa_nodes_number": "2",
            "numa_nodes_first_cpus": [0, 1],
        },
        "Gold 6130": {
            "architecture": "Skylake-SP",
            "vendor": "Intel",
            "generation": 6,
            "launch_date": "2017 Q3",
            "numa_nodes_number": "2",
            "numa_nodes_first_cpus": [0, 1],
        },
        "E5-2620": {
            "architecture": "Sandy Bridge-EP",
            "vendor": "Intel",
            "generation": 3,
            "launch_date": "2012 Q1",
            "numa_nodes_number": "2",
            "numa_nodes_first_cpus": [0, 1],
        },
        "E5-2630": {
            "architecture": "Sandy Bridge-EP",
            "vendor": "Intel",
            "generation": 3,
            "launch_date": "2012 Q1",
            "numa_nodes_number": "2",
            "numa_nodes_first_cpus": [0, 1],
        },
        "E5-2630L": {
            "architecture": "Sandy Bridge-EP",
            "vendor": "Intel",
            "generation": 3,
            "launch_date": "2012 Q1",
            "numa_nodes_number": "2",
            "numa_nodes_first_cpus": [0, 1],
        },
        "E5-2660": {
            "architecture": "Sandy Bridge-EP",
            "vendor": "Intel",
            "generation": 3,
            "launch_date": "2012 Q1",
            "numa_nodes_number": "2",
            "numa_nodes_first_cpus": [0, 1],
        },
        "X5670": {
            "architecture": "Westmere-EP",
            "vendor": "Intel",
            "generation": 1,
            "launch_date": "2010 Q1",
            "numa_nodes_number": "2",
            "numa_nodes_first_cpus": [0, 1],
        },
        "7301": {
            "architecture": "Zen",
            "vendor": "AMD",
            "generation": 1,
            "launch_date": "2017 Q2",
            "numa_nodes_number": "8",
            "numa_nodes_first_cpus": [0, 1, 2, 3, 4, 5, 6, 7],
        },
        "7352": {
            "architecture": "Zen 2",
            "vendor": "AMD",
            "generation": 2,
            "launch_date": "2019 Q3",
            "numa_nodes_number": "2",
            "numa_nodes_first_cpus": [0, 1],
        },
        "7452": {
            "architecture": "Zen 2",
            "vendor": "AMD",
            "generation": 2,
            "launch_date": "2019 Q3",
            "numa_nodes_number": "2",
            "numa_nodes_first_cpus": [0, 1],
        },
        "7642": {
            "architecture": "Zen 2",
            "vendor": "AMD",
            "generation": 2,
            "launch_date": "2019 Q3",
            "numa_nodes_number": "2",
            "numa_nodes_first_cpus": [0, 1],
        },
        "7742": {
            "architecture": "Zen 2",
            "vendor": "AMD",
            "generation": 2,
            "launch_date": "2019 Q3",
            "numa_nodes_number": "2",
            "numa_nodes_first_cpus": [0, 1],
        },
        "250": {
            "architecture": "Opteron",
            "vendor": "AMD",
            "generation": 1,
            "launch_date": "2004 Q4",
            "numa_nodes_number": "2",
            "numa_nodes_first_cpus": [0, 1],
        },
        "99xx": {
            "architecture": "ThunderX2",
            "vendor": "Cavium",
            "generation": 1,
            "launch_date": "2016 Q2",
            "numa_nodes_number": "2",
            "numa_nodes_first_cpus": [0, 1],
        },
    }

    return (vendor_generation_map,)


@app.cell
def globals(sns):
    TOOLS = ["hwpc", "codecarbon", "alumet", "scaphandre", "vjoule"]
    palette_for_tools = {
        "hwpc": "#4878CF",        
        "codecarbon": "#6ACC65",  
        "alumet": "#D65F5F",      
        "scaphandre": "#B47CC7",  
        "vjoule": "#C4AD66",      
    }
    sns_palette_for_tools = sns.color_palette(list(palette_for_tools.values()))

    batch_identifier = "ubuntu2404nfs-6.8-6"#input("Enter the batch identifier : e.g ubuntu2404nfs-6.10-6")
    results_directory = f"../data/{batch_identifier}.d/results-{batch_identifier}.d"
    inventories_directory = (f"../data/{batch_identifier}.d/inventories-{batch_identifier}.d")
    return (
        batch_identifier,
        inventories_directory,
        palette_for_tools,
        results_directory,
    )


@app.cell
def _(Path, inventories_directory, json, pl, vendor_generation_map):
    def load_inventory(directory: str) -> pl.DataFrame:
        data = []
        print("Loading inventory from:", directory)

        for file_path in Path(directory).rglob("*.json"):
            try:
                with open(file_path, "r") as f:
                    content = json.load(f)

                cluster = content.get("cluster")
                cores = content.get("architecture", {}).get("nb_cores")
                microarch = content.get("processor", {}).get("microarchitecture")
                vendor = content.get("processor", {}).get("vendor")
                version = content.get("processor", {}).get("version")
                other_desc = content.get("processor", {}).get("other_description")

                data.append({
                    "cluster": cluster,
                    "cores_per_node": cores,
                    "microarchitecture": microarch,
                    "vendor": vendor,
                    "version": version,
                    "other_description": other_desc
                })

            except Exception as e:
                print(f"Error reading {file_path}: {e}")

        df = pl.DataFrame(data)

        # Count nodes & compute total cores per cluster
        return (
            df.group_by("cluster")
            .agg([
                pl.len().alias("node_count"),
                pl.first("cores_per_node"),
                pl.first("microarchitecture"),
                pl.first("vendor"),
                pl.first("version"),
                pl.first("other_description")
            ])
            .with_columns(
                (pl.col("node_count") * pl.col("cores_per_node")).alias("total_cores")
            )
        )

    inventory = load_inventory(directory=inventories_directory)

    # Step 1: Convert vendor_generation_map to a Polars DataFrame
    map_data = [
        {"version": version, **info}
        for version, info in vendor_generation_map.items()
    ]

    vendor_map_df = pl.DataFrame(map_data)

    # Step 2: Join with inventory on "version"
    inventory = inventory.join(
        vendor_map_df,
        left_on="version",
        right_on="version",
        how="left"
    )

    # Step 3: Optional: create processor_description column
    inventory = inventory.with_columns([
        (pl.col("architecture").cast(str) + " (" + pl.col("launch_date") + ")").alias("processor_description")
    ])
    return (inventory,)


@app.cell
def _():
    return


@app.cell
def _(mo):
    mo.md(r"""# Testing loading""")
    return


@app.cell
def _(results_directory, test_file_load):
    test_file_load.test_all_files(
        results_dir=f"{results_directory}/rennes/parasilo/parasilo-24",
        nb_core=32,
        nb_ops=25_000,
    )
    return


@app.cell
def _(mo):
    mo.md(r"""# Baseline Consumption analysis""")
    return


@app.cell
def _(batch_identifier, inventory, load, pl, plt, results_directory, sns):


    baseline_consumptions = load.load_baseline(
            batch_identifier=batch_identifier,
            results_directory=results_directory)

    baseline_consumptions = baseline_consumptions.with_columns([
        # Compute lower bound of the 5°C bin
        (pl.col("average_temperature") // 5 * 5).alias("temp_lower"),
        # Compute upper bound
        ((pl.col("average_temperature") // 5 * 5) + 4).alias("temp_upper")
    ])

    # Combine into formatted interval strings like "45-50°C"
    baseline_consumptions = baseline_consumptions.with_columns([
        (pl.col("temp_lower").cast(pl.Float64).cast(pl.Utf8) + "-" +
         pl.col("temp_upper").cast(pl.Float64).cast(pl.Utf8) + "°C"
        ).alias("temperature_range")
    ])

    baseline_consumptions = baseline_consumptions.sql(
        """
        SELECT 
            g5k_cluster, 
            avg(pkg) AS average_pkg, 
            avg(ram) AS average_ram,
            stddev(pkg) AS std_pkg,
            stddev(ram) AS std_ram,
            temperature_range
        FROM self 
        GROUP BY 
            g5k_cluster,
            temperature_range
        ORDER BY g5k_cluster
        """
    )



    baseline = baseline_consumptions.join(
        other=inventory,
        left_on=["g5k_cluster"],
        right_on=["cluster"],
        how="left",
        #validate="1:m"
    )

    baseline = baseline.with_columns([
        (pl.col("average_pkg") / pl.col("cores_per_node")).alias("pkg_per_core"),
        (pl.col("average_ram") / pl.col("cores_per_node")).alias("ram_per_core"),
        (pl.col("std_pkg") / pl.col("cores_per_node")).alias("pkg_per_core_std"),
        (pl.col("std_ram") / pl.col("cores_per_node")).alias("ram_per_core_std"),
    ])




    df_baseline_facetgrid = baseline.to_pandas()

    df_baseline_facetgrid = df_baseline_facetgrid.sort_values(
        ["temperature_range"]
    )


    unique_temps = sorted(df_baseline_facetgrid["temperature_range"].unique())
    n_colors = len(unique_temps)
    cmap = sns.color_palette("coolwarm", n_colors=n_colors)  # you can also try "viridis" or "Spectral"

    # Map each temperature range low to a specific color
    color_map = dict(zip(unique_temps, cmap))


    # --- Custom plotting function with color and error bars ---
    def plot_with_errorbars(data, **kwargs):
        # Sort values for consistent bar order
        data = data.sort_values("temperature_range")

        colors = [color_map[val] for val in data["temperature_range"]]


        ax = sns.barplot(
            data=data,
            x="temperature_range",
            y="pkg_per_core",
            estimator="median",
            hue="temperature_range",
            palette=color_map,
            errorbar=None,     # Disable seaborn error bars
            **kwargs
        )

        # Extract bar center positions
        x_coords = [p.get_x() + p.get_width() / 2 for p in ax.patches]

        # Pull standard deviations for each bar
        yerr = data["pkg_per_core_std"].values

        # Add error bars manually
        ax.errorbar(
            x=x_coords,
            y=data["pkg_per_core"],
            yerr=yerr,
            fmt="none",
            capsize=3,
            linewidth=1,
            color="black"
        )
        #ax.set_title(ax.get_title().split("processor_description = ")[1])
        every_nth = 2
        for n, label in enumerate(ax.xaxis.get_ticklabels()):
            if n % every_nth != 0:
                label.set_visible(False)
        plt.xticks(rotation=45, ha="right", fontsize=8)



    sns.set_theme(context="paper", style="whitegrid")
    selected_clusters = [
        "chiclet",
        "chuc",
        "gros",
        "parasilo",
        "paradoxe",
        "taurus",
        "chifflot",
        "fleckenstein",
        "montcalm",
        "econome",
        "ecotype",
        "nova"
    ]
    df_baseline_facetgrid_filtered_temperatures = df_baseline_facetgrid[df_baseline_facetgrid["g5k_cluster"].isin(selected_clusters)]

    # Compute a paper-friendly figure size (7in wide total)
    g = sns.FacetGrid(
        df_baseline_facetgrid_filtered_temperatures,
        col="g5k_cluster",
        col_wrap=5,
        height=2.2,         # Adjust to make it compact
        aspect=1.0,
        sharex=True,
        sharey=True,
    )

    g.map_dataframe(plot_with_errorbars)

    # Axis labels and main title
    g.set_axis_labels("Temperature Range", "Baseline Package \nConsumption per Core (W)", fontsize=8)
    g.fig.suptitle("", y=1.03, fontsize=10)
    g.set_titles(col_template="{col_name}", fontsize=12)


    g.savefig("baseline_consumption_clusters.png", bbox_inches="tight", dpi=600)
    plt.show()
    return baseline, selected_clusters


@app.cell
def _(batch_identifier, inventory, load, pl, plt, results_directory, sns):
    baseline_consumptions_n = load.load_baseline(
            batch_identifier=batch_identifier,
            results_directory=results_directory)

    baseline_consumptions_n = baseline_consumptions_n.join(
        other=inventory,
        left_on=["g5k_cluster"],
        right_on=["cluster"],
        how="left"
    )

    baseline_consumptions_n = baseline_consumptions_n.with_columns([
        (pl.col("pkg") / pl.col("cores_per_node")).alias("pkg_per_core"),
        (pl.col("ram") / pl.col("cores_per_node")).alias("ram_per_core")
    ])


    baseline_consumptions_n.sort("launch_date")

    baseline_long = baseline_consumptions_n.select(
        pl.col("g5k_cluster"),
        pl.col("microarchitecture"),
        pl.col("version"),
        pl.col("launch_date"),
        pl.col("pkg_per_core").alias("value"),
        pl.lit("Package").alias("metric")
    ).vstack(
        baseline_consumptions_n.select(
            pl.col("g5k_cluster"),
            pl.col("microarchitecture"),
            pl.col("version"),
            pl.col("launch_date"),
            pl.col("ram_per_core").alias("value"),
            pl.lit("RAM").alias("metric")
        )
    )


    df_long = baseline_long.to_pandas()
    df_long["processor_label"] = (
        df_long["microarchitecture"] + " (" +
        df_long["version"] + ", " +
        df_long["launch_date"].astype(str) + ")"
    )


    sns.set_theme(context="paper", style="whitegrid")

    fig, ax = plt.subplots(figsize=(12, 5))

    # Draw grouped bars (pkg and ram)
    barplot = sns.barplot(
        data=df_long,
        x="processor_label",
        y="value",
        hue="metric",
        estimator="median",
        errorbar=("pi", 50),      
        ax=ax
    )

    # Format x-axis labels and axis titles
    ax.set_xlabel("Processor (Architecture, Version, Launch Date)", fontsize=12)
    ax.set_ylabel("Baseline Consumption\nper Core (W)", fontsize=12)
    ax.tick_params(axis="x", labelrotation=45, labelsize=10)
    plt.legend(frameon=False, fontsize=12, title_fontsize=10, loc="upper left", title="Domain")
    for label in ax.get_xticklabels():
        label.set_ha("right")
        label.set_rotation_mode("anchor")

    plt.savefig("baseline_consumption_clusters_domains.png", bbox_inches="tight", dpi=600)

    plt.tight_layout()
    plt.show()

    return


@app.cell
def _():
    return


@app.cell
def _(mo):
    mo.md(r"""#Frequency analysis""")
    return


@app.cell
def _(batch_identifier, load, results_directory):

    (
        perf_frequency,
        hwpc_frequency,
        codecarbon_frequency,
        alumet_frequency,
        scaphandre_frequency,
        vjoule_frequency,
    ) = load.load_frequency(
        batch_identifier=batch_identifier, results_directory=results_directory
    )

    vjoule_frequency_agg_raw = load.load_vjoule_frequency_agg(batch_identifier, results_directory)
    codecarbon_frequency_agg_raw = load.load_codecarbon_frequency_agg(batch_identifier, results_directory)
    return (
        alumet_frequency,
        codecarbon_frequency,
        codecarbon_frequency_agg_raw,
        hwpc_frequency,
        scaphandre_frequency,
        vjoule_frequency,
        vjoule_frequency_agg_raw,
    )


@app.cell
def _(
    alumet_frequency,
    codecarbon_frequency,
    hwpc_frequency,
    np,
    pl,
    scaphandre_frequency,
    vjoule_frequency,
):
    def collect_frequency_data(frequency_df, frequencies, metadatada):
        tool = metadatada["tool"]
        unit = metadatada["unit"]

        target = []
        reached = []

        for frequency in frequencies:
            df_ts = frequency_df.sql(
                f"""
                SELECT node, iteration, timestamp
                FROM self
                WHERE frequency = {frequency}
                ORDER BY node, iteration, timestamp
                """
            ).to_pandas()

            for (node, iteration), group in df_ts.groupby(["node", "iteration"]):
                arr = group["timestamp"].values.astype(float)

                if arr.size < 2:
                    continue

                # computes (n+1 - n) interval and get inverse
                arr = np.sort(arr)
                intervals = arr[1:] - arr[:-1]

                if unit == "milliseconds":
                    inst_freqs = 1000.0 / intervals
                else:
                    inst_freqs = 1.0 / intervals

                reached.extend(inst_freqs.tolist())
                target.extend([frequency] * len(inst_freqs))

        return pl.DataFrame({
            "tool": tool,
            "target_frequency": target,
            "reached_frequency": reached,
        })



    df_all = pl.concat([
        collect_frequency_data(hwpc_frequency, [1, 10, 100, 1000], {"tool": "hwpc", "unit": "milliseconds"}),
        collect_frequency_data(codecarbon_frequency, [1, 10, 100, 1000], {"tool": "codecarbon", "unit": "seconds"}),
        collect_frequency_data(alumet_frequency, [1, 10, 100, 1000], {"tool": "alumet", "unit": "seconds"}),
        collect_frequency_data(scaphandre_frequency, [1, 10, 100, 1000], {"tool": "scaphandre", "unit": "seconds"}),
        collect_frequency_data(vjoule_frequency, [1, 10, 100, 1000], {"tool": "vjoule", "unit": "seconds"}),
    ])
    return (df_all,)


@app.cell
def _(df_all):
    sampled = df_all.sample(fraction=0.10).sort("tool")
    return (sampled,)


@app.cell
def _(palette_for_tools, plt, sampled, sns):
    plt.figure(figsize=(8,8))
    sns.lineplot(
        data=sampled, x="target_frequency", y="reached_frequency", hue="tool", err_style="bars", errorbar=("ci"), palette=palette_for_tools
    )
    sns.lineplot(
        x=[0,1000], y=[0,1000], dashes=(2, 2), legend="auto"
    )

    plt.xscale("log")
    plt.yscale("log")

    plt.xlabel("Target Frequency (Hz)", fontsize=12)
    plt.ylabel("Reached Frequency (Hz)", fontsize=12)
    plt.tick_params(axis="x", labelsize=12)
    plt.tick_params(axis="y", labelsize=12)
    plt.title("", pad=6, fontsize=12)
    plt.xlim(0,10000)
    plt.ylim(0,10000)
    plt.legend(frameon=False, fontsize=12, title_fontsize=10, loc="upper left")
    plt.grid(True, which="major", linestyle="--", linewidth=0.4, alpha=0.6)

    plt.savefig("reached_vs_target_frequency.png", bbox_inches="tight", dpi=600)
    plt.show()
    return


@app.cell
def _(mo):
    mo.md(r"""##Overhead function of frequency""")
    return


@app.cell
def _(Path, pl, re, results_directory):
    # Define the root directory to search
    temperatures_root_dir = Path(results_directory)  # change this to your directory

    # Define the filename pattern (regex to extract frequency and tool)
    temperatures_pattern = re.compile(r"temperatures_frequency_(\d+)_perf_and_(\w+)\.csv")

    # List of tools of interest
    temperatures_valid_tools = {"hwpc", "codecarbon", "scaphandre", "alumet", "vjoule"}

    # Collect all matching CSV files
    temperatures_csv_files = []
    for temperatures_file_path in temperatures_root_dir.rglob("temperatures_frequency_*_perf_and_*.csv"):
        temperatures_match = temperatures_pattern.match(temperatures_file_path.name)
        if temperatures_match:
            temperatures_frequency, temperatures_tested_tool = temperatures_match.groups()
            if temperatures_tested_tool in temperatures_valid_tools:
                temperatures_node = temperatures_file_path.parent.name  
                temperatures_g5k_cluster = temperatures_node.split("-")[0] if "-" in temperatures_node else temperatures_node
                temperatures_csv_files.append((temperatures_file_path, int(temperatures_frequency), temperatures_tested_tool, temperatures_node, temperatures_g5k_cluster))

    # Load all CSVs into a list of DataFrames
    temperatures_overhead_dfs = []
    for temperatures_file_path, temperatures_frequency, temperatures_valid_tool, temperatures_node, temperatures_g5k_cluster in temperatures_csv_files:
        temperatures_df = (
            pl.read_csv(temperatures_file_path)
            .with_columns([
                pl.lit(temperatures_frequency).alias("target_frequency"),
                pl.lit(temperatures_valid_tool).alias("tool"),
                pl.lit(temperatures_node).alias("node"),
                pl.lit(temperatures_g5k_cluster).alias("g5k_cluster"),
            ])
        )
        temperatures_overhead_dfs.append(temperatures_df)

    # Concatenate all into one big Polars DataFrame
    if temperatures_overhead_dfs:
        temperatures_all_data = pl.concat(temperatures_overhead_dfs, how="vertical")
    else:
        temperatures_all_data = pl.DataFrame()

    temperatures_all_data = temperatures_all_data.with_columns([
        ((pl.col("temperature_start") + pl.col("temperature_stop")) / 2).alias("average_temperature").cast(pl.Int64)
    ])
    print(temperatures_all_data.head())
    return (temperatures_all_data,)


@app.cell
def _(
    Path,
    baseline,
    inventory,
    pl,
    re,
    results_directory,
    temperatures_all_data,
):

    # Define the root directory to search
    root_dir = Path(results_directory)  # change this to your directory

    # Define the filename pattern (regex to extract frequency and tool)
    pattern = re.compile(r"frequency_(\d+)_perf_and_(\w+)\.csv")

    # List of tools of interest
    valid_tools = {"hwpc", "codecarbon", "scaphandre", "alumet", "vjoule"}

    # Collect all matching CSV files
    csv_files = []
    for file_path in root_dir.rglob("frequency_*_perf_and_*.csv"):
        match = pattern.match(file_path.name)
        if match:
            frequency, tested_tool = match.groups()
            if tested_tool in valid_tools:
                node = file_path.parent.name  # e.g. "paravance-5"
                g5k_cluster = node.split("-")[0] if "-" in node else node
                csv_files.append((file_path, int(frequency), tested_tool, node, g5k_cluster))

    # Load all CSVs into a list of DataFrames
    overhead_dfs = []
    for file_path, frequency, valid_tool, node, g5k_cluster in csv_files:
        df = (
            pl.read_csv(file_path)
            .with_columns([
                pl.lit(frequency).alias("target_frequency"),
                pl.lit(valid_tool).alias("tool"),
                pl.lit(node).alias("node"),
                pl.lit(g5k_cluster).alias("g5k_cluster"),
            ])
        )
        overhead_dfs.append(df)

    # Concatenate all into one big Polars DataFrame
    if overhead_dfs:
        all_data = pl.concat(overhead_dfs, how="vertical")
    else:
        all_data = pl.DataFrame()

    all_data = all_data.join(
        other=temperatures_all_data,
        left_on=["node", "target_frequency", "tool", "iteration"],
        right_on=["node", "target_frequency", "tool", "iteration"],
        how="left",
        validate="1:1"
    )

    all_data = all_data.with_columns([
        # Compute lower bound of the 5°C bin
        (pl.col("average_temperature") // 5 * 5).alias("temp_lower"),
        # Compute upper bound
        ((pl.col("average_temperature") // 5 * 5) + 4).alias("temp_upper")
    ])

    # Combine into formatted interval strings like "45-50°C"
    all_data = all_data.with_columns([
        (pl.col("temp_lower").cast(pl.Float64).cast(pl.Utf8) + "-" +
         pl.col("temp_upper").cast(pl.Float64).cast(pl.Utf8) + "°C"
        ).alias("temperature_range")
    ])


    stats = (
        all_data
        .group_by(["g5k_cluster", "tool", "target_frequency", "temperature_range"])
        .agg([
            # Package domain
            pl.col("power_energy_pkg").median().alias("median_pkg"),
            pl.col("power_energy_pkg").mean().alias("mean_pkg"),
            pl.col("power_energy_pkg").std().alias("std_pkg"),

            # RAM domain
            pl.col("power_energy_ram").median().alias("median_ram"),
            pl.col("power_energy_ram").mean().alias("mean_ram"),
            pl.col("power_energy_ram").std().alias("std_ram"),

        ])
        .sort(["g5k_cluster", "tool", "target_frequency"])
    )
    stats = stats.with_columns([
        pl.col("g5k_cluster").cast(pl.Utf8),
        pl.col("temperature_range").cast(pl.Utf8),
    ])
    stats = stats.join(
        other=inventory,
        left_on=["g5k_cluster"],
        right_on=["cluster"],
        how="left",
        #validate="1:m"
    )


    stats = stats.with_columns([
        (pl.col("median_pkg") / pl.col("cores_per_node")).alias("median_pkg_per_core"),
        (pl.col("median_ram") / pl.col("cores_per_node")).alias("median_ram_per_core")
    ])

    stats = stats.join(
        other=baseline.with_columns([
        pl.col("g5k_cluster").cast(pl.Utf8),
        pl.col("temperature_range").cast(pl.Utf8),
    ]).sql("SELECT g5k_cluster, pkg_per_core, ram_per_core, pkg_per_core_std, ram_per_core_std, temperature_range FROM self"),
        left_on=["g5k_cluster", "temperature_range"],
        right_on=["g5k_cluster", "temperature_range"],
        how="left",
        #validate="1:m"
    )

    stats = stats.with_columns([
        (pl.col("median_pkg_per_core") - pl.col("pkg_per_core")).alias("pkg_overhead_per_core"),
        (pl.col("median_ram_per_core") - pl.col("ram_per_core")).alias("ram_overhead_per_core"),
    ])

    stats.describe()
    return all_data, stats


@app.cell
def _(pd, stats):
    # Convert from Polars if needed
    overhead_df = stats.to_pandas()

    # Ensure numeric and categorical order
    overhead_df["target_frequency"] = overhead_df["target_frequency"].astype(int)
    overhead_df["tool"] = pd.Categorical(overhead_df["tool"], ordered=True)
    overhead_df = overhead_df.sort_values("tool")
    return (overhead_df,)


@app.cell
def _(overhead_df, palette_for_tools, plt, sns):
    def draw_barplot(data, **kwargs):
        """
        Draw grouped barplot of mean pkg_overhead_per_core per frequency, with error bars per tool.
        """
        sns.barplot(
            data=data,
            x="target_frequency",
            y="pkg_overhead_per_core",
            hue="tool",
            estimator="median",
            palette=palette_for_tools,
            errorbar=("pi", 50), capsize=.2,
            err_kws={"color": ".3", "linewidth": 1.2},
            **kwargs
        )

    # Facet by cluster
    g_bar = sns.FacetGrid(
        overhead_df,
        col="processor_description",
        col_wrap=3,
        margin_titles=True,
        height=3.7,
        aspect=1.5
    )

    plt.suptitle("", fontsize=18)
    g_bar.map_dataframe(draw_barplot)

    # Beautify
    g_bar.set_axis_labels("Frequency (Hz)", "Package domain overhead\nper core with IQR (W)", fontsize=14)
    g_bar.set_titles(col_template="{col_name}", fontsize=12)
    g_bar.add_legend(fontsize=16, ncol=5, bbox_to_anchor=(0.0, -0.3175, 0.5, 0.5))

    for axis in g_bar.axes:
        axis.tick_params(axis="x", labelsize=14)
        axis.tick_params(axis="y", labelsize=14)
        axis.set_title(label=axis.get_title(), fontsize=16)
    plt.savefig("package_overhead.png", bbox_inches="tight", dpi=600)
    plt.show()
    return


@app.cell
def _(overhead_df, palette_for_tools, plt, sns):
    def draw_barplot_ram(data, **kwargs):
        """
        Draw grouped barplot of mean pkg_overhead_per_core per frequency, with error bars per tool.
        """
        sns.barplot(
            data=data,
            x="target_frequency",
            y="ram_overhead_per_core",
            hue="tool",
            estimator="median",
            palette=palette_for_tools,
            errorbar=("pi", 50), capsize=.2,
            err_kws={"color": ".3", "linewidth": 1.2},
            **kwargs
        )

    # Facet by cluster
    g_bar_ram = sns.FacetGrid(
        overhead_df,
        col="processor_description",
        col_wrap=3,
        margin_titles=True,
        height=3.7,
        aspect=1.5
    )

    plt.suptitle("", fontsize=18)
    g_bar_ram.map_dataframe(draw_barplot_ram)

    # Beautify
    g_bar_ram.set_axis_labels("Frequency (Hz)", "RAM domain overhead\nper core with IQR (W)", fontsize=14)
    g_bar_ram.set_titles(col_template="{col_name}", fontsize=12)
    g_bar_ram.add_legend(fontsize=16, ncol=5, bbox_to_anchor=(0.0, -0.3175, 0.5, 0.5))

    for axis_ram in g_bar_ram.axes:
        axis_ram.tick_params(axis="x", labelsize=14)
        axis_ram.tick_params(axis="y", labelsize=14)
        axis_ram.set_title(label=axis_ram.get_title(), fontsize=16)
    plt.savefig("ram_overhead.png", bbox_inches="tight", dpi=600)
    plt.show()
    return


@app.cell
def _(
    alumet_frequency,
    codecarbon_frequency_agg_raw,
    hwpc_frequency,
    math,
    pl,
    scaphandre_frequency,
    vjoule_frequency_agg_raw,
):
    hwpc_frequency_agg = (
                            hwpc_frequency.group_by(["iteration", "node", "frequency"])
                            .agg([
                                pl.sum("cores").alias("cores_raw"),
                                pl.sum("pkg").alias("pkg_raw"),
                                pl.sum("ram").alias("ram_raw"),
                            ])
                            .with_columns([
                                pl.col("cores_raw").map_elements(lambda x: math.ldexp(x, -32), return_dtype=pl.Float64).alias("cores_total"),
                                pl.col("pkg_raw").map_elements(lambda x: math.ldexp(x, -32),return_dtype=pl.Float64).alias("pkg_total"),
                                pl.col("ram_raw").map_elements(lambda x: math.ldexp(x, -32),return_dtype=pl.Float64).alias("ram_total"),

                pl.lit("hwpc").alias("tool")
                            ])
                            .select([
                                "node", "cores_total", "pkg_total", "ram_total","iteration", "frequency", "tool"
                            ]).cast({"pkg_total": pl.Float32, "cores_total": pl.Float32, "ram_total": pl.Float32, "iteration": pl.Int32, "frequency": pl.Int32})
                        )

    alumet_frequency_agg = (
                            alumet_frequency.group_by(["iteration", "node", "frequency"])
                            .agg([
                                pl.sum("cores").alias("cores_total"),
                                pl.sum("pkg").alias("pkg_total"),
                                pl.sum("ram").alias("ram_total"),
                            ])
                            .with_columns([
                                pl.lit("alumet").alias("tool")
                            ])
                            .select([
                                "node", "cores_total", "pkg_total", "ram_total","iteration", "frequency", "tool"
                            ]).cast({"pkg_total": pl.Float32, "cores_total": pl.Float32, "ram_total": pl.Float32, "iteration": pl.Int32, "frequency": pl.Int32})
                        )

    scaphandre_frequency_agg = (
                            scaphandre_frequency.group_by(["iteration", "node", "frequency"])
                            .agg([
                                pl.sum("cores").alias("cores_raw"),
                                pl.sum("pkg").alias("pkg_raw"),
                                pl.sum("ram").alias("ram_raw"),
                            ]).with_columns([
                                (pl.col("cores_raw") / (pl.col("frequency") * 1_000_000)).alias("cores_total"),
                                (pl.col("pkg_raw")/ (pl.col("frequency") * 1_000_000)).alias("pkg_total"),
                                (pl.col("ram_raw")/ (pl.col("frequency") * 1_000_000)).alias("ram_total"),
                                pl.lit("scaphandre").alias("tool")
                            ])
                            .select([
                                "node", "cores_total", "pkg_total", "ram_total","iteration", "frequency", "tool"
                            ]).cast({"pkg_total": pl.Float32, "cores_total": pl.Float32, "ram_total": pl.Float32, "iteration": pl.Int32, "frequency": pl.Int32})
                        )

    vjoule_frequency_agg = vjoule_frequency_agg_raw.with_columns([
                                pl.col("cores").alias("cores_total"),
                                pl.col("pkg").alias("pkg_total"),
                                pl.col("ram").alias("ram_total"),
                                pl.lit("vjoule").alias("tool")
                            ]).select(["node", "cores_total", "pkg_total", "ram_total","iteration", "frequency", "tool"]).cast({"pkg_total": pl.Float32, "cores_total": pl.Float32, "ram_total": pl.Float32, "iteration": pl.Int32, "frequency": pl.Int32})


    codecarbon_frequency_agg = codecarbon_frequency_agg_raw.with_columns([
                                (pl.col("cores") * 1_000_000).alias("cores_total"),
                                (pl.col("pkg") * 1_000_000).alias("pkg_total"),
                                (pl.col("ram") * 1_000_000).alias("ram_total"),
                                pl.lit("codecarbon").alias("tool")
                            ]).select(["node", "cores_total", "pkg_total", "ram_total","iteration", "frequency", "tool"]).cast({"pkg_total": pl.Float32, "cores_total": pl.Float32, "ram_total": pl.Float32, "iteration": pl.Int32, "frequency": pl.Int32})

    frequency_agg = pl.concat([alumet_frequency_agg, hwpc_frequency_agg, scaphandre_frequency_agg, vjoule_frequency_agg, codecarbon_frequency_agg])
    return (
        alumet_frequency_agg,
        codecarbon_frequency_agg,
        frequency_agg,
        hwpc_frequency_agg,
        scaphandre_frequency_agg,
        vjoule_frequency_agg,
    )


@app.cell
def _(
    alumet_frequency_agg,
    codecarbon_frequency_agg,
    frequency_agg,
    hwpc_frequency_agg,
    scaphandre_frequency_agg,
    vjoule_frequency_agg,
):
    print(alumet_frequency_agg.columns)
    print(hwpc_frequency_agg.columns)
    print(scaphandre_frequency_agg.columns)
    print(vjoule_frequency_agg.columns)
    print(codecarbon_frequency_agg.columns)
    print(frequency_agg.columns)
    return


@app.cell
def _(all_data, frequency_agg, pl):
    merged_frequency_measurements_df = frequency_agg.join(
        all_data,
        left_on=["node", "tool", "frequency", "iteration"],
        right_on=["node", "tool", "frequency", "iteration"],
        how="left"
    )

    merged_frequency_measurements_df = merged_frequency_measurements_df.cast({"cores_total": pl.Float32, "power_energy_cores": pl.Float32})
    merged_frequency_measurements_df = merged_frequency_measurements_df.with_columns([
        (((pl.col("power_energy_pkg") - pl.col("pkg_total")).abs()) / pl.col("power_energy_pkg")).alias("pkg_diff"),
        (((pl.col("power_energy_cores") - pl.col("cores_total")).abs()) /pl.col("power_energy_cores")).alias("cores_diff"),
        (((pl.col("power_energy_ram") - pl.col("ram_total")).abs()) /pl.col("power_energy_ram")).alias("ram_diff")])
    return (merged_frequency_measurements_df,)


@app.cell
def _(merged_frequency_measurements_df, palette_for_tools, plt, sns):
    fig_diff, axes = plt.subplots(nrows=2, ncols=1,  sharex=True, figsize=(10,6))
    from matplotlib.patches import Rectangle

    # --- Add rectangle to axes[0] ---
    # Coordinates are in data space by default; you can switch to axes fraction if preferred.

    rect_x_100 = 1.65  # rectangle lower-left x
    rect_y_100 = 0.8# rectangle lower-left y
    rect_width_100 = 0.35
    rect_height_100 = 0.1

    # Add rectangle patch
    rect_100 = Rectangle(
        (rect_x_100, rect_y_100),
        rect_width_100,
        rect_height_100,
        linewidth=0.5,
        edgecolor='black',
        facecolor='white',
        fill=True
    )

    rect_x_1000 = 2.625# rectangle lower-left x
    rect_y_1000 = 0.8# rectangle lower-left y
    rect_width_1000 = 0.35
    rect_height_1000 = 0.1
    rect_1000 = Rectangle(
        (rect_x_1000, rect_y_1000),
        rect_width_1000,
        rect_height_1000,
        linewidth=0.5,
        edgecolor='black',
        facecolor='white',
        fill=True
    )


    sns.barplot(
            data=merged_frequency_measurements_df.sort("tool"),
            x="frequency",
            y="pkg_diff",
            hue="tool",
            palette=palette_for_tools,
            ax=axes[0],
            errorbar=("pi", 50)
        )
    sns.barplot(
            data=merged_frequency_measurements_df.sql("SELECT * FROM self WHERE tool != 'scaphandre'").sort("tool"),
            x="frequency",
            y="ram_diff",
            hue="tool",
            palette=palette_for_tools,
            ax=axes[1]
        )
    fig_diff.suptitle("", fontsize=10)
    for axe_diff in axes:
        axe_diff.tick_params(axis="x", labelsize=14)    
        axe_diff.tick_params(axis="y", labelsize=14)

        axe_diff.set_xlabel("Sampling frequency (Hz)", fontsize=14)
        axe_diff.set_ylim(0, top=1.0)
        axe_diff.set_ylabel("")
    axes[1].get_legend().remove()
    axes[0].legend(title="", fontsize=14, bbox_to_anchor=(.475,-2, .5, .5), frameon=False, ncols=5)
    axes[0].set_ylabel("", fontsize=10)
    #axes[1].set_ylabel("Package domain ratio", fontsize=10)
    axes[1].text(x=-1, y=0.1, s="RAM domain ratio", fontsize=14, rotation="vertical")

    axes[0].text(x=-1, y=0.0, s="Package domain ratio", fontsize=14, rotation="vertical")
    axes[0].add_patch(rect_100)
    axes[0].add_patch(rect_1000)

    # Add text inside the rectangle
    axes[0].text(
        rect_x_100 + rect_width_100/2,
        rect_y_100 + rect_height_100/2,
        "y=1.4",
        ha='center',
        va='center',
        fontsize=12
    )

    axes[0].text(
        rect_x_1000 + rect_width_1000/2,
        rect_y_1000 + rect_height_1000/2,
        "y=1.8E4",
        ha='center',
        va='center',
        fontsize=12
    )


    plt.savefig("frequency_measurements_diff.png", bbox_inches="tight", dpi=600)
    plt.show()
    return


@app.cell
def _(plt):
    fig_ram_freq = plt.figure(figsize=(8,6))

    fig_ram_freq.axes[0].set_ylim(0, top=1.0)
    plt.title("")
    plt.xlabel("Sampling frequency (Hz)")
    plt.ylabel("Relative difference of perf and tools over ram RAPL domain (1.0 = 100%)")
    plt.tight_layout(pad=0.1)
    plt.savefig("frequency_measurements_diff_ram.pdf", bbox_inches="tight")
    plt.show()
    return


@app.cell
def _(mo):
    mo.md(r"""# Stability of measurement tool""")
    return


@app.cell
def _(Path, inventory, math, pl, re, results_directory):
    def load_tool_csvs(base_directory: str):
        """
        Load all TOOL_and_perf_*.csv and perf_and_TOOL_*.csv files recursively
        into per-tool DataFrames with added columns 'node' and 'g5k_cluster'.

        Returns a dict: {tool_name: DataFrame}
        """
        # Define the supported tools
        tools = ["hwpc", "alumet", "codecarbon", "vjoule", "scaphandre"]
        pattern = re.compile(rf"({'|'.join(tools)})_and_perf_\d+_\d+\.csv")

        # Prepare results dict
        dfs = {tool: [] for tool in tools}

        base_path = Path(base_directory)
        print(f"Loading CSVs from: {base_path.resolve()}")

        for file_path in base_path.rglob("*.csv"):
            filename = file_path.name

            # Match the file pattern
            if not pattern.match(filename):
                continue

            # Extract node and cluster
            node = file_path.parent.name
            g5k_cluster = node.split("-")[0] if "-" in node else node

            # Determine tool name
            tool = None
            for t in tools:
                if t in filename:
                    tool = t
                    break
            if tool is None:
                continue
            print("Reading file:", file_path)

            # Choose schema depending on the tool
            try:
                df = pl.read_csv(file_path)

                if tool == "hwpc":
                    try:
                        df = (
                            df.group_by(["iteration"])
                            .agg([
                                pl.sum("rapl_energy_cores").alias("energy_cores_raw"),
                                pl.sum("rapl_energy_pkg").alias("energy_pkg_raw"),
                                pl.sum("rapl_energy_dram").alias("energy_ram_raw"),
                                pl.first("nb_core"),
                                pl.first("nb_ops_per_core"),
                            ])
                            .with_columns([
                                pl.col("energy_cores_raw").map_elements(lambda x: math.ldexp(x, -32), return_dtype=pl.Float64).alias("energy_cores"),
                                pl.col("energy_pkg_raw").map_elements(lambda x: math.ldexp(x, -32),return_dtype=pl.Float64).alias("energy_pkg"),
                                pl.col("energy_ram_raw").map_elements(lambda x: math.ldexp(x, -32),return_dtype=pl.Float64).alias("energy_ram"),
                            ])
                            .select([
                                "energy_cores", "energy_pkg", "energy_ram",
                                "nb_core", "nb_ops_per_core", "iteration"
                            ])
                            .with_columns([
                                pl.lit(node).alias("node"),
                                pl.lit(g5k_cluster).alias("g5k_cluster")
                            ])
                        )

                        dfs[tool].append(df)
                        continue

                    except Exception as e:
                        print(f"❌ Error reading HWPC file {file_path}: {e}")
                else:
                    expected_columns = [
                        "energy_cores", "energy_pkg", "energy_ram",
                        "nb_core", "nb_ops_per_core", "iteration"
                    ]

                # Keep only expected columns (if file has extras)
                df = df.select([col for col in expected_columns if col in df.columns])

                # Add metadata columns
                df = df.with_columns([
                    pl.lit(node).alias("node"),
                    pl.lit(g5k_cluster).alias("g5k_cluster")
                ])
                dfs[tool].append(df)

            except Exception as e:
                print(f"❌ Error reading {file_path}: {e}")


        merged_dfs = {}
        for tool in tools:

            merged_df = pl.DataFrame(schema=[
                    "energy_cores", "energy_pkg", "energy_ram",
                    "nb_core", "nb_ops_per_core", "iteration", "node", "g5k_cluster"
                ])
            for df in dfs[tool]:
                try:
                    merged_df = pl.concat([merged_df, df], how="vertical_relaxed")
                except Exception as e:
                    print("Failed for:", df.describe(), "because:", e, "with tool", tool)
            try:
                merged_df = merged_df.join(
                    other=inventory,
                    left_on=["g5k_cluster"],
                    right_on=["cluster"],
                    how="left",
                    #validate="1:m"
                )
            except Exception as e:
                print(f"❌ Error merging {tool}: {e}")            
            merged_dfs[tool] = merged_df
        return merged_dfs

    dfs = load_tool_csvs(results_directory)
    return (dfs,)


@app.cell
def _(dfs, np, pl, plt, selected_clusters, sns):
    def compute_cv_per_tool(tool_dfs, filler=np.nan):
        """
        Compute coefficient of variation (std/mean) across iterations for each tool, node, and cluster.
        If a field is missing or has only nulls, fill with a filler value.
        """
        all_domains = ["energy_cores", "energy_pkg", "energy_ram"]
        results = []

        for tool_name, df in tool_dfs.items():
            df = df.lazy()
            available_cols = set(df.columns)

            # Identify grouping columns dynamically (some datasets may not have g5k_cluster)
            group_cols = ["node"]
            if "g5k_cluster" in available_cols:
                group_cols.append("g5k_cluster")

            for field in all_domains:
                if field in available_cols:
                    # Check if at least one non-null value exists
                    has_data = df.select(pl.col(field).drop_nulls().count()).collect().item() > 0
                else:
                    has_data = False

                if has_data:
                    # Compute CV across iterations for each node (+ cluster if present)
                    cv_df = (
                        df.group_by(group_cols)
                        .agg([
                            (pl.std(field) / pl.mean(field)).alias("cv")
                        ])
                        .with_columns([
                            pl.lit(tool_name).alias("tool"),
                            pl.lit(field).alias("domain")
                        ])
                        .collect()
                    )

                else:
                    # Fill with the filler value for each node/cluster
                    nodes = df.select(group_cols).unique().collect()
                    cv_df = nodes.with_columns([
                        pl.lit(filler).alias("cv"),
                        pl.lit(tool_name).alias("tool"),
                        pl.lit(field).alias("domain")
                    ])

                results.append(cv_df)

        all_cv = pl.concat(results)
        return all_cv.to_pandas()



    # --- Compute CVs ---
    cv_df = compute_cv_per_tool(dfs)

    # Clean up domain names for display
    cv_df["domain"] = cv_df["domain"].str.replace("energy_", "").str.capitalize()



    colors_domain= {
        "Cores": "#4878CF",        
        "Ram": "#6ACC65",  
        "Pkg": "#D65F5F",  
    }

    def fancy_boxplot(data, color=None, **kwargs):
        _ = sns.boxplot(
            data=data.sort_values("tool"),
            x="tool",
            y="cv",
            palette=colors_domain, 
            showmeans=False,
            showfliers=False,
            hue="domain",
        )

    # Assume cv_df also has a column 'g5k_cluster'
    domains = cv_df["domain"].unique()

    # --- pick 6 clusters ---
    cv_df_filtered = cv_df[cv_df["g5k_cluster"].isin(selected_clusters)]

    #for domain in domains:
    #    df_sub = cv_df_filtered[cv_df_filtered["domain"] == domain]
    g_cv = sns.FacetGrid(
        cv_df_filtered,
        col="g5k_cluster",
        col_wrap=5,
        sharey=True,
        sharex=True
    )

    g_cv.map_dataframe(fancy_boxplot)
    for ax_cv in g_cv.axes.flat:
        ax_cv.set_facecolor("#F8FAFC")
        ax_cv.grid(True, color="#E2E8F0")
        ax_cv.set_xlabel("Tools", fontsize=12)
        ax_cv.set_ylabel("Coefficient of Variation", fontsize=12)

    # Title per domain
    g_cv.fig.suptitle(
        f"",
        fontsize=12,
        fontweight="bold",
        color="#1E293B",
        x=0.425,
        y=1.1
    )

    # Beautify
    g_cv.set_axis_labels("Tools", "Coefficient of Variation", fontsize=12)
    g_cv.set_titles(col_template="{col_name}", fontsize=12)
    for axis_stability in g_cv.axes:
        axis_stability.tick_params(axis="x", labelsize=12, labelrotation=45)
        axis_stability.tick_params(axis="y", labelsize=12)
        axis_stability.set_title(label=axis_stability.get_title(), fontsize=12)
        if axis_stability.get_legend():
            axis_stability.get_legend().remove()
    g_cv.add_legend(fontsize=12, ncols=3,  bbox_to_anchor=(0.02, -0.3875, 0.5, 0.5))

    sns.despine(left=True, bottom=True)
    #plt.subplots_adjust(top=0.88, hspace=0.25)


    # Save figure for that domain
    g_cv.savefig(f"cv_per_tool_per_cluster.pdf")
    g_cv.savefig(f"cv_per_tool_per_cluster.png", bbox_inches="tight", dpi=600)
    plt.show()
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
