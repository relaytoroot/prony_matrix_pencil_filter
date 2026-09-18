from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd

from .filtering import filter_known_modes
from .resonance import modes_in_resonance_bands, physical_modes, representative_band_mode


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
                    band_modes = physical_modes(modes_in_resonance_bands(result.analysis.modes, result.selection_bands))
                    representatives = [representative_band_mode(result.analysis.modes, band) for band in result.selection_bands]
                    representative_mode = next((mode for mode in representatives if mode is not None and mode.removed), None)
                    if representative_mode is None:
                        representative_mode = next((mode for mode in representatives if mode is not None), None)
                    band_frequencies = "; ".join(f"{mode.frequency_hz:.6f}" for mode in band_modes)
                    band_dampings = "; ".join(f"{mode.damping:.6f}" for mode in band_modes)

                    rows.append(
                        {
                            "model_order": model_order,
                            "t0_s": current_t0,
                            "t0_offset_s": t0_offset_s,
                            "window_length_s": window_length_s,
                            "band_match_count": sum(mode.removed for mode in band_modes),
                            "band_candidate_count": len(band_modes),
                            "estimation_rate_hz": result.analysis.estimation_rate_hz,
                            "relative_reconstruction_error": result.analysis.relative_fit_error,
                            "band_mode_frequencies_hz": band_frequencies,
                            "band_mode_dampings": band_dampings,
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


def build_stability_summary_markdown(result_frame: pd.DataFrame) -> str:
    total_runs = len(result_frame)
    successful = result_frame[(result_frame["error"] == "") & (result_frame["band_match_count"] > 0)]
    failed = result_frame[result_frame["error"] != ""]
    missing_band_match = result_frame[(result_frame["error"] == "") & (result_frame["band_match_count"] == 0)]

    lines = [
        "# Stability Summary",
        "",
        f"- Analysed configurations: {total_runs}",
        f"- Configurations with at least one accepted mode in the resonance band: {len(successful)}",
        f"- Configurations without an accepted band mode: {len(missing_band_match)}",
        f"- Configurations that failed before estimation: {len(failed)}",
        "",
    ]

    if not successful.empty:
        frequencies = successful["representative_mode_frequency_hz"].dropna().astype(float)
        dampings = successful["representative_mode_damping"].dropna().astype(float)
        lines.extend(
            [
                "## Representative band mode statistics",
                "",
                f"- Frequency mean: {frequencies.mean():.6f} Hz",
                f"- Frequency min/max: {frequencies.min():.6f} / {frequencies.max():.6f} Hz",
                f"- Frequency std: {frequencies.std(ddof=0):.6f} Hz",
                f"- Damping mean: {dampings.mean():.6f} 1/s",
                f"- Damping min/max: {dampings.min():.6f} / {dampings.max():.6f} 1/s",
                "",
                "## Successful configurations",
                "",
            ]
        )
        lines.append("| order | t0 [s] | window [s] | representative frequency [Hz] | band frequencies [Hz] |")
        lines.append("| --- | ---: | ---: | ---: | --- |")
        for row in successful.itertuples(index=False):
            window_value = "full" if pd.isna(row.window_length_s) else f"{float(row.window_length_s):.2f}"
            lines.append(
                f"| {int(row.model_order)} | {float(row.t0_s):.2f} | {window_value} | "
                f"{float(row.representative_mode_frequency_hz):.6f} | {row.band_mode_frequencies_hz or '-'} |"
            )
        lines.append("")

    if not missing_band_match.empty:
        lines.extend(["## Configurations without a band match", ""])
        lines.append("| order | t0 [s] | window [s] | closest mode [Hz] | reason |")
        lines.append("| --- | ---: | ---: | ---: | --- |")
        for row in missing_band_match.itertuples(index=False):
            window_value = "full" if pd.isna(row.window_length_s) else f"{float(row.window_length_s):.2f}"
            closest_value = "-" if pd.isna(row.representative_mode_frequency_hz) else f"{float(row.representative_mode_frequency_hz):.6f}"
            lines.append(
                f"| {int(row.model_order)} | {float(row.t0_s):.2f} | {window_value} | "
                f"{closest_value} | {row.selection_reason or '-'} |"
            )
        lines.append("")

    if not failed.empty:
        lines.extend(["## Failed configurations", ""])
        lines.append("| order | t0 [s] | window [s] | error |")
        lines.append("| --- | ---: | ---: | --- |")
        for row in failed.itertuples(index=False):
            window_value = "full" if pd.isna(row.window_length_s) else f"{float(row.window_length_s):.2f}"
            lines.append(f"| {int(row.model_order)} | {float(row.t0_s):.2f} | {window_value} | {row.error} |")
        lines.append("")

    return "\n".join(lines)
