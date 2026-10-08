"""Vorführbeispiel: beide lokalen Sprungmessungen einlesen, auswerten und speichern.

In Git Bash aus dem Projektordner starten:
    ./.venv/Scripts/python.exe examples/presentation_demo.py

Eingabe: die beiden XLS-Dateien im Ordner data/, jeweils die Leistung P_pos
mit ihrer zugehörigen Zeitspalte. Ausgabe: Excel, Diagramme und Diagnosetabellen
unter outputs/presentation_demo/positive/ bzw. negative/ sowie summary.json.
"""
from pathlib import Path
import json

import numpy as np
from scipy.signal import detrend, windows

from prony_filter.filtering import filter_known_modes
from prony_filter.io import read_table, extract_time_signal, export_results
from prony_filter.plotting import save_comparison_plot
from prony_filter.resonance import representative_band_mode
from prony_filter.spectral import analyze_fft_spectrum, build_resonance_comparison_rows


ROOT = Path(__file__).resolve().parents[1]


def late_band_energy(time, values, dt):
    """Vergleicht die spektrale Bandenergie im festen Abschnitt von 4 bis 7 Sekunden.

    Original und bereinigtes Signal erhalten dieselbe lineare Trendbereinigung
    und dasselbe Hann-Fenster. Anschließend werden die quadrierten FFT-Beträge
    im Band 1,76 bis 2,64 Hz addiert. Dies ist eine spektrale Vergleichsgröße,
    keine physikalische Energie in Joule und kein Nachweis einer Resonanzursache.
    """
    selected = values[(time >= 4.0) & (time <= 7.0)]
    spectrum = np.fft.rfft(detrend(selected) * windows.hann(len(selected), sym=False))
    frequencies = np.fft.rfftfreq(len(selected), dt)
    return float(np.sum(np.abs(spectrum[(frequencies >= 1.76) & (frequencies <= 2.64)]) ** 2))


def main():
    """Führt den gesamten Ablauf für positiven und negativen Leistungssprung aus."""
    summary = []
    for name, filename in [
        ("positive", "Frequenz_Leistungs_Pendelung.XLS"),
        ("negative", "Frequenz_Leistungs_Pendelung_negativer_Sprung.XLS"),
    ]:
        source = ROOT / "data" / filename
        output = ROOT / "outputs" / "presentation_demo" / name
        # 1. Leistungssignal P_pos und die zugehörige Zeitachse aus Excel einlesen.
        time, values, _, signal_column = extract_time_signal(read_table(source), signal_column="P_pos")
        # 2. Ab t0 = 1 s analysieren. 2,2 Hz +/- 20 % ergibt 1,76 bis 2,64 Hz.
        # Modellordnung 12 erlaubt bis zu zwölf komplexe Exponentialanteile.
        # Geeignete Moden im Band rekonstruieren und vom Original abziehen.
        result = filter_known_modes(time, values, t0=1.0, remove_frequencies_hz=[2.2],
                                    relative_tolerance=0.2, model_order=12)
        # 3. FFT-Spektrum des Restsignals als zusätzlichen Frequenzvergleich berechnen.
        fft = analyze_fft_spectrum(result.residual, result.analysis.dt, peak_count=50)
        comparison = build_resonance_comparison_rows(result.selection_bands, result.modes, fft)
        # 4. Original, entfernten Anteil und bereinigtes Signal als Tabellen und
        # Diagramm auf den Messzeitpunkten ausgeben.
        export_results(result, output, source, signal_column, 1.0, fft_result=fft,
                       resonance_comparison_rows=comparison, debug=True)
        save_comparison_plot(result, output / "comparison_plot.png", signal_column)
        mode = representative_band_mode(result.modes, result.selection_bands[0])
        # 5. Abschwächung im Band messen und zwei Eigenschaften kontrollieren:
        # Vor dem Sprung bleibt das Signal gleich; Original - Abzug = Ergebnis.
        before = late_band_energy(result.time, result.original, result.analysis.dt)
        after = late_band_energy(result.time, result.filtered, result.analysis.dt)
        summary.append({
            "dataset": name,
            "frequency_hz": None if mode is None else mode.frequency_hz,
            "damping_per_s": None if mode is None else mode.damping,
            "cosine_amplitude": None if mode is None else mode.oscillation_amplitude,
            "removed": mode is not None and mode.removed,
            "estimation_rate_hz": result.analysis.estimation_rate_hz,
            "relative_fit_error": result.analysis.relative_fit_error,
            "late_band_energy_reduction_percent": 100 * (1 - after / before) if before else None,
            "pre_step_unchanged": bool(np.array_equal(result.original[result.time < 1], result.filtered[result.time < 1])),
            "subtraction_identity": bool(np.allclose(result.filtered, result.original - result.removed_component)),
        })
    text = json.dumps(summary, indent=2, ensure_ascii=False)
    (ROOT / "outputs" / "presentation_demo" / "summary.json").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
