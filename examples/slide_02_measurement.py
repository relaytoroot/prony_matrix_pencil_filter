r"""Messkurve fuer Folie 2 mit expliziten Achsen und Darstellungsfaktor.

Start im Projektordner:
    .\.venv\Scripts\python.exe examples\slide_02_measurement.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MultipleLocator
import numpy as np

from prony_filter.io import extract_time_signal, read_table


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    source = ROOT / "data" / "Frequenz_Leistungs_Pendelung_negativer_Sprung.XLS"
    time, values, time_column, signal_column = extract_time_signal(
        read_table(source), signal_column="P_pos"
    )

    # Die Zeitspalte gehoert zum Leistungskanal; der Zeitursprung bleibt erhalten.
    # Die Toleranz schliesst den Excel-Wert 7.00000000003 s am Fensterrand ein.
    selected = (
        np.isfinite(time)
        & np.isfinite(values)
        & (time >= 2.0 - 1e-9)
        & (time <= 7.0 + 1e-9)
    )
    # Fuer die Anzeige kuerzere Zahlen verwenden: 6 900 000 wird zu 6,90.
    # Es erfolgen weder eine Filterung noch ein Mittelwertabzug.
    displayed_values = values[selected] / 1_000_000

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(time[selected], displayed_values, color="#246b91", linewidth=1.2)
    ax.set_title("Negative Frequenzsprungantwort: Messkanal P_pos", pad=16)
    ax.set_xlabel("Zeit (s)")
    ax.set_ylabel("P_pos / 10⁶ (Dateieinheit)")

    # Dieselben linearen Achsengrenzen und Teilstriche wie in der vorhandenen Folie 2.
    # PowerPoint zaehlt den Hauptschritt 0,03 ab dem Minimum 6,85, nicht ab null.
    ax.set_xlim(2.0, 7.0)
    ax.set_ylim(6.85, 7.00)
    ax.xaxis.set_major_locator(MultipleLocator(1.0))
    ax.set_yticks(np.linspace(6.85, 7.00, 6))
    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda value, _position: f"{value:.2f}".replace(".", ","))
    )
    ax.grid(True, color="#d8e1e7", linewidth=0.7)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(
        0.5,
        0.025,
        "Anzeigewert 6,90 entspricht 6 900 000 in der Datei. "
        "Die physikalische Einheit ist nicht dokumentiert.",
        ha="center",
        fontsize=9,
        color="#445566",
    )
    fig.tight_layout(rect=(0, 0.065, 1, 1))

    output = ROOT / "outputs" / "folienaufbau"
    output.mkdir(parents=True, exist_ok=True)
    for suffix in ("png", "svg"):
        fig.savefig(output / f"folie_02_messkurve.{suffix}", dpi=180)
    plt.close(fig)

    step = np.median(np.diff(time[selected]))
    print(f"Spalten: {time_column} -> {signal_column}")
    print(f"Gezeigte Messpunkte: {selected.sum()}")
    print(f"Zeitraster: {step * 1000:.2f} ms, also {1 / step:.0f} Werte pro Sekunde")
    print(
        f"Wertebereich: {values[selected].min():.0f} bis {values[selected].max():.0f} in der Datei, "
        f"angezeigt {displayed_values.min():.3f} bis {displayed_values.max():.3f}"
    )
    print(f"Grafik: {output / 'folie_02_messkurve.png'}")


if __name__ == "__main__":
    main()
