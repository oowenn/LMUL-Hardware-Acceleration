# LMUL Hardware Acceleration - Project Exploration

**Last Updated:** November 25, 2025 (Updated after git pull)  
**Purpose:** Comprehensive overview of current project state and recent developments

---

## 🔄 Recent Changes (Latest Git Pull)

### New Files Added:
1. **`sim/matrix_accuracy_tester.ipynb`** ⭐ NEW
   - Comprehensive matrix multiplication accuracy testing
   - Compares 6 different implementations (NumPy standard, PyTorch standard, NumPy LMUL matrix/scalar, PyTorch LMUL matrix/scalar)
   - Generates heat matrix showing pairwise mismatch percentages
   - Tests 100 random 20×20 matrix multiplications

2. **`sim/matrix_speed_tester.ipynb`** ⭐ NEW
   - Matrix multiplication performance benchmarking
   - Tests same 6 implementations across multiple matrix sizes (10×10 to 200×200)
   - Log-log plots showing time per operation vs matrix size
   - Helps understand scaling behavior of different implementations

### Modified Files:
1. **`rtl/numpy_lmul.py`** - Enhanced
   - Added `lmul_numpy_matmul()` function for matrix multiplication
   - Function signature: `lmul_numpy_matmul(a_bf16: np.ndarray, b_bf16: np.ndarray) -> np.ndarray`
   - Uses broadcasting to compute (m,n) @ (n,p) using element-wise LMUL
   - Converts products to float before summing to avoid BF16 overflow

2. **`rtl/pytorch_lmul.py`** - Enhanced
   - Added `lmul_torch_matmul()` function for matrix multiplication
   - Function signature: `lmul_torch_matmul(a_bf16: torch.Tensor, b_bf16: torch.Tensor) -> torch.Tensor`
   - Supports batched matrix operations for neural networks
   - Same approach as NumPy version but using PyTorch tensors

3. **`sim/lmul_accuracy_tester.ipynb`** - Updated
   - (Changes to be verified when notebook is run)

4. **`sim/lmul_speed_tester.ipynb`** - Updated
   - (Changes to be verified when notebook is run)

### Key Improvements:
- **Matrix Multiplication Support**: Both NumPy and PyTorch now support full matrix multiplication using LMUL, not just element-wise operations
- **Comprehensive Testing**: New notebooks provide thorough accuracy and speed testing for matrix operations
- **Neural Network Ready**: Matrix multiplication is the core operation in neural networks, so this enables more realistic testing

---

---

## 🎯 Project Overview

This is a UCSD capstone project implementing the **L-Mul (Linear-complexity Multiplication)** algorithm - a faster, more energy-efficient alternative to standard IEEE floating-point multiplication for ML inference.

### Core Innovation
- **Traditional Multiplication**: O(n²) complexity with mantissa multiplication
- **L-Mul**: O(n) complexity by replacing multiplication with addition
- **Trade-off**: 67-99% reduction in area/power/delay for only ~0.1-0.5% accuracy loss

---

## 📁 Current Repository Structure

```
LMUL-Hardware-Acceleration/
├── rtl/                         # Hardware RTL (Register Transfer Level)
│   ├── lmul_bf16.v             # ✅ Core LMUL hardware (Verilog)
│   ├── top_lmul.v              # ✅ Top-level wrapper module
│   ├── simple_function.v       # Simple test module
│   ├── py_lmul.py              # ✅ Python implementation of LMUL
│   ├── numpy_lmul.py           # ✅ NEW: Vectorized NumPy implementation
│   ├── pytorch_lmul.py         # ✅ NEW: PyTorch implementation with autograd
│   └── lmul_tester.py          # ✅ Enhanced batch testing (cycle counting, parallel)
│
├── sim/                         # Simulation & Testing
│   ├── lmul_accuracy_tester.ipynb   # ✅ Enhanced: 10K tests, multiple implementations
│   ├── lmul_speed_tester.ipynb      # ✅ Performance benchmarks (updated)
│   ├── matrix_accuracy_tester.ipynb # ✅ NEW: Matrix multiplication accuracy testing
│   ├── matrix_speed_tester.ipynb    # ✅ NEW: Matrix multiplication speed benchmarking
│   └── test_simple.ipynb            # Basic Verilog test example
│
├── NNs/                         # Neural Network Testing (renamed from mnistmlptest/)
│   ├── lmul_mlp_mnist.ipynb    # ✅ MNIST MLP with LMUL (97% accuracy!)
│   ├── LSTM_test.ipynb         # ✅ NEW: LSTM with LMUL (MNIST, Fashion-MNIST, KMNIST)
│   ├── LSTM_LMUL_LLM.ipynb     # ✅ NEW: Tiny LLM with LSTM+LMUL
│   ├── lmul_nn_funcs.py        # ✅ NEW: LSTM-specific LMUL functions
│   ├── archive_lmul.ipynb       # Archived experiments
│   ├── LSTM_Verilog/           # ✅ NEW: Hardware validation for LSTM operations
│   │   ├── LMUL_LSTM.v         # LMUL unit for LSTM
│   │   ├── FP32.v              # FP32 reference for comparison
│   │   ├── TB_WX.v             # Testbench for matrix-vector multiplication
│   │   └── lstm_verilog_tester.ipynb  # Hardware validation notebook
│   ├── MNIST/                   # Dataset directories
│   ├── FashionMNIST/
│   └── KMNIST/
│
├── utils/                       # ✅ NEW: Utility functions
│   └── floats.py               # BF16 conversion utilities (NumPy & PyTorch)
│
├── report/                      # ✅ NEW: Project report
│   ├── report.tex              # LaTeX source
│   └── report.pdf              # Compiled report
│
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container setup
└── README.md                    # Basic setup instructions
```

---

## ✅ What's Working (Verified)

### 1. **Python LMUL Implementation** (`rtl/py_lmul.py`)
- **Status**: ✅ Working correctly
- **Function**: `lmul(a_bf16: int, b_bf16: int) -> int`
- **Format**: BF16 (BFloat16: 1 sign + 8 exp + 7 mantissa bits)
- **Algorithm**:
  ```
  1. Extract sign, exponent, mantissa from both inputs
  2. Check for zero/subnormal cases → return 0
  3. ADD the 15-bit fields (exp+mant) with offset: a_fld + b_fld + 0x4080
  4. Use carry bits to determine overflow/underflow/normal
  5. XOR signs for output sign
  6. Return packed BF16 result
  ```
- **Key Insight**: This replaces expensive mantissa multiplication with simple addition!

### 2. **Hardware LMUL Implementation** (`rtl/lmul_bf16.v`)
- **Status**: ✅ Working correctly (verified by accuracy tester)
- **Module**: `lmul_bf16` with ready/valid handshake protocol
- **Latency**: 1 cycle (combinational logic + output register)
- **Interface**:
  - Input: `i_a[15:0]`, `i_b[15:0]`, `i_valid`, `o_ready`
  - Output: `o_p[15:0]`, `o_valid`, `i_ready`
- **Features**:
  - Handles zero/subnormal inputs
  - Saturates on overflow
  - Proper signed zero handling

### 3. **Batch Testing Framework** (`rtl/lmul_tester.py`)
- **Status**: ✅ Enhanced with new features
- **Classes**: 
  - `BatchLMULTester`: Original batch testing with cycle counting
  - `BatchLMULTesterParallel`: NEW - Parallel testing with multiple DUTs
- **Purpose**: Test multiple operations in single simulation run
- **Process**:
  1. Generates Verilog testbench dynamically
  2. Compiles with iverilog
  3. Runs with vvp simulator
  4. Parses results back to Python
- **New Features**:
  - Cycle counting and performance metrics
  - Returns cycle counts along with results
  - Parallel testing capability for throughput analysis
- **Performance**: Can test 1000 operations in ~30ms

### 4. **Accuracy Verification** (`sim/lmul_accuracy_tester.ipynb`)
- **Status**: ✅ Enhanced - Comprehensive validation
- **Result**: All implementations match Hardware LMUL output exactly!
- **Test**: 10,000 random BF16 multiplications (expanded from 10)
- **Tested Implementations**:
  - Hardware (Verilog simulation)
  - Python reference (`py_lmul.py`)
  - NumPy vectorized (`numpy_lmul.py`)
  - PyTorch vectorized (`pytorch_lmul.py`)
- **Results** (from report):
  - Verilog vs Python LMUL: 0.00% difference (bit-exact match)
  - LMUL vs FP32: 1.51% average error (expected for BF16 approximation)

### 5. **MNIST MLP with LMUL** (`NNs/lmul_mlp_mnist.ipynb`)
- **Status**: ✅ Working (97% accuracy!)
- **Architecture**: 784 → 128 (ReLU) → 10 (softmax)
- **Training**: Standard backprop with exact math (2-5 epochs)
- **Inference**: Two modes:
  - Baseline (standard multiplication): 97.02%
  - LMUL (approximate multiplication): 97.01%
- **Result**: **Only 0.01% accuracy loss!** 🎉
- **Note**: Uses PyTorch-level LMUL, not hardware simulation

### 6. **LSTM with LMUL** (`NNs/LSTM_test.ipynb`) ⭐ NEW
- **Status**: ✅ Working - Extended to multiple architectures!
- **Architectures Tested**:
  - LSTM for MNIST classification
  - LSTM for Fashion-MNIST classification
  - LSTM for KMNIST classification
- **Results**:
  - **MNIST**: 97.72% baseline vs **97.75% LMUL** (slightly better!)
  - **Fashion-MNIST**: 86.13% baseline vs 85.01% LMUL (1.12% drop)
  - **KMNIST**: Similar results showing minimal accuracy loss
- **Key Finding**: LSTM requires bias correction (+5% adjustment) due to error accumulation
- **Implementation**: Uses `lmul_nn_funcs.py` with bias correction term
- **Note**: LSTM has more multiplications per forward pass, so error accumulation is more significant than MLP

### 7. **Vectorized Implementations** ⭐ NEW
- **NumPy Vectorized** (`rtl/numpy_lmul.py`):
  - Status: ✅ Working - Enhanced with matrix multiplication
  - Purpose: Batch operations on NumPy arrays
  - Functions: 
    - `lmul_numpy_vectorized()`: Element-wise LMUL on arrays
    - `lmul_numpy_float()`: LMUL with float conversion
    - `lmul_numpy_matmul()`: ⭐ NEW - Matrix multiplication using LMUL
  - Performance: Much faster than Python loop for large batches
  - **Matrix Multiplication**: Uses broadcasting to compute (m,n) @ (n,p) using element-wise LMUL
  
- **PyTorch Implementation** (`rtl/pytorch_lmul.py`):
  - Status: ✅ Working with autograd support - Enhanced with matrix multiplication
  - Purpose: PyTorch tensor operations with gradient support
  - Functions: 
    - `lmul_torch_vectorized()`: Element-wise LMUL on tensors
    - `lmul_torch_float()`: LMUL with float conversion
    - `lmul_torch()`: Autograd-enabled LMUL
    - `lmul_torch_matmul()`: ⭐ NEW - Matrix multiplication using LMUL
  - **Key Feature**: Can be used in training (backprop works!)
  - Uses `LMULFunction` extending `torch.autograd.Function`
  - **Matrix Multiplication**: Supports batched matrix operations for neural networks

### 8. **LSTM Verilog Hardware Validation** (`NNs/LSTM_Verilog/`) ⭐ NEW
- **Status**: ✅ Working - Hardware validation for neural network operations
- **Components**:
  - `LMUL_LSTM.v`: LMUL unit with 5-cycle latency
  - `FP32.v`: FP32 reference using precomputed products
  - `TB_WX.v`: Testbench for matrix-vector multiplication (W @ x)
- **Purpose**: Validate that hardware LMUL gives correct results for actual neural network matrix operations
- **Process**:
  1. Extract weights and inputs from trained LSTM
  2. Convert to BF16 format
  3. Run matrix-vector multiplication in Verilog
  4. Compare LMUL vs FP32 results
- **Notebook**: `lstm_verilog_tester.ipynb` automates the validation process

### 9. **Tiny LLM with LMUL** (`NNs/LSTM_LMUL_LLM.ipynb`) ⭐ NEW
- **Status**: ✅ In progress
- **Purpose**: Character-level language model using LSTM with LMUL
- **Architecture**: Embedding → LSTM → Linear → Vocabulary
- **Goal**: Test LMUL on more complex sequential tasks (language modeling)
- **Note**: This extends beyond classification to generative tasks

### 10. **Matrix Multiplication Testing** ⭐ NEW
- **Matrix Accuracy Tester** (`sim/matrix_accuracy_tester.ipynb`):
  - Status: ✅ NEW - Comprehensive matrix multiplication accuracy testing
  - Purpose: Compare accuracy of matrix multiplication using different methods
  - Tests:
    1. Standard NumPy matrix multiplication (baseline)
    2. Standard PyTorch matrix multiplication
    3. NumPy LMUL matrix multiplication (vectorized)
    4. NumPy LMUL scalar (element-wise, slower but more accurate)
    5. PyTorch LMUL matrix multiplication (vectorized)
    6. PyTorch LMUL scalar (element-wise)
  - Output: Heat matrix showing pairwise % mismatch between implementations
  - Matrix Size: 20×20 matrices, 100 test cases
  - **Key Finding**: LMUL matrix multiplication maintains accuracy comparable to standard methods

- **Matrix Speed Tester** (`sim/matrix_speed_tester.ipynb`):
  - Status: ✅ NEW - Matrix multiplication performance benchmarking
  - Purpose: Compare speed of different matrix multiplication implementations
  - Tests: Same implementations as accuracy tester
  - Matrix Sizes: 10×10, 20×20, 50×50, 100×100, 200×200
  - Output: Log-log plot showing time per operation vs matrix size
  - **Note**: These are software benchmarks; hardware synthesis metrics are still needed for true comparison

---

## ⚠️ What's Missing / What to Work On

### 1. **Speed Benchmarks Are Misleading** (`sim/lmul_speed_tester.ipynb`)
- **Status**: ⚠️ Tests exist but measure the wrong thing
- **Current tests compare**: Verilog simulation vs native Python (meaningless comparison)
- **What SHOULD be compared**: L-Mul hardware vs IEEE-754 hardware (synthesis metrics)
- **Results** (1000 operations):
  ```
  Python FP32:         1.03 μs/op  →  975,000 ops/sec  (BASELINE)
  NumPy vectorized:    2.16 μs/op  →  463,000 ops/sec  (0.47x)
  Python LMUL:         0.55 μs/op  →  1,812,000 ops/sec (1.86x faster!)
  Hardware LMUL sim:  30.06 μs/op  →  33,000 ops/sec   (Expected - simulation is always slow)
  ```
- **Why simulation is slow**: It's interpreting circuit behavior, not running on real hardware
- **Real metrics needed**: Synthesize both L-Mul and IEEE multipliers, compare area/power/delay
- **Action item**: Either get synthesis working OR acknowledge these tests aren't meaningful

### 2. **No Synthesis Results Yet**
- **Status**: ❌ Missing - This is the KEY metric!
- **What's needed**: 
  - Synthesis tools (OpenROAD, Yosys)
  - IEEE-754 multiplier Verilog (for comparison)
  - Synthesis scripts to generate area/power/delay reports
- **What last year's team claimed**:
  - 67-89% area reduction
  - 89-99% power reduction  
  - 72-80% delay reduction
- **Impact**: Can't verify the main benefit of L-Mul without this!
- **Priority**: HIGH - This is what proves L-Mul is better

### 3. **No Systolic Array Implementation**
- **Status**: ❌ Missing from repo
- **Expected**: 8×8 systolic array with DiP dataflow (from paper)
- **Impact**: Can only test single multiplications, not matrix operations
- **Why it matters**: ML uses matrix multiplication, not individual multiplies
- **Priority**: MEDIUM - Would be good to have but single multiplier proves the concept

### 4. **PyRTL Not Used**
- **Status**: PyRTL installed but code uses hand-written Verilog
- **Impact**: Minor - hand-written Verilog works fine
- **Priority**: LOW - Nice to have but not critical

### 5. **LSTM Bias Correction Needed**
- **Status**: ⚠️ Workaround implemented, but indicates approximation limitations
- **Issue**: LSTM requires +5% bias correction to maintain accuracy
- **Why**: Error accumulation in sequential operations (many multiplications per forward pass)
- **Current Solution**: Added correction term `result + (result / (1 << 5)) + (result / (1 << 6))`
- **Impact**: Shows that for complex architectures, raw LMUL may need calibration
- **Priority**: MEDIUM - Understand when/why correction is needed

---

## 🧠 Key Technical Concepts

### 1. **BFloat16 (BF16) Format**
```
|  Sign  |  Exponent  |  Mantissa  |
|   1    |     8      |     7      |  = 16 bits total
```
- Truncated FP32 (keeps same exponent range)
- Popular in ML (Google TPUs, AMD GPUs)
- Easier to convert from FP32 than FP16

### 2. **L-Mul Algorithm Insight**
Traditional FP multiplication:
```
(s1 ⊕ s2) × 2^(e1+e2-bias) × (1.m1 × 1.m2)
                             ^^^^^^^^^^^^^ This is expensive!
```

L-Mul approximation:
```
(s1 ⊕ s2) × 2^(e1+e2-bias) × (1 + m1 + m2 + 2^(-L(M)))
                             ^^^^^^^^^^^^^^^^^^^^^^^ Just addition!
```

The key trick: Instead of multiplying mantissas, ADD them!
- Loss: Accuracy (1.m1 × 1.m2 ≈ 1 + m1 + m2 + correction)
- Gain: Speed, area, power (addition is much simpler than multiplication)

### 3. **Why Hardware Simulation is Slow**
```
Real ASIC chip: ~1 GHz clock → 1 ns per operation
Verilog simulation: Event-driven interpreter → ~30 μs per operation
Slowdown factor: 30,000x slower than real hardware!
```

### 4. **Ready/Valid Handshake Protocol**
The hardware uses a proper handshake:
```
Source → [i_valid, i_data] → DUT → [o_valid, o_data] → Sink
       ← [i_ready]              ← [o_ready]
```
Transaction occurs when: `i_valid && i_ready` (for input) and `o_valid && o_ready` (for output)

---

## 📊 Current Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| **Core L-Mul Multiplier (Python)** | ✅ Working | Fast, correct, reference implementation |
| **Core L-Mul Multiplier (Verilog)** | ✅ Working | Matches Python exactly |
| **NumPy Vectorized LMUL** | ✅ Enhanced | Batch operations + matrix multiplication |
| **PyTorch LMUL with Autograd** | ✅ Enhanced | Training support + matrix multiplication |
| **Matrix Multiplication Testing** | ✅ NEW | Accuracy and speed benchmarks for matrix ops |
| **Accuracy Validation** | ✅ Enhanced | 10K tests, all implementations verified |
| **MNIST MLP Test** | ✅ Excellent | 97.01% vs 97.02% (0.01% loss) |
| **LSTM Tests** | ✅ NEW | MNIST: 97.75% vs 97.72% (better!), Fashion-MNIST: 85.01% vs 86.13% |
| **LSTM Verilog Validation** | ✅ NEW | Hardware validation for matrix operations |
| **Tiny LLM** | ✅ NEW | Character-level language model in progress |
| **Testing Infrastructure** | ✅ Enhanced | Cycle counting, parallel testing, comprehensive validation |
| | | |
| **Synthesis Metrics** | ❌ Missing | **THIS IS THE KEY THING TO DO** |
| **IEEE Multiplier (for comparison)** | ❌ Missing | Need this to prove L-Mul is better |
| **Systolic Array** | ❌ Missing | Would enable full matrix multiplication pipeline |
| **Speed Benchmarks** | ⚠️ Misleading | Current tests compare wrong things (simulation vs real HW) |

### Bottom Line
✅ **Core algorithm validated** - L-Mul works and preserves accuracy across multiple architectures  
✅ **Extended to LSTM** - Works on sequential models with minimal accuracy loss  
✅ **Vectorized implementations** - NumPy and PyTorch versions for efficient batch operations  
✅ **Matrix multiplication support** - NEW: Full matrix multiplication using LMUL (both NumPy and PyTorch)  
✅ **Matrix testing infrastructure** - NEW: Comprehensive accuracy and speed testing for matrix operations  
✅ **Hardware validation** - Verilog testing for actual neural network operations  
❌ **Need synthesis results** - Can't prove hardware benefits without area/power/delay metrics  
🎯 **Next priority** - Get synthesis working to prove 67-99% improvements claimed in paper

---

