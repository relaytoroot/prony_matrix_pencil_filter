"""Matrix-Pencil-Versuche für den Signalgenerator und den lokalen Messkatalog."""

from __future__ import annotations

from functools import lru_cache

import numpy as np

from .filtering import analyze_prepared_segment, prepare_signal_segment
from .io import extract_time_signal, read_table
from .labor_catalog import catalog, xls_path
from .resonance import physical_modes


PENCIL_COLUMNS = 256


def _number(settings, key, label, default, minimum, maximum):
    value = settings.get(key, default)
    if type(value) not in (int, float) or not minimum <= value <= maximum:
        raise ValueError(f"{label} muss zwischen {minimum:g} und {maximum:g} liegen.")
    return float(value)


def _synthetic_signal(settings):
    time = np.arange(800) / 100.0
    values = np.zeros_like(time)
    for i, frequency, amplitude, decay, phase in [
        (1, 3, 4, 0.4, 0.3),
        (2, 7, 0, 0.2, -0.4),
    ]:
        frequency = _number(settings, f"f{i}", f"Frequenz {i}", frequency, 0.25, 40)
        amplitude = _number(settings, f"a{i}", f"Amplitude {i}", amplitude, 0, 12)
        decay = _number(settings, f"d{i}", f"Abklingrate {i}", decay, 0, 2)
        values += amplitude * np.exp(-decay * time) * np.cos(2 * np.pi * frequency * time + phase)

    # Dieselbe Rauschfolge erlaubt einen direkten Vergleich zweier Einstellungen.
    noise = _number(settings, "noise", "Rauschstärke", 0, 0, 2)
    values += noise * np.random.default_rng(42).standard_normal(len(time))
    if not np.any(values):
        raise ValueError("Das Eingangssignal ist überall null. Erhöhe eine Amplitude oder füge Rauschen hinzu.")
    return time, values


@lru_cache(maxsize=32)
def _measurement(source):
    entry = catalog()[source]
    if "csvPath" in entry:
        points = np.loadtxt(entry["csvPath"], delimiter=",", skiprows=1)
        return points[:, 0], points[:, 1]
    path = xls_path(source)
    if not path.is_file():
        raise ValueError(f"Die Messdatei {path.name} fehlt im Datenordner des Projekts.")
    time, values, _, _ = extract_time_signal(read_table(path), signal_column="P_pos")
    return time, values


def _selection_status(result):
    if result.remove_indices:
        return ""
    band = result.selection_bands[0]
    candidates = [mode for mode in result.modes if band.contains(mode.frequency_hz)]
    if not candidates:
        return "Keine geschätzte Mode liegt im Zielband. Im gefilterten Signal bleiben alle Anteile erhalten."
    if result.analysis.relative_fit_error > 0.1:
        return "Der Modellfehler übersteigt 10 %. Der Filter behält die Moden im Signal."
    if any("modal cancellation" in mode.selection_reason for mode in candidates):
        return "Der geschätzte Abzug ist zu groß. Der Filter behält die Moden im Signal."
    return "Die Moden im Zielband wachsen oder klingen zu stark ab. Der Filter behält sie im Signal."


def analyze(settings: dict) -> dict:
    """Berechnet die Kurven und physikalischen Moden für einen Laborversuch.

    Alle Kurven haben dieselben absoluten Zeitpunkte im Analysefenster.
    Bei Messungen umfasst das Modell auch den zuvor abgezogenen Mittelwert.
    Der relative Fitfehler bezieht sich auf das Signal nach Abzug des
    Grundanteils bei der Abtastrate der Polschätzung. Eine positive Abklingrate
    entspricht dem Parameter d in A * exp(-d*t) * cos(2*pi*f*t + phase).
    """
    if not isinstance(settings, dict):
        raise ValueError("Für die Analyse wird ein Objekt mit Signalparametern benötigt.")
    source = settings.get("source", "synthetic")
    if not isinstance(source, str) or source not in catalog():
        raise ValueError("Wähle einen Versuch aus dem Messkatalog.")
    entry = catalog()[source]
    synthetic = source == "synthetic"
    order = _number(settings, "order", "Modellordnung", entry["order"], 2, 12)
    if order not in (2, 4, 6, 8, 10, 12):
        raise ValueError("Wähle eine gerade Modellordnung zwischen 2 und 12.")
    target = _number(settings, "target", "Zielfrequenz", entry["target"], entry["minTarget"], entry["maxTarget"])
    tolerance = _number(settings, "tolerance", "Bandtoleranz", entry["tolerance"], entry["minTolerance"], entry["maxTolerance"])

    time, values = _synthetic_signal(settings) if synthetic else _measurement(source)
    prepared = prepare_signal_segment(
        time, values, t0=entry["t0"],
        detrend="none" if synthetic else "constant", model_order=int(order),
    )
    try:
        result = analyze_prepared_segment(
            prepared, model_order=int(order),
            remove_frequencies_hz=[target], tolerance_hz=tolerance,
            pencil_parameter=PENCIL_COLUMNS,
            analysis_rate_hz=entry.get("analysisRateHz"),
        )
    except (np.linalg.LinAlgError, ValueError, FloatingPointError) as exc:
        raise ValueError("Die Modenschätzung ist für diese Einstellung numerisch instabil. "
                         "Versuche eine kleinere Modellordnung.") from exc

    # Die Schätzung nutzt alle Daten. Für die Anzeige genügt ein gemeinsames
    # Teilraster, das auch den ersten und letzten Zeitpunkt enthält.
    count = len(prepared.uniform_time)
    # Kleine CSV-Ausschnitte vollständig übertragen, damit auch schnelle
    # Schwingungen im Zeitzoom am ursprünglichen Raster ablesbar sind.
    plot_count = count if "csvPath" in entry else min(count, 1600)
    indices = np.linspace(0, count - 1, plot_count, dtype=int)
    analysis = result.analysis
    # resample_poly liefert bei Reduktion um q genau ceil(N/q) Werte.
    factor = analysis.decimation_factor
    estimation_count = (count + factor - 1) // factor
    columns = min(estimation_count // 2, PENCIL_COLUMNS)
    modes = sorted(physical_modes(result.modes), key=lambda mode: mode.frequency_hz)
    return {
        "time": (prepared.segment_time[0] + prepared.uniform_time[indices]).tolist(),
        "signal": prepared.uniform_values[indices].tolist(),
        "model": (analysis.reconstruction[indices] + prepared.baseline[indices]).tolist(),
        "filtered": result.filtered_uniform[indices].tolist(),
        "removed": result.removed_component_uniform[indices].tolist(),
        "modes": [
            {
                "frequency": mode.frequency_hz,
                "decay": -mode.damping,
                "amplitude": mode.oscillation_amplitude,
                "phase": mode.phase_rad,
                "poleReal": float((mode.pole ** factor).real),
                "poleImag": float((mode.pole ** factor).imag),
                "selected": mode.removed,
            }
            for mode in modes
        ],
        "sampleCount": count,
        "pencil": {"rows": estimation_count - columns, "columns": columns, "rank": int(analysis.model_order),
                   "samples": result.estimation_preview},
        "sampleRate": 1.0 / prepared.dt,
        "analysisRate": analysis.estimation_rate_hz,
        "fitError": analysis.relative_fit_error,
        "unit": entry["unit"],
        "status": _selection_status(result),
    }
