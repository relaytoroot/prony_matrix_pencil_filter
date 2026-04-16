from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import signal as scipy_signal

from .matrix_pencil import Mode
from .resonance import ResonanceBand


@dataclass(slots=True)
class FFTPeak:
    rank: int
    frequency_hz: float
    magnitude: float


@dataclass(slots=True)
class FFTSpectrumResult:
    frequencies_hz: np.ndarray
    magnitudes: np.ndarray
    peaks: list[FFTPeak]
    dt: float
    n_samples: int

    def spectrum_table(self) -> list[dict[str, float]]:
        return [
            {
                "frequency_hz": float(frequency_hz),
                "magnitude": float(magnitude),
            }
            for frequency_hz, magnitude in zip(self.frequencies_hz, self.magnitudes)
        ]

    def peaks_table(self) -> list[dict[str, float | int]]:
        return [
            {
                "peak_rank": peak.rank,
                "frequency_hz": peak.frequency_hz,
                "magnitude": peak.magnitude,
            }
            for peak in self.peaks
        ]


def analyze_fft_spectrum(
    signal: np.ndarray,
    dt: float,
    peak_count: int = 5,
    min_frequency_hz: float = 0.05,
) -> FFTSpectrumResult:
    values = np.asarray(signal, dtype=float)
    if values.ndim != 1:
        raise ValueError("signal must be one-dimensional")
    if len(values) < 4:
        raise ValueError("signal must contain at least 4 samples")
    if dt <= 0:
        raise ValueError("dt must be positive")
    if peak_count < 1:
        raise ValueError("peak_count must be at least 1")

    frequencies_hz = np.fft.rfftfreq(len(values), d=dt)
    spectrum = np.fft.rfft(values)
    magnitudes = 2.0 * np.abs(spectrum) / len(values)
    magnitudes[0] *= 0.5
    if len(values) % 2 == 0 and len(magnitudes) > 1:
        magnitudes[-1] *= 0.5

    peak_indices, _ = scipy_signal.find_peaks(magnitudes)
    peak_indices = peak_indices[frequencies_hz[peak_indices] >= min_frequency_hz]
    if len(peak_indices) == 0:
        candidate_indices = np.where(frequencies_hz >= min_frequency_hz)[0]
        if len(candidate_indices) > 0:
            peak_indices = candidate_indices[np.argsort(magnitudes[candidate_indices])[::-1][:peak_count]]
    else:
        peak_indices = peak_indices[np.argsort(magnitudes[peak_indices])[::-1][:peak_count]]

    peaks = [
        FFTPeak(
            rank=rank,
            frequency_hz=float(frequencies_hz[index]),
            magnitude=float(magnitudes[index]),
        )
        for rank, index in enumerate(peak_indices, start=1)
    ]
    return FFTSpectrumResult(
        frequencies_hz=frequencies_hz,
        magnitudes=magnitudes,
        peaks=peaks,
        dt=dt,
        n_samples=len(values),
    )


def build_resonance_comparison_rows(
    bands: list[ResonanceBand],
    modes: list[Mode],
    fft_result: FFTSpectrumResult | None,
) -> list[dict[str, float | int | bool | str | None]]:
    rows: list[dict[str, float | int | bool | str | None]] = []
    peaks = fft_result.peaks if fft_result is not None else []

    for selector_index, band in enumerate(bands):
        peak = _best_peak_for_band(peaks, band)
        mode = _best_mode_for_band(modes, band)
        peak_in_band = peak is not None and band.contains(peak.frequency_hz)
        mode_in_band = mode is not None and band.contains(mode.frequency_hz)

        rows.append(
            {
                "selector_index": selector_index,
                "target_frequency_hz": band.target_frequency_hz,
                "band_low_hz": band.low_hz,
                "band_high_hz": band.high_hz,
                "band_source": band.source,
                "fft_peak_rank": peak.rank if peak is not None else None,
                "fft_peak_frequency_hz": peak.frequency_hz if peak is not None else None,
                "fft_peak_magnitude": peak.magnitude if peak is not None else None,
                "fft_peak_in_band": peak_in_band,
                "mode_index": mode.index if mode is not None else None,
                "matrix_pencil_frequency_hz": mode.frequency_hz if mode is not None else None,
                "matrix_pencil_damping": mode.damping if mode is not None else None,
                "mode_in_band": mode_in_band,
                "removed": bool(mode.removed) if mode is not None else False,
                "selection_reason": mode.selection_reason if mode is not None else "no Matrix-Pencil mode available",
                "decision": _decision_text(band, peak, mode, peak_in_band, mode_in_band),
            }
        )

    return rows


def _best_peak_for_band(peaks: list[FFTPeak], band: ResonanceBand) -> FFTPeak | None:
    if not peaks:
        return None
    peaks_in_band = [peak for peak in peaks if band.contains(peak.frequency_hz)]
    if peaks_in_band:
        return max(peaks_in_band, key=lambda peak: peak.magnitude)
    return min(
        peaks,
        key=lambda peak: (
            band.distance_to_band_hz(peak.frequency_hz),
            abs(peak.frequency_hz - band.midpoint_hz),
            -peak.magnitude,
        ),
    )


def _best_mode_for_band(modes: list[Mode], band: ResonanceBand) -> Mode | None:
    if not modes:
        return None
    modes_in_band = [mode for mode in modes if band.contains(mode.frequency_hz)]
    if modes_in_band:
        return min(
            modes_in_band,
            key=lambda mode: (
                _target_distance_or_midpoint(mode.frequency_hz, band),
                mode.index,
            ),
        )
    return min(
        modes,
        key=lambda mode: (
            band.distance_to_band_hz(mode.frequency_hz),
            _target_distance_or_midpoint(mode.frequency_hz, band),
            mode.index,
        ),
    )


def _target_distance_or_midpoint(frequency_hz: float, band: ResonanceBand) -> float:
    target_distance = band.distance_to_target_hz(frequency_hz)
    if target_distance is not None:
        return target_distance
    return abs(abs(float(frequency_hz)) - band.midpoint_hz)


def _decision_text(
    band: ResonanceBand,
    peak: FFTPeak | None,
    mode: Mode | None,
    peak_in_band: bool,
    mode_in_band: bool,
) -> str:
    peak_text = "no FFT peak available"
    if peak is not None:
        peak_text = (
            f"FFT peak {peak.frequency_hz:.6f} Hz "
            f"{'inside' if peak_in_band else 'outside'} band"
        )

    mode_text = "no Matrix-Pencil mode available"
    if mode is not None:
        mode_text = (
            f"Matrix-Pencil mode {mode.frequency_hz:.6f} Hz "
            f"{'inside' if mode_in_band else 'outside'} band"
        )

    if mode_in_band:
        return (
            f"removed: {peak_text}; target band {band.low_hz:.6f}-{band.high_hz:.6f} Hz; "
            f"{mode_text}"
        )
    return (
        f"kept: {peak_text}; target band {band.low_hz:.6f}-{band.high_hz:.6f} Hz; "
        f"{mode_text}"
    )
