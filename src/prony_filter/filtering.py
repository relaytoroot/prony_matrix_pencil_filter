from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
from scipy import signal as scipy_signal

from .matrix_pencil import MatrixPencilResult, Mode, estimate_coefficients, matrix_pencil, reconstruct_from_poles


@dataclass(slots=True)
class FilterResult:
    time: np.ndarray
    original: np.ndarray
    filtered: np.ndarray
    removed_component: np.ndarray
    segment_time: np.ndarray
    segment_original: np.ndarray
    segment_filtered: np.ndarray
    modes: list[Mode]
    analysis: MatrixPencilResult


def filter_known_modes(
    time: np.ndarray,
    values: np.ndarray,
    t0: float,
    remove_frequencies_hz: Iterable[float] | None = None,
    tolerance_hz: float = 0.2,
    model_order: int = 12,
    detrend: str = "constant",
    pencil_parameter: int | None = None,
) -> FilterResult:
    time_array, value_array = _prepare_time_series(time, values)
    segment_mask = time_array >= t0
    if np.count_nonzero(segment_mask) < max(8, model_order + 4):
        raise ValueError("not enough samples after t0 for the selected model order")

    segment_time = time_array[segment_mask]
    segment_values = value_array[segment_mask]
    uniform_time, uniform_values = _resample_if_needed(segment_time, segment_values)
    dt = float(np.median(np.diff(uniform_time)))

    baseline = _baseline(uniform_values, detrend)
    residual = uniform_values - baseline
    analysis = matrix_pencil(
        residual,
        dt=dt,
        model_order=model_order,
        pencil_parameter=pencil_parameter,
    )

    remove_indices = _matching_mode_indices(analysis.modes, remove_frequencies_hz or [], tolerance_hz)
    poles = np.array([mode.pole for mode in analysis.modes], dtype=complex)
    coefficients = estimate_coefficients(residual, poles)
    removed_component_uniform = np.zeros_like(uniform_values, dtype=float)
    if remove_indices:
        selected_poles = poles[remove_indices]
        selected_coefficients = coefficients[remove_indices]
        removed_component_uniform = reconstruct_from_poles(
            selected_poles,
            selected_coefficients,
            len(uniform_values),
        ).real

    for mode in analysis.modes:
        mode.removed = mode.index in remove_indices

    filtered_uniform = uniform_values - removed_component_uniform
    segment_filtered = np.interp(segment_time, uniform_time, filtered_uniform)
    removed_component = np.zeros_like(value_array, dtype=float)
    removed_component[segment_mask] = np.interp(segment_time, uniform_time, removed_component_uniform)
    filtered = value_array.copy()
    filtered[segment_mask] = segment_filtered

    return FilterResult(
        time=time_array,
        original=value_array,
        filtered=filtered,
        removed_component=removed_component,
        segment_time=segment_time,
        segment_original=segment_values,
        segment_filtered=segment_filtered,
        modes=analysis.modes,
        analysis=analysis,
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


def _matching_mode_indices(modes: list[Mode], targets: Iterable[float], tolerance_hz: float) -> list[int]:
    if tolerance_hz < 0:
        raise ValueError("tolerance_hz must be non-negative")
    target_values = [abs(float(target)) for target in targets]
    if not target_values:
        return []
    indices: list[int] = []
    for mode in modes:
        if any(abs(mode.frequency_hz - target) <= tolerance_hz for target in target_values):
            indices.append(mode.index)
    return indices
