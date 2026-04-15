from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .filtering import filter_known_modes
from .io import export_results, extract_time_signal, list_columns, read_table
from .plotting import save_comparison_plot


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Filter damped oscillations after a step test.")
    parser.add_argument("--file", required=True, help="Input XLS/XLSX/CSV file")
    parser.add_argument("--sheet", default=0, help="Excel sheet name or index. Default: 0")
    parser.add_argument("--list-columns", action="store_true", help="Only list available columns and exit")
    parser.add_argument("--time-column", help="Name of the time column")
    parser.add_argument("--signal-column", help="Name of the signal column")
    parser.add_argument("--t0", type=float, help="Step time. Samples before this time are left unchanged")
    parser.add_argument("--remove", nargs="*", type=float, default=[], help="Known resonance frequencies to remove in Hz")
    parser.add_argument("--tol", type=float, default=0.2, help="Frequency tolerance in Hz")
    parser.add_argument("--order", type=int, default=12, help="Matrix-Pencil model order")
    parser.add_argument(
        "--detrend",
        choices=("none", "constant", "linear"),
        default="constant",
        help="Baseline/trend handling before modal estimation",
    )
    parser.add_argument("--output-dir", default="outputs", help="Directory for CSV/Excel/plot outputs")
    parser.add_argument("--no-excel", action="store_true", help="Do not write results.xlsx")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    sheet = _parse_sheet(args.sheet)
    frame = read_table(args.file, sheet_name=sheet)

    if args.list_columns:
        print("Available columns:")
        for column in list_columns(frame):
            print(f"- {column}")
        return 0

    if args.t0 is None:
        parser.error("--t0 is required unless --list-columns is used")

    time, values, time_column, signal_column = extract_time_signal(
        frame,
        time_column=args.time_column,
        signal_column=args.signal_column,
    )
    print(f"Using time column: {time_column}")
    print(f"Using signal column: {signal_column}")

    result = filter_known_modes(
        time=time,
        values=values,
        t0=args.t0,
        remove_frequencies_hz=args.remove,
        tolerance_hz=args.tol,
        model_order=args.order,
        detrend=args.detrend,
    )
    output_dir = Path(args.output_dir)
    written = export_results(result, output_dir=output_dir, write_excel=not args.no_excel)
    plot_path = save_comparison_plot(result, output_dir / "comparison_plot.png")
    modes_frame = pd.DataFrame(result.analysis.as_table())

    print("\nDetected modes:")
    if modes_frame.empty:
        print("No modes detected")
    else:
        print(modes_frame.to_string(index=False))
    print("\nWritten files:")
    for key, path in written.items():
        print(f"- {key}: {path}")
    print(f"- plot: {plot_path}")
    return 0


def _parse_sheet(raw_sheet: str) -> str | int:
    try:
        return int(raw_sheet)
    except ValueError:
        return raw_sheet


if __name__ == "__main__":
    raise SystemExit(main())

