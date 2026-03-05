# LMUL Accelerator gem5 Simulation

gem5 integration for simulating the LMUL (Logarithmic Multiplication) BF16 hardware accelerator and comparing it to native IEEE BF16 on the CPU.

## Overview

This directory provides:
- A custom gem5 device model for the LMUL accelerator
- Configs and benchmarks to run matrix multiply with the accelerator or on the CPU
- Scripts to compare both runs and validate correctness

**Setup and workflow:** Use **workflow.ipynb** for the full flow (clone gem5, install model, build benchmark, run comparisons, validate, and plot). The notebook documents configurable parameters for each step.

## Directory Structure

```
gem5-sim/
├── README.md                 # This file
├── configs/                  # System config (lmul_system.py)
├── models/                   # gem5 accelerator model (C++ + Python + SConscript)
├── benchmarks/               # Benchmarks
│   ├── matrix_multiply/      # BF16 matrix-multiply (matrix_multiply.c, matrix_multiply_no_printf.c, Makefile)
│   └── read_accelerator_results.c
├── scripts/                  # Setup, run, and analysis scripts
│   ├── install_model.sh      # Install accelerator into gem5 and build
│   ├── test_accelerator.sh   # Verify build
│   ├── run_simulation.sh     # Single run (LMUL or IEEE)
│   ├── compare_lmul_vs_ieee.sh   # Run both + compare metrics + correctness
│   ├── compare_metrics.py    # Build performance_comparison_<size>.txt
│   ├── validate_result_against_reference.py  # Correctness vs software reference
│   ├── extract_stats.py      # Dump stats from one stats.txt
│   ├── check_compatibility.sh
│   ├── check_gem5_dependencies.sh
│   ├── scons_with_zlib.sh    # Used by install_model.sh
│   └── verify_setup.sh       # Lightweight environment sanity check
├── utils/                    # Python utilities for parsing + plotting results
│   └── utils.py
├── lmul_vs_ieee_comparison/  # Example output from compare_lmul_vs_ieee.sh
│   ├── performance_comparison_*.txt
│   ├── lmul/                 # LMUL accelerator run stats + logs
│   └── ieee/                 # IEEE CPU run stats + logs
├── infra/                    # Cluster/container helpers (e.g., Expanse, Singularity)
│   ├── Singularity.def
│   └── requirements.txt
└── workflow.ipynb            # End-to-end setup and LMUL vs IEEE workflow (start here)
```

---

## Prerequisites

- **RAM**: 32GB+ recommended (16GB minimum; linker may fail with less).
- **Disk**: 50GB+ free.
- **OS**: Linux (e.g. Ubuntu 20.04+), x86_64.
- **Software**: `git`, `python3` (3.6+), `scons` (e.g. `pip install scons`), and for building benchmarks: **ARM cross-compiler** `gcc-arm-linux-gnueabihf` (`sudo apt-get install gcc-arm-linux-gnueabihf`).

---

## Setup and Workflow

**Run the notebook** `workflow.ipynb` (from the repo root or with `gem5-sim/` as the working directory). It walks through:

1. Cloning gem5 (if missing) and checking out `stable` + installing Python requirements  
2. Optional system/dependency checks  
3. Installing the LMUL model into gem5 and building gem5  
4. Building the BF16 matrix-multiply benchmark  
5. Running LMUL vs IEEE comparisons for configurable sizes and options  
6. Validating outputs (when extraction is enabled)  
7. Parsing and plotting performance comparison tables  

Each section in the notebook describes the **configurable parameters** for that step (matrix sizes, PE array, CPU model, clocks, output extraction, etc.). For one-off commands and script options, see the notebook cells and the script `--help` (e.g. `./gem5-sim/scripts/compare_lmul_vs_ieee.sh --help`).

---

## Understanding Output

- **stats.txt** (per run): `sim_seconds`, `system.cpu.numCycles`, `system.cpu.committedInsts`, CPI, IPC, DRAM energy, and accelerator stats (e.g. `system.lmul_accel.totalcycles`, `totalops`).
- **performance_comparison_\*.txt**: side-by-side LMUL vs IEEE and speedups (sim time, cycles, DRAM ratio, accelerator energy, modeled CPU energy, estimated total energy), plus cycle categorization.
- Correctness is reported when you run the comparison with output extraction enabled: the script compares each run’s output to the reference (`rtl.numpy_lmul.lmul_numpy_matmul` for LMUL, IEEE matmul for CPU).

CPU energy in the comparison report is a first-order model derived from cycle count, instruction count, and static power parameters. It does not require `system.cpu.power_model.dynamicPower` and avoids unit/path issues in gem5 power-model stats.

The IEEE path uses an optimized but still realistic software implementation: BF16 inputs are converted once to float32, matrix multiply is cache-friendly (tiled), and outputs are rounded back to BF16. This keeps the comparison "realistic LMUL accelerator vs realistic IEEE software."

---

## Energy and Clock Parameters (References)

Energy- and speed-related hyperparameters and their grounding in literature or the lack thereof:

### Accelerator (LMulAccelerator)

| Parameter | Default | Source / Notes |
|-----------|---------|----------------|
| `energy_per_op_pj` | 0.5 pJ | **Referenced.** State-of-the-art DNN accelerators report ~0.1 pJ/op (NVIDIA 16nm multi-chip DNN accelerator, 8-bit: 0.11 pJ/op; DiP systolic array: ~0.1 pJ/op). Our 0.5 pJ is a conservative estimate for BF16 matmul (higher precision than 8-bit). See [NVIDIA DNN accelerator (0.11 pJ/op, 16nm)](https://research.nvidia.com/publication/2019-06_011-pjop-032-128-tops-scalable-multi-chip-module-based-deep-neural-network), [DiP systolic array (arXiv:2412.09709)](https://arxiv.org/abs/2412.09709). |
| `dma_energy_per_byte_pj` | 0.05 pJ | **No reliable source found.** Literature reports DRAM access energy per byte as highly variable (bank activation dominates). On-chip SRAM access is on the order of 0.1 pJ/byte. Our value is a placeholder; consider calibrating to hardware if available. |
| `leakage_power_mw` | 1.0 mW | **No reliable source found.** Small systolic array (e.g. 4×4 PE); leakage scales with area. Placeholder for relative comparison. |
| `--accel-clock` | 2 GHz | **Referenced.** TPU systolic arrays operate around 1.5 GHz; modern systolic/GEMM accelerators often run 1–2+ GHz. 2 GHz is a reasonable default for a small PE array. See [TPU v1 (Jouppi et al.)](https://dl.acm.org/doi/10.1145/3079856.3080246), [DiP (arXiv:2412.09709)](https://arxiv.org/abs/2412.09709). |

### CPU (first-order model)

| Parameter | Default | Source / Notes |
|-----------|---------|----------------|
| `--cpu-dyn-energy-per-cycle-pj` | 500 pJ | **No specific hardware source.** First-order model for gem5 TimingSimpleCPU. ARM Cortex-M0 studies report ~170 µW/MHz; at 2 GHz that implies order-of-magnitude hundreds of pJ per effective cycle depending on activity. 500 pJ is a plausible placeholder for a simple in-order core. |
| `--cpu-dyn-energy-per-inst-pj` | 50 pJ | **No specific hardware source.** Extra energy attributed per committed instruction (e.g. pipeline overhead). Calibrate to target CPU if needed. |
| `--cpu-static-power-mw` | 200 mW | **No specific hardware source.** Placeholder for static/leakage power of a small CPU core. |

### Summary

- **With references:** `energy_per_op_pj`, `--accel-clock`
- **Without references (placeholder):** `dma_energy_per_byte_pj`, `leakage_power_mw`, all CPU power parameters

To calibrate parameters for a specific target, consult vendor datasheets or measured power/energy studies for your CPU and accelerator.

---

## Troubleshooting

| Problem | What to do |
|--------|------------|
| **zlib missing** | `./gem5-sim/scripts/check_zlib.sh`; install with `sudo apt-get install zlib1g-dev`. |
| **Linker OOM** | Build on a machine with 32GB+ RAM. |
| **Syscall 403** | Use the no-printf benchmark: `make matrix_multiply_no_printf.arm` in `gem5-sim/benchmarks/matrix_multiply`. |
| **Empty stats.txt** | Check `lmul_vs_ieee_comparison/lmul/simulation.log` (or `ieee/`) for errors; ensure the benchmark binary exists. |
| **Permission denied** | `chmod +x gem5-sim/scripts/*.sh` |

---

## Quick reference

- **Full workflow:** Open and run `workflow.ipynb` (see notebook for all parameters).
- **Single test run (after setup):** `./gem5-sim/scripts/run_simulation.sh --test`
- **One comparison (from repo root):** `./gem5-sim/scripts/compare_lmul_vs_ieee.sh --size 64` then `cat gem5-sim/lmul_vs_ieee_comparison/performance_comparison_64.txt`
