# IMPORTS
import os
import sys
import polars as pl
import schemas
import extract
import load
import rq34


vendor_generation_map = {
    "E5-2620 v4": {
        "architecture": "Broadwell-E",
        "vendor": "Intel",
        "generation": 6,
        "launch_date": "Q1 2016",
    },
    "E5-2630L v4": {
        "architecture": "Broadwell-E",
        "vendor": "Intel",
        "generation": 6,
        "launch_date": "Q1 2016",
    },
    "E5-2698 v4": {
        "architecture": "Broadwell-E",
        "vendor": "Intel",
        "generation": 6,
        "launch_date": "Q1 2016",
    },
    "E5-2630 v3": {
        "architecture": "Haswell-E",
        "vendor": "Intel",
        "generation": 5,
        "launch_date": "Q3 2014",
    },
    "Gold 5220": {
        "architecture": "Cascade Lake-SP",
        "vendor": "Intel",
        "generation": 10,
        "launch_date": "Q2 2019",
    },
    "Gold 5218": {
        "architecture": "Cascade Lake-SP",
        "vendor": "Intel",
        "generation": 10,
        "launch_date": "Q2 2019",
    },
    "i7-9750H": {
        "architecture": "Coffee Lake",
        "vendor": "Intel",
        "generation": 9,
        "launch_date": "Q2 2019",
    },
    "Silver 4314": {
        "architecture": "Ice Lake-SP",
        "vendor": "Intel",
        "generation": 10,
        "launch_date": "Q2 2021",
    },
    "Gold 5320": {
        "architecture": "Ice Lake-SP",
        "vendor": "Intel",
        "generation": 10,
        "launch_date": "Q2 2021",
    },
    "Gold 6126": {
        "architecture": "Skylake-SP",
        "vendor": "Intel",
        "generation": 6,
        "launch_date": "Q3 2017",
    },
    "Gold 6130": {
        "architecture": "Skylake-SP",
        "vendor": "Intel",
        "generation": 6,
        "launch_date": "Q3 2017",
    },
    "E5-2620": {
        "architecture": "Sandy Bridge-EP",
        "vendor": "Intel",
        "generation": 3,
        "launch_date": "Q1 2012",
    },
    "E5-2630": {
        "architecture": "Sandy Bridge-EP",
        "vendor": "Intel",
        "generation": 3,
        "launch_date": "Q1 2012",
    },
    "E5-2630L": {
        "architecture": "Sandy Bridge-EP",
        "vendor": "Intel",
        "generation": 3,
        "launch_date": "Q1 2012",
    },
    "E5-2660": {
        "architecture": "Sandy Bridge-EP",
        "vendor": "Intel",
        "generation": 3,
        "launch_date": "Q1 2012",
    },
    "7301": {
        "architecture": "Zen",
        "vendor": "AMD",
        "generation": 1,
        "launch_date": "Q2 2017",
    },
    "7352": {
        "architecture": "Zen 2",
        "vendor": "AMD",
        "generation": 2,
        "launch_date": "Q3 2019",
    },
    "7452": {
        "architecture": "Zen 2",
        "vendor": "AMD",
        "generation": 2,
        "launch_date": "Q3 2019",
    },
    "7642": {
        "architecture": "Zen 2",
        "vendor": "AMD",
        "generation": 2,
        "launch_date": "Q3 2019",
    },
    "7742": {
        "architecture": "Zen 2",
        "vendor": "AMD",
        "generation": 2,
        "launch_date": "Q3 2019",
    },
}


def main():

    test = sys.argv[1]
    if test == "test":
        test = True
    else:
        test = False

    debian11_energy_stats_df = energy_for_os(
        "debian11-5.10-0",
        r"batches/debian11-5\.10-0\.d/results-debian11-5\.10-0\.d/([^/]+)/([^/]+)/([^/]+)/[^_]*_([^_]+).*",
        test,
    )
    ubuntu2404_energy_stats_df = energy_for_os(
        "ubuntu2404nfs-6.8-0",
        r"batches/ubuntu2404nfs-6\.8-0\.d/results-ubuntu2404nfs-6\.8-0\.d/([^/]+)/([^/]+)/([^/]+)/[^_]*_([^_]+).*",
        test,
    )

    powerapi_energy_stats_df = energy_for_os(
        "powerapi",
        r"batches/powerapi/results/([^/]+)/([^/]+)/([^/]+)/[^_]*_([^_]+).*",
        test,
    )

    concatenated_dfs = pl.concat([debian11_energy_stats_df, ubuntu2404_energy_stats_df])
    concatenated_dfs = concatenated_dfs.sql(
        "SELECT * FROM self WHERE nb_ops_per_core > 25"
    )

    joined_df = ubuntu2404_energy_stats_df.join(
        debian11_energy_stats_df,
        on=["node", "nb_ops_per_core", "nb_core", "job"],
        suffix="_debian",
    )

    # Get rid of 25 OPS as it may be unrelevant
    joined_df = joined_df.sql("SELECT * FROM self WHERE nb_ops_per_core > 25")


    # RQ3/4
    rq34.os_comparison_boxplots_processor_versions_pkg_all(
        [debian11_energy_stats_df, ubuntu2404_energy_stats_df]
    )
    rq34.os_comparison_boxplots_processor_versions_ram_all(
        [debian11_energy_stats_df, ubuntu2404_energy_stats_df]
    )
    rq34.os_comparison_heatmap_processor_versions_pkg_nb_ops(joined_df)
    rq34.os_comparison_heatmap_processor_versions_ram_nb_ops(joined_df)
    rq34.os_comparison_heatmap_processor_versions_pkg_percent_used(joined_df)
    rq34.os_comparison_heatmap_processor_versions_ram_percent_used(joined_df)

    rq34.debian_facetgrid_processor_versions_pkg_cv_nb_ops(debian11_energy_stats_df.sql("SELECT * FROM self WHERE nb_ops_per_core > 25"))
    rq34.debian_facetgrid_processor_versions_ram_cv_nb_ops(debian11_energy_stats_df.sql("SELECT * FROM self WHERE nb_ops_per_core > 25"))
    rq34.ubuntu_facetgrid_processor_versions_pkg_cv_nb_ops(ubuntu2404_energy_stats_df.sql("SELECT * FROM self WHERE nb_ops_per_core > 25"))
    rq34.ubuntu_facetgrid_processor_versions_ram_cv_nb_ops(ubuntu2404_energy_stats_df.sql("SELECT * FROM self WHERE nb_ops_per_core > 25"))


def energy_for_os(os_flavor, results_directory_match, test):
    if test:
        energy_stats_csv_file = (
            f"batches/{os_flavor}.d/{os_flavor}_energy_stats_sample.csv"
        )
    else:
        energy_stats_csv_file = f"batches/{os_flavor}.d/{os_flavor}_energy_stats.csv"
    if os.path.exists(energy_stats_csv_file):
        return pl.read_csv(energy_stats_csv_file)
    results_directory: str = f"batches/{os_flavor}.d/results-{os_flavor}.d/"
    inventories_directory: str = f"batches/{os_flavor}.d/inventories-{os_flavor}.d/"
    (hwpc_files, perf_files) = extract.extract_csv_files(results_directory)

    nodes_df = extract.extract_json_files(
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
                    lambda x: vendor_generation_map[x]["generation"],
                    return_dtype=pl.String,
                )
                .alias("processor_generation")
            ),
            (
                pl.col("processor_version")
                .map_elements(
                    lambda x: vendor_generation_map[x]["vendor"], return_dtype=pl.String
                )
                .alias("processor_vendor")
            ),
        ]
    )

    print("Nodes Configuration glimpse:\n", nodes_df.head())

    # Data Exploration
    (hwpc_results, perf_results) = load.load_results(
        hwpc_files, perf_files, results_directory_match, test
    )
    print(
        "HWPC Results glimpse:\n",
        hwpc_results.head(),
        "\nHWPC Results stats:\n",
        hwpc_results.describe(),
    )
    print(hwpc_results.sql("select energy_pkg from self").describe())
    print(
        "Perf Results glimpse:\n",
        perf_results.head(),
        "\nPerf Results stats:\n",
        perf_results.describe(),
    )

    energy_stats_df = load.load_energy(hwpc_results, perf_results, nodes_df, os_flavor)
    energy_stats_df.write_csv(energy_stats_csv_file, separator=",")

    return energy_stats_df


if __name__ == "__main__":
    main()
