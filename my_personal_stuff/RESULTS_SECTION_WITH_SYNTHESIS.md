# Complete Results Section with Synthesis Integrated

```latex
\section{Results}

\subsection{Numerical Accuracy Evaluation}

We evaluated the accuracy of LMUL implementations at both the scalar (element-wise) and matrix multiplication levels, comparing them against standard floating-point arithmetic and verifying consistency across different software implementations.

\paragraph{Scalar Accuracy Evaluation.}

For element-wise multiplication operations, we compared multiple LMUL implementations against standard floating-point multiplication \footnote{\texttt{sim/lmul\_accuracy\_tester.ipynb}}\label{fn:lmul_accuracy}. Our evaluation includes Python scalar LMUL, NumPy vectorized LMUL, PyTorch vectorized LMUL, and Verilog hardware simulation, all tested against standard IEEE 32-bit floating-point multiplication. For each test configuration, we generated $N = 10,000$ randomly sampled operand pairs, with each operand drawn uniformly from the range [-10,000, +10,000]. The inputs were evaluated by all multiplication methods, and the average absolute error was normalized by the numerical range of the test dataset to yield a percentage error metric.

The results demonstrate that all LMUL implementations produce consistent results, with the Verilog hardware simulation matching the Python LMUL emulator exactly. When compared to standard floating-point multiplication, LMUL exhibits a bounded and predictable precision loss consistent with the reduced precision of the BF16-style format used internally. These results indicate that LMUL preserves correctness relative to its software specification while introducing precision loss that is small enough to support downstream inference tasks.

\begin{figure}[h]
    \centering
    \includegraphics[width=\linewidth]{figure/scalar_accuracy.png}
    \caption{Accuracy comparison of scalar LMUL implementations against standard floating-point multiplication.}
    \label{fig:scalar_accuracy}
\end{figure}

\paragraph{Matrix Multiplication Accuracy Evaluation.}

For matrix-level operations, we evaluated LMUL-based matrix multiplication against standard NumPy and PyTorch matrix multiplication implementations \footnote{\texttt{sim/matrix\_accuracy\_tester.ipynb}}\label{fn:matrix_accuracy}. We tested $N = 100$ randomly generated matrix pairs of size $20 \times 20$, with values drawn from uniform distributions. The evaluation compares NumPy standard matrix multiplication, PyTorch standard matrix multiplication, NumPy LMUL matrix multiplication, and PyTorch LMUL matrix multiplication, measuring pairwise percentage mismatch between implementations.

The results reveal how the approximate nature of LMUL propagates through matrix operations, showing the cumulative effect of element-wise approximation errors when aggregated across full matrix multiplications. This analysis provides insights into the numerical stability of LMUL for neural network applications where matrix operations are fundamental.

\begin{figure}[h]
    \centering
    \includegraphics[width=\linewidth]{figure/matrix_accuracy.png}
    \caption{Pairwise accuracy comparison heat matrix for matrix multiplication implementations.}
    \label{fig:matrix_accuracy}
\end{figure}

\subsection{Execution Speed}

We benchmarked the performance of LMUL implementations at both scalar and matrix multiplication levels, comparing them against standard implementations across various batch sizes and matrix dimensions.

\paragraph{Scalar Multiplication Speed.}

We benchmarked multiple multiplication backends for element-wise operations across batch sizes ranging from $10^1$ to $10^5$ operations \footnote{\texttt{sim/lmul\_speed\_tester.ipynb}}\label{fn:lmul_speed}. The evaluation includes standard Python \texttt{float32} multiplication, NumPy vectorized multiplication, PyTorch vectorized multiplication, Python scalar LMUL, NumPy vectorized LMUL, PyTorch vectorized LMUL, Verilog LMUL hardware simulation, and parallelized Verilog simulation with 4 DUTs. The measured quantity is the average time per multiplication after removing initialization overhead.

As shown in Figure~\ref{fig:scalar_speed}, NumPy achieves the lowest latency due to optimized vectorized execution, reaching sub-nanosecond performance for large batches. Standard Python and PyTorch multiplications scale well as loop overhead amortizes. The LMUL hardware simulation path incurs larger per-call overhead from Verilog simulation, but its time per operation decreases with batch size. This reflects simulator cost rather than hardware speed---a synthesized implementation would operate at clock-cycle scale. The Python LMUL model is slower due to explicit bit-level emulation, while vectorized NumPy and PyTorch LMUL implementations provide intermediate performance.

\begin{figure}[h]
    \centering
    \includegraphics[width=\linewidth]{figure/scalar_speed.png}
    \caption{Average time per scalar multiplication (log--log scale) for multiple implementations over increasing batch sizes.}
    \label{fig:scalar_speed}
\end{figure}

\paragraph{Matrix Multiplication Speed.}

We benchmarked matrix multiplication performance for standard and LMUL-based implementations across matrix sizes ranging from $10 \times 10$ to $200 \times 200$ \footnote{\texttt{sim/matrix\_speed\_tester.ipynb}}\label{fn:matrix_speed}. The evaluation compares NumPy standard matrix multiplication, PyTorch standard matrix multiplication, NumPy LMUL matrix multiplication, and PyTorch LMUL matrix multiplication. Performance is measured as time per operation normalized by matrix size ($n^3$ operations for $n \times n$ matrices).

As shown in Figure~\ref{fig:matrix_speed}, standard NumPy and PyTorch implementations leverage optimized BLAS routines for high performance. LMUL-based matrix multiplication implementations show different performance characteristics due to the overhead of BF16 conversion and element-wise LMUL operations, though they provide the approximate arithmetic needed for neural network inference scenarios. The results demonstrate the performance trade-offs when using approximate arithmetic for matrix operations in software implementations.

\begin{figure}[h]
    \centering
    \includegraphics[width=\linewidth]{figure/matrix_speed.png}
    \caption{Time per operation for matrix multiplication implementations across different matrix sizes (log--log scale).}
    \label{fig:matrix_speed}
\end{figure}

\subsection{MLP–L-Mul Integration Results}

After training the baseline multilayer perceptron (MLP) for five epochs on the MNIST dataset using standard floating-point arithmetic, the model achieved a test accuracy of \textbf{97.02\%}. The same trained weights were subsequently evaluated using the L-Mul arithmetic mode, in which all elementwise multiplications within the linear layers were replaced by the approximate L-Mul operator as described in Section~\ref{subsec:mlp_lmul}. The resulting test accuracy under L-Mul computation was \textbf{97.01\%}.

This outcome supports the hypothesis that approximate arithmetic primitives such as L-Mul can be integrated into neural inference pipelines without sacrificing predictive accuracy, provided that proper magnitude calibration is applied. The finding also suggests that hardware implementations based on L-Mul may yield reductions in power consumption or silicon area without compromising functional correctness at the algorithmic level. However, further testing may be needed to investigate the breadth of this claim across different neural network architectures (e.g Transformers, LSTM, etc.).

\subsection{LSTM L-Mul Integration Results}

We evaluated the impact of replacing standard FP32 multiplication with the L-Mul operator inside the LSTM cell across FashionMNIST, KMNIST, and SeqMNIST. For each configuration, five runs were performed to estimate mean accuracy and variance.

\begin{figure}[h!]
    \centering
    \includegraphics[width=0.75\linewidth]{figure/LSTMInfer.png}
    \caption{Comparison of FP32 vs.\ L-Mul inference accuracy across datasets. Error bars denote standard deviation over five runs.}
    \label{fig:lstm_infer_bar}
\end{figure}

As shown in Figure~\ref{fig:lstm_infer_bar}, across all datasets, L-Mul closely matches FP32 performance.

Overall, L-Mul introduces less than a \(1\%\) accuracy change across all tasks. Furthermore, upon investigating the FashionMNIST predictions between L-Mul and floating point multiplication LSTMs, there is a 96.6\% agreement rate between the two models. This demonstrates that the operator remains an effective approximation with relatively low classification error within a recurrent architecture (LSTM) but non-negligible prediction disagreement where multiplicative approximation errors can accumulate.

\subsection{Hardware Synthesis Comparison}

To quantify the hardware efficiency advantages of L-Mul, we synthesized both the L-Mul and IEEE BF16 multiplier designs using the methodology described in Section~\ref{subsec:synthesis_methodology}. This synthesis process converts our Verilog RTL descriptions into gate-level netlists, enabling quantitative comparison of area and architectural characteristics.

\paragraph{Area Metrics.}

Table~\ref{tab:synthesis_area} presents the area comparison between L-Mul and IEEE BF16 multipliers. The L-Mul design achieves a \textbf{66.8\% reduction in standard cell area} compared to the IEEE multiplier, using 180.88 area units versus 545.03 area units. This represents a 3.01× reduction in silicon area, meaning that approximately three L-Mul units can fit in the same area as one IEEE multiplier. The cell count comparison shows a \textbf{63.0\% reduction}, with L-Mul requiring 181 cells compared to 489 cells for the IEEE design.

\begin{table}[h]
\centering
\begin{tabular}{lccc}
\hline
\textbf{Metric} & \textbf{L-Mul} & \textbf{IEEE BF16} & \textbf{Improvement} \\
\hline
Standard Cell Area & 180.88 units & 545.03 units & \textbf{66.8\% reduction} \\
Number of Cells & 181 & 489 & \textbf{63.0\% reduction} \\
Area Ratio (L-Mul/IEEE) & 0.332 & 1.000 & 3.01× smaller \\
\hline
\end{tabular}
\caption{Area comparison between L-Mul and IEEE BF16 multipliers synthesized with Nangate 45nm library.}
\label{tab:synthesis_area}
\end{table}

\paragraph{Architectural Analysis.}

The cell type breakdown reveals the fundamental architectural difference between the two designs. The L-Mul implementation uses only basic logic gates (AND, OR, XOR, NAND, NOR) and adders—\textbf{no multiplier cells are present}. In contrast, the IEEE BF16 multiplier contains complex multiplier logic implemented as optimized gate networks to perform 8×8 bit mantissa multiplication. This architectural difference explains the area savings: L-Mul avoids the expensive multiplier hardware entirely, replacing it with simple addition operations. This finding connects to our software and neural network results, demonstrating that L-Mul maintains accuracy despite using simpler arithmetic operations.
```

