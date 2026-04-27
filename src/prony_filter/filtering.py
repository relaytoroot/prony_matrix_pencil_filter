from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
from scipy import signal as scipy_signal

from .matrix_pencil import MatrixPencilResult, Mode, estimate_coefficients, matrix_pencil, reconstruct_from_poles
from .resonance import ResonanceBand, annotate_modes_for_resonance_bands, build_resonance_bands


@dataclass(slots=True)
class FilterResult:
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
) -> FilterResult:
    prepared = prepare_signal_segment(
        time=time,
        values=values,
        t0=t0,
        detrend=detrend,
        model_order=model_order,
        window_length_s=window_length_s,
    )
    segment_analysis = analyze_prepared_segment(
        prepared=prepared,
        model_order=model_order,
        remove_frequencies_hz=remove_frequencies_hz,
        tolerance_hz=tolerance_hz,
        relative_tolerance=relative_tolerance,
        remove_bands_hz=remove_bands_hz,
        pencil_parameter=pencil_parameter,
    )
    # uniform_time is normalized to the segment start, so interpolate on the
    # same relative axis when mapping results back to the original timestamps.
    segment_time_relative = prepared.segment_time - prepared.segment_time[0]
    removed_component = np.zeros_like(prepared.full_values, dtype=float)
    removed_component_segment = np.interp(
        segment_time_relative,
        prepared.uniform_time,
        segment_analysis.removed_component_uniform,
    )
    removed_component[prepared.segment_mask] = removed_component_segment
    filtered = prepared.full_values.copy()
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
    time_array, value_array = _prepare_time_series(time, values)
    segment_mask = time_array >= t0
    if window_length_s is not None:
        if window_length_s <= 0:
            raise ValueError("window_length_s must be positive")
        segment_mask &= time_array <= t0 + window_length_s
    if np.count_nonzero(segment_mask) < max(8, model_order + 4):
        raise ValueError("not enough samples after t0 for the selected model order")

    segment_time = time_array[segment_mask]
    segment_values = value_array[segment_mask]
    uniform_time, uniform_values = _resample_if_needed(segment_time, segment_values)
    dt = float(np.median(np.diff(uniform_time)))
    baseline = _baseline(uniform_values, detrend)
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
) -> SegmentAnalysisResult:
    analysis = matrix_pencil(
        prepared.residual,
        dt=prepared.dt,
        model_order=model_order,
        pencil_parameter=pencil_parameter,
    )

    absolute_tolerance = None if relative_tolerance is not None else tolerance_hz
    selection_bands = build_resonance_bands(
        remove_frequencies_hz=remove_frequencies_hz,
        tolerance_hz=absolute_tolerance,
        relative_tolerance=relative_tolerance,
        remove_bands_hz=remove_bands_hz,
    )
    remove_indices = annotate_modes_for_resonance_bands(analysis.modes, selection_bands)
    poles = np.array([mode.pole for mode in analysis.modes], dtype=complex)
    coefficients = estimate_coefficients(prepared.residual, poles)
    removed_component_uniform = np.zeros_like(prepared.uniform_values, dtype=float)
    if remove_indices:
        selected_poles = poles[remove_indices]
        selected_coefficients = coefficients[remove_indices]
        removed_component_uniform = reconstruct_from_poles(
            selected_poles,
            selected_coefficients,
            len(prepared.uniform_values),
        ).real
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


def _prepare_time_series(time: np.ndarray, values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
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
    if detrend == "none":
        return np.zeros_like(values)
    if detrend == "constant":
        return np.full_like(values, float(np.mean(values)))
    if detrend == "linear":
        return values - scipy_signal.detrend(values, type="linear")
    raise ValueError("detrend must be one of: none, constant, linear")
