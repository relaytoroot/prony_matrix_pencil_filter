from __future__ import annotations

import argparse
from pathlib import Path

from prony_filter.io import extract_time_signal, read_table
from prony_filter.stability import build_stability_summary_markdown, run_stability_scan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scan Matrix-Pencil stability across nearby parameter choices.")
    parser.add_argument("--file", required=True, help="Input XLS/XLSX/CSV file")
    parser.add_argument("--sheet", default=0, help="Excel sheet name or index. Default: 0")
    parser.add_argument("--time-column", help="Name of the time column")
    parser.add_argument("--signal-column", help="Name of the signal column")
    parser.add_argument("--t0", type=float, required=True, help="Base step time")
    parser.add_argument("--output-dir", default="outputs/stability_scan", help="Directory for CSV output")
    parser.add_argument("--remove", nargs="*", type=float, default=[2.2], help="Resonance target frequencies in Hz")
    parser.add_argument(
        "--remove-band",
        nargs=2,
        action="append",
        metavar=("LOW_HZ", "HIGH_HZ"),
        type=float,
        help="Explicit resonance band, e.g. --remove-band 1.76 2.64",
    )
    parser.add_argument("--tol", type=float, default=0.2, help="Absolute tolerance in Hz")
    parser.add_argument("--rel-tol", type=float, default=0.2, help="Relative tolerance for --remove targets")
    parser.add_argument(
        "--orders",
        nargs="*",
        type=int,
        default=[8, 10, 12, 14, 16],
        help="Model orders to test",
    )
    parser.add_argument(
        "--t0-offsets",
        nargs="*",
        type=float,
        default=[-0.02, 0.0, 0.02],
        help="Offsets around t0 in seconds",
    )
    parser.add_argument(
        "--window-seconds",
        nargs="*",
        type=float,
        default=[3.0, 5.0, 7.0],
        help="Optional analysis window lengths in seconds after each t0",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    frame = read_table(args.file, sheet_name=_parse_sheet(args.sheet))
    time, values, _, _ = extract_time_signal(
        frame,
        time_column=args.time_column,
        signal_column=args.signal_column,
    )

    result_frame = run_stability_scan(
        time=time,
        values=values,
        t0=args.t0,
        model_orders=args.orders,
        t0_offsets_s=args.t0_offsets,
        remove_frequencies_hz=args.remove,
        tolerance_hz=args.tol,
        relative_tolerance=args.rel_tol,
        remove_bands_hz=args.remove_band,
        window_lengths_s=args.window_seconds,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "stability_report.csv"
    summary_path = output_dir / "stability_summary.md"
    result_frame.to_csv(output_path, index=False)
    summary_path.write_text(build_stability_summary_markdown(result_frame), encoding="utf-8")

    print(result_frame.to_string(index=False))
    print(f"\nWritten stability scan to {output_path}")
    print(f"Written summary to {summary_path}")
    return 0


def _parse_sheet(raw_sheet: str) -> str | int:
    try:
        return int(raw_sheet)
    except ValueError:
        return raw_sheet


if __name__ == "__main__":
    raise SystemExit(main())
