# Prompt for New Chat Session

Copy and paste this into a new chat to get an AI assistant up to speed on the project:

---

**I'm working on a capstone project about L-Mul (Linear-complexity Multiplication) hardware acceleration. Help me understand the project and continue working on it.**

## Project Overview

**L-Mul** is an approximate floating-point multiplication algorithm that replaces expensive mantissa multiplication with addition for efficiency. The project goal is to:
1. Implement L-Mul in hardware (Verilog)
2. Synthesize it and compare against standard IEEE BF16 multipliers
3. Prove L-Mul's efficiency (area, timing, power)
4. Apply it to neural network workloads (LSTMs, Transformers)

**Key Concept:** L-Mul approximates FP multiplication by using addition instead of full mantissa multiplication, trading slight accuracy for significant hardware efficiency.

## Essential Files to Read (in order)

**Start with these to understand the project:**

1. **`my_personal_stuff/ARCHITECTURE_GUIDE.md`** - Complete system architecture, how everything connects
2. **`my_personal_stuff/SYNTHESIS_STEP_BY_STEP.md`** - Detailed synthesis workflow guide (Steps 1-7 completed)
3. **`my_personal_stuff/SYNTHESIS_REPORT.md`** - Synthesis results and findings
4. **`synthesis/README.md`** - Synthesis folder structure and status
5. **`synthesis/synthesis_results.ipynb`** - Jupyter notebook with complete analysis and visualizations
6. **`my_personal_stuff/HARDWARE_BASICS_EXPLAINED.md`** - Hardware concepts (cells, gates, area, mapping)

**Core Implementation Files:**
- `rtl/lmul_bf16.v` - Main L-Mul Verilog implementation
- `synthesis/rtl/top_lmul_synth.v` - L-Mul synthesis wrapper
- `synthesis/rtl/bf16_mul.v` - IEEE BF16 multiplier (baseline comparison)
- `synthesis/scripts/synth_lmul.ys` - Yosys synthesis script for L-Mul
- `synthesis/scripts/sta_lmul.tcl` - OpenSTA timing analysis script

**Testing/Simulation:**
- `rtl/lmul_tester.py` - Verilog testbench runner
- `sim/` - Various accuracy and speed testing notebooks
- `demo_lmul.py` - Python demonstration of L-Mul algorithm

## Current Status

**Completed:**
- ✅ L-Mul Verilog implementation (BF16 format)
- ✅ IEEE BF16 multiplier implementation (for comparison)
- ✅ Complete synthesis workflow (Yosys + OpenSTA)
- ✅ Area comparison: **66.8% reduction** (L-Mul vs IEEE)
- ✅ Cell count comparison: **63.0% reduction**
- ✅ Timing analysis: Both designs meet 1 GHz (1.0 ns) timing constraints
- ✅ Synthesis results documented in Jupyter notebook

**Current Work:**
- Working on Week 1 task: "Power analysis and energy estimation for L-Mul vs IEEE BF16 using synthesis results"
- Project schedule includes 6 weeks of tasks (LSTM/Transformer speedup calculations, validation, etc.)

## Recent Changes (Check These!)

**Recent commits show:**
- Latest: "kept only matrix operations" (commit 628fb22)
- "add python lmul" (commit f7ecc74)
- "Update synthesis: Push to 1GHz timing and improve analysis" (commits aae854f, a5ef08f)

**Files recently modified:**
- `sim/matrix_accuracy_tester.ipynb` and `sim/matrix_speed_tester.ipynb` - Matrix operation testing
- `sim/lmul_speed_tester.ipynb` - Speed testing updates
- `synthesis/scripts/sta_*.tcl` - Timing analysis scripts updated for 1GHz
- `synthesis/scripts/synth_*.ys` - Synthesis scripts updated
- `synthesis/synthesis_results.ipynb` - Results notebook updated

**Important:** Check the `synthesis/out/` folder for latest synthesis logs, netlists, and visualizations (though these are gitignored, they may exist locally).

## Key Technical Details

- **Technology:** Nangate 45nm standard cell library
- **Synthesis Tool:** Yosys
- **Timing Tool:** OpenSTA
- **Target Clock:** 1.0 ns (1 GHz)
- **Format:** BFloat16 (1 sign, 8 exponent, 7 mantissa bits)
- **Results:** L-Mul uses 180.88 area units vs IEEE's 545.03 (66.8% reduction)

## What I Need Help With

1. **Understanding the codebase** - Get familiar with the architecture and implementation
2. **Continuing synthesis work** - Power analysis, energy estimation
3. **Future tasks** - LSTM/Transformer speedup calculations, validation
4. **Code improvements** - Any optimizations or fixes needed

**Please:**
- Read the essential files listed above to understand the project
- Check recent commits/files to see what's changed
- Ask clarifying questions if anything is unclear
- Help me proceed with the current week's task (power analysis)

---

