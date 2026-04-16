from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd

from .filtering import filter_known_modes


def run_stability_scan(
    time: np.ndarray,
    values: np.ndarray,
    t0: float,
    model_orders: Iterable[int],
    t0_offsets_s: Iterable[float],
    remove_frequencies_hz: Iterable[float] | None = None,
    tolerance_hz: float = 0.2,
    relative_tolerance: float | None = None,
    remove_bands_hz: Iterable[tuple[float, float]] | None = None,
    detrend: str = "constant",
    pencil_parameter: int | None = None,
    window_lengths_s: Iterable[float | None] | None = None,
) -> pd.DataFrame:
    time_array = np.asarray(time, dtype=float)
    value_array = np.asarray(values, dtype=float)
    rows: list[dict[str, object]] = []
    scan_windows = list(window_lengths_s) if window_lengths_s is not None else [None]

    for model_order in model_orders:
        for t0_offset_s in t0_offsets_s:
            current_t0 = float(t0 + t0_offset_s)
            for window_length_s in scan_windows:
                try:
                    truncated_time, truncated_values = _truncate_window(
                        time_array,
                        value_array,
                        current_t0=current_t0,
                        window_length_s=window_length_s,
                    )
                    result = filter_known_modes(
                        time=truncated_time,
                        values=truncated_values,
                        t0=current_t0,
                        remove_frequencies_hz=remove_frequencies_hz,
                        tolerance_hz=tolerance_hz,
                        relative_tolerance=relative_tolerance,
                        remove_bands_hz=remove_bands_hz,
                        model_order=model_order,
                        detrend=detrend,
                        pencil_parameter=pencil_parameter,
                    )
                    representative_mode = _representative_mode(result.analysis.modes)
                    modes_in_band = [mode for mode in result.analysis.modes if mode.removed]

                    rows.append(
                        {
                            "model_order": model_order,
                            "t0_s": current_t0,
                            "t0_offset_s": t0_offset_s,
                            "window_length_s": window_length_s,
                            "band_match_count": len(modes_in_band),
                            "representative_mode_index": None if representative_mode is None else representative_mode.index,
                            "representative_mode_frequency_hz": None
                            if representative_mode is None
                            else representative_mode.frequency_hz,
                            "representative_mode_damping": None
                            if representative_mode is None
                            else representative_mode.damping,
                            "representative_removed": False if representative_mode is None else representative_mode.removed,
                            "target_frequency_hz": None if representative_mode is None else representative_mode.target_frequency_hz,
                            "band_low_hz": None if representative_mode is None else representative_mode.band_low_hz,
                            "band_high_hz": None if representative_mode is None else representative_mode.band_high_hz,
                            "selection_reason": None if representative_mode is None else representative_mode.selection_reason,
                            "error": "",
                        }
                    )
                except ValueError as exc:
                    rows.append(
                        {
                            "model_order": model_order,
                            "t0_s": current_t0,
                            "t0_offset_s": t0_offset_s,
                            "window_length_s": window_length_s,
                            "band_match_count": 0,
                            "representative_mode_index": None,
                            "representative_mode_frequency_hz": None,
                            "representative_mode_damping": None,
                            "representative_removed": False,
                            "target_frequency_hz": None,
                            "band_low_hz": None,
                            "band_high_hz": None,
                            "selection_reason": "",
                            "error": str(exc),
                        }
                    )

    return pd.DataFrame(rows)


def _truncate_window(
    time: np.ndarray,
    values: np.ndarray,
    current_t0: float,
    window_length_s: float | None,
) -> tuple[np.ndarray, np.ndarray]:
    if window_length_s is None:
        return time, values
    if window_length_s <= 0:
        raise ValueError("window_length_s must be positive")
    end_time = current_t0 + window_length_s
    mask = time <= end_time
    if np.count_nonzero(mask) < 8:
        raise ValueError("window_length_s leaves too few samples")
    return time[mask], values[mask]


def _representative_mode(modes: list) -> object | None:
    if not modes:
        return None
    removed_modes = [mode for mode in modes if mode.removed]
    if removed_modes:
        return min(
            removed_modes,
            key=lambda mode: (
                mode.distance_to_target_hz if mode.distance_to_target_hz is not None else 0.0,
                mode.index,
            ),
        )
    return min(
        modes,
        key=lambda mode: (
            float("inf") if mode.band_low_hz is None else _distance_to_band(mode.frequency_hz, mode.band_low_hz, mode.band_high_hz),
            mode.index,
        ),
    )


def _distance_to_band(frequency_hz: float, low_hz: float | None, high_hz: float | None) -> float:
    if low_hz is None or high_hz is None:
        return float("inf")
    frequency = abs(float(frequency_hz))
    if low_hz <= frequency <= high_hz:
        return 0.0
    return min(abs(frequency - low_hz), abs(frequency - high_hz))
