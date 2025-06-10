# IMPORTS
import os
import argparse
import sys
import polars as pl
import schemas
import load
import rq1
import rq2
import rq3
import rq34
import visualization
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import polars as pl
import re

palette_for_tools = {
        "hwpc": "#ef5552",
        "codecarbon": "#c9fb36",
        "alumet": "#00cdfe",
        "scaphandre": "#fcaf3f",
        "vjoule": "#9f2281",
    }

vendor_generation_map = {
    "E5-2620 v4": {
        "architecture": "Broadwell-E",
        "vendor": "Intel",
        "generation": 6,
        "launch_date": "Q1 2016",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus" : [0, 1]
    },
    "E5-2630L v4": {
        "architecture": "Broadwell-E",
        "vendor": "Intel",
        "generation": 6,
        "launch_date": "Q1 2016",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus" : [0, 1]
    },
    "E5-2698 v4": {
        "architecture": "Broadwell-E",
        "vendor": "Intel",
        "generation": 6,
        "launch_date": "Q1 2016",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus" : [0, 1]
    },
    "E5-2630 v3": {
        "architecture": "Haswell-E",
        "vendor": "Intel",
        "generation": 5,
        "launch_date": "Q3 2014",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus" : [0, 1]
    },
    "Gold 5220": {
        "architecture": "Cascade Lake-SP",
        "vendor": "Intel",
        "generation": 10,
        "launch_date": "Q2 2019",
        "numa_nodes_number": "1",
        "numa_nodes_first_cpus" : [0]
    },
    "Gold 5218": {
        "architecture": "Cascade Lake-SP",
        "vendor": "Intel",
        "generation": 10,
        "launch_date": "Q2 2019",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus" : [0, 1]
    },
    "i7-9750H": {
        "architecture": "Coffee Lake",
        "vendor": "Intel",
        "generation": 9,
        "launch_date": "Q2 2019",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus" : [0, 1]
    },
    "Silver 4314": {
        "architecture": "Ice Lake-SP",
        "vendor": "Intel",
        "generation": 10,
        "launch_date": "Q2 2021",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus" : [0, 1]
    },
    "Gold 5320": {
        "architecture": "Ice Lake-SP",
        "vendor": "Intel",
        "generation": 10,
        "launch_date": "Q2 2021",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus" : [0, 1]
    },
    "Gold 6126": {
        "architecture": "Skylake-SP",
        "vendor": "Intel",
        "generation": 6,
        "launch_date": "Q3 2017",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus" : [0, 1]
    },
    "Gold 6130": {
        "architecture": "Skylake-SP",
        "vendor": "Intel",
        "generation": 6,
        "launch_date": "Q3 2017",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus" : [0, 1]
    },
    "E5-2620": {
        "architecture": "Sandy Bridge-EP",
        "vendor": "Intel",
        "generation": 3,
        "launch_date": "Q1 2012",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus" : [0, 1]
    },
    "E5-2630": {
        "architecture": "Sandy Bridge-EP",
        "vendor": "Intel",
        "generation": 3,
        "launch_date": "Q1 2012",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus" : [0, 1]
    },
    "E5-2630L": {
        "architecture": "Sandy Bridge-EP",
        "vendor": "Intel",
        "generation": 3,
        "launch_date": "Q1 2012",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus" : [0, 1]
    },
    "E5-2660": {
        "architecture": "Sandy Bridge-EP",
        "vendor": "Intel",
        "generation": 3,
        "launch_date": "Q1 2012",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus" : [0, 1]
    },
    "X5670": {
        "architecture": "Westmere-EP",
        "vendor": "Intel",
        "generation": 1,
        "launch_date": "Q1 2010",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus" : [0, 1]
    },
    "7301": {
        "architecture": "Zen",
        "vendor": "AMD",
        "generation": 1,
        "launch_date": "Q2 2017",
        "numa_nodes_number": "8",
        "numa_nodes_first_cpus" : [0, 1, 2, 3, 4, 5, 6, 7]
    },
    "7352": {
        "architecture": "Zen 2",
        "vendor": "AMD",
        "generation": 2,
        "launch_date": "Q3 2019",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus" : [0, 1]
    },
    "7452": {
        "architecture": "Zen 2",
        "vendor": "AMD",
        "generation": 2,
        "launch_date": "Q3 2019",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus" : [0, 1]
    },
    "7642": {
        "architecture": "Zen 2",
        "vendor": "AMD",
        "generation": 2,
        "launch_date": "Q3 2019",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus" : [0, 1]
    },
    "7742": {
        "architecture": "Zen 2",
        "vendor": "AMD",
        "generation": 2,
        "launch_date": "Q3 2019",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus" : [0, 1]
    },
    "250": {
        "architecture": "Opteron",
        "vendor": "AMD",
        "generation": 1,
        "launch_date": "Q4 2004",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus" : [0, 1]
    },
    "99xx": {
        "architecture": "ThunderX2",
        "vendor": "Cavium",
        "generation": 1,
        "launch_date": "Q2 2016",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus" : [0, 1]
    },
}


def main(batch_identifier="ubuntu2404nfs-6.8-3"):
    results_directory: str = f"../data/{batch_identifier}.d/results-{batch_identifier}.d/"
    inventories_directory: str = f"../data/{batch_identifier}.d/inventories-{batch_identifier}.d/"
    results_directory_match=rf"{results_directory}([^/]+)/([^/]+)/([^/]+)/(.+)_([0-9]+)_([0-9]+).*"

    current_energy_df, current_energy_stats_df= energy_for_os(
            batch_identifier=batch_identifier,
            inventories_directory=inventories_directory,
            results_directory=results_directory,
            results_directory_match=results_directory_match,
            )

    ###
    ###
    pivot_table_for_adastop(dataframe=current_energy_df)
    ###
    ###

    # Looking for differences between PERF and other tools measurements
    # When available, comparison of PGK to PKG
    rq1.heatmap_tools_cv(dataframe=current_energy_stats_df)
    rq1.ratio_tool_perf(dataframe=current_energy_df, other_tool="hwpc", other_tool_domain="energy_pkg", perf_domain="energy_pkg")
    rq1.ratio_tool_perf(dataframe=current_energy_df, other_tool="hwpc", other_tool_domain="energy_ram", perf_domain="energy_ram")
    rq1.ratio_tool_perf(dataframe=current_energy_df, other_tool="codecarbon", other_tool_domain="energy_cores", perf_domain="energy_pkg")
    rq1.ratio_tool_perf(dataframe=current_energy_df, other_tool="codecarbon", other_tool_domain="energy_ram", perf_domain="energy_ram")
    rq1.ratio_tool_perf(dataframe=current_energy_df, other_tool="alumet", other_tool_domain="energy_pkg", perf_domain="energy_pkg")
    rq1.ratio_tool_perf(dataframe=current_energy_df, other_tool="alumet", other_tool_domain="energy_ram", perf_domain="energy_ram")
    rq1.ratio_tool_perf(dataframe=current_energy_df, other_tool="scaphandre", other_tool_domain="energy_pkg", perf_domain="energy_pkg")
    rq1.ratio_tool_perf(dataframe=current_energy_df, other_tool="vjoule", other_tool_domain="energy_cores", perf_domain="energy_pkg")
    rq1.ratio_tool_perf(dataframe=current_energy_df, other_tool="vjoule", other_tool_domain="energy_ram", perf_domain="energy_ram")

    rq1.plot_correlation_tools_cv(df=current_energy_df)
    

    


    debian11_energy_stats_df = energy_for_os(
        "debian11-5.10-0",
        r"data/debian11-5\.10-0\.d/results-debian11-5\.10-0\.d/([^/]+)/([^/]+)/([^/]+)/[^_]*_([^_]+).*",
    )
    ubuntu2404_energy_stats_df = energy_for_os(
        "ubuntu2404nfs-6.8-0",
        r"data/ubuntu2404nfs-6\.8-0\.d/results-ubuntu2404nfs-6\.8-0\.d/([^/]+)/([^/]+)/([^/]+)/[^_]*_([^_]+).*",
    )

    powerapi_energy_stats_df = energy_for_os(
        "powerapi",
        r"data/powerapi\.d/results-powerapi\.d/([^/]+)/([^/]+)/([^/]+)/[^_]*_([^_]+).*",
    )

def pivot_table_for_adastop(dataframe):
    dataframe_pandas = dataframe.sql("SELECT * FROM self WHERE node LIKE 'gros-1'").to_pandas()
    print("Filtered :", dataframe_pandas.head())
    pivot_pkg = dataframe_pandas.pivot_table(columns="task", index=["node", "iteration"], values="energy_pkg")
    pivot_pkg = pivot_pkg.drop(["codecarbon_and_perf", "vjoule_and_perf"], axis='columns')
    print("Pivot table for PKG domain :", pivot_pkg)
    pivot_cores = dataframe_pandas.pivot_table(columns="task", index=["node", "iteration"], values="energy_cores")
    pivot_cores = pivot_cores.drop(["perf_and_hwpc", "perf_and_codecarbon", "perf_and_alumet", "perf_and_scaphandre", "perf_and_vjoule", "hwpc_and_perf", "alumet_and_perf", "scaphandre_and_perf"], axis='columns')
    print("Pivot table for Cores domain :", pivot_cores)
    pivot_pkg.insert(loc=1, column="codecarbon_and_perf", value=pivot_cores["codecarbon_and_perf"])
    pivot_pkg.insert(loc=9, column="vjoule_and_perf", value=pivot_cores["vjoule_and_perf"])
    pivot_pkg = pivot_pkg.dropna(axis='index', how="any", inplace=False)
    pivot_pkg = pivot_pkg.reset_index(level=None, drop=True)
    pivot_pkg.to_csv(path_or_buf="test_csv_domains.csv") 
    print("Pivot table for domains :", pivot_pkg)
    return pivot_pkg


def energy_for_os(batch_identifier, inventories_directory, results_directory, results_directory_match):
    energy_csv_file = f"../data/{batch_identifier}.d/{batch_identifier}_energy.csv"
    energy_stats_csv_file = f"../data/{batch_identifier}.d/{batch_identifier}_energy_stats.csv"
    if os.path.exists(energy_stats_csv_file) and os.path.exists(energy_csv_file):
        print("Returning content from :", energy_csv_file, "and", energy_stats_csv_file)
        return (pl.read_csv(energy_csv_file), pl.read_csv(energy_stats_csv_file))

    (hwpc_files, perf_files, codecarbon_files, alumet_files, scaphandre_files, vjoule_files) = load.extract_csv_files(results_directory)

    nodes_df = load.extract_inventory_json_files(
        directory=inventories_directory, schema=schemas.nodes_configuration_columns
    )

    nodes_df = nodes_df.with_columns(
        [
            # (pl.col("processor_version").map_elements(lambda x: f"{x}\nGen: {vendor_generation_map[x]['architecture']}\nRelease: {vendor_generation_map[x]['launch_date']}", return_dtype=pl.String).alias("processor_detail")),
            (
                pl.col("processor_version")
                .map_elements(
                    lambda x: f"{x}\n{vendor_generation_map[x]['architecture']}",
                    return_dtype=pl.String,
                )
                .alias("processor_detail")
            ),
            (
                pl.col("processor_version")
                .map_elements(
                    lambda x: f"{vendor_generation_map[x]['generation']}",
                    return_dtype=pl.String,
                )
                .alias("processor_generation")
            ),
            (
                pl.col("processor_version")
                .map_elements(
                    lambda x: f"{vendor_generation_map[x]['vendor']}", return_dtype=pl.String
                )
                .alias("processor_vendor")
            ),
            (
                pl.col("processor_version")
                .map_elements(
                    lambda x: vendor_generation_map[x]['numa_nodes_first_cpus'], return_dtype=pl.List(pl.Int64)
                )
                .alias("numa_nodes_first_cpus")
            ),
        ]
    )
    print("nodes numas", nodes_df.sql("SELECT uid, processor_version, numa_nodes_first_cpus FROM self").head(10))

    print("Nodes Configuration glimpse:\n", nodes_df.head())

    # Data Exploration
    (hwpc_results, perf_results, codecarbon_results, alumet_results, scaphandre_results, vjoule_results) = load.load_results(
        hwpc_files, perf_files, codecarbon_files, alumet_files, scaphandre_files, vjoule_files, results_directory_match, nodes_df
    )
    print(
        "HWPC Results glimpse:\n",
        hwpc_results.sql("SELECT iteration, node, energy_pkg, energy_ram, energy_cores FROM self").head(10),
        hwpc_results.describe(),
    )
    print(
        "Perf Results glimpse:\n",
        perf_results.head(),
        perf_results.describe(),
    )

    print(
        "codecarbon Results glimpse:\n",
        codecarbon_results.head(),
        codecarbon_results.describe(),
    )

    print(
        "alumet Results glimpse:\n",
        alumet_results.head(),
        alumet_results.describe(),
    )
    print(
        "scaphandre Results glimpse:\n",
        scaphandre_results.head(),
        scaphandre_results.describe(),
    )
    print(
        "vjoule Results glimpse:\n",
        vjoule_results.head(),
        vjoule_results.describe(),
    )
    energy_df, energy_stats_df = load.load_energy(hwpc_results, perf_results, codecarbon_results, alumet_results, scaphandre_results, vjoule_results)

    energy_df.write_csv(energy_csv_file, separator=",")
    energy_stats_df.write_csv(energy_stats_csv_file, separator=",")

    return energy_df, energy_stats_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Args for analysis")
    parser.add_argument('--batch_identifier', action="store", help="Batch identifier, format is {environment_distribution}-{environment_kernel_version}-{id} e.g ubuntu2404nfs-6.8-3", default="ubuntu2404nfs-6.8-3")
    args = parser.parse_args()

    main(batch_identifier=args.batch_identifier)
