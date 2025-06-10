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
import polars as pl


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
        for g5k_cluster in os.scandir(site.path):
            for node in os.scandir(g5k_cluster.path):
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
    return hwpc_files, perf_files, codecarbon_files, alumet_files, scaphandre_files, vjoule_files

# Parse HWPC files, PKG, Cores or RAM can be missing, if so, we put a 0.0 value
# Conversions are done later because measures as fixed point arithmetic (32.32) (needs to be ldexp(x, -32)ed)
def read_hwpc_csv(file_path: str, results_directory_match: str):
    """
    """
    # Paths follow the following format : 
    # <RESULTS_DIR_PATH>/<G5K_SITE>/<G5K_CLUSTER>/<G5K_NODE>/<TASK>_<NB_CORES>_<NB_OPS_PER_CORE>.csv
    (site, g5k_cluster, node, task, nb_cores, nb_ops_per_core) = re.match(results_directory_match, file_path).groups()
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
                int(raw_row["rapl_energy_cores"]) if raw_row["rapl_energy_cores"] else 0,
                int(raw_row["time_enabled"]),
                int(raw_row["time_running"]),
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
def load_hwpc_results(hwpc_df):
    """
    """
    # HWPC, by default, produces reports with 1 row for each combination of (socket, cpu)
    # Considering some system counters (such are RAPL PKG) are shared for all cpu of a given socket
    # We do have to filter out redundant values to prevent counting something twice.
    # We chose to keep only the first 
    hwpc_df = hwpc_df.filter(pl.col("cpu").is_in("numa_nodes_first_cpus"))
    print("HWPC rows :", hwpc_df.sql("SELECT node, cpu, numa_nodes_first_cpus, rapl_energy_pkg, rapl_energy_cores, rapl_energy_dram FROM self").head())
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
            g5k_cluster,
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
            g5k_cluster,
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
                        g5k_cluster,
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
                     """
                     )

# Parse Perf files, again PKG, Cores or RAM can be missing,
def read_perf_csv(file_path: str, results_directory_match: str):
    # Paths follow the following format : 
    # <RESULTS_DIR_PATH>/<G5K_SITE>/<G5K_CLUSTER>/<G5K_NODE>/<TASK>_<NB_CORES>_<NB_OPS_PER_CORE>.csv
    (site, g5k_cluster, node, task, nb_cores, nb_ops_per_core) = re.match(results_directory_match, file_path).groups()
    parsed_and_converted_rows = []
    with open(file_path, "r") as csv_file:
        reader = csv.DictReader(csv_file)
        for raw_row in reader:
            parsed_row = (
                float(raw_row["power_energy_pkg"]) if raw_row["power_energy_pkg"] else 0.0,
                float(raw_row["power_energy_ram"]) if raw_row["power_energy_ram"] else 0.0,
                float(raw_row["power_energy_cores"]) if raw_row["power_energy_cores"] else 0.0,
                int(raw_row["nb_core"]),
                int(raw_row["nb_ops_per_core"]),
                int(raw_row["iteration"]),
                task,
                site,
                g5k_cluster,
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
                        g5k_cluster,
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
                     """
                     )

def read_codecarbon_csv(file_path: str, results_directory_match: str):
    # Paths follow the following format : 
    # <RESULTS_DIR_PATH>/<G5K_SITE>/<G5K_CLUSTER>/<G5K_NODE>/<TASK>_<NB_CORES>_<NB_OPS_PER_CORE>.csv
    (site, g5k_cluster, node, task, nb_cores, nb_ops_per_core) = re.match(results_directory_match, file_path).groups()
    parsed_and_converted_rows = []
    with open(file_path, "r") as csv_file:
        reader = csv.DictReader(csv_file)
        for raw_row in reader:
            parsed_row = (
                float(raw_row["energy_cores"])*3_600_000 if raw_row["energy_cores"] else 0.0,
                float(raw_row["energy_pkg"])*3_600_000 if raw_row["energy_pkg"] else 0.0,
                float(raw_row["energy_ram"])*3_600_000 if raw_row["energy_ram"] else 0.0,
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

def read_alumet_csv(file_path: str, results_directory_match: str):
    # Paths follow the following format : 
    # <RESULTS_DIR_PATH>/<G5K_SITE>/<G5K_CLUSTER>/<G5K_NODE>/<TASK>_<NB_CORES>_<NB_OPS_PER_CORE>.csv
    (site, g5k_cluster, node, task, nb_cores, nb_ops_per_core) = re.match(results_directory_match, file_path).groups()
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

def read_scaphandre_csv(file_path: str, results_directory_match: str):
    # Paths follow the following format : 
    # <RESULTS_DIR_PATH>/<G5K_SITE>/<G5K_CLUSTER>/<G5K_NODE>/<TASK>_<NB_CORES>_<NB_OPS_PER_CORE>.csv
    (site, g5k_cluster, node, task, nb_cores, nb_ops_per_core) = re.match(results_directory_match, file_path).groups()
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

def read_vjoule_csv(file_path: str, results_directory_match: str):
    # Paths follow the following format : 
    # <RESULTS_DIR_PATH>/<G5K_SITE>/<G5K_CLUSTER>/<G5K_NODE>/<TASK>_<NB_CORES>_<NB_OPS_PER_CORE>.csv
    (site, g5k_cluster, node, task, nb_cores, nb_ops_per_core) = re.match(results_directory_match, file_path).groups()
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

def load_results(hwpc_files, perf_files, codecarbon_files, alumet_files, scaphandre_files, vjoule_files, results_directory_match, nodes_df):
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
        other=nodes_df, left_on=["node", "g5k_cluster"], right_on=["uid", "g5k_cluster"], how="left", validate="m:1"
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
        other=nodes_df, left_on=["node", "g5k_cluster"], right_on=["uid", "g5k_cluster"], how="left", validate="m:1"
    )
    perf_df = perf_df.drop(["numa_nodes_first_cpus"])
    perf_df = load_perf_results(perf_df)
    print("Perf columns :", perf_df.columns)
    codecarbon_df = codecarbon_df.join(
        other=nodes_df, left_on=["node", "g5k_cluster"], right_on=["uid", "g5k_cluster"], how="left", validate="m:1"
    )
    codecarbon_df = codecarbon_df.drop(["numa_nodes_first_cpus"])
    print("codecarbon columns :", codecarbon_df.columns)
    alumet_df = alumet_df.join(
        other=nodes_df, left_on=["node", "g5k_cluster"], right_on=["uid", "g5k_cluster"], how="left", validate="m:1"
    )
    alumet_df = alumet_df.drop(["numa_nodes_first_cpus"])
    print("alumet columns :", alumet_df.columns)
    scaphandre_df = scaphandre_df.join(
        other=nodes_df, left_on=["node", "g5k_cluster"], right_on=["uid", "g5k_cluster"], how="left", validate="m:1"
    )
    scaphandre_df = scaphandre_df.drop(["numa_nodes_first_cpus"])
    print("scaphandre columns :", scaphandre_df.columns)
    vjoule_df = vjoule_df.join(
        other=nodes_df, left_on=["node", "g5k_cluster"], right_on=["uid", "g5k_cluster"], how="left", validate="m:1"
    )
    vjoule_df = vjoule_df.drop(["numa_nodes_first_cpus"])
    print("vjoule columns :", vjoule_df.columns)
    #perf_df = load_perf_results(perf_df)

    return (hwpc_df, perf_df, codecarbon_df, alumet_df, scaphandre_df, vjoule_df)

def load_energy(hwpc_df, perf_df, codecarbon_df, alumet_df, scaphandre_df, vjoule_df):
    energy_df = pl.concat([hwpc_df, perf_df, codecarbon_df, alumet_df, scaphandre_df, vjoule_df])
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
