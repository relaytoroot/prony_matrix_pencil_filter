r"""Pruefung mit bekannter Sollkurve: synthetisches Signal mit zwei Schwingungen.

Start im Projektordner:
    .\.venv\Scripts\python.exe examples\synthetic_reference.py

Das Signal ersetzt das in den Folien genannte, im Repository nicht vorhandene
Skript create_demo_measurement.py. Die Parameter wurden aus den gespeicherten
Diagrammdaten der Originalfolie 13 zurueckgerechnet und stimmen mit ihnen ueberein.
Ausgabe: outputs/synthetic_reference/synthetic_reference.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd

from prony_filter.filtering import filter_known_modes


ROOT = Path(__file__).resolve().parents[1]
DT = 0.01
STEP_TIME = 1.0


def build_signal() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Grundwertsprung 100 -> 120 bei 1 s plus zwei gedaempfte Schwingungen."""
    # 1200 Werte im Abstand 0,01 s: 0 bis 11,99 s.
    time = np.arange(1200) * DT
    tau = time - STEP_TIME
    after = time >= STEP_TIME
    base = np.where(after, 120.0, 100.0)
    # Zu entfernen: 2,24 Hz, Anfangsamplitude 3, Abklingrate -0,25 1/s.
    target = np.where(after, 3.0 * np.exp(-0.25 * tau) * np.cos(2 * np.pi * 2.24 * tau + 0.2), 0.0)
    # Zu erhalten: 5 Hz, Anfangsamplitude 0,8, Abklingrate -0,1 1/s, als Sinus.
    keep = np.where(after, 0.8 * np.exp(-0.10 * tau) * np.sin(2 * np.pi * 5.0 * tau), 0.0)
    return time, base + target + keep, base + keep, target


def main() -> None:
    time, values, expected, target = build_signal()
    # Ordnung 5: zwei Polpaare fuer die Schwingungen und ein reeller Pol fuer
    # den Gleichanteil, der nach der Mittelwertbereinigung im Abschnitt bleibt.
    result = filter_known_modes(time, values, t0=STEP_TIME, remove_frequencies_hz=[2.24],
                                relative_tolerance=0.2, model_order=5)
    deviation = result.filtered - expected

    print(f"Werte: {len(time)}, Zeitraster {DT * 1000:.0f} ms, {time[0]:.2f} bis {time[-1]:.2f} s")
    # Ein konjugiertes Polpaar erscheint zweimal; jede Schwingung nur einmal ausgeben.
    shown = set()
    for mode in result.modes:
        key = (round(mode.frequency_hz, 6), round(mode.damping, 6))
        if mode.frequency_hz > 0 and key not in shown:
            shown.add(key)
            print(f"Mode {mode.frequency_hz:.6f} Hz, Abklingrate {mode.damping:.6f} 1/s, "
                  f"Amplitude {mode.oscillation_amplitude:.6f}, entfernt: {mode.removed}")
    print(f"Relativer Modellfehler: {result.analysis.relative_fit_error:.3e}")
    print(f"Max |Ausgabe - Sollkurve|: {np.max(np.abs(deviation)):.3e}")
    print(f"Max |entfernter Anteil - 2,24-Hz-Anteil|: {np.max(np.abs(result.removed_component - target)):.3e}")

    output = ROOT / "outputs" / "synthetic_reference"
    output.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({
        "time": time,
        "input": values,
        "filtered": result.filtered,
        "expected": expected,
        "deviation": deviation,
    }).to_csv(output / "synthetic_reference.csv", index=False)
    print(f"Gespeichert: {output / 'synthetic_reference.csv'}")


if __name__ == "__main__":
    main()
