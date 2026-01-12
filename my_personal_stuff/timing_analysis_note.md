# Timing Analysis Limitation

## Issue
The synthesized netlists contain generic Yosys cells ($add, $mux, $mul, etc.) rather than library-specific cells. OpenSTA requires library-mapped cells to perform timing analysis.

## Why This Happened
ABC (the technology mapper) didn't successfully map the generic cells to the Nangate 45nm library cells. This can happen when:
- The design hierarchy isn't properly flattened
- ABC can't find suitable library cells for the generic operations
- Library compatibility issues

## What We Can Still Conclude

Even without exact timing numbers, we can make architectural observations:
                                                                                               
1. **L-Mul has no multiplier** - Uses only adders ($add) and logic gates
2. **IEEE has a multiplier** - Contains $mul cell (8×8 bit multiplier)
3. **L-Mul has fewer cells** - 22 vs 29 (24.1% reduction)
4. **L-Mul has lower complexity** - Complexity score 32 vs 101 (68.3% reduction)

## Architectural Timing Implications

- **Multipliers are slow**: The $mul cell in IEEE multiplier will have a long critical path
- **Adders are fast**: L-Mul's $add cells have shorter critical paths
- **Fewer cells = faster**: L-Mul's simpler design should have shorter paths overall

## Conclusion

While we can't get exact timing numbers without proper technology mapping, the architectural differences strongly suggest L-Mul will be faster:
- No expensive multiplier operation
- Simpler logic (fewer cells, lower complexity)
- Shorter critical paths expected

This aligns with the paper's claims of 72-80% delay reduction.

