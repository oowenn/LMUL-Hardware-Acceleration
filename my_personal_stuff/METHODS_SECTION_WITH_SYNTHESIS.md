# Complete Methods Section with Synthesis Integrated

```latex
\section{Methods}

\subsection{Standard BFloat16 Multiplication}

\label{subsec:standard_bf16}

Before discussing the L-Mul approximation, we first establish how standard BFloat16 multiplication works. BFloat16 (BF16) is a 16-bit floating-point format consisting of 1 sign bit, 8 exponent bits, and 7 mantissa bits. This format is particularly popular in machine learning due to its compatibility with single-precision (FP32) exponents while requiring only half the storage.

A BF16 number $x$ represents the value:

\begin{equation}
x = (-1)^s \times 2^{e - 127} \times (1.m)
\label{eq:bf16_representation}
\end{equation}

where $s$ is the sign bit, $e$ is the 8-bit exponent, $m$ represents the 7-bit mantissa, and 127 is the bias.

Standard BF16 multiplication follows the IEEE 754 approach: the signs are XORed, the exponents are added (with bias correction), and the mantissas are multiplied. This mantissa multiplication is the expensive part—it requires a hardware multiplier and subsequent normalization logic to handle carries. For neural network inference where millions of multiplications occur, this computational cost adds up quickly in terms of both latency and power consumption.

\subsection{LMUL Algorithm}

\label{subsec:lmul_algorithm}

The L-Mul algorithm takes a different approach \footnote{\texttt{rtl/lmul\_bf16.v}}\label{fn:lmul_bf16}. Instead of treating the exponent and mantissa as separate entities, it exploits a clever observation: if we treat the combined exponent-mantissa field as a single fixed-point number, multiplication can be approximated by simple addition. This works because logarithms transform multiplication into addition, and the floating-point exponent already represents a logarithmic quantity.

\paragraph{Algorithm Overview.}

Given two BF16 operands $a$ and $b$, L-Mul works by adding their exponent-mantissa fields directly. Here's how it breaks down:

\textbf{Step 1: Extract the fields.} We pull out the components from each 16-bit operand:

\begin{align}
a_{sign} &= a[15], \quad b_{sign} = b[15] \\
a_{field} &= a[14:0], \quad b_{field} = b[14:0]
\end{align}

The $field$ values contain the concatenated exponent and mantissa bits, which we'll treat as a single 15-bit integer.

\textbf{Step 2: Handle edge cases.} If either input is zero or subnormal (indicated by a zero exponent), we immediately return zero. This keeps the algorithm simple and handles the most common edge case:

\begin{equation}
\text{if } a_{exp} = 0 \text{ or } b_{exp} = 0 \text{, return } 0
\end{equation}

\textbf{Step 3: Add the fields.} We add the two fields together, but we need to correct for the fact that adding exponents naturally doubles the bias:

\begin{equation}
\text{sum}_{full} = a_{field} + b_{field} + \text{OFFSET}_{MOD}
\label{eq:lmul_addition}
\end{equation}

The offset term compensates for this doubled bias:

\begin{equation}
\text{OFFSET}_{MOD} = ((2^{15}) - (127 \ll 7)) \text{ AND } 0x7FFF = 0x4080
\end{equation}

We use 17 bits for the sum to capture potential overflow.

\textbf{Step 4: Check for overflow or underflow.} The top two bits of our 17-bit sum tell us what happened:

\begin{equation}
\text{carry}_2 = \text{sum}_{full}[16:15]
\end{equation}

These bits give us three cases:

\begin{itemize}
    \item $00_2$: The result underflowed—return zero
    \item $01_2$: Normal result—use the lower 15 bits
    \item $1x_2$: The result overflowed—saturate to maximum value ($0x7FFF$)
\end{itemize}

\textbf{Step 5: Calculate the sign.} This follows standard multiplication rules—XOR the input signs, but force the result to positive zero if the magnitude is zero:

\begin{equation}
s_{result} = \begin{cases}
0 & \text{if field} = 0 \\
a_{sign} \oplus b_{sign} & \text{otherwise}
\end{cases}
\end{equation}

\textbf{Step 6: Pack the result.} Finally, we combine the sign bit with the selected field value:

\begin{equation}
\text{result} = (s_{result} \ll 15) \text{ OR } \text{field}_{sel}
\end{equation}

\paragraph{Why This Works.}

The key insight is that the exponent field already represents a logarithm (base 2), and the mantissa can be approximated as part of this logarithmic representation. When we add these combined fields, we're essentially performing multiplication in log space. The approximation comes from treating the mantissa bits as part of a continuous logarithmic scale rather than as a separate fractional multiplier. For neural network inference, this approximation is remarkably accurate—accurate enough that we see virtually no loss in classification accuracy, as we'll show in the results.

\subsection{Development Environment and Docker Configuration}

Docker was used for containerization to ensure consistent package reliability across different machines. Using the relevant files \footnote{\texttt{Dockerfile}}\label{fn:dockerfile}\footnote{\texttt{.devcontainer/devcontainer.json}}\label{fn:devcontainer.json}\footnote{\texttt{requirements.txt}}\label{fn:requirements.txt}, a VS Code pipeline was developed to automate the installation of necessary Python and Verilog dependencies, while ensuring compatability, as well as relevant VS Code extensions such as Python and Jupyter.

\subsection{Verilog Simulation}

\label{subsec:simulation_infrastructure}

To validate our LMUL hardware design and enable integration with machine learning workloads, we developed a simulation pipeline that bridges Verilog hardware descriptions with Python-based testing and neural network frameworks. This infrastructure allows us to verify correctness, measure performance characteristics, and ultimately test LMUL on real ML tasks without requiring physical hardware.

\paragraph{Simulation Approach.}

We use Icarus Verilog (iverilog), an open-source Verilog simulator, to compile and execute our hardware descriptions. The simulation flow works as follows: our Verilog modules are compiled into an executable simulation model, which we then run using the \texttt{vvp} (Verilog VVP) runtime. This generates cycle-accurate behavior that matches what the actual hardware would do, including all timing, handshaking protocols, and pipeline stages.

% could omit

The key challenge was creating a seamless interface between this low-level hardware simulation and high-level Python code. We needed a way to feed test vectors into the simulator, run the hardware through multiple clock cycles, and extract results—all from within a Python environment where we could easily work with ML frameworks like PyTorch.

\paragraph{Batch Testing Architecture.}

Rather than spawning a new simulation process for every single multiplication (which would be prohibitively slow), we developed a batch testing system. Our \texttt{BatchLMULTester} class \footnote{\texttt{rtl/lmul\_tester.py}}\label{fn:lmul_tester} generates a complete Verilog testbench that includes:

\begin{itemize}
    \item Arrays of pre-loaded test input pairs ($a$, $b$)
    \item Clock generation and reset logic
    \item Ready/valid handshaking to properly interface with our LMUL module's pipeline
    \item Result capture logic that stores outputs as they become available
    \item Automatic result printing for parsing by Python
\end{itemize}

This approach means we compile and run the simulator once per batch, rather than once per operation. For testing 1000 multiplications, this reduces overhead from roughly 50 seconds to about 30 milliseconds—a speedup of over 1500x compared to naive per-operation simulation.

\paragraph{Parallelized Testing Architecture.}

To further enhance our simulation performance and diagnostic capabilities, we also explored a parallelized approach. Parallelization of the testbench involved instantiating multiple Designs Under Test (DUT), to operate on multiple numbers in one clock cycle. This however yielded minimal speed gains due to the serial nature of our current DUT instantiation and the single-threaded execution of Icarus Verilog and vvp. Recognizing this, we shifted our simulation environment from Icarus Verilog to Vivado, a dedicated FPGA development tool, which enables us to generate detailed waveforms. This visual feedback allows us to precisely identify bottlenecks and verify correctness more effectively. Additionally, we optimized our input signals by removing unnecessary handshaking logic, which previously enforced a 20ns delay between reading new input pairs. By eliminating these handshake checks, we reduced the input signal latency to 10ns, effectively halving the simulation runtime associated with positive clock edges. These improvements collectively contributed to a significant reduction in simulation time and enhanced our ability to analyze and verify the hardware behavior efficiently.

% include figure?

\subsection{Hardware Synthesis Methodology}

\label{subsec:synthesis_methodology}

While our simulation work (Section~\ref{subsec:simulation_infrastructure}) validated the functional correctness of our L-Mul hardware design, synthesis provides concrete hardware metrics that quantify the efficiency advantages. To validate the hardware efficiency claims of L-Mul and obtain quantitative metrics for comparison with standard IEEE BF16 multiplication, we synthesized both designs using industry-standard EDA tools. This synthesis process converts our Verilog RTL descriptions into gate-level netlists mapped to a standard cell library, enabling quantitative comparison of area and architectural characteristics.

\paragraph{Synthesis Flow.}

We used Yosys 0.9, an open-source synthesis tool, to perform technology mapping of both multiplier designs to the Nangate 45nm Open Cell Library \footnote{\texttt{synthesis/scripts/synth\_lmul.ys}}\footnote{\texttt{synthesis/scripts/synth\_bf16.ys}}. The synthesis flow for each design followed a standard sequence: (1) reading the Verilog RTL and standard cell library, (2) hierarchy processing and optimization, (3) finite state machine optimization, (4) memory optimization, (5) flattening for technology mapping, (6) flip-flop mapping to library cells, (7) combinational logic mapping using ABC with a 1.0 ns target clock period, and (8) final optimization and cleanup. This process generated gate-level netlists where each logic operation is implemented using standard cells from the Nangate library, providing concrete area and cell count metrics for comparison.

\paragraph{Design Wrappers.}

To ensure fair comparison, we created synthesis-specific wrapper modules that isolate the core multiplier logic from testbench code \footnote{\texttt{synthesis/rtl/top\_lmul\_synth.v}}\footnote{\texttt{synthesis/rtl/top\_bf16\_synth.v}}. The L-Mul wrapper instantiates our \texttt{lmul\_bf16} module, while the IEEE BF16 wrapper instantiates a standard IEEE-754 BF16 multiplier implementation \footnote{\texttt{synthesis/rtl/bf16\_mul.v}} that performs full mantissa multiplication. Both wrappers maintain identical interfaces with ready/valid handshaking protocols, ensuring equivalent control logic overhead in the comparison.

\paragraph{Technology Library.}

The Nangate 45nm Open Cell Library provides a comprehensive set of standard cells including basic logic gates (AND, OR, XOR, NAND, NOR), complex gates (AOI, OAI), flip-flops, and specialized cells. This library is widely used in academic research and provides realistic area and timing characteristics for 45nm CMOS technology. All area measurements are reported in library-specific area units, which represent the physical silicon area required for each standard cell.

\subsection{Software Testing}

To support comprehensive validation and performance analysis of LMUL across different computational contexts, we developed multiple software implementations targeting distinct use cases. These implementations enable us to verify correctness and benchmark performance characteristics.

\paragraph{Scalar Implementations and Comparisons.}

For element-wise multiplication operations, we implemented scalar LMUL versions across multiple frameworks. Our pure Python scalar implementation \footnote{\texttt{rtl/py\_lmul.py}}\label{fn:py_lmul} processes individual BF16 operand pairs and serves as our primary reference for validation, providing a fast and transparent way to generate expected results without the overhead of hardware simulation. The Python version follows the exact same algorithm as our Verilog implementation, ensuring bit-exact matches for verification. For efficient batch processing, we developed vectorized NumPy \footnote{\texttt{rtl/numpy\_lmul.py}}\label{fn:numpy_lmul} and PyTorch \footnote{\texttt{rtl/pytorch\_lmul.py}}\label{fn:pytorch_lmul} implementations that operate on entire arrays of BF16 values simultaneously, leveraging optimized array operations and SIMD capabilities to process thousands of element-wise multiplications in parallel. These scalar implementations are used in our speed and accuracy testing frameworks \footnote{\texttt{sim/lmul\_speed\_tester.ipynb}} \footnote{\texttt{sim/lmul\_accuracy\_tester.ipynb}} to compare LMUL performance and accuracy against standard floating-point multiplication across different input ranges and batch sizes. The scalar implementations enable us to understand the performance characteristics and numerical behavior of LMUL at the fundamental operation level, providing insights into how approximate arithmetic affects individual multiplications.

\paragraph{Matrix Multiplication Implementations and Comparisons.}

For matrix-level operations, we implemented LMUL-based matrix multiplication functions in both NumPy \footnote{\texttt{rtl/numpy\_lmul.py}}\label{fn:numpy_lmul} and PyTorch \footnote{\texttt{rtl/pytorch\_lmul.py}}\label{fn:pytorch_lmul} that perform full matrix multiplications using LMUL for the underlying element-wise products. These implementations broadcast input matrices to compute all pairwise LMUL products, then sum along the appropriate dimensions to produce matrix multiplication results. The NumPy implementation enables direct comparison with standard BLAS-optimized matrix multiplication, while the PyTorch version integrates with neural network frameworks and includes a custom \texttt{torch.autograd.Function} that enables automatic differentiation during training. Our matrix multiplication implementations are evaluated in dedicated speed and accuracy testing frameworks \footnote{\texttt{sim/matrix\_speed\_tester.ipynb}} \footnote{\texttt{sim/matrix\_accuracy\_tester.ipynb}} that compare LMUL-based matrix operations against standard NumPy and PyTorch matrix multiplication across various matrix sizes. These comparisons reveal how the approximate nature of LMUL propagates through matrix operations and provide performance benchmarks for potential neural network integration scenarios.

\subsection{MLP–L-Mul Integration}

\label{subsec:mlp_lmul}

To investigate the integration of approximate arithmetic within neural networks, we implemented a modified multilayer perceptron (MLP) in PyTorch \footnote{\texttt{mnistmlptest/lmul\_mlp\_mnist.ipynb}}\label{fn:lmul_mlp_mnist} capable of operating under both conventional and L-Mul modes. The objective was to directly substitute the standard floating-point multiply operation in the forward pass with an approximate function that more closely resembles a hardware-efficient arithmetic primitive.

\paragraph{Model Architecture.}

The MLP architecture consists of two fully connected layers with ReLU activations, followed by a log-softmax output layer. The first layer maps a flattened $28\times 28$ input image to a 128-dimensional hidden representation, while the second projects to the 10 output classes corresponding to the MNIST digits. 

\paragraph{Vectorized Implementation.}

For efficiency, a custom function \texttt{lmul\_linear} was implemented to perform the equivalent of a dense linear transformation using L-Mul arithmetic. Given an input tensor $x \in \mathbb{R}^{B \times I}$ and a weight matrix $W \in \mathbb{R}^{O \times I}$, the computation proceeds as

\[
Y_{b,o} = \sum_{i=1}^{I} \text{L-Mul}(x_{b,i}, W_{o,i}) + b_o,
\]

where $b$ denotes the batch dimension. Broadcasting and tensor expansion were used to apply L-Mul elementwise over all input–weight pairs, followed by summation across input features.

\paragraph{Training and Evaluation Procedure.}

The model was first trained for both two and five epochs on the MNIST training set using standard floating-point arithmetic and the Adam optimizer. After training, the learned weights were evaluated under the L-Mul mode using the same architecture and parameter values. This allowed direct comparison between true multiplication and its L-Mul approximation under identical learned representations. All experiments were conducted on CPU using PyTorch's built-in automatic differentiation and tensor operations.

\subsection{LSTM–L-Mul Integration}

Towards testing L-Mul's approximation cost among other neural networks, we implemented a Long-Short Term Memory (LSTM) in Pytorch also capable of operating under both conventional and L-Mul multiplication. Like the MLP Layer, the objective is to directly substitute the standard floating-point multiply operation in the forward pass with an approximate function (L-Mul). 

\paragraph{Model Architecture.}

For each timestep in a sequence, the input embedding $x_t$ is concatenated with the previous hidden state $h_{t-1}$ and passed through linear transformations to compute the LSTM gates: input ($i_t$), forget ($f_t$), cell candidate ($g_t$), and output ($o_t$). The cell state $c_t$ and hidden state $h_t$ are then updated according to the standard LSTM equations:

\[
c_t = f_t \odot c_{t-1} + i_t \odot g_t, \quad
h_t = o_t \odot \tanh(c_t)
\]

For sequence classification, the final hidden state $h_T$ is used as input to a linear layer to produce logits for the output classes. A token is sampled from these logits, and its embedding is used as the input for the next timestep. The hidden and cell states carry over, providing context, while the logits themselves are only used for sampling and not fed directly back into the model. For language modeling, each timestep's hidden state can be used to predict the next token, and generation continues recursively until an end-of-sequence token or a maximum length is reached.

\paragraph{PyTorch L-Mul Implementation}  

Considering that the LSTM is significantly more computationally intensive than the MLP layer, a specialized L-Mul algorithm was implemented to optimize runtime and allow PyTorch compilation. The algorithm simulates bfloat16 multiplication within float32 tensors by extracting the sign and field bits of each input, performing field addition with bias correction, and handling underflow and overflow conditions explicitly. The resulting bits are then repacked into a float32 tensor, with a small heuristic bitshift correction added to improve accuracy for LSTM operations, where multiplication errors accumulate rapidly. Finally, zeros and subnormal values are explicitly managed to maintain numerical stability. 

\paragraph{Training and Evaluation Procedure.}

The model was first trained for three epochs across 5 seeds on the FashionMNIST, KMNIST, SeqMNIST datasets using standard floating-point arithmetic and the Adam optimizer. As in the MLP Layer methodology section, after training, the learned weights were evaluated under the L-Mul mode using the same architecture and parameter values against floating-point multiplication.
```

