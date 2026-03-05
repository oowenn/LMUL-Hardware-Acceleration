import matplotlib.pyplot as plt
import matplotlib.transforms as mpl_transforms
import numpy as np
import pandas as pd
from pathlib import Path
import re
import subprocess


def parse_performance_comparison_txt(path: Path, size: int):
    section_sep = "----------------------------------------------------------------------"
    text = path.read_text().split(section_sep)
    final_metric_lines = text[1].strip().splitlines()
    rows = []
    paths = None
    regex = r'\s{2,}'
    for line in final_metric_lines:
        line = line.strip()
        if line.startswith("Metric"):
            paths = re.split(regex, line)[1:]
            rows = [{"Size": size, "Path": path} for path in paths]        
        elif line.startswith("Simulation Time"):
            for i in range(len(rows)):
                rows[i]['Sim Time (s)'] = float(re.split(regex, line)[i + 1].strip())
        elif line.startswith("CPU Cycles"):
            for i in range(len(rows)):
                rows[i]['CPU Cycles'] = int(re.split(regex, line)[i + 1].strip().replace(',', ''))
        elif line.startswith("Estimated total energy"):
            for i in range(len(rows)):
                rows[i]['Energy (µJ)'] = float(re.split(regex, line)[i + 1].strip())
            break
    # Optionally enrich rows with per-path instruction counts from the Performance Details section.
    # This lets downstream callers swap CPU Cycles for Instructions without changing the text format.
    if len(text) > 2 and rows:
        details_lines = text[2].strip().splitlines()
        for line in details_lines:
            line = line.strip()
            if line.startswith("Instructions"):
                parts = re.split(regex, line)
                for i in range(len(rows)):
                    rows[i]["Instructions"] = int(parts[i + 1].strip().replace(",", ""))
                break
    return rows


def validate_all_runs(gem5_sim: Path, sizes):
    """
    Validate LMUL, CPU LMUL, and IEEE runs for each size using validate_result_against_reference.py.
    Mirrors the logic previously embedded in workflow.ipynb.
    """
    validate_script = gem5_sim / "scripts" / "validate_result_against_reference.py"
    results_root = gem5_sim / "lmul_vs_ieee_comparison"

    for n in sizes:
        run_dirs = {
            "lmul": results_root / "lmul",
            "ieee": results_root / "ieee",
            "cpu_lmul": results_root / "cpu_lmul",
        }
        size_result = f"result_{n}.bin"
        size_inputs = f"inputs_{n}.bin"

        print(f"\n=== Validation for size {n} ===")

        # LMUL accelerator vs LMUL software reference
        if run_dirs["lmul"].is_dir():
            print("[LMUL Accel vs LMUL reference]")
            result_path = run_dirs["lmul"] / size_result
            inputs_path = run_dirs["lmul"] / size_inputs
            if not result_path.is_file() and (run_dirs["lmul"] / "result.bin").is_file():
                result_path = run_dirs["lmul"] / "result.bin"
                inputs_path = run_dirs["lmul"] / "inputs.bin"
            if result_path.is_file() and inputs_path.is_file():
                subprocess.run(
                    [
                        "python3",
                        str(validate_script),
                        str(run_dirs["lmul"]),
                        "--mode",
                        "lmul",
                        "--result",
                        str(result_path),
                        "--inputs",
                        str(inputs_path),
                    ],
                    cwd=gem5_sim,
                    check=False,
                )
            else:
                print(f"Missing LMUL artifacts for size {n}; skipping ({result_path.name}, {inputs_path.name}).")
        else:
            print("LMUL run directory missing; skipping.")

        # CPU LMUL (if present)
        if run_dirs["cpu_lmul"].is_dir():
            print("[CPU LMUL vs LMUL reference]")
            result_path = run_dirs["cpu_lmul"] / size_result
            inputs_path = run_dirs["cpu_lmul"] / size_inputs
            if not result_path.is_file() and (run_dirs["cpu_lmul"] / "result.bin").is_file():
                result_path = run_dirs["cpu_lmul"] / "result.bin"
                inputs_path = run_dirs["cpu_lmul"] / "inputs.bin"
            if result_path.is_file() and inputs_path.is_file():
                subprocess.run(
                    [
                        "python3",
                        str(validate_script),
                        str(run_dirs["cpu_lmul"]),
                        "--mode",
                        "lmul",
                        "--result",
                        str(result_path),
                        "--inputs",
                        str(inputs_path),
                    ],
                    cwd=gem5_sim,
                    check=False,
                )
            else:
                print(f"Missing CPU LMUL artifacts for size {n}; skipping ({result_path.name}, {inputs_path.name}).")

        # IEEE CPU vs IEEE software reference
        if run_dirs["ieee"].is_dir():
            print("[IEEE CPU vs IEEE reference]")
            result_path = run_dirs["ieee"] / size_result
            inputs_path = run_dirs["ieee"] / size_inputs
            if not result_path.is_file() and (run_dirs["ieee"] / "result.bin").is_file():
                result_path = run_dirs["ieee"] / "result.bin"
                inputs_path = run_dirs["ieee"] / "inputs.bin"
            if result_path.is_file() and inputs_path.is_file():
                subprocess.run(
                    [
                        "python3",
                        str(validate_script),
                        str(run_dirs["ieee"]),
                        "--mode",
                        "ieee",
                        "--result",
                        str(result_path),
                        "--inputs",
                        str(inputs_path),
                    ],
                    cwd=gem5_sim,
                    check=False,
                )
            else:
                print(f"Missing IEEE artifacts for size {n}; skipping ({result_path.name}, {inputs_path.name}).")
        else:
            print("IEEE run directory missing; skipping.")

# Merge Size cell (0,0) with the cell below (1,0)
def mergecells(table, ix0, ix1):
    ix0, ix1 = np.asarray(ix0), np.asarray(ix1)
    d = ix1 - ix0
    if not (0 in d and 1 in np.abs(d)):
        raise ValueError("Cells must be adjacent")
    if d[0] == -1:
        edges = ("BRL", "TRL")
    elif d[0] == 1:
        edges = ("TRL", "BRL")
    elif d[1] == -1:
        edges = ("BTR", "BTL")
    else:
        edges = ("BTL", "BTR")
    for ix, e in zip((ix0, ix1), edges):
        table[ix[0], ix[1]].visible_edges = e
    txts = [table[ix[0], ix[1]].get_text() for ix in (ix0, ix1)]
    tpos = [np.array(t.get_position()) for t in txts]
    trans = (tpos[1] - tpos[0]) / 2
    txts[0].set_transform(mpl_transforms.Affine2D().translate(trans[0], trans[1]) + txts[0].get_transform())
    txts[1].set_visible(False)


# Merge each metric title in row 0 across its three sub-columns.
def merge_header_triplet(table, row, col_start, label, fig, ax):
    c0, c1, c2 = col_start, col_start + 1, col_start + 2
    table[row, c0].visible_edges = "BTL"
    table[row, c1].visible_edges = "BT"
    table[row, c2].visible_edges = "BTR"

    # Hide per-cell text and draw one centered label over the 3-cell span.
    table[row, c0].get_text().set_visible(False)
    table[row, c1].get_text().set_visible(False)
    table[row, c2].get_text().set_visible(False)

    renderer = fig.canvas.get_renderer()
    bbox_disp = mpl_transforms.Bbox.union([
        table[row, c0].get_window_extent(renderer=renderer),
        table[row, c1].get_window_extent(renderer=renderer),
        table[row, c2].get_window_extent(renderer=renderer),
    ])
    bbox_axes = bbox_disp.transformed(ax.transAxes.inverted())
    cx = bbox_axes.x0 + bbox_axes.width / 2
    cy = bbox_axes.y0 + bbox_axes.height / 2
    ax.text(cx, cy, label, transform=ax.transAxes,
            ha="center", va="center", color="black", weight="bold", fontsize=10)


def plot_table(sizes, core, save_fig=False):
    metric_names = ["Simulation Time (s)", "Estimated Total Energy (J)", "Instructions (millions)"]
    metric_cols = ["Sim Time (s)", "Energy (µJ)", "Instructions"]

    def fmt_val(m, val):
        if m == "Sim Time (s)":
            return f"{val:.6f}"
        if m == "Instructions":
            return f"{(val / 1e6):,.3f}"
        if m == "Energy (µJ)":
            return f"{(val / 1e6):,.6f}"
        return f"{val:,.3f}"

    def fmt_rel_faster_slower(val, ref):
        if val <= 0 or ref <= 0:
            return "-"
        ratio = ref / val
        if ratio >= 1:
            return f"{ratio:.2f}x faster"
        return f"{(1 / ratio):.2f}x slower"

    def fmt_rel_more_less(val, ref):
        if val <= 0 or ref <= 0:
            return "-"
        ratio = val / ref
        if ratio >= 1:
            return f"{ratio:.2f}x more"
        return f"{(1 / ratio):.2f}x less"

    body = []
    for n in sizes:
        sub = core[(core["Size"] == n) & core["Path"].isin(["LMUL ACL", "IEEE", "CPU LMUL"])]
        lmul_accel = sub[sub["Path"] == "LMUL ACL"].iloc[0]
        ieee = sub[sub["Path"] == "IEEE"].iloc[0]
        cpu_lmul_rows = sub[sub["Path"] == "CPU LMUL"]
        has_cpu_lmul = len(cpu_lmul_rows) > 0
        cpu_lmul = cpu_lmul_rows.iloc[0] if has_cpu_lmul else None
        row = [f"n={n}"]
        for m in metric_cols:
            if m == "Sim Time (s)":
                row.append(fmt_rel_faster_slower(lmul_accel[m], ieee[m]))
                row.append(fmt_val(m, ieee[m]))
                row.append(fmt_rel_faster_slower(cpu_lmul[m], ieee[m]) if has_cpu_lmul else "-")
            else:
                row.append(fmt_rel_more_less(lmul_accel[m], ieee[m]))
                row.append(fmt_val(m, ieee[m]))
                row.append(fmt_rel_more_less(cpu_lmul[m], ieee[m]) if has_cpu_lmul else "-")
        body.append(row)

    col_headers_row1 = ["Size"] + [name if j == 0 else "" for name in metric_names for j in range(3)]
    col_headers_row2 = [""] + ["LMUL ACL", "IEEE CPU", "LMUL CPU", "LMUL ACL", "IEEE CPU", "LMUL CPU", "LMUL ACL", "IEEE CPU", "LMUL CPU"]
    cell_text = [col_headers_row1, col_headers_row2] + body

    fig, ax = plt.subplots(figsize=(14, 2.8))
    ax.axis("off")
    tbl = ax.table(
        cellText=cell_text,
        loc="center",
        cellLoc="center",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    tbl.scale(1.0, 1.8)

    shade_sizes = {4, 256}
    shade_rows = {row_idx for row_idx, n in enumerate(sizes, start=2) if n in shade_sizes}
    for (i, j), cell in tbl.get_celld().items():
        cell.set_facecolor("#f3f3f3" if i in shade_rows else "white")
        cell.set_edgecolor("#2f2f2f")
        cell.set_linewidth(1.0)
        cell.set_text_props(color="black")
        if i in (0, 1) or j == 0:
            cell.set_text_props(color="black", weight="bold")

    fig.canvas.draw()
    mergecells(tbl, (0, 0), (1, 0))

    for start_col, title in [(1, metric_names[0]), (4, metric_names[1]), (7, metric_names[2])]:
        merge_header_triplet(tbl, 0, start_col, title, fig, ax)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    cell_bboxes = [cell.get_window_extent(renderer=renderer) for cell in tbl.get_celld().values()]
    bbox_disp = mpl_transforms.Bbox.union(cell_bboxes)
    bbox_inches = bbox_disp.transformed(fig.dpi_scale_trans.inverted())
    if save_fig:
        output_path = "comparison_results_table.png"
        fig.savefig(output_path, dpi=300, bbox_inches=bbox_inches, pad_inches=0)
        print(f"Saved {output_path}")
    plt.show()