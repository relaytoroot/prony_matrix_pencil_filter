"""Ablauf der Filterung: Messdaten vorbereiten, Moden schätzen und abziehen.

Einstieg ist filter_known_modes(time, values, t0, ...). Die reine
Polberechnung liegt in matrix_pencil.py, die Bandauswahl in resonance.py.
Dieses Modul übernimmt Zeitfenster, Abtastraster, Trendbehandlung,
Qualitätsprüfung und Rückgabe auf den ursprünglichen Messzeitpunkten.

Begriffe: segment = Analyseabschnitt, uniform = gleichmäßig abgetastet,
baseline = Grundanteil (Mittelwert oder linearer Trend), residual = Messwerte
nach Abzug dieses Grundanteils, removed_component = entfernter Signalanteil.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
from scipy import signal as scipy_signal

from .matrix_pencil import (
    MatrixPencilResult,
    Mode,
    estimate_coefficients,
    matrix_pencil,
    matrix_pencil_rayleigh,
    reconstruct_from_poles,
    modes_from_poles,
)
from .resonance import ResonanceBand, annotate_modes_for_resonance_bands, build_resonance_bands


@dataclass(slots=True)
class FilterResult:
    """Original, entfernter Anteil und bereinigtes Signal samt Analyseergebnis.

    time/original/filtered beziehen sich auf die gültigen, sortierten
    Messpunkte. segment_* enthält nur das gewählte Analysefenster;
    uniform_* beschreibt dessen gegebenenfalls vereinheitlichtes Zeitraster.
    Es gilt filtered = original - removed_component.
    """

    time: np.ndarray
    original: np.ndarray
    filtered: np.ndarray
    removed_component: np.ndarray
    segment_time: np.ndarray
    segment_original: np.ndarray
    segment_filtered: np.ndarray
    uniform_time: np.ndarray
    uniform_values: np.ndarray
    baseline: np.ndarray
    residual: np.ndarray
    modes: list[Mode]
    analysis: MatrixPencilResult
    selection_bands: list[ResonanceBand]


@dataclass(slots=True)
class PreparedSignalSegment:
    """Vorbereitete Messwerte und Zuordnung zum vollständigen Signal.

    segment_mask markiert die Messpunkte im gewählten Zeitfenster.
    uniform_time beginnt bei null; dt ist der Abtastabstand in Sekunden.
    residual = uniform_values - baseline ist das Signal für die Modenschätzung.
    """

    full_time: np.ndarray
    full_values: np.ndarray
    segment_mask: np.ndarray
    segment_time: np.ndarray
    segment_values: np.ndarray
    uniform_time: np.ndarray
    uniform_values: np.ndarray
    baseline: np.ndarray
    residual: np.ndarray
    dt: float
    detrend: str
    t0: float
    window_length_s: float | None


@dataclass(slots=True)
class SegmentAnalysisResult:
    """Analyse, Modenauswahl und Filterergebnis auf dem gleichmäßigen Zeitraster."""

    prepared: PreparedSignalSegment
    modes: list[Mode]
    analysis: MatrixPencilResult
    selection_bands: list[ResonanceBand]
    remove_indices: list[int]
    removed_component_uniform: np.ndarray
    filtered_uniform: np.ndarray


def filter_known_modes(
    time: np.ndarray,
    values: np.ndarray,
    t0: float,
    remove_frequencies_hz: Iterable[float] | None = None,
    tolerance_hz: float = 0.2,
    relative_tolerance: float | None = None,
    remove_bands_hz: Iterable[tuple[float, float]] | None = None,
    model_order: int = 12,
    detrend: str = "constant",
    pencil_parameter: int | None = None,
    window_length_s: float | None = None,
    eigen_solver: str = "dense",
    rayleigh_initial_damping: float = 0.0,
    analysis_rate_hz: float | None = None,
    max_damping_ratio: float = 0.3,
) -> FilterResult:
    """Entfernt zugelassene Schwingungsanteile innerhalb des Analysefensters.

    time: Messzeitpunkte in Sekunden; values: zugehörige Signalwerte.
    t0: Beginn der Analyse; window_length_s: optionale Fensterlänge ab t0.
    remove_frequencies_hz und Toleranz bzw. remove_bands_hz legen fest,
    in welchen Frequenzbereichen Schwingungen entfernt werden dürfen.
    model_order begrenzt die Anzahl komplexer Exponentialanteile.

    Ablauf: vorbereiten -> schätzen und auswählen -> rekonstruieren -> abziehen.
    Messwerte außerhalb des Fensters bleiben erhalten. Die Rückgabe enthält
    zusätzlich Grundanteil, Restsignal, Moden und Angaben zur Modellanpassung.
    """
    # 1. Zeitfenster auswählen, Abtastraster prüfen und Grundanteil bestimmen.
    prepared = prepare_signal_segment(
        time=time,
        values=values,
        t0=t0,
        detrend=detrend,
        model_order=model_order,
        window_length_s=window_length_s,
    )
    # 2. Schwingungen schätzen und die zur Entfernung geeigneten Anteile wählen.
    segment_analysis = analyze_prepared_segment(
        prepared=prepared,
        model_order=model_order,
        remove_frequencies_hz=remove_frequencies_hz,
        tolerance_hz=tolerance_hz,
        relative_tolerance=relative_tolerance,
        remove_bands_hz=remove_bands_hz,
        pencil_parameter=pencil_parameter,
        eigen_solver=eigen_solver,
        rayleigh_initial_damping=rayleigh_initial_damping,
        analysis_rate_hz=analysis_rate_hz,
        max_damping_ratio=max_damping_ratio,
    )
    # 3. Den rekonstruierten Anteil auf die Messzeitpunkte zurückübertragen.
    # Beide Zeitachsen müssen relativ zum Anfang des Analyseabschnitts sein.
    segment_time_relative = prepared.segment_time - prepared.segment_time[0]
    removed_component = np.zeros_like(prepared.full_values, dtype=float)
    removed_component_segment = np.interp(
        segment_time_relative,
        prepared.uniform_time,
        segment_analysis.removed_component_uniform,
    )
    removed_component[prepared.segment_mask] = removed_component_segment
    filtered = prepared.full_values.copy()
    # 4. Bereinigtes Signal = Originalsignal - ausgewählte Schwingungsanteile.
    filtered[prepared.segment_mask] = prepared.segment_values - removed_component_segment
    segment_filtered = filtered[prepared.segment_mask]

    return FilterResult(
        time=prepared.full_time,
        original=prepared.full_values,
        filtered=filtered,
        removed_component=removed_component,
        segment_time=prepared.segment_time,
        segment_original=prepared.segment_values,
        segment_filtered=segment_filtered,
        uniform_time=prepared.uniform_time,
        uniform_values=prepared.uniform_values,
        baseline=prepared.baseline,
        residual=prepared.residual,
        modes=segment_analysis.analysis.modes,
        analysis=segment_analysis.analysis,
        selection_bands=segment_analysis.selection_bands,
    )


def prepare_signal_segment(
    time: np.ndarray,
    values: np.ndarray,
    t0: float,
    detrend: str = "constant",
    model_order: int = 12,
    window_length_s: float | None = None,
) -> PreparedSignalSegment:
    """Wählt Messwerte ab t0 aus und bereitet sie für die Modenschätzung vor.

    Ungültige Werte und doppelte Zeitpunkte werden entfernt, Zeiten sortiert.
    Ein ungleichmäßiges Zeitraster wird durch lineare Interpolation vereinheitlicht.
    detrend='constant' zieht den Mittelwert ab, 'linear' einen linearen Trend,
    'none' lässt die Werte für die Analyse unverändert.
    """
    time_array, value_array = _prepare_time_series(time, values)
    if not np.isfinite(t0):
        raise ValueError("t0 must be finite")
    segment_mask = time_array >= t0
    if window_length_s is not None:
        if not np.isfinite(window_length_s) or window_length_s <= 0:
            raise ValueError("window_length_s must be finite and positive")
        segment_mask &= time_array <= t0 + window_length_s
    if np.count_nonzero(segment_mask) < max(8, model_order + 4):
        raise ValueError("not enough samples after t0 for the selected model order")

    segment_time = time_array[segment_mask]
    segment_values = value_array[segment_mask]
    uniform_time, uniform_values = _resample_if_needed(segment_time, segment_values)
    # Alle benachbarten Zeitabstände berücksichtigen: dt = Median der Differenzen.
    dt = float(np.median(np.diff(uniform_time)))
    baseline = _baseline(uniform_values, detrend)
    # Das Restsignal enthält die Anteile, die Matrix Pencil modellieren soll.
    residual = uniform_values - baseline
    return PreparedSignalSegment(
        full_time=time_array,
        full_values=value_array,
        segment_mask=segment_mask,
        segment_time=segment_time,
        segment_values=segment_values,
        uniform_time=uniform_time,
        uniform_values=uniform_values,
        baseline=baseline,
        residual=residual,
        dt=dt,
        detrend=detrend,
        t0=t0,
        window_length_s=window_length_s,
    )


def analyze_prepared_segment(
    prepared: PreparedSignalSegment,
    model_order: int,
    remove_frequencies_hz: Iterable[float] | None = None,
    tolerance_hz: float = 0.2,
    relative_tolerance: float | None = None,
    remove_bands_hz: Iterable[tuple[float, float]] | None = None,
    pencil_parameter: int | None = None,
    eigen_solver: str = "dense",
    rayleigh_initial_damping: float = 0.0,
    analysis_rate_hz: float | None = None,
    max_damping_ratio: float = 0.3,
) -> SegmentAnalysisResult:
    """Schätzt Moden, prüft ihre Eignung und rekonstruiert den zu entfernenden Anteil.

    Die Pole werden bei Bedarf auf einem gröberen, tiefpassgefilterten Raster
    geschätzt. Anschließend werden alle Koeffizienten gemeinsam an das Restsignal
    auf dem ursprünglichen Analyseraster angepasst. Frequenzband, Dämpfung und
    Anpassungsfehler entscheiden, welche Anteile tatsächlich entfernt werden.
    """
    absolute_tolerance = None if relative_tolerance is not None else tolerance_hz
    remove_frequencies = [] if remove_frequencies_hz is None else list(remove_frequencies_hz)
    remove_bands = None if remove_bands_hz is None else list(remove_bands_hz)
    selection_bands = build_resonance_bands(
        remove_frequencies_hz=remove_frequencies,
        tolerance_hz=absolute_tolerance,
        relative_tolerance=relative_tolerance,
        remove_bands_hz=remove_bands,
    )
    estimation_signal, factor = _prepare_estimation_signal(prepared, selection_bands, analysis_rate_hz)
    estimation_dt = prepared.dt * factor
    rayleigh_poles = None
    if eigen_solver == "dense":
        analysis = matrix_pencil(
            estimation_signal,
            dt=estimation_dt,
            model_order=model_order,
            pencil_parameter=pencil_parameter,
        )
    elif eigen_solver == "rayleigh":
        initial_frequencies = _rayleigh_initial_frequencies(remove_frequencies, remove_bands)
        analysis = matrix_pencil_rayleigh(
            estimation_signal,
            dt=estimation_dt,
            model_order=model_order,
            initial_frequencies_hz=initial_frequencies,
            initial_damping=rayleigh_initial_damping,
            pencil_parameter=pencil_parameter,
        )
        rayleigh_poles = np.array([mode.pole for mode in analysis.modes])
        # Zusätzliche Signalanteile mit anpassen: Ein einzelnes Zielpolpaar
        # könnte sonst Sprunganteile oder andere Schwingungen mit aufnehmen.
        analysis = matrix_pencil(
            estimation_signal, dt=estimation_dt, model_order=model_order,
            pencil_parameter=pencil_parameter,
        )
    else:
        raise ValueError("eigen_solver must be one of: dense, rayleigh")
    # Pole vom gröberen auf das ursprüngliche Analyseraster übertragen:
    # z_original = exp(log(z_grob) / factor). Koeffizienten dort neu bestimmen.
    # Der Tiefpass dient nur der Polschätzung; subtrahiert wird auf den Messwerten.
    poles = np.exp(np.log(np.array([mode.pole for mode in analysis.modes], dtype=complex)) / factor)
    coefficients = estimate_coefficients(prepared.residual, poles)
    analysis = MatrixPencilResult(
        modes=modes_from_poles(poles, coefficients, prepared.dt),
        dt=prepared.dt,
        model_order=analysis.model_order,
        reconstruction=reconstruct_from_poles(poles, coefficients, len(prepared.residual)).real,
        estimation_dt=estimation_dt,
        decimation_factor=factor,
    )
    fit_reconstruction = analysis.reconstruction if factor == 1 else scipy_signal.resample_poly(
        analysis.reconstruction, 1, factor, padtype="line"
    )
    # Relativer Anpassungsfehler = ||Modell - Signal|| / ||Signal|| im Schätzraster.
    analysis.relative_fit_error = float(np.linalg.norm(fit_reconstruction - estimation_signal) / max(np.linalg.norm(estimation_signal), 1e-12))
    remove_indices = annotate_modes_for_resonance_bands(analysis.modes, selection_bands, max_damping_ratio)
    if rayleigh_poles is not None:
        for mode in analysis.modes:
            if mode.removed and not np.any(np.abs(mode.pole ** factor - rayleigh_poles) < 1e-6):
                mode.removed = False
                mode.selection_reason = "kept: not selected by Rayleigh iteration"
        remove_indices = [mode.index for mode in analysis.modes if mode.removed]
    removed_component_uniform = np.zeros_like(prepared.uniform_values, dtype=float)
    if remove_indices:
        selected_poles = poles[remove_indices]
        selected_coefficients = coefficients[remove_indices]
        removed_component_uniform = reconstruct_from_poles(
            selected_poles,
            selected_coefficients,
            len(prepared.uniform_values),
        ).real
    # Bei schlechter Anpassung oder auffällig großem Abzugsanteil bleibt das
    # Original erhalten. Diese Grenzen sind Prüfregeln, kein Resonanznachweis.
    fit_error = analysis.relative_fit_error
    rejection = ""
    if fit_error > 0.1:
        rejection = f"kept: relative reconstruction error {fit_error:.3f} exceeds 0.1"
    elif np.linalg.norm(removed_component_uniform) > 1.25 * np.linalg.norm(prepared.residual):
        rejection = "kept: removed component exceeds 1.25 times residual norm; modal cancellation suspected"
    if rejection:
        for mode in analysis.modes:
            if mode.removed:
                mode.removed = False
                mode.selection_reason = rejection
        remove_indices = []
        removed_component_uniform.fill(0.0)
    filtered_uniform = prepared.uniform_values - removed_component_uniform
    return SegmentAnalysisResult(
        prepared=prepared,
        modes=analysis.modes,
        analysis=analysis,
        selection_bands=selection_bands,
        remove_indices=remove_indices,
        removed_component_uniform=removed_component_uniform,
        filtered_uniform=filtered_uniform,
    )


def _prepare_estimation_signal(
    prepared: PreparedSignalSegment,
    bands: list[ResonanceBand],
    analysis_rate_hz: float | None,
) -> tuple[np.ndarray, int]:
    """Verringert die Abtastrate für die Polschätzung mit vorgeschaltetem Tiefpass.

    Automatische Zielrate: mindestens 100 Hz bzw. zehn Messwerte pro Periode
    an der oberen Bandgrenze, sofern die Eingangsrate dies erlaubt. Ohne Band
    oder mit analysis_rate_hz=0 bleibt die Rate erhalten. Der Tiefpass verhindert,
    dass hohe Frequenzen beim Herunterabtasten als niedrige erscheinen (Aliasing).
    Rückgabe: Signal für die Polschätzung und ganzzahliger Reduktionsfaktor.
    """
    highest_frequency = max((band.high_hz for band in bands), default=0.0)
    input_rate = 1.0 / prepared.dt
    if highest_frequency >= input_rate / 2:
        raise ValueError("resonance band must lie below the input Nyquist frequency")
    if analysis_rate_hz is None:
        analysis_rate_hz = max(100.0, 10.0 * highest_frequency) if bands else input_rate
    if not np.isfinite(analysis_rate_hz) or analysis_rate_hz < 0:
        raise ValueError("analysis_rate_hz must be finite and non-negative (0 disables reduction)")
    factor = 1 if analysis_rate_hz == 0 else max(1, int(np.floor(input_rate / analysis_rate_hz + 1e-9)))
    if factor > 1 and highest_frequency and input_rate / factor < 4.0 * highest_frequency:
        raise ValueError("analysis rate must provide at least four samples per period at the band edge")
    if factor == 1:
        return prepared.residual, factor
    return scipy_signal.resample_poly(prepared.residual, 1, factor, padtype="line"), factor


def _prepare_time_series(time: np.ndarray, values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Entfernt ungültige Werte, sortiert Zeiten und behält jeden Zeitpunkt einmal."""
    time_array = np.asarray(time, dtype=float)
    value_array = np.asarray(values, dtype=float)
    if time_array.ndim != 1 or value_array.ndim != 1:
        raise ValueError("time and values must be one-dimensional")
    if len(time_array) != len(value_array):
        raise ValueError("time and values must have the same length")
    valid = np.isfinite(time_array) & np.isfinite(value_array)
    time_array = time_array[valid]
    value_array = value_array[valid]
    if len(time_array) < 8:
        raise ValueError("time series contains too few valid samples")
    order = np.argsort(time_array)
    time_array = time_array[order]
    value_array = value_array[order]
    unique_time, unique_indices = np.unique(time_array, return_index=True)
    return unique_time, value_array[unique_indices]


def _resample_if_needed(time: np.ndarray, values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Prüft alle Zeitabstände und interpoliert bei Bedarf auf ein gleichmäßiges Raster."""
    diffs = np.diff(time)
    dt = float(np.median(diffs))
    if dt <= 0:
        raise ValueError("time must be strictly increasing")
    if np.allclose(diffs, dt, rtol=1e-3, atol=max(1e-12, dt * 1e-6)):
        return time - time[0], values
    uniform_time = np.arange(time[0], time[-1] + dt * 0.5, dt)
    uniform_values = np.interp(uniform_time, time, values)
    return uniform_time - uniform_time[0], uniform_values


def _baseline(values: np.ndarray, detrend: str) -> np.ndarray:
    """Bestimmt den abzuziehenden Grundanteil: null, Mittelwert oder linearen Trend."""
    if detrend == "none":
        return np.zeros_like(values)
    if detrend == "constant":
        return np.full_like(values, float(np.mean(values)))
    if detrend == "linear":
        return values - scipy_signal.detrend(values, type="linear")
    raise ValueError("detrend must be one of: none, constant, linear")


def _rayleigh_initial_frequencies(
    remove_frequencies_hz: list[float],
    remove_bands_hz: list[tuple[float, float]] | None,
) -> list[float]:
    """Leitet Startfrequenzen für Rayleigh aus Zielwerten oder Bandmitten ab."""
    frequencies = [abs(float(frequency)) for frequency in remove_frequencies_hz]
    if remove_bands_hz is not None:
        frequencies.extend(0.5 * (abs(float(low_hz)) + abs(float(high_hz))) for low_hz, high_hz in remove_bands_hz)
    if not frequencies:
        raise ValueError("rayleigh eigen_solver requires --remove or --remove-band as initial frequency guess")
    unique: list[float] = []
    for frequency in frequencies:
        if not any(abs(frequency - existing) <= 1e-9 for existing in unique):
            unique.append(frequency)
    return unique
