"""Startskript für die Parameterstudie auf einer eingelesenen Messdatei.

Start in Git Bash: ./.venv/Scripts/python.exe examples/stability_scan.py --help
Die Berechnungen übernimmt prony_filter.stability; hier stehen Einlesen und Ausgabe.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from prony_filter.io import extract_time_signal, read_table
from prony_filter.stability import build_stability_summary_markdown, run_stability_scan


def build_parser() -> argparse.ArgumentParser:
    """Definiert Eingabedatei und zu vergleichende Modellordnungen und Zeitfenster."""
    parser = argparse.ArgumentParser(description="Empfindlichkeit der Matrix-Pencil-Schätzung gegenüber den Analyseparametern prüfen.")
    parser.add_argument("--file", required=True, help="Eingabedatei im Format XLS, XLSX oder CSV")
    parser.add_argument("--sheet", default=0, help="Name oder Index des Excel-Blatts; Standard: 0")
    parser.add_argument("--time-column", help="Name der Zeitspalte")
    parser.add_argument("--signal-column", help="Name der Signalspalte")
    parser.add_argument("--t0", type=float, required=True, help="Ausgangswert des Analysebeginns in Sekunden")
    parser.add_argument("--output-dir", default="outputs/stability_scan", help="Ausgabeordner für Tabelle und Bericht")
    parser.add_argument("--remove", nargs="*", type=float, default=[2.2], help="Zielresonanzfrequenzen in Hz")
    parser.add_argument(
        "--remove-band",
        nargs=2,
        action="append",
        metavar=("LOW_HZ", "HIGH_HZ"),
        type=float,
        help="Direkte Bandgrenzen in Hz, z. B. --remove-band 1.76 2.64",
    )
    parser.add_argument("--tol", type=float, default=0.2, help="Absolute Frequenztoleranz in Hz")
    parser.add_argument("--rel-tol", type=float, default=0.2, help="Relative Toleranz für die Zielwerte aus --remove")
    parser.add_argument(
        "--orders",
        nargs="*",
        type=int,
        default=[8, 10, 12, 14, 16],
        help="Zu untersuchende Modellordnungen",
    )
    parser.add_argument(
        "--t0-offsets",
        nargs="*",
        type=float,
        default=[-0.02, 0.0, 0.02],
        help="Verschiebungen gegenüber t0 in Sekunden",
    )
    parser.add_argument(
        "--window-seconds",
        nargs="*",
        type=float,
        default=[3.0, 5.0, 7.0],
        help="Fensterlängen ab dem jeweiligen Analysebeginn in Sekunden",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Liest Messwerte, führt die Parameterstudie aus und speichert CSV und Bericht."""
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
    print(f"\nParameterstudie gespeichert unter {output_path}")
    print(f"Zusammenfassung gespeichert unter {summary_path}")
    return 0


def _parse_sheet(raw_sheet: str) -> str | int:
    try:
        return int(raw_sheet)
    except ValueError:
        return raw_sheet


if __name__ == "__main__":
    raise SystemExit(main())
