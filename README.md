# Power-meter Software Benchmarks Framework

## Purpose

This repository provides the framework for generating and executing benchmarks targeting multiple **power-meter software stacks**. The framework automatically adapts benchmark generation and execution to the configuration and architecture of nodes available in the **Grid5000** infrastructure.

It enables experimenters to compare different power-meter tools across a consistent set of criteria, supporting the selection of the most appropriate software for specific measurement or experimentation needs.

---

## Overview of Core Processes

1. **Node Discovery**
   The framework begins by querying the Grid5000 API to collect hardware and configuration details for all available nodes.

2. **Optional Reuse of Existing Job Metadata**
   If a `jobs.yaml` file already exists, the framework loads it to initialize and resume a previous benchmarking session.

3. **Benchmark Script Generation**
   For each node that meets the configured filters, a dedicated benchmark script is generated using the templates stored in the `/templates` directory.

4. **Distributed Job Submission via OAR**
   The generated scripts are submitted using **OAR** through SSH on the corresponding Grid5000 sites. The framework enforces a configurable maximum number of concurrently active jobs.

5. **Execution Monitoring and Result Retrieval**

   * Each job is continuously monitored until it reaches a terminal state.
   * Once completed, the associated results are fetched locally via **rsync**.
   * If retrieval fails, the job is marked as `UnknownState` for manual inspection.

6. **Result Storage**
   When all benchmark jobs for the filtered node set have finished, the resulting data is stored under the `/results.d` directory.

7. **Result Processing**
   When a job reaches a terminal state (e.g., `Terminated` or `Failed`), all relevant output files are automatically aggregated into structured CSV files. Exact formats are documented in the [`src/results`](./src/results) module.

---

## Configuration Requirements

### Environment Variables

Before running the framework, you **must** create a `.env` file to supply authentication credentials and registry information.
A template is provided as `.env.example`:

```
G5K_USERNAME="TO_BE_DEFINED"
G5K_PASSWORD="TO_BE_DEFINED"
DOCKER_HUB_USERNAME="TO_BE_DEFINED"
DOCKER_HUB_TOKEN="TO_BE_DEFINED"
```

**Instructions:**

1. Copy the template to create the actual configuration file:

   ```bash
   cp .env.example .env
   ```
2. Replace all `TO_BE_DEFINED` values with your personal credentials:

   * `G5K_USERNAME` and `G5K_PASSWORD` must reference your Grid5000 account.
   * `DOCKER_HUB_USERNAME` and `DOCKER_HUB_TOKEN` must reference valid Docker Hub credentials if pushing/pulling benchmark-related images.

The framework will not function properly until this `.env` file is correctly populated.

---

## Installation

To use the framework, clone the repository, ensure Rust and Cargo are installed, configure your environment, and build the project.

### Prerequisites

* **Rust and Cargo**
  Rust (including Cargo) is required to build the project. Install using:

  ```bash
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
  ```

  Follow the installer instructions and restart your terminal if needed.

* **Grid5000 Access and Dependencies**

  * A working **OAR** environment on the targeted Grid5000 site.
  * SSH access configured so that commands like `ssh rennes` connect to the corresponding frontend.
  * Required node-side tools are automatically deployed or assumed available depending on the target configuration.

### Clone the Repository

```bash
git clone https://github.com/powerapi-ng/benchmarking.git
cd benchmarking
```

### Build the Project

```bash
cargo build --release
```

The executable will be generated under `target/release/`.

### Running the Benchmark Framework

```bash
./target/release/benchmarking
```

Execution may be stopped and resumed at any time, provided that the `jobs.yaml` file remains present.
