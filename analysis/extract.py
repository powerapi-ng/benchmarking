import os
import json
import csv
import re
from typing import Tuple, List
import polars as pl


# Extract CSV to Polars DataFrames
# Extract HWPC & PERF CSVs
def extract_csv_files(directory: str) -> Tuple[List[str], List[str]]:
    hwpc_files = []
    perf_files = []
    for site in os.scandir(directory):
        for cluster in os.scandir(site.path):
            for node in os.scandir(cluster.path):
                if node.is_dir():
                    for filename in os.scandir(node.path):

                        if filename.path.endswith(".csv"):
                            if filename.name.startswith("hwpc"):
                                hwpc_files.append(filename.path)
                            elif filename.name.startswith("perf"):
                                perf_files.append(filename.path)
    return hwpc_files, perf_files


def read_hwpc_csv(file_path: str, results_directory_match: str):
    (site, cluster, node, task) = re.match(results_directory_match, file_path).groups()
    with_perf = False
    if task == "and":
        with_perf = True
    rows = []
    with open(file_path, "r") as csv_file:
        reader = csv.reader(csv_file)
        next(reader)  # Skip header
        for row in reader:
            parsed_row = (
                int(row[0]),
                row[1],
                row[2],
                int(row[3]),
                int(row[4]),
                int(row[5]) if row[5] else None,
                int(row[6]) if row[6] else None,
                int(row[7]) if row[7] else None,
                int(row[8]),
                int(row[9]),
                int(row[10]),
                int(row[11]),
                int(row[12]),
                with_perf,
                site,
                cluster,
                node,
            )
            rows.append(parsed_row)

    return rows


def read_perf_csv(file_path: str, results_directory_match: str):
    (site, clstr, node, task) = re.match(results_directory_match, file_path).groups()
    with_hwpc = False
    if task == "and":
        with_hwpc = True
    rows = []
    with open(file_path, "r") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            try:
                power_energy_pkg = float(row["power_energy_pkg"])
            except ValueError:
                power_energy_pkg = 0.0
            try:
                power_energy_ram = float(row["power_energy_ram"])
            except ValueError:
                power_energy_ram = 0.0
            try:
                power_energy_cores = (float(row["power_energy_cores"]),)
            except ValueError:
                power_energy_cores = 0.0
            parsed_row = (
                float(power_energy_pkg),
                float(power_energy_ram),
                float(power_energy_cores),
                float(row["time_elapsed"]),
                int(row["nb_core"]),
                int(row["nb_ops_per_core"]),
                int(row["iteration"]),
                bool(with_hwpc),
                site,
                clstr,
                node,
            )
            rows.append(parsed_row)
    return rows


# Extract JSON nodes information


def extract_json_files(directory: str, schema: str):

    nodes_df = pl.DataFrame(schema=schema, strict=True)

    for site in os.scandir(directory):
        for cluster in os.scandir(site.path):

            for node in os.scandir(cluster.path):
                if node.name.endswith(".json"):
                    with open(node.path, "r") as json_file:
                        data = json.load(json_file)
                        # Assuming proper parsing and casting here
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
