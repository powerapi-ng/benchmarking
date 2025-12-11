# IMPORTS
import os
import argparse
import sys
import polars as pl
import numpy as np
import gc

import schemas
import load
import rq1
import rq2
import rq3
import rq34
import utils
import visualization
import matplotlib.pyplot as plt
import seaborn as sns
from pprint import pprint
import re
import test_file_load

TOOLS = ["hwpc", "codecarbon", "alumet", "scaphandre", "vjoule"]
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
        "numa_nodes_first_cpus": [0, 1],
    },
    "E5-2630L v4": {
        "architecture": "Broadwell-E",
        "vendor": "Intel",
        "generation": 6,
        "launch_date": "Q1 2016",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus": [0, 1],
    },
    "E5-2698 v4": {
        "architecture": "Broadwell-E",
        "vendor": "Intel",
        "generation": 6,
        "launch_date": "Q1 2016",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus": [0, 1],
    },
    "E5-2630 v3": {
        "architecture": "Haswell-E",
        "vendor": "Intel",
        "generation": 5,
        "launch_date": "Q3 2014",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus": [0, 1],
    },
    "Gold 5220": {
        "architecture": "Cascade Lake-SP",
        "vendor": "Intel",
        "generation": 10,
        "launch_date": "Q2 2019",
        "numa_nodes_number": "1",
        "numa_nodes_first_cpus": [0],
    },
    "Gold 5218": {
        "architecture": "Cascade Lake-SP",
        "vendor": "Intel",
        "generation": 10,
        "launch_date": "Q2 2019",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus": [0, 1],
    },
    "i7-9750H": {
        "architecture": "Coffee Lake",
        "vendor": "Intel",
        "generation": 9,
        "launch_date": "Q2 2019",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus": [0, 1],
    },
    "Silver 4314": {
        "architecture": "Ice Lake-SP",
        "vendor": "Intel",
        "generation": 10,
        "launch_date": "Q2 2021",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus": [0, 1],
    },
    "Gold 5320": {
        "architecture": "Ice Lake-SP",
        "vendor": "Intel",
        "generation": 10,
        "launch_date": "Q2 2021",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus": [0, 1],
    },
    "Gold 6126": {
        "architecture": "Skylake-SP",
        "vendor": "Intel",
        "generation": 6,
        "launch_date": "Q3 2017",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus": [0, 1],
    },
    "Gold 6130": {
        "architecture": "Skylake-SP",
        "vendor": "Intel",
        "generation": 6,
        "launch_date": "Q3 2017",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus": [0, 1],
    },
    "E5-2620": {
        "architecture": "Sandy Bridge-EP",
        "vendor": "Intel",
        "generation": 3,
        "launch_date": "Q1 2012",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus": [0, 1],
    },
    "E5-2630": {
        "architecture": "Sandy Bridge-EP",
        "vendor": "Intel",
        "generation": 3,
        "launch_date": "Q1 2012",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus": [0, 1],
    },
    "E5-2630L": {
        "architecture": "Sandy Bridge-EP",
        "vendor": "Intel",
        "generation": 3,
        "launch_date": "Q1 2012",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus": [0, 1],
    },
    "E5-2660": {
        "architecture": "Sandy Bridge-EP",
        "vendor": "Intel",
        "generation": 3,
        "launch_date": "Q1 2012",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus": [0, 1],
    },
    "X5670": {
        "architecture": "Westmere-EP",
        "vendor": "Intel",
        "generation": 1,
        "launch_date": "Q1 2010",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus": [0, 1],
    },
    "7301": {
        "architecture": "Zen",
        "vendor": "AMD",
        "generation": 1,
        "launch_date": "Q2 2017",
        "numa_nodes_number": "8",
        "numa_nodes_first_cpus": [0, 1, 2, 3, 4, 5, 6, 7],
    },
    "7352": {
        "architecture": "Zen 2",
        "vendor": "AMD",
        "generation": 2,
        "launch_date": "Q3 2019",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus": [0, 1],
    },
    "7452": {
        "architecture": "Zen 2",
        "vendor": "AMD",
        "generation": 2,
        "launch_date": "Q3 2019",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus": [0, 1],
    },
    "7642": {
        "architecture": "Zen 2",
        "vendor": "AMD",
        "generation": 2,
        "launch_date": "Q3 2019",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus": [0, 1],
    },
    "7742": {
        "architecture": "Zen 2",
        "vendor": "AMD",
        "generation": 2,
        "launch_date": "Q3 2019",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus": [0, 1],
    },
    "250": {
        "architecture": "Opteron",
        "vendor": "AMD",
        "generation": 1,
        "launch_date": "Q4 2004",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus": [0, 1],
    },
    "99xx": {
        "architecture": "ThunderX2",
        "vendor": "Cavium",
        "generation": 1,
        "launch_date": "Q2 2016",
        "numa_nodes_number": "2",
        "numa_nodes_first_cpus": [0, 1],
    },
}


def main(batch_identifier=""):
    print("Starting")
    test_file_load.test_all_files(
        results_dir="../data/ubuntu2404nfs-6.8-6.d/results-ubuntu2404nfs-6.8-6.d/rennes/parasilo/parasilo-24",
        nb_core=32,
        nb_ops=25_000,
    )

    inventories_directory = (
        f"../data/{batch_identifier}.d/inventories-{batch_identifier}.d"
    )
    results_directory = f"../data/{batch_identifier}.d/results-{batch_identifier}.d"
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

    print("Alumet frequency", alumet_frequency.describe())
    print("Alumet columns", alumet_frequency.columns)
    print("Perf columns", perf_frequency.columns)
    perf_and_alumet = perf_frequency.sql("SELECT * FROM self WHERE tool = 'alumet'")

    perf_and_alumet=perf_and_alumet.join(
            other=alumet_frequency,
            left_on=["node", "g5k_cluster", "frequency", "iteration"],
            right_on=["node", "g5k_cluster", "frequency", "iteration"],
            how="left",
            validate="1:1"
            )
    print("Joined perf and alumet", perf_and_alumet.describe())

    baseline_consumptions = load.load_baseline(
        batch_identifier=batch_identifier, results_directory=results_directory
    )

    baseline_consumptions = baseline_consumptions.sql(
        """SELECT 
                g5k_cluster, 
                floor(average_temperature / 5.0)*5.0 as range_temperature_low, 
                floor(average_temperature / 5.0)*5.0 + 5.0 as range_temperature_high,
                avg(pkg) as average_pkg, 
                avg(ram) as average_ram 
            FROM 
                self 
            GROUP BY 
                g5k_cluster,
                floor(average_temperature / 5.0)*5.0,
            ORDER BY
                g5k_cluster,
         """
    )
    node = "parasilo-24"
    separator = "-"
    cluster = node.split(separator)[0]
    temperature = 53.4
    print(
        f"Average consumptions of cluster containing {node} : ",
        baseline_consumptions.sql(
            f"""SELECT g5k_cluster, range_temperature_high, range_temperature_low, average_pkg, average_ram 
              FROM self 
              WHERE g5k_cluster = '{cluster}'
              """
        ),
    )
    print(
        f"Average consumptions of cluster containing {node} at 50°C : ",
        baseline_consumptions.sql(
            f"""
             SELECT 
                 g5k_cluster, 
                 average_pkg, 
                 average_ram 
             FROM self 
             WHERE 
                 g5k_cluster = '{cluster}'
               AND {temperature} between range_temperature_low and range_temperature_high """
        ),
    )
    sns.scatterplot(
        data=baseline_consumptions, x="average_temperature", y="pkg", hue="g5k_cluster"
    )
    plt.show()

    # TODO
    # 1 Manque de référence, raisonnement et méthodologie
    # TODO
    ## a. Recherche de consensus et comparaison des approches
    # TODO
    ## b. Inventaire des outils et leurs caractéristiques
    # TODO
    #### Table 1.b.1 Tableau des outils, approche, langage, philosophie, stade, couverture matériel

    # TODO
    # 2 Quelle influence de l'environnement sur les outils étudiés ?
    # TODO
    ## a. Paramètres d'environnement
    # TODO
    ### i. Hardware
    # TODO
    ### ii. Distribution & kernel
    # TODO
    ### iii. Governor
    # TODO
    ### iv. Turbo-boost
    # TODO
    #### v. Pinning ?
    # TODO
    ## b. Critères évalués
    # TODO
    ### i. Coefficient de variation
    # TODO
    ### ii. Déployabilité

    # TODO
    # 3 Quelle influence de la fréquence de mesure sur les outils étudiés ?
    # TODO
    ## a. Changes in source code
    # TODO
    ## b. Référence
    # TODO
    ## c. Fréquence atteinte
    # TODO
    ### i. Critères évalués
    # TODO
    ### ii. Fréquence atteinte
    # DONE
    #### Figure 3.a.ii.1 (lineplot f(target_frequency) = reached_frequency + optionnel : distrib interval ?
    target_vs_reached_frequency(
        hwpc_frequency, [1, 10, 100, 1000], {"tool": "hwpc", "unit": "milliseconds"}
    )
    target_vs_reached_frequency(
        codecarbon_frequency,
        [1, 10, 100, 1000],
        {"tool": "codecarbon", "unit": "seconds"},
    )
    target_vs_reached_frequency(
        alumet_frequency, [1, 10, 100, 1000], {"tool": "alumet", "unit": "seconds"}
    )
    target_vs_reached_frequency(
        scaphandre_frequency,
        [1, 10, 100, 1000],
        {"tool": "scaphandre", "unit": "seconds"},
    )
    target_vs_reached_frequency(
        vjoule_frequency, [1, 10, 100, 1000], {"tool": "vjoule", "unit": "seconds"}
    )
    # TODO
    #### Figure 3.a.ii.2 Heatmap ratio |(perf - tool)/((perf+tool)/2)|
    # TODO
    ## d. Influence sur la consommation énergétique
    # TODO
    ### i. Protocole de mesure de baseline

    # TODO
    # Utilisation du travail

    # TODO
    # Discussions

    # TODO
    # Conclusion


def target_vs_reached_frequency(frequency_df, frequencies, metadatada):
    target_frequencies = []
    reached_frequencies = []
    for frequency in frequencies:
        timestamps = frequency_df.sql(
            f"SELECT timestamp FROM self WHERE frequency = {frequency} AND iteration = 1 AND node = 'parasilo-24'"
        ).to_numpy()
        shapes = timestamps.shape
        timestamps = np.sort(timestamps.reshape(1, shapes[0]))
        # t2 - t1
        intervals = timestamps[0, 1:] - timestamps[0, :-1]
        print(f"Intervals {metadatada['tool']}: \n", intervals[:5])
        if metadatada["unit"] == "milliseconds":
            instant_frequencies = 1_000 / intervals
        elif metadatada["unit"] == "seconds":
            instant_frequencies = 1 / intervals
        print(f"Instant frequencies {metadatada['tool']}: \n", instant_frequencies[:5])
        reached_frequencies += instant_frequencies.tolist()
        target_frequencies += [frequency] * len(instant_frequencies)
        del timestamps
        gc.collect()

    print(
        "target_frequencies : ",
        target_frequencies[:10],
        target_frequencies[100:110],
        target_frequencies[1000:1010],
        target_frequencies[4000:4010],
    )
    print(
        "reached_frequencies : ",
        reached_frequencies[:10],
        reached_frequencies[100:110],
        reached_frequencies[1000:1010],
        reached_frequencies[4000:4010],
    )
    sns.lineplot(x=target_frequencies, y=reached_frequencies, errorbar="pi")
    sns.lineplot(x=[1, 1_000], y=[1, 1_000], label=f"f(x)=x", linestyle="dashed")
    plt.xscale("log")
    plt.xlabel("Target frequency (Hz)")
    plt.yscale("log")
    plt.ylabel("Reached frequency (Hz)")

    plt.title(f"Target vs Reached Frequencies for {metadatada['tool']}")
    plt.show()


if __name__ == "__main__":
    main(batch_identifier="ubuntu2404nfs-6.8-6")
