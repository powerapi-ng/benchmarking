# Powermeter Software Benchmarks Framework 

## What It Does

This repository contains the source code for generating and running benchmarks for several **power-meter softwares**. These benchmarks are designed to adapt to the configuration and architecture of underlying nodes in the **Grid5000** infrastructure. 

### Key Processes:

1. **Gather Node Information**: The benchmarks start by scraping the Grid5000 API to collect details about all available nodes.
2. **Reuse Existing Job List (Optional)**: If a `jobs.yaml` file exists, the tool can leverage it to initialize the job list.
3. **Generate Bash Scripts**: For each filtered node, a custom bash script is generated using templates located in the `/templates` directory.
4. **Submit Jobs via OAR**: The generated scripts are submitted to corresponding nodes through SSH using **OAR**, ensuring that no more than `N` jobs are simultaneously active.
5. **Monitor and Collect Results**:
    - The status of each submitted job is tracked until it completes (either successfully or in a failed state).
    - Upon completion, **rsync** is used to retrieve the results files locally. If the retrieval fails, the job’s state is marked as `UnknownState` for manual review.
6. **Store Results**: Once all filtered nodes have completed their benchmark jobs, the benchmarking process concludes, and all result files are stored in the `/results.d` directory.
7. **Processe Results**: Once a job reaches a terminal state (likely Terminated or Failed), aggregates all files into proper CSVs. Formats can be found in [the results source code](./src/results), structures provides it.

## Why it exists.

This benchmarks aim at comparing different power-meter softwares on several selected criteria and serve as guideling for experimenters to choose the most suitable tool.

## Installation

To use this repository, you need to clone it locally, ensure you have Cargo installed, and then compile and run the project. Follow the steps below:

### Prerequisites

Before proceeding, make sure your system meets the following requirements:

- **Rust and Cargo**: Install Rust (which includes Cargo, Rust’s package manager and build system). If Rust is not installed, follow the instructions below:
    1. Download and install Rust by running:
     ```bash
     curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
     ```
    2. Follow the on-screen instructions to complete the installation.
    3. Add Cargo to your PATH (usually done by Rust installer automatically). Restart your terminal if necessary.

- **Dependencies**:
  - A working installation of **OAR** on your Grid5000 node (or appropriate access).
  - SSH access configured to interact with the Grid5000 nodes (for example, `ssh rennes` ran locally shall connect you to the rennes' frontend).

### Clone the Repository

Clone this repository to your local machine:

```bash
git clone https://github.com/powerapi-ng/benchmarking.git
cd benchmarking
```

### Build the Project

Compile the project using Cargo:

```bash
cargo build --release
```

This will produce an optimized executable located in the `target/release/` directory.

### Run the Project

Execute the compiled program:

```bash
./target/release/benchmarking
```
  
You may stop the execution of the process and start it again later, as long as the "jobs.yaml" file is present so the necessary information can be retrieved.  

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

