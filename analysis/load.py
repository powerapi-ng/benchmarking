import schemas
from typing import *
import polars as pl
from tqdm import tqdm
from math import ldexp
import numpy as np
import os
import json
import csv
import re
from typing import Tuple, List
import utils
from datetime import datetime
import polars.selectors as cs

TOOLS = ["hwpc", "codecarbon", "alumet", "scaphandre", "vjoule"]


# Extract CSV to Polars DataFrames
# Extract HWPC, Perf, Codecarbon, alumet, vjoule and scaphandre files


def extract_csv_files(directory: str) -> Tuple[List[str], List[str]]:
    """
    TODO
    """
    hwpc_files = []
    perf_files = []
    codecarbon_files = []
    alumet_files = []
    vjoule_files = []
    scaphandre_files = []
    for site in os.scandir(directory):
        for g5k_g5k_cluster in os.scandir(site.path):
            for node in os.scandir(g5k_g5k_cluster.path):
                if node.is_dir():
                    for filename in os.scandir(node.path):
                        if filename.path.endswith(".csv"):
                            if filename.name.startswith("hwpc"):
                                hwpc_files.append(filename.path)
                            elif filename.name.startswith("perf"):
                                perf_files.append(filename.path)
                            elif filename.name.startswith("codecarbon"):
                                codecarbon_files.append(filename.path)
                            elif filename.name.startswith("alumet"):
                                alumet_files.append(filename.path)
                            elif filename.name.startswith("vjoule"):
                                vjoule_files.append(filename.path)
                            elif filename.name.startswith("scaphandre"):
                                scaphandre_files.append(filename.path)
    return (
        hwpc_files,
        perf_files,
        codecarbon_files,
        alumet_files,
        scaphandre_files,
        vjoule_files,
    )


# Parse HWPC files, PKG, Cores or RAM can be missing, if so, we put a 0.0 value
# Conversions are done later because measures as fixed point arithmetic (32.32) (needs to be ldexp(x, -32)ed)


def read_hwpc_csv(file_path: str, results_directory_match: str):
    """ """
    # Paths follow the following format :
    # <RESULTS_DIR_PATH>/<G5K_SITE>/<G5K_CLUSTER>/<G5K_NODE>/<TASK>_<NB_CORES>_<NB_OPS_PER_CORE>.csv
    (site, g5k_g5k_cluster, node, task, nb_cores, nb_ops_per_core) = re.match(
        results_directory_match, file_path
    ).groups()
    parsed_and_converted_rows = []
    with open(file_path, "r") as csv_file:
        reader = csv.DictReader(csv_file)
        for raw_row in reader:
            parsed_row = (
                int(raw_row["timestamp"]),
                raw_row["sensor"],
                raw_row["target"],
                int(raw_row["socket"]),
                int(raw_row["cpu"]),
                int(raw_row["rapl_energy_pkg"]) if raw_row["rapl_energy_pkg"] else 0,
                int(raw_row["rapl_energy_dram"]) if raw_row["rapl_energy_dram"] else 0,
                int(raw_row["rapl_energy_cores"])
                if raw_row["rapl_energy_cores"]
                else 0,
                int(raw_row["time_enabled"]),
                int(raw_row["time_running"]),
                int(raw_row["nb_core"]),
                int(raw_row["nb_ops_per_core"]),
                int(raw_row["iteration"]),
                task,
                site,
                g5k_g5k_cluster,
                node,
            )
            parsed_and_converted_rows.append(parsed_row)
    return parsed_and_converted_rows


def load_hwpc_results(hwpc_df):
    """ """
    # HWPC, by default, produces reports with 1 row for each combination of (socket, cpu)
    # Considering some system counters (such are RAPL PKG) are shared for all cpu of a given socket
    # We do have to filter out redundant values to prevent counting something twice.
    # We chose to keep only the first
    hwpc_df = hwpc_df.filter(pl.col("cpu").is_in("numa_nodes_first_cpus"))
    print(
        "HWPC rows :",
        hwpc_df.sql(
            "SELECT node, cpu, numa_nodes_first_cpus, rapl_energy_pkg, rapl_energy_cores, rapl_energy_dram FROM self"
        ).head(),
    )
    hwpc_results = hwpc_df.sql("""
        SELECT
            SUM(rapl_energy_cores) AS energy_cores_int,
            SUM(rapl_energy_pkg) AS energy_pkg_int,
            SUM(rapl_energy_dram) AS energy_ram_int,
            nb_core,
            nb_ops_per_core,
            iteration,
            task,
            site,
            g5k_g5k_cluster,
            node,
            exotic,
            architecture_nb_cores,
            architecture_nb_threads,
            processor_vendor,
            processor_clock_speed,
            processor_instruction_set,
            processor_ht_capable,
            processor_microarchitecture,
            processor_microcode,
            processor_model,
            processor_version,
            os_cstate_driver,
            os_cstate_governor,
            os_pstate_driver,
            os_pstate_governor,
            os_turboboost_enabled,
            processor_detail,
            processor_generation,
        FROM self
        GROUP BY
            nb_core,
            nb_ops_per_core,
            iteration,
            task,
            site,
            g5k_g5k_cluster,
            node,
            exotic,
            architecture_nb_cores,
            architecture_nb_threads,
            processor_vendor,
            processor_clock_speed,
            processor_instruction_set,
            processor_ht_capable,
            processor_microarchitecture,
            processor_microcode,
            processor_model,
            processor_version,
            os_cstate_driver,
            os_cstate_governor,
            os_pstate_driver,
            os_pstate_governor,
            os_turboboost_enabled,
            processor_detail,
            processor_generation,
    """)

    hwpc_results = hwpc_results.with_columns(
        pl.col("energy_pkg_int")
        .map_elements(lambda x: ldexp(x, -32), return_dtype=pl.Float64)
        .alias("energy_pkg"),
    )

    hwpc_results = hwpc_results.with_columns(
        pl.col("energy_cores_int")
        .map_elements(lambda x: ldexp(x, -32), return_dtype=pl.Float64)
        .alias("energy_cores"),
    )

    hwpc_results = hwpc_results.with_columns(
        pl.col("energy_ram_int")
        .map_elements(lambda x: ldexp(x, -32), return_dtype=pl.Float64)
        .alias("energy_ram"),
    )

    hwpc_results = hwpc_results.drop(
        ["energy_pkg_int", "energy_cores_int", "energy_ram_int"]
    )
    return hwpc_results.sql("""
                     SELECT 
                        energy_cores,
                        energy_pkg,
                        energy_ram,
                        nb_core,
                        nb_ops_per_core,
                        iteration,
                        task,
                        site,
                        g5k_g5k_cluster,
                        node,
                        exotic,
                        architecture_nb_cores,
                        architecture_nb_threads,
                        processor_vendor,
                        processor_clock_speed,
                        processor_instruction_set,
                        processor_ht_capable,
                        processor_microarchitecture,
                        processor_microcode,
                        processor_model,
                        processor_version,
                        os_cstate_driver,
                        os_cstate_governor,
                        os_pstate_driver,
                        os_pstate_governor,
                        os_turboboost_enabled,
                        processor_detail,
                        processor_generation,
                    FROM self
                     """)


# Parse Perf files, again PKG, Cores or RAM can be missing,
def read_perf_csv(file_path: str, results_directory_match: str):
    # Paths follow the following format :
    # <RESULTS_DIR_PATH>/<G5K_SITE>/<G5K_CLUSTER>/<G5K_NODE>/<TASK>_<NB_CORES>_<NB_OPS_PER_CORE>.csv
    (site, g5k_g5k_cluster, node, task, nb_cores, nb_ops_per_core) = re.match(
        results_directory_match, file_path
    ).groups()
    parsed_and_converted_rows = []
    with open(file_path, "r") as csv_file:
        reader = csv.DictReader(csv_file)
        for raw_row in reader:
            parsed_row = (
                float(raw_row["power_energy_pkg"])
                if raw_row["power_energy_pkg"]
                else 0.0,
                float(raw_row["power_energy_ram"])
                if raw_row["power_energy_ram"]
                else 0.0,
                float(raw_row["power_energy_cores"])
                if raw_row["power_energy_cores"]
                else 0.0,
                int(raw_row["nb_core"]),
                int(raw_row["nb_ops_per_core"]),
                int(raw_row["iteration"]),
                task,
                site,
                g5k_g5k_cluster,
                node,
            )
            print("\tparsed_row :", parsed_row)
            parsed_and_converted_rows.append(parsed_row)
    return parsed_and_converted_rows


def load_perf_results(perf_df):
    return perf_df.sql("""
                     SELECT 
                        energy_cores,
                        energy_pkg,
                        energy_ram,
                        nb_core,
                        nb_ops_per_core,
                        iteration,
                        task,
                        site,
                        g5k_g5k_cluster,
                        node,
                        exotic,
                        architecture_nb_cores,
                        architecture_nb_threads,
                        processor_vendor,
                        processor_clock_speed,
                        processor_instruction_set,
                        processor_ht_capable,
                        processor_microarchitecture,
                        processor_microcode,
                        processor_model,
                        processor_version,
                        os_cstate_driver,
                        os_cstate_governor,
                        os_pstate_driver,
                        os_pstate_governor,
                        os_turboboost_enabled,
                        processor_detail,
                        processor_generation,
                    FROM self
                     """)


def read_codecarbon_csv(file_path: str, results_directory_match: str):
    # Paths follow the following format :
    # <RESULTS_DIR_PATH>/<G5K_SITE>/<G5K_CLUSTER>/<G5K_NODE>/<TASK>_<NB_CORES>_<NB_OPS_PER_CORE>.csv
    (site, g5k_g5k_cluster, node, task, nb_cores, nb_ops_per_core) = re.match(
        results_directory_match, file_path
    ).groups()
    parsed_and_converted_rows = []
    with open(file_path, "r") as csv_file:
        reader = csv.DictReader(csv_file)
        for raw_row in reader:
            parsed_row = (
                float(raw_row["energy_cores"]) * 3_600_000
                if raw_row["energy_cores"]
                else 0.0,
                float(raw_row["energy_pkg"]) * 3_600_000
                if raw_row["energy_pkg"]
                else 0.0,
                float(raw_row["energy_ram"]) * 3_600_000
                if raw_row["energy_ram"]
                else 0.0,
                int(raw_row["nb_core"]),
                int(raw_row["nb_ops_per_core"]),
                int(raw_row["iteration"]),
                task,
                site,
                g5k_g5k_cluster,
                node,
            )
            parsed_and_converted_rows.append(parsed_row)
    return parsed_and_converted_rows


def read_alumet_csv(file_path: str, results_directory_match: str):
    # Paths follow the following format :
    # <RESULTS_DIR_PATH>/<G5K_SITE>/<G5K_CLUSTER>/<G5K_NODE>/<TASK>_<NB_CORES>_<NB_OPS_PER_CORE>.csv
    (site, g5k_g5k_cluster, node, task, nb_cores, nb_ops_per_core) = re.match(
        results_directory_match, file_path
    ).groups()
    parsed_and_converted_rows = []
    with open(file_path, "r") as csv_file:
        reader = csv.DictReader(csv_file)
        for raw_row in reader:
            parsed_row = (
                float(raw_row["energy_cores"]) if raw_row["energy_cores"] else 0.0,
                float(raw_row["energy_pkg"]) if raw_row["energy_pkg"] else 0.0,
                float(raw_row["energy_ram"]) if raw_row["energy_ram"] else 0.0,
                int(raw_row["nb_core"]),
                int(raw_row["nb_ops_per_core"]),
                int(raw_row["iteration"]),
                task,
                site,
                g5k_g5k_cluster,
                node,
            )
            parsed_and_converted_rows.append(parsed_row)
    return parsed_and_converted_rows


def read_scaphandre_csv(file_path: str, results_directory_match: str):
    # Paths follow the following format :
    # <RESULTS_DIR_PATH>/<G5K_SITE>/<G5K_CLUSTER>/<G5K_NODE>/<TASK>_<NB_CORES>_<NB_OPS_PER_CORE>.csv
    (site, g5k_g5k_cluster, node, task, nb_cores, nb_ops_per_core) = re.match(
        results_directory_match, file_path
    ).groups()
    parsed_and_converted_rows = []
    with open(file_path, "r") as csv_file:
        reader = csv.DictReader(csv_file)
        for raw_row in reader:
            parsed_row = (
                float(raw_row["energy_cores"]) if raw_row["energy_cores"] else 0.0,
                float(raw_row["energy_pkg"]) if raw_row["energy_pkg"] else 0.0,
                float(raw_row["energy_ram"]) if raw_row["energy_ram"] else 0.0,
                int(raw_row["nb_core"]),
                int(raw_row["nb_ops_per_core"]),
                int(raw_row["iteration"]),
                task,
                site,
                g5k_g5k_cluster,
                node,
            )
            parsed_and_converted_rows.append(parsed_row)
    return parsed_and_converted_rows


def read_vjoule_csv(file_path: str, results_directory_match: str):
    # Paths follow the following format :
    # <RESULTS_DIR_PATH>/<G5K_SITE>/<G5K_CLUSTER>/<G5K_NODE>/<TASK>_<NB_CORES>_<NB_OPS_PER_CORE>.csv
    (site, g5k_g5k_cluster, node, task, nb_cores, nb_ops_per_core) = re.match(
        results_directory_match, file_path
    ).groups()
    parsed_and_converted_rows = []
    with open(file_path, "r") as csv_file:
        reader = csv.DictReader(csv_file)
        for raw_row in reader:
            parsed_row = (
                float(raw_row["energy_cores"]) if raw_row["energy_cores"] else 0.0,
                float(raw_row["energy_pkg"]) if raw_row["energy_pkg"] else 0.0,
                float(raw_row["energy_ram"]) if raw_row["energy_ram"] else 0.0,
                int(raw_row["nb_core"]),
                int(raw_row["nb_ops_per_core"]),
                int(raw_row["iteration"]),
                task,
                site,
                g5k_cluster,
                node,
            )
            parsed_and_converted_rows.append(parsed_row)
    return parsed_and_converted_rows


def load_results(
    hwpc_files,
    perf_files,
    codecarbon_files,
    alumet_files,
    scaphandre_files,
    vjoule_files,
    results_directory_match,
    nodes_df,
):
    perf_df = pl.DataFrame(schema=schemas.raw_perf_columns, strict=True)
    hwpc_df = pl.DataFrame(schema=schemas.hwpc_columns, strict=True)
    codecarbon_df = pl.DataFrame(schema=schemas.raw_energy_columns, strict=True)
    alumet_df = pl.DataFrame(schema=schemas.raw_energy_columns, strict=True)
    scaphandre_df = pl.DataFrame(schema=schemas.raw_energy_columns, strict=True)
    vjoule_df = pl.DataFrame(schema=schemas.raw_energy_columns, strict=True)

    for hwpc_file in hwpc_files:
        hwpc_df = pl.concat(
            [
                hwpc_df,
                pl.from_records(
                    schema=schemas.hwpc_columns,
                    data=read_hwpc_csv(hwpc_file, results_directory_match),
                    strict=True,
                    orient="row",
                ),
            ]
        )

    hwpc_df = hwpc_df.join(
        other=nodes_df,
        left_on=["node", "g5k_cluster"],
        right_on=["uid", "g5k_cluster"],
        how="left",
        validate="m:1",
    )
    hwpc_df = load_hwpc_results(hwpc_df)
    for perf_file in perf_files:
        perf_df = pl.concat(
            [
                perf_df,
                pl.from_records(
                    schema=schemas.raw_perf_columns,
                    data=read_perf_csv(perf_file, results_directory_match),
                    strict=True,
                    orient="row",
                ),
            ]
        )
    print("perf", perf_df.head())

    for codecarbon_file in codecarbon_files:
        codecarbon_df = pl.concat(
            [
                codecarbon_df,
                pl.from_records(
                    schema=schemas.raw_energy_columns,
                    data=read_codecarbon_csv(codecarbon_file, results_directory_match),
                    strict=True,
                    orient="row",
                ),
            ]
        )
    for alumet_file in alumet_files:
        alumet_df = pl.concat(
            [
                alumet_df,
                pl.from_records(
                    schema=schemas.raw_energy_columns,
                    data=read_alumet_csv(alumet_file, results_directory_match),
                    strict=True,
                    orient="row",
                ),
            ]
        )
    for scaphandre_file in scaphandre_files:
        scaphandre_df = pl.concat(
            [
                scaphandre_df,
                pl.from_records(
                    schema=schemas.raw_energy_columns,
                    data=read_scaphandre_csv(scaphandre_file, results_directory_match),
                    strict=True,
                    orient="row",
                ),
            ]
        )
    for vjoule_file in vjoule_files:
        vjoule_df = pl.concat(
            [
                vjoule_df,
                pl.from_records(
                    schema=schemas.raw_energy_columns,
                    data=read_vjoule_csv(vjoule_file, results_directory_match),
                    strict=True,
                    orient="row",
                ),
            ]
        )

    perf_df = perf_df.join(
        other=nodes_df,
        left_on=["node", "g5k_cluster"],
        right_on=["uid", "g5k_cluster"],
        how="left",
        validate="m:1",
    )
    perf_df = perf_df.drop(["numa_nodes_first_cpus"])
    perf_df = load_perf_results(perf_df)
    print("Perf columns :", perf_df.columns)
    codecarbon_df = codecarbon_df.join(
        other=nodes_df,
        left_on=["node", "g5k_cluster"],
        right_on=["uid", "g5k_cluster"],
        how="left",
        validate="m:1",
    )
    codecarbon_df = codecarbon_df.drop(["numa_nodes_first_cpus"])
    print("codecarbon columns :", codecarbon_df.columns)
    alumet_df = alumet_df.join(
        other=nodes_df,
        left_on=["node", "g5k_cluster"],
        right_on=["uid", "g5k_cluster"],
        how="left",
        validate="m:1",
    )
    alumet_df = alumet_df.drop(["numa_nodes_first_cpus"])
    print("alumet columns :", alumet_df.columns)
    scaphandre_df = scaphandre_df.join(
        other=nodes_df,
        left_on=["node", "g5k_cluster"],
        right_on=["uid", "g5k_cluster"],
        how="left",
        validate="m:1",
    )
    scaphandre_df = scaphandre_df.drop(["numa_nodes_first_cpus"])
    print("scaphandre columns :", scaphandre_df.columns)
    vjoule_df = vjoule_df.join(
        other=nodes_df,
        left_on=["node", "g5k_cluster"],
        right_on=["uid", "g5k_cluster"],
        how="left",
        validate="m:1",
    )
    vjoule_df = vjoule_df.drop(["numa_nodes_first_cpus"])
    print("vjoule columns :", vjoule_df.columns)
    # perf_df = load_perf_results(perf_df)

    return (hwpc_df, perf_df, codecarbon_df, alumet_df, scaphandre_df, vjoule_df)


def load_energy(hwpc_df, perf_df, codecarbon_df, alumet_df, scaphandre_df, vjoule_df):
    energy_df = pl.concat(
        [hwpc_df, perf_df, codecarbon_df, alumet_df, scaphandre_df, vjoule_df]
    )
    energy_df = pl.DataFrame(schema=schemas.energy_columns, data=energy_df)

    energy_stats_df = energy_df.sql(
        """
        SELECT
            node,
            task,
            nb_core,
            nb_ops_per_core,
            avg(energy_pkg) as pkg_average,
            median(energy_pkg) as pkg_median,
            min(energy_pkg) as pkg_minimum,
            max(energy_pkg) as pkg_maximum,
            stddev(energy_pkg) as pkg_standard_deviation,
            quantile_cont(energy_pkg, 0.25) as pkg_quantile_25,
            quantile_cont(energy_pkg, 0.75) as pkg_quantile_75,
            (stddev(energy_pkg) / avg(energy_pkg)) as pkg_coefficient_of_variation,
            avg(energy_cores) as cores_average,
            median(energy_cores) as cores_median,
            min(energy_cores) as cores_minimum,
            max(energy_cores) as cores_maximum,
            stddev(energy_cores) as cores_standard_deviation,
            quantile_cont(energy_cores, 0.25) as cores_quantile_25,
            quantile_cont(energy_cores, 0.75) as cores_quantile_75,
            (stddev(energy_cores)/avg(energy_cores)) as cores_coefficient_of_variation,
            avg(energy_ram) as ram_average,
            median(energy_ram) as ram_median,
            min(energy_ram) as ram_minimum,
            max(energy_ram) as ram_maximum,
            stddev(energy_ram) as ram_standard_deviation,
            quantile_cont(energy_ram, 0.25) as ram_quantile_25,
            quantile_cont(energy_ram, 0.75) as ram_quantile_75,
            (stddev(energy_ram) / avg(energy_ram)) as ram_coefficient_of_variation,
            exotic,
            architecture_nb_cores,
            architecture_nb_threads,
            processor_vendor,
            processor_clock_speed,
            processor_instruction_set,
            processor_ht_capable,
            processor_microarchitecture,
            processor_microcode,
            processor_model,
            processor_version,
            os_cstate_driver,
            os_cstate_governor,
            os_pstate_driver,
            os_pstate_governor,
            os_turboboost_enabled,
            processor_detail,
            processor_generation,
        FROM self
        GROUP BY 
            node, 
            task, 
            nb_core, 
            nb_ops_per_core,
            exotic,
            architecture_nb_cores,
            architecture_nb_threads,
            processor_vendor,
            processor_clock_speed,
            processor_instruction_set,
            processor_ht_capable,
            processor_microarchitecture,
            processor_microcode,
            processor_model,
            processor_version,
            os_cstate_driver,
            os_cstate_governor,
            os_pstate_driver,
            os_pstate_governor,
            os_turboboost_enabled,
            processor_detail,
            processor_generation,
    """
    )
    energy_stats_df = pl.DataFrame(energy_stats_df, schema=schemas.stats_columns)

    return energy_df, energy_stats_df


# Extract JSON nodes information
def extract_inventory_json_files(directory: str, schema: str):
    nodes_df = pl.DataFrame(schema=schema, strict=True)
    for site in os.scandir(directory):
        for g5k_cluster in os.scandir(site.path):
            for node in os.scandir(g5k_cluster.path):
                if node.name.endswith(".json"):
                    with open(node.path, "r") as json_file:
                        data = json.load(json_file)
                        node = (
                            data["uid"],
                            data["cluster"],
                            bool(data["exotic"]),
                            int(data["architecture"]["nb_cores"]),
                            int(data["architecture"]["nb_threads"]),
                            data["processor"]["vendor"],
                            int(data["processor"]["clock_speed"]),
                            data["processor"]["instruction_set"],
                            bool(data["processor"]["ht_capable"]),
                            data["processor"]["microarchitecture"],
                            data["processor"]["microcode"],
                            data["processor"]["model"],
                            data["processor"]["version"],
                            data["operating_system"]["cstate_driver"],
                            data["operating_system"]["cstate_governor"],
                            data["operating_system"]["pstate_driver"],
                            data["operating_system"]["pstate_governor"],
                            bool(data["operating_system"]["turboboost_enabled"]),
                        )
                        nodes_df = pl.concat(
                            [
                                nodes_df,
                                pl.from_records(
                                    schema=schema,
                                    data=[node],
                                    strict=True,
                                    orient="row",
                                ),
                            ]
                        )
    return nodes_df


def frequency_file_metadata(filename):
    frequency, tool1, _and_, tool2 = filename.split("/")[-1].split("_")[1:5]
    site, g5k_cluster, node = filename.split("/")[4:7]
    return site, g5k_cluster, node, int(frequency), tool1, tool2.split(".")[0]


def load_frequency(batch_identifier="", results_directory=""):
    print("Loading Frequency Results")
    frequency_csv_file = f"../data/{batch_identifier}/frequency.csv"
    if os.path.exists(frequency_csv_file):
        print("Returning content from :", frequency_csv_file)
        return pl.read_csv(frequency_csv_file)
    # TODO

    perf_frequency_df = load_perf_frequency(
        batch_identifier=batch_identifier, results_directory=results_directory
    )
    hwpc_frequency_df = load_hwpc_frequency(
        batch_identifier=batch_identifier, results_directory=results_directory
    )
    codecarbon_frequency_df = load_codecarbon_frequency(
        batch_identifier=batch_identifier, results_directory=results_directory
    )
    alumet_frequency_df = load_alumet_frequency(
        batch_identifier=batch_identifier, results_directory=results_directory
    )
    scaphandre_frequency_df = load_scaphandre_frequency(
        batch_identifier=batch_identifier, results_directory=results_directory
    )
    vjoule_frequency_df = load_vjoule_frequency(
        batch_identifier=batch_identifier, results_directory=results_directory
    )

    return (
        perf_frequency_df,
        hwpc_frequency_df,
        codecarbon_frequency_df,
        alumet_frequency_df,
        scaphandre_frequency_df,
        vjoule_frequency_df,
    )


def load_perf_frequency(batch_identifier="", results_directory=""):
    print("Loading Perf Frequency Results")
    perf_frequency_csv_file = f"../data/{batch_identifier}.d/perf_frequency.csv"
    if os.path.exists(perf_frequency_csv_file):
        print("Returning content from :", perf_frequency_csv_file)
        perf_df = pl.read_csv(perf_frequency_csv_file)
        return perf_df
    else:
        regex = "frequency.*perf_and.*csv"
        print("No import found, will load from raw files matching regex : ", regex)
        perf_frequency_raw_files = utils.find_files(
            root_dir=results_directory, regex=regex
        )
        perf_dfs = []
        for file in perf_frequency_raw_files:
            print("Reading perf file :", file)
            site, g5k_cluster, node, frequency, tool1, tool2 = frequency_file_metadata(
                file
            )
            matching_temperature_file = f"{results_directory}/{site}/{g5k_cluster}/{node}/temperatures_frequency_{frequency}_perf_and_{tool2}.csv"
            perf_df = pl.read_csv(file).with_columns(
                tool=pl.lit(tool2),
                node=pl.lit(node),
                g5k_cluster=pl.lit(g5k_cluster),
                target_frequency=pl.lit(frequency),
            )
            temperature_df = pl.read_csv(matching_temperature_file)
            perf_df = pl.sql(
                "SELECT * FROM perf_df JOIN temperature_df ON perf_df.iteration = temperature_df.iteration"
            ).collect()
            perf_dfs.append(perf_df)
        perf_df = pl.concat(perf_dfs)
        perf_df.write_csv(perf_frequency_csv_file)
        return perf_df.sql(
            "SELECT g5k_cluster, node, tool, power_energy_cores as cores, power_energy_pkg as pkg, power_energy_ram as ram, target_frequency, temperature_start, temperature_stop, iteration FROM self"
        )


def load_hwpc_frequency(batch_identifier="", results_directory=""):
    print("Loading HWPC Frequency Results")
    hwpc_frequency_csv_file = f"../data/{batch_identifier}.d/hwpc_frequency.csv"
    if os.path.exists(hwpc_frequency_csv_file):
        print("Returning content from :", hwpc_frequency_csv_file)
        hwpc_df = pl.read_csv(hwpc_frequency_csv_file)
        return hwpc_df
    else:
        regex = "frequency.*hwpc_and.*csv"
        print("No import found, will load from raw files matching regex : ", regex)
        hwpc_frequency_raw_files = utils.find_files(
            root_dir=results_directory, regex=regex
        )
        hwpc_dfs = []
        for file in hwpc_frequency_raw_files:
            site, g5k_cluster, node, frequency, _tool1, _tool2 = (
                frequency_file_metadata(file)
            )
            hwpc_df = pl.read_csv(file)
            hwpc_df = hwpc_df.with_columns(
                node=pl.lit(node),
                g5k_cluster=pl.lit(g5k_cluster),
            )
            hwpc_dfs.append(hwpc_df)
        hwpc_df = pl.concat(hwpc_dfs)
        hwpc_df = hwpc_df.drop(["sensor", "target", "time_enabled", "time_running"])
        hwpc_df = hwpc_df.sql("""
                              SELECT g5k_cluster, node, timestamp, SUM(rapl_energy_cores) as cores, SUM(rapl_energy_pkg) as pkg, SUM(rapl_energy_dram) as ram, iteration, frequency 
                              FROM self 
                              GROUP BY timestamp, frequency, iteration, node, g5k_cluster
                              """)
        hwpc_df.write_csv(hwpc_frequency_csv_file)
        return hwpc_df


def load_codecarbon_frequency(batch_identifier="", results_directory=""):
    print("Loading Codecarbon Frequency Results")
    codecarbon_frequency_csv_file = (
        f"../data/{batch_identifier}.d/codecarbon_frequency.csv"
    )
    if os.path.exists(codecarbon_frequency_csv_file):
        print("Returning content from :", codecarbon_frequency_csv_file)
        codecarbon_df = pl.read_csv(codecarbon_frequency_csv_file)
        return codecarbon_df
    else:
        regex = "frequency.*codecarbon_and.*csv"
        print("No import found, will load from raw files matching regex : ", regex)
        codecarbon_frequency_raw_files = utils.find_files(
            root_dir=results_directory, regex=regex
        )

        codecarbon_dfs = []
        for file in codecarbon_frequency_raw_files:
            site, g5k_cluster, node, frequency, _tool1, _tool2 = (
                frequency_file_metadata(file)
            )
            codecarbon_df = pl.read_csv(
                source=file,
            )
            codecarbon_df = codecarbon_df.unique(keep="any")
            codecarbon_df = codecarbon_df.with_columns(
                [
                    (
                        pl.col("timestamp")
                        .map_elements(
                            lambda x: datetime.timestamp(datetime.fromisoformat(x)),
                            return_dtype=pl.Float64,
                        )
                        .alias("timestamp")
                    )
                ]
            )
            codecarbon_df = codecarbon_df.pivot(
                on="domain",
                index="timestamp",
                values=["energy", "iteration"],
                aggregate_function="sum",
            )
            codecarbon_df = codecarbon_df.with_columns(
                g5k_cluster=pl.lit(g5k_cluster),
                node=pl.lit(node),
                frequency=pl.lit(frequency),
                pkg=pl.lit(0.0),
            )
            codecarbon_dfs.append(
                codecarbon_df.sql(
                    "SELECT g5k_cluster, node, timestamp, energy_CPU as cores, pkg, energy_RAM as ram, iteration_CPU as iteration, frequency FROM self"
                )
            )

        codecarbon_df = pl.concat(codecarbon_dfs)
        codecarbon_df.write_csv(codecarbon_frequency_csv_file)
        return codecarbon_df


def load_alumet_frequency(batch_identifier="", results_directory=""):
    print("Loading alumet Frequency Results")
    alumet_frequency_csv_file = f"../data/{batch_identifier}.d/alumet_frequency.csv"
    if os.path.exists(alumet_frequency_csv_file):
        print("Returning content from :", alumet_frequency_csv_file)
        alumet_df = pl.read_csv(alumet_frequency_csv_file)
        return alumet_df
    else:
        regex = "frequency.*alumet_and.*csv"
        print("No import found, will load from raw files matching regex : ", regex)
        alumet_frequency_raw_files = utils.find_files(
            root_dir=results_directory, regex=regex
        )
        alumet_dfs = []
        for file in alumet_frequency_raw_files:
            site, g5k_cluster, node, frequency, _tool1, _tool2 = (
                frequency_file_metadata(file)
            )
            alumet_df = pl.read_csv(
                source=file,
            )
            alumet_df = alumet_df.with_columns(
                [
                    (
                        pl.col("timestamp")
                        .map_elements(
                            lambda x: datetime.timestamp(
                                datetime.fromisoformat(clamp_date(x))
                            ),
                            return_dtype=pl.Float64,
                        )
                        .alias("timestamp")
                    )
                ]
            )
            alumet_df = alumet_df.unique(keep="any")
            alumet_df = alumet_df.sql(
                "SELECT domain, timestamp, SUM(energy) as energy, iteration FROM self GROUP BY domain, timestamp, iteration"
            )
            alumet_df = alumet_df.pivot(
                on="domain", index="timestamp", values=["energy", "iteration"]
            )
            alumet_df = alumet_df.with_columns(
                g5k_cluster=pl.lit(g5k_cluster),
                node=pl.lit(node),
                frequency=pl.lit(frequency),
                cores=pl.lit(0.0),
            )
            alumet_dfs.append(
                alumet_df.sql(
                    "SELECT g5k_cluster, node, timestamp, cores, energy_package as pkg, energy_dram as ram, iteration_package as iteration, frequency FROM self"
                )
            )
        alumet_df = pl.concat(alumet_dfs)
        alumet_df.write_csv(alumet_frequency_csv_file)
        return alumet_df


def clamp_date(date):
    if len(date) > 26:
        return date[:26]
    elif len(date) > 23:
        return date[:23]
    else:
        return date


def load_scaphandre_frequency(batch_identifier="", results_directory=""):
    print("Loading scaphandre Frequency Results")
    scaphandre_frequency_csv_file = (
        f"../data/{batch_identifier}.d/scaphandre_frequency.csv"
    )
    if os.path.exists(scaphandre_frequency_csv_file):
        print("Returning content from :", scaphandre_frequency_csv_file)
        scaphandre_df = pl.read_csv(scaphandre_frequency_csv_file)
        return scaphandre_df
    else:
        regex = "frequency.*scaphandre_and.*csv"
        print("No import found, will load from raw files matching regex : ", regex)
        scaphandre_frequency_raw_files = utils.find_files(
            root_dir=results_directory, regex=regex
        )
        scaphandre_dfs = []
        for file in scaphandre_frequency_raw_files:
            print("Reading scaphandre frequency file", file)
            site, g5k_cluster, node, frequency, _tool1, _tool2 = (
                frequency_file_metadata(file)
            )
            scaphandre_df = pl.read_csv(
                source=file,
            )
            scaphandre_df = scaphandre_df.unique(keep="any")
            scaphandre_df = scaphandre_df.pivot(
                on="domain", index="timestamp", values=["energy", "iteration"]
            )
            scaphandre_df = scaphandre_df.with_columns(
                g5k_cluster=pl.lit(g5k_cluster),
                node=pl.lit(node),
                cores=pl.lit(0.0),
                ram=pl.lit(0.0),
                frequency=pl.lit(frequency),
            )
            scaphandre_dfs.append(
                scaphandre_df.sql(
                    "SELECT g5k_cluster, node, timestamp, cores, energy_package as pkg, ram, iteration_package as iteration, frequency FROM self"
                )
            )
        scaphandre_df = pl.concat(scaphandre_dfs)
        scaphandre_df.write_csv(scaphandre_frequency_csv_file)
        return scaphandre_df


def load_vjoule_frequency(batch_identifier="", results_directory=""):
    print("Loading vjoule Frequency Results")
    vjoule_frequency_csv_file = f"../data/{batch_identifier}.d/vjoule_frequency.csv"
    if os.path.exists(vjoule_frequency_csv_file):
        print("Returning content from :", vjoule_frequency_csv_file)
        vjoule_df = pl.read_csv(vjoule_frequency_csv_file)
        return vjoule_df
    else:
        regex = "frequency.*vjoule_and.*csv"
        print("No import found, will load from raw files matching regex : ", regex)
        vjoule_dfs = []
        vjoule_frequency_raw_files = utils.find_files(
            root_dir=results_directory, regex=regex
        )
        for file in vjoule_frequency_raw_files:
            site, g5k_cluster, node, frequency, _tool1, _tool2 = (
                frequency_file_metadata(file)
            )
            vjoule_df = pl.read_csv(
                source=file,
            )
            vjoule_df = vjoule_df.unique(keep="any")
            vjoule_df = vjoule_df.with_columns(
                [
                    (pl.col("timestamp").str.strip_chars().alias("timestamp")),
                    (pl.col("energy").str.strip_chars().alias("energy")),
                ]
            )
            vjoule_df = vjoule_df.cast(
                {
                    "energy": pl.Float64,
                }
            )

            vjoule_df = vjoule_df.pivot(
                on="domain",
                index="timestamp",
                values=["energy", "iteration"],
                aggregate_function="sum",
            )
            vjoule_df = vjoule_df.with_columns(
                g5k_cluster=pl.lit(g5k_cluster),
                node=pl.lit(node),
                cores=pl.lit(0.0),
                frequency=pl.lit(frequency),
            )
            vjoule_dfs.append(
                vjoule_df.sql(
                    "SELECT g5k_cluster, node, timestamp, cores, energy_CPU as pkg, energy_RAM as ram, iteration_CPU as iteration, frequency FROM self"
                )
            )
        vjoule_df = pl.concat(vjoule_dfs)
        vjoule_df.write_csv(vjoule_frequency_csv_file)
        return vjoule_df

def load_vjoule_frequency_agg(batch_identifier="", results_directory=""):
    print("Loading vjoule Frequency Results")
    vjoule_frequency_csv_file = f"../data/{batch_identifier}.d/vjoule_frequency_agg.csv"

    if os.path.exists(vjoule_frequency_csv_file):
        print("Returning content from :", vjoule_frequency_csv_file)
        return pl.read_csv(vjoule_frequency_csv_file)

    # Else: load raw files
    regex = "frequency.*vjoule_and.*csv"
    print("No import found, will load from raw files matching regex : ", regex)

    vjoule_dfs = []
    vjoule_frequency_raw_files = utils.find_files(
        root_dir=results_directory,
        regex=regex
    )

    for file in vjoule_frequency_raw_files:
        site, g5k_cluster, node, frequency, _tool1, _tool2 = frequency_file_metadata(file)

        vjoule_df = pl.read_csv(file).unique(keep="any")

        # Clean columns
        vjoule_df = vjoule_df.with_columns(
            [
                pl.col("timestamp").str.strip_chars().alias("timestamp"),
                pl.col("energy").str.strip_chars().alias("energy"),
            ]
        )

        # Cast types
        vjoule_df = vjoule_df.cast({"energy": pl.Float64})

        # ---- NEW PART: keep only last energy per (iteration, domain) ----
        vjoule_df = (
            vjoule_df
            .sort("timestamp")
            .group_by(["iteration", "domain"])
            .tail(1)    # keep latest record for each pair
        )

        # Pivot
        vjoule_df = vjoule_df.pivot(
            on="domain",
            index="timestamp",
            values=["energy", "iteration"],
            aggregate_function="sum",
        )

        # Add metadata
        vjoule_df = vjoule_df.with_columns(
            g5k_cluster=pl.lit(g5k_cluster),
            node=pl.lit(node),
            cores=pl.lit(0.0),
            frequency=pl.lit(frequency),
        )

        # Reorder/select columns via SQL
        vjoule_dfs.append(
            vjoule_df.sql(
                """
                SELECT 
                    g5k_cluster, node, timestamp, cores,
                    energy_CPU AS pkg,
                    energy_RAM AS ram,
                    iteration_CPU AS iteration,
                    frequency
                FROM self
                """
            )
        )

    # Concatenate across files
    vjoule_df = pl.concat(vjoule_dfs)

    # Save cache
    vjoule_df.write_csv(vjoule_frequency_csv_file)

    return vjoule_df


def load_codecarbon_frequency_agg(batch_identifier="", results_directory=""):
    print("Loading codecarbon Frequency Results")
    codecarbon_frequency_csv_file = f"../data/{batch_identifier}.d/codecarbon_frequency_agg.csv"

    if os.path.exists(codecarbon_frequency_csv_file):
        print("Returning content from :", codecarbon_frequency_csv_file)
        return pl.read_csv(codecarbon_frequency_csv_file)

    # Else: load raw files
    regex = "frequency.*codecarbon_and.*csv"
    print("No import found, will load from raw files matching regex : ", regex)

    codecarbon_dfs = []
    codecarbon_frequency_raw_files = utils.find_files(
        root_dir=results_directory,
        regex=regex
    )

    for file in codecarbon_frequency_raw_files:
        site, g5k_cluster, node, frequency, _tool1, _tool2 = frequency_file_metadata(file)

        codecarbon_df = pl.read_csv(file).unique(keep="any")

        # Clean columns
        codecarbon_df = codecarbon_df.with_columns(
            [
                pl.col("timestamp").str.strip_chars().alias("timestamp"),
            ]
        )

        # Cast types
        codecarbon_df = codecarbon_df.cast({"energy": pl.Float64})

        # ---- NEW PART: keep only last energy per (iteration, domain) ----
        codecarbon_df = (
            codecarbon_df
            .sort("timestamp")
            .group_by(["iteration", "domain"])
            .tail(1)    # keep latest record for each pair
        )

        # Pivot
        codecarbon_df = codecarbon_df.pivot(
            on="domain",
            index="timestamp",
            values=["energy", "iteration"],
            aggregate_function="sum",
        )

        # Add metadata
        codecarbon_df = codecarbon_df.with_columns(
            g5k_cluster=pl.lit(g5k_cluster),
            node=pl.lit(node),
            cores=pl.lit(0.0),
            frequency=pl.lit(frequency),
        )

        # Reorder/select columns via SQL
        codecarbon_dfs.append(
            codecarbon_df.sql(
                """
                SELECT 
                    g5k_cluster, node, timestamp, cores,
                    energy_CPU AS pkg,
                    energy_RAM AS ram,
                    iteration_CPU AS iteration,
                    frequency
                FROM self
                """
            )
        )

    # Concatenate across files
    codecarbon_df = pl.concat(codecarbon_dfs)

    # Save cache
    codecarbon_df.write_csv(codecarbon_frequency_csv_file)

    return codecarbon_df




def polish_frequency(frequency_df):
    print("Polishing Frequency Results")
    print("No operations yet")
    return frequency_df


def frequency_validation(frequency_df):
    print("Frequency Validation Results")
    print("No operations yet")
    return True


def load_inventory(batch_identifier=""):
    print("Loading Inventory Results")
    inventories_directory = (
        f"../data/{batch_identifier}/inventories-{batch_identifier}.d"
    )
    inventory_csv_file = f"../data/{batch_identifier}/inventory.csv"
    if os.path.exists(inventory_csv_file):
        print("Returning content from :", inventory_csv_file)
        inventory_df = pd.read_csv(inventory_csv_file)
        return inventory_df
    inventory_df = extract_inventory_json_files(
        directory=inventories_directory, schema=schemas.nodes_configuration_columns
    )

    inventory_df = inventory_df.with_columns(
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
                    lambda x: f"{vendor_generation_map[x]['vendor']}",
                    return_dtype=pl.String,
                )
                .alias("processor_vendor")
            ),
            (
                pl.col("processor_version")
                .map_elements(
                    lambda x: vendor_generation_map[x]["numa_nodes_first_cpus"],
                    return_dtype=pl.List(pl.Int64),
                )
                .alias("numa_nodes_first_cpus")
            ),
        ]
    )
    return inventory_df


def load_energy(batch_identifier=""):
    print("Loading Energy Results")
    energy_csv_file = f"../data/{batch_identifier}/energy.csv"
    if os.path.exists(energy_csv_file):
        print("Returning content from :", energy_csv_file)
        energy_df = pd.read_csv(energy_csv_file)
        return energy_df
    # TODO
    return energy_df


def load_energy_stats(batch_identifier=""):
    print("Loading Energy Stats Results")
    energy_stats_csv_file = f"../data/{batch_identifier}/energy_stats.csv"
    if os.path.exists(energy_stats_csv_file):
        print("Returning content from :", energy_stats_csv_file)
        energy_stats_df = pd.read_csv(energy_stats_csv_file)
        return energy_stats_df
    # TODO
    return energy_stats_df


def baseline_file_metadata(filename):
    g5k_cluster, node = filename.split("/")[5:7]
    return g5k_cluster, node


def load_baseline(batch_identifier="", results_directory=""):
    print("Loading Baseline Results")
    baseline_csv_file = f"../data/{batch_identifier}.d/baseline_consumption.csv"
    if os.path.exists(baseline_csv_file):
        print("Returning content from :", baseline_csv_file)
        baseline_df = pl.read_csv(baseline_csv_file)
        return baseline_df
    else:
        regex = "baseline_consumption.csv"
        print("No import found, will load from raw files matching regex : ", regex)
        baseline_raw_files = utils.find_files(root_dir=results_directory, regex=regex)
        baseline_dfs = []
        for file in baseline_raw_files:
            g5k_cluster, node = baseline_file_metadata(file)
            baseline_df = pl.read_csv(file)
            if baseline_df.shape[0] == 0:
                print("No Baseline data found for ", file)
                continue
            baseline_df = baseline_df.cast({cs.numeric(): pl.Float32})
            baseline_df = baseline_df.with_columns(
                g5k_cluster=pl.lit(g5k_cluster), node=pl.lit(node)
            )
            baseline_dfs.append(baseline_df)

        baseline_df = pl.concat(baseline_dfs)
        baseline_df.write_csv(baseline_csv_file)
        return baseline_df
