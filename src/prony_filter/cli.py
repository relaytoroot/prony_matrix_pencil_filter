"""Programmeinstieg für die Bedienung im Terminal.

Start in Git Bash: ./.venv/Scripts/python.exe -m prony_filter.cli --help
main() liest die Optionen, lädt Messwerte, ruft die Filterung auf und speichert
Tabellen und Diagramme. Die mathematischen Verfahren stehen in den Fachmodulen.
Die Optionsnamen bleiben für bestehende Startbefehle unverändert.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .filtering import filter_known_modes
from .io import build_report_tables, export_results, extract_time_signal, list_columns, read_table
from .plotting import save_comparison_plot, save_fft_plot
from .spectral import analyze_fft_spectrum, build_resonance_comparison_rows


def build_parser() -> argparse.ArgumentParser:
    """Definiert die Terminaloptionen und erklärt ihre Bedeutung auf Deutsch."""
    parser = argparse.ArgumentParser(description="Gedämpfte Schwingungen nach einem Sprungtest analysieren und entfernen.")
    parser.add_argument("--file", required=True, help="Eingabedatei im Format XLS, XLSX oder CSV")
    parser.add_argument("--sheet", default=0, help="Name oder Index des Excel-Blatts; Standard: 0 (erstes Blatt)")
    parser.add_argument("--list-columns", action="store_true", help="Verfügbare Spalten anzeigen und beenden")
    parser.add_argument("--time-column", help="Name der Zeitspalte; Zeitwerte in Sekunden")
    parser.add_argument(
        "--signal-column",
        default="P_pos",
        help="Name der Signalspalte; Standard: P_pos (Leistung)",
    )
    parser.add_argument("--t0", type=float, help="Beginn des Analysefensters in Sekunden; frühere Werte bleiben erhalten")
    parser.add_argument("--remove", nargs="*", type=float, default=[], help="Zielresonanzfrequenzen der zu entfernenden Schwingungen in Hz")
    parser.add_argument(
        "--remove-band",
        nargs=2,
        action="append",
        metavar=("LOW_HZ", "HIGH_HZ"),
        type=float,
        help="Unter- und Obergrenze des Resonanzbands in Hz, z. B. --remove-band 1.76 2.64",
    )
    parser.add_argument("--tol", type=float, help="Absolute Frequenztoleranz in Hz; Standard: 0.2")
    parser.add_argument(
        "--rel-tol",
        type=float,
        help="Relative Toleranz je Zielwert aus --remove, z. B. 0.2 entspricht +/- 20 %%",
    )
    parser.add_argument("--order", type=int, default=12, help="Modellordnung: maximale Anzahl komplexer Exponentialanteile; Standard: 12")
    parser.add_argument("--analysis-rate", type=float, help="Abtastrate für die Polschätzung in Hz; automatisch bei Bandwahl, 0 erhält die Eingangsrate")
    parser.add_argument("--window-seconds", type=float, help="Dauer des Analyse- und Filterfensters ab t0 in Sekunden")
    parser.add_argument("--max-damping-ratio", type=float, default=0.3, help="Maximales Dämpfungsverhältnis zeta der entfernbaren Moden (0 < zeta <= 1); Standard: 0.3")
    parser.add_argument(
        "--pencil",
        type=int,
        help="Anzahl der Hankel-Spalten im Schätzraster; kleinere Werte verringern den Rechenaufwand",
    )
    parser.add_argument(
        "--detrend",
        choices=("none", "constant", "linear"),
        default="constant",
        help="Grundanteil vor der Schätzung: none = keiner, constant = Mittelwert, linear = linearer Trend",
    )
    parser.add_argument(
        "--eigen-solver",
        choices=("dense", "rayleigh"),
        default="dense",
        help="Eigenwertverfahren: dense = alle Eigenwerte (Standard); rayleigh = gezielte Suche nahe den Zielwerten mit ergänzender Gesamtschätzung",
    )
    parser.add_argument(
        "--rayleigh-initial-damping",
        type=float,
        default=0.0,
        help="Startschätzung des Dämpfungsexponenten d in 1/s für Rayleigh; Standard: 0.0",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs",
        help="Ausgabeordner für result.xlsx, comparison_plot.png und optionale Diagnosedateien",
    )
    parser.add_argument("--no-excel", action="store_true", help="Keine Excel-Ergebnisdatei schreiben")
    parser.add_argument(
        "--fft",
        action="store_true",
        help="Kompatibilitätsoption; der FFT-Vergleich wird bereits automatisch berechnet",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Zusätzliche Diagnosedateien wie CSV-Tabellen und FFT-Diagramm speichern",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Führt Einlesen, Filterung, FFT-Vergleich und Ausgabe nacheinander aus."""
    parser = build_parser()
    args = parser.parse_args(argv)
    sheet = _parse_sheet(args.sheet)
    frame = read_table(args.file, sheet_name=sheet)

    if args.list_columns:
        print("Verfügbare Spalten:")
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
    print(f"Verwendete Zeitspalte: {time_column}")
    print(f"Verwendete Signalspalte: {signal_column}")
    tolerance_hz = 0.2 if args.rel_tol is None and args.tol is None else args.tol
    remove_bands_hz = None if args.remove_band is None else [(band[0], band[1]) for band in args.remove_band]

    # Zeit- und Signalwerte an den Filterablauf übergeben; die CLI rechnet keine Pole selbst.
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
        eigen_solver=args.eigen_solver,
        rayleigh_initial_damping=args.rayleigh_initial_damping,
        analysis_rate_hz=args.analysis_rate,
        window_length_s=args.window_seconds,
        max_damping_ratio=args.max_damping_ratio,
    )
    output_dir = Path(args.output_dir)
    # Ergänzender FFT-Vergleich auf demselben vorbereiteten Restsignal.
    fft_result = analyze_fft_spectrum(result.residual, dt=result.analysis.dt, peak_count=50)
    resonance_comparison_rows = None
    if result.selection_bands:
        resonance_comparison_rows = build_resonance_comparison_rows(
            result.selection_bands,
            result.analysis.modes,
            fft_result,
        )

    report = build_report_tables(
        result,
        input_path=args.file,
        signal_column=signal_column,
        t0=args.t0,
        fft_result=fft_result,
        resonance_comparison_rows=resonance_comparison_rows,
    )
    written = export_results(
        result,
        output_dir=output_dir,
        input_path=args.file,
        signal_column=signal_column,
        t0=args.t0,
        write_excel=not args.no_excel,
        debug=args.debug,
        fft_result=fft_result,
        resonance_comparison_rows=resonance_comparison_rows,
        report=report,
    )
    plot_path = save_comparison_plot(
        result,
        output_dir / "comparison_plot.png",
        signal_label=signal_column,
    )

    print("\nZusammenfassung:")
    print(f"- Abtastrate der Polschätzung: {result.analysis.estimation_rate_hz:.6f} Hz (Faktor {result.analysis.decimation_factor})")
    for field in (
        "Zielresonanz",
        "Resonanzband",
        "Staerkster FFT-Peak im Resonanzband",
        "Ausgewaehlte Matrix-Pencil-Mode",
        "Daempfung",
        "Amplitude",
        "Entscheidung",
    ):
        print(f"- {field}: {report.summary_items[field]}")

    if report.warnings:
        print("\nHinweise:")
        for warning in report.warnings:
            print(f"- {warning}")

    if args.debug:
        fft_plot_path = save_fft_plot(
            fft_result,
            output_dir / "fft_plot.png",
            title=f"{signal_column}: FFT-Spektrum des Analysefensters",
        )
        written["fft_plot"] = fft_plot_path
        if not report.modes_frame.empty:
            print("\nModen in den Resonanzbändern:")
            print(report.modes_frame.to_string(index=False))
        if report.fft_peaks_frame is not None and not report.fft_peaks_frame.empty:
            print("\nDominante FFT-Spektralspitzen:")
            print(report.fft_peaks_frame.to_string(index=False))
        if report.resonance_comparison_frame is not None and not report.resonance_comparison_frame.empty:
            print("\nResonanzvergleich:")
            print(report.resonance_comparison_frame.to_string(index=False))

    print("\nGespeicherte Dateien:")
    for key, path in written.items():
        print(f"- {key}: {path}")
    print(f"- comparison_plot: {plot_path}")
    return 0


def _parse_sheet(raw_sheet: str) -> str | int:
    try:
        return int(raw_sheet)
    except ValueError:
        return raw_sheet


if __name__ == "__main__":
    raise SystemExit(main())
