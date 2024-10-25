# PowerAPI Benchmark Procedure

This project benchmarks **PowerAPI** measurements and **RAPL** (using performance events) to evaluate variability. The procedures are designed for reproducibility, ensuring consistent results across future versions of PowerAPI, RAPL, and related dependencies.

## Overview

The benchmark involves automating several tasks, including inventory management, job creation and submission, monitoring, and results aggregation. The process is run across the G5K nodes and consists of a series of sequential steps:

1. **Inventory Update**: Create or update a G5K node inventory with metadata (accessible via API), which is subsequently used in further steps.
2. **Job Generation and Submission**: For each node, generate a job submission and save it in JSON format. Each job file includes:
     - Paths to generated bash script for the specific node
     - Metadata file path
     - Result directory path
     - The `OAR_JOB_ID` of the submitted job and its state.
     - The job's site information.
3. **Job Monitoring**:  
    - Loop until all jobs reach a “terminal state” ([Finishing | Terminated | Failed]).
    - For jobs still running or waiting ([Waiting, Launching, Running]), check their status via `oarstat` and update accordingly.
4. **Results Aggregation** (To Be Implemented): Aggregate raw results into a centralized location.
5. **Report Generation** (To Be Implemented): Create a summary report from aggregated results.

Steps 4 and 5 are planned but not yet implemented.

--- 

## Benchmark Execution Details

The benchmark approach is designed to maximize efficiency and resource utilization by reserving each node only once per benchmark run. The generated scripts handle all necessary steps for each measurement.

### Measurement Collection Workflow

1. **Performance Event Measurements**:
    - Execute `perf` events for `NB_ITER` iterations with: `perf event -a -o /tmp/perf_${i}.stat -e ${PROCESSOR_CORRESPONDING_EVENTS} stress-ng --cpu ${NB_CPU} --cpu-ops ${NB_CPU_OPS}`
     - **PROCESSOR_CORRESPONDING_EVENTS** are selected based on a hardcoded mapping.
     - **NB_CPU** iterates through a list from 1 to the maximum CPU count.
     - **NB_CPU_OPS** is processed to meet two conditions:
        - Cumulative `stress-ng` run times stay below the reservation time.
        - Each measurement uses a consistent operation count.

2. **Aggregation of `perf` Results**:
    - Once `${NB_ITER}` iterations are complete, aggregate `perf_${i}.stat` files into a single `perf_${NB_CPU}_${NB_CPU_OPS}.csv` stored on NFS.

3. **HWPC Sensor Measurements**:
    - Execute HWPC measurements, storing the data in CSV format similar to `perf`.

4. **SmartWatts Post-Mortem Processing**:
    - Generate PowerReports from HWPC data in post-mortem mode.

5. **Final Aggregation**:
    - Consolidate `[HWPC|SMARTWATTS|PERF]_[NB_CPU]_[NB_CPU_LOAD].csv` files on the NFS storage.

### Key Considerations

- Using **SmartWatts in post-mortem mode** aligns with the variability measurement goals.
- **Storage Constraints**: NFS storage limits are set at 25GB per site. With uniform node distribution, this equates to an approximate maximum file size of 3.32 MB per aggregated result file, which is manageable.
- **Run Repetition**: Each `stress-ng` run will be executed **30 times** to establish statistical robustness.

---

# Tips G5k

- To execute a script on a given list of servers (chifflot) during 4 hours max: 

```
oarsub -l {"host in ('chifflot-1.lille.grid5000.fr','chifflot-4.lille.grid5000.fr','chifflot-5.lille.grid5000.fr')"}/host=1,walltime=4 ./my_script.sh
```

- To check usage policy: 

```
usagepolicycheck -t
```

- To install docker : 

```
g5k-setup-docker -t
``` 

- To check reservations at Lille site (with authentification): 

