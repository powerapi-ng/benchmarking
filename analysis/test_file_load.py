import polars as pl


def test_all_files(results_dir="", nb_core=0, nb_ops=0):
    describe_file(
        separator=",", path=f"{results_dir}/frequency_1_codecarbon_and_perf.csv"
    )
    describe_file(
        separator=",", path=f"{results_dir}/frequency_10_codecarbon_and_perf.csv"
    )
    describe_file(
        separator=",", path=f"{results_dir}/frequency_100_codecarbon_and_perf.csv"
    )
    describe_file(
        separator=",", path=f"{results_dir}/frequency_1000_codecarbon_and_perf.csv"
    )
    describe_file(path=f"{results_dir}/frequency_1_vjoule_and_perf.csv")
    describe_file(path=f"{results_dir}/frequency_10_vjoule_and_perf.csv")
    describe_file(path=f"{results_dir}/frequency_100_vjoule_and_perf.csv")
    describe_file(path=f"{results_dir}/frequency_1000_vjoule_and_perf.csv")
    describe_file(path=f"{results_dir}/frequency_1_scaphandre_and_perf.csv")
    describe_file(path=f"{results_dir}/frequency_10_scaphandre_and_perf.csv")
    describe_file(path=f"{results_dir}/frequency_100_scaphandre_and_perf.csv")
    describe_file(path=f"{results_dir}/frequency_1000_scaphandre_and_perf.csv")
    describe_file(path=f"{results_dir}/frequency_1_alumet_and_perf.csv")
    describe_file(path=f"{results_dir}/frequency_10_alumet_and_perf.csv")
    describe_file(path=f"{results_dir}/frequency_100_alumet_and_perf.csv")
    describe_file(path=f"{results_dir}/frequency_1000_alumet_and_perf.csv")
    describe_file(path=f"{results_dir}/frequency_1_hwpc_and_perf.csv")
    describe_file(path=f"{results_dir}/frequency_10_hwpc_and_perf.csv")
    describe_file(path=f"{results_dir}/frequency_100_hwpc_and_perf.csv")
    describe_file(path=f"{results_dir}/frequency_1000_hwpc_and_perf.csv")
    describe_file(path=f"{results_dir}/temperatures_frequency_1_perf_and_vjoule.csv")
    describe_file(path=f"{results_dir}/temperatures_frequency_10_perf_and_vjoule.csv")
    describe_file(path=f"{results_dir}/temperatures_frequency_100_perf_and_vjoule.csv")
    describe_file(path=f"{results_dir}/temperatures_frequency_1000_perf_and_vjoule.csv")
    describe_file(
        path=f"{results_dir}/temperatures_frequency_1_perf_and_scaphandre.csv"
    )
    describe_file(
        path=f"{results_dir}/temperatures_frequency_10_perf_and_scaphandre.csv"
    )
    describe_file(
        path=f"{results_dir}/temperatures_frequency_100_perf_and_scaphandre.csv"
    )
    describe_file(
        path=f"{results_dir}/temperatures_frequency_1000_perf_and_scaphandre.csv"
    )
    describe_file(
        path=f"{results_dir}/temperatures_frequency_1_perf_and_codecarbon.csv"
    )
    describe_file(
        path=f"{results_dir}/temperatures_frequency_10_perf_and_codecarbon.csv"
    )
    describe_file(
        path=f"{results_dir}/temperatures_frequency_100_perf_and_codecarbon.csv"
    )
    describe_file(
        path=f"{results_dir}/temperatures_frequency_1000_perf_and_codecarbon.csv"
    )
    describe_file(path=f"{results_dir}/temperatures_frequency_1_perf_and_alumet.csv")
    describe_file(path=f"{results_dir}/temperatures_frequency_10_perf_and_alumet.csv")
    describe_file(path=f"{results_dir}/temperatures_frequency_100_perf_and_alumet.csv")
    describe_file(path=f"{results_dir}/temperatures_frequency_1000_perf_and_alumet.csv")
    describe_file(path=f"{results_dir}/temperatures_frequency_1_perf_and_hwpc.csv")
    describe_file(path=f"{results_dir}/temperatures_frequency_10_perf_and_hwpc.csv")
    describe_file(path=f"{results_dir}/temperatures_frequency_100_perf_and_hwpc.csv")
    describe_file(path=f"{results_dir}/temperatures_frequency_1000_perf_and_hwpc.csv")
    describe_file(path=f"{results_dir}/baseline_consumption.csv")
    describe_file(path=f"{results_dir}/alumet_and_perf_{nb_core}_{nb_ops}.csv")
    describe_file(path=f"{results_dir}/perf_and_alumet_{nb_core}_{nb_ops}.csv")
    describe_file(
        path=f"{results_dir}/perf_and_alumet_{nb_core}_{nb_ops}_temperatures.csv"
    )
    describe_file(path=f"{results_dir}/hwpc_and_perf_{nb_core}_{nb_ops}.csv")
    describe_file(path=f"{results_dir}/perf_and_hwpc_{nb_core}_{nb_ops}.csv")
    describe_file(
        path=f"{results_dir}/perf_and_hwpc_{nb_core}_{nb_ops}_temperatures.csv"
    )
    describe_file(path=f"{results_dir}/codecarbon_and_perf_{nb_core}_{nb_ops}.csv")
    describe_file(path=f"{results_dir}/perf_and_codecarbon_{nb_core}_{nb_ops}.csv")
    describe_file(
        path=f"{results_dir}/perf_and_codecarbon_{nb_core}_{nb_ops}_temperatures.csv"
    )
    describe_file(path=f"{results_dir}/vjoule_and_perf_{nb_core}_{nb_ops}.csv")
    describe_file(path=f"{results_dir}/perf_and_vjoule_{nb_core}_{nb_ops}.csv")
    describe_file(
        path=f"{results_dir}/perf_and_vjoule_{nb_core}_{nb_ops}_temperatures.csv"
    )
    describe_file(path=f"{results_dir}/scaphandre_and_perf_{nb_core}_{nb_ops}.csv")
    describe_file(path=f"{results_dir}/perf_and_scaphandre_{nb_core}_{nb_ops}.csv")
    describe_file(
        path=f"{results_dir}/perf_and_scaphandre_{nb_core}_{nb_ops}_temperatures.csv"
    )


def describe_file(separator=",", path=""):
    print("Testing file" + path)
    try:
        df = pl.read_csv(source=path, separator=separator)
        with pl.Config(tbl_cols=-1):
            print(df.describe())
        print("[OK] : File " + path + " ok")
    except Exception as e:
        print("[KO] : File " + path + " failed : " + str(e))
