import schemas
import extract
from typing import *
import polars as pl
from tqdm import tqdm
from math import ldexp


def load_hwpc_results(hwpc_df):
    print(hwpc_df.sql("select rapl_energy_pkg from self").describe())
    hwpc_results = pl.sql(
        """
        SELECT node, nb_core, nb_ops_per_core, iteration, alone,
               SUM(rapl_energy_pkg) as energy_pkg_int,
               SUM(rapl_energy_cores) as energy_cores_int,
               SUM(rapl_energy_dram) as energy_ram_int
        FROM hwpc_df
        GROUP BY sensor, target, socket, cpu, node, nb_core,
                 nb_ops_per_core, iteration, alone
    """
    ).collect()

    hwpc_results = hwpc_results.with_columns(
        pl.col("energy_pkg_int")
        .map_elements(lambda x: ldexp(x, -32) * 10e6, return_dtype=pl.Float64)
        .alias("energy_pkg"),
    )

    hwpc_results = hwpc_results.with_columns(
        pl.col("energy_cores_int")
        .map_elements(lambda x: ldexp(x, -32) * 10e6, return_dtype=pl.Float64)
        .alias("energy_cores"),
    )

    hwpc_results = hwpc_results.with_columns(
        pl.col("energy_ram_int")
        .map_elements(lambda x: ldexp(x, -32) * 10e6, return_dtype=pl.Float64)
        .alias("energy_ram"),
    )

    hwpc_results = hwpc_results.drop(
        ["energy_pkg_int", "energy_cores_int", "energy_ram_int"]
    )

    task = pl.Series("task", ["hwpc" for i in range(hwpc_results.shape[0])])
    hwpc_results.insert_column(1, task)

    return hwpc_results


def load_perf_results(perf_df):
    perf_results = pl.sql(
        """
        SELECT node, nb_core, nb_ops_per_core, iteration, alone,
               power_energy_pkg as energy_pkg,
               power_energy_cores as energy_cores,
               power_energy_ram as energy_ram FROM perf_df
    """
    ).collect()
    perf_results = perf_results.with_columns(pl.col("energy_pkg") * 10e6)
    perf_results = perf_results.with_columns(pl.col("energy_cores") * 10e6)
    perf_results = perf_results.with_columns(pl.col("energy_ram") * 10e6)
    task = pl.Series("task", ["perf" for i in range(perf_results.shape[0])])
    perf_results.insert_column(1, task)

    return perf_results


def load_results(hwpc_files, perf_files, results_directory_match, test):
    hwpc_df = pl.DataFrame(schema=schemas.hwpc_columns, strict=True)

    perf_df = pl.DataFrame(schema=schemas.perf_columns, strict=True)

    if test:
        count = 0
    for hwpc_file, perf_file in tqdm(zip(hwpc_files, perf_files)):
        if test:
            count += 1
            if count == 100:
                break
        hwpc_df = pl.concat(
            [
                hwpc_df,
                pl.from_records(
                    schema=schemas.hwpc_columns,
                    data=extract.read_hwpc_csv(hwpc_file, results_directory_match),
                    strict=True,
                    orient="row",
                ),
            ]
        )
        perf_df = pl.concat(
            [
                perf_df,
                pl.from_records(
                    schema=schemas.perf_columns,
                    data=extract.read_perf_csv(perf_file, results_directory_match),
                    strict=True,
                    orient="row",
                ),
            ]
        )

    hwpc_results = load_hwpc_results(hwpc_df)
    perf_results = load_perf_results(perf_df)

    return (hwpc_results, perf_results)


def load_energy(hwpc_results, perf_results, nodes_df, os):
    energy_df = pl.concat([hwpc_results, perf_results])
    energy_df = pl.DataFrame(schema=schemas.energy_columns, data=energy_df)

    energy_stats_df = energy_df.sql(
        """
        SELECT
            node,
            task,
            nb_core,
            nb_ops_per_core,
            alone,
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
        FROM self
        GROUP BY node, task, nb_core, nb_ops_per_core, alone
    """
    )
    energy_stats_df = pl.DataFrame(energy_stats_df, schema=schemas.stats_columns)
    energy_stats_df = energy_stats_df.join(
        other=nodes_df, left_on="node", right_on="uid", how="left", validate="m:1"
    )
    energy_stats_df = energy_stats_df.with_columns([
        (pl.col("nb_core") / pl.col("architecture_nb_cores")).alias("percent_cores_used"),
        (pl.col("nb_core") / pl.col("architecture_nb_threads")).alias("percent_threads_used"),
        
    ])
    print("New columns :", energy_stats_df.sql("SELECT percent_cores_used, percent_threads_used FROM self").describe())

    ranges = {
        "10%": (0, 0.1),
        "25": (0.1, 0.25),
        "50": (0.25, 0.5),
        "75": (0.5, 0.75),
        "90": (0.75, 0.9),
        "100": (0.9, 1.0),
        "110": (1.0, 1.1)
    }

    def assign_category(value):
        for label, (low, high) in ranges.items():
            if low <= value < high:
                return int(label)
        return None

    energy_stats_df = energy_stats_df.with_columns(
        pl.col("percent_cores_used")
        .map_elements(lambda x : assign_category(x))
        .alias("percent_cores_used_category")
    )

    energy_stats_df = energy_stats_df.with_columns(
        pl.col("percent_threads_used")
        .map_elements(lambda x : assign_category(x))
        .alias("percent_threads_used_category")
    )


    jobs = {
        "hwpc_true": "hwpc_alone",
        "hwpc_false": "hwpc_with_perf",
        "perf_true": "perf_alone",
        "perf_false": "perf_with_hwpc",
    }

    energy_stats_df = energy_stats_df.with_columns(
        pl.concat_str(["task", "alone"], separator="_").alias("job")
    )

    energy_stats_df = energy_stats_df.with_columns(pl.col("job").replace_strict(jobs))

    print("New columns :", energy_stats_df.sql("SELECT percent_cores_used, percent_threads_used, percent_cores_used_category, percent_threads_used_category FROM self").describe())

    return energy_stats_df
