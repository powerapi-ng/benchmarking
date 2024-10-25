# Hypotheses

This document tracks hypotheses to be validated in the benchmarking process, organized by **Tested** and **To Be Tested** sections. Each hypothesis includes the rationale and expected outcome.

## To Be Tested

1. **Statistical Sufficiency of 30 Iterations**
    - **Hypothesis**: Running 30 iterations per measurement will yield sufficient data for statistical analysis of energy results, ensuring reliability in evaluating variability.
    - **Expected Outcome**: Consistent patterns emerge within 30 iterations, showing clear trends in energy measurements without requiring additional runs.
    - **Rationale**: 30 iterations are often a threshold for normal distribution in statistical sampling.

2. **Validity of `NB_CPU_OPS` Values `[10^7, 10^8, 10^9]`**
    - **Hypothesis**: Using `NB_CPU_OPS` values of `[10^7, 10^8, 10^9]` allows all measurements to complete within the allocated G5K reservation time.
    - **Expected Outcome**: These values will yield consistent, complete data sets without running into time constraints.
    - **Rationale**: Choosing `NB_CPU_OPS` values that finish within the reservation time maximizes efficiency and resource usage while keeping results comprehensive.

3. **Post-Mortem Mode Accuracy for SmartWatts**
    - **Hypothesis**: Running SmartWatts in post-mortem mode will still produce accurate energy measurement results, suitable for evaluating the precision of PowerAPI tools.
    - **Expected Outcome**: SmartWatts post-mortem results closely match real-time energy data.
    - **Rationale**: Save another set of stress-ng would be intesting. No proof of difference in precision have been demonstrated between CSV and MongoDB output mode for HWPC Sensor.

4. **Feasibility of Storing Results on NFS**
    - **Hypothesis**: The average size of each aggregated results file will be under 3.32 MB, allowing for efficient storage within the 25GB per site NFS limit.
    - **Expected Outcome**: Average file size per node stays within the 3.32 MB limit, avoiding storage issues.
    - **Rationale**: Storage constraints on NFS necessitate a size estimation for scalability.

5. **Parallel Execution of HWPC Sensor & Perf**
    - **Hypothesis**: HWPC Sensor and `perf` measurements can run concurrently on the same `stress-ng` process without interference or measurement degradation.
    - **Expected Outcome**: Both HWPC and `perf` output valid data when run in parallel, with no notable interference.
    - **Rationale**: Efficient benchmarking may require concurrent measurements to maximize data collection without extending reservation times.

---

## Tested Hypotheses
