from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .filtering import filter_known_modes
from .io import build_modes_frame, export_results, extract_time_signal, list_columns, read_table
from .plotting import save_comparison_plot, save_fft_plot
from .spectral import analyze_fft_spectrum, build_resonance_comparison_rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Filter damped oscillations after a step test.")
    parser.add_argument("--file", required=True, help="Input XLS/XLSX/CSV file")
    parser.add_argument("--sheet", default=0, help="Excel sheet name or index. Default: 0")
    parser.add_argument("--list-columns", action="store_true", help="Only list available columns and exit")
    parser.add_argument("--time-column", help="Name of the time column")
    parser.add_argument("--signal-column", help="Name of the signal column")
    parser.add_argument("--t0", type=float, help="Step time. Samples before this time are left unchanged")
    parser.add_argument("--remove", nargs="*", type=float, default=[], help="Known resonance frequencies to remove in Hz")
    parser.add_argument(
        "--remove-band",
        nargs=2,
        action="append",
        metavar=("LOW_HZ", "HIGH_HZ"),
        type=float,
        help="Explicit resonance band to remove, e.g. --remove-band 1.76 2.64",
    )
    parser.add_argument("--tol", type=float, help="Absolute frequency tolerance in Hz. Default: 0.2")
    parser.add_argument(
        "--rel-tol",
        type=float,
        help="Relative tolerance for each --remove target, e.g. 0.2 -> target +/- 20%",
    )
    parser.add_argument("--order", type=int, default=12, help="Matrix-Pencil model order")
    parser.add_argument(
        "--pencil",
        type=int,
        help="Optional Matrix-Pencil parameter. Smaller values are faster for large measurements.",
    )
    parser.add_argument(
        "--detrend",
        choices=("none", "constant", "linear"),
        default="constant",
        help="Baseline/trend handling before modal estimation",
    )
    parser.add_argument("--output-dir", default="outputs", help="Directory for CSV/Excel/plot outputs")
    parser.add_argument("--no-excel", action="store_true", help="Do not write results.xlsx")
    parser.add_argument("--fft", action="store_true", help="Also compute and export an FFT preview for the analysis segment")
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
    if args.rel_tol is not None and not args.remove:
        parser.error("--rel-tol requires at least one value in --remove")
    if args.rel_tol is not None and args.tol is not None:
        parser.error("--tol and --rel-tol are mutually exclusive")

    time, values, time_column, signal_column = extract_time_signal(
        frame,
        time_column=args.time_column,
        signal_column=args.signal_column,
    )
    print(f"Using time column: {time_column}")
    print(f"Using signal column: {signal_column}")
    tolerance_hz = 0.2 if args.rel_tol is None and args.tol is None else args.tol
    remove_bands_hz = None if args.remove_band is None else [(band[0], band[1]) for band in args.remove_band]

    result = filter_known_modes(
        time=time,
        values=values,
        t0=args.t0,
        remove_frequencies_hz=args.remove,
        tolerance_hz=tolerance_hz,
        relative_tolerance=args.rel_tol,
        remove_bands_hz=remove_bands_hz,
        model_order=args.order,
        detrend=args.detrend,
        pencil_parameter=args.pencil,
    )
    output_dir = Path(args.output_dir)
    fft_result = None
    resonance_comparison_rows = None
    if args.fft:
        fft_result = analyze_fft_spectrum(result.residual, dt=result.analysis.dt)
        if result.selection_bands:
            resonance_comparison_rows = build_resonance_comparison_rows(
                result.selection_bands,
                result.analysis.modes,
                fft_result,
            )

    written = export_results(
        result,
        output_dir=output_dir,
        write_excel=not args.no_excel,
        fft_result=fft_result,
        resonance_comparison_rows=resonance_comparison_rows,
    )
    plot_path = save_comparison_plot(result, output_dir / "comparison_plot.png")
    modes_frame = build_modes_frame(result)
    fft_plot_path = None
    fft_peaks_frame = None
    comparison_frame = None
    if fft_result is not None:
        fft_plot_path = save_fft_plot(fft_result, output_dir / "fft_plot.png")
        fft_peaks_frame = pd.DataFrame(fft_result.peaks_table())
        comparison_frame = pd.DataFrame(resonance_comparison_rows or [])

    print("\nDetected modes:")
    if modes_frame.empty:
        print("No modes detected")
    else:
        print(modes_frame.to_string(index=False))
    if fft_peaks_frame is not None:
        print("\nDominant FFT peaks:")
        if fft_peaks_frame.empty:
            print("No FFT peaks detected")
        else:
            print(fft_peaks_frame.to_string(index=False))
    if comparison_frame is not None and not comparison_frame.empty:
        print("\nResonance comparison:")
        print(comparison_frame.to_string(index=False))
    print("\nWritten files:")
    for key, path in written.items():
        print(f"- {key}: {path}")
    print(f"- plot: {plot_path}")
    if fft_plot_path is not None:
        print(f"- fft_plot: {fft_plot_path}")
    return 0


def _parse_sheet(raw_sheet: str) -> str | int:
    try:
        return int(raw_sheet)
    except ValueError:
        return raw_sheet


if __name__ == "__main__":
    raise SystemExit(main())
