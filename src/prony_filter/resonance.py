from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .matrix_pencil import Mode


@dataclass(slots=True)
class ResonanceBand:
    low_hz: float
    high_hz: float
    target_frequency_hz: float | None = None
    source: str = "explicit_band"
    tolerance_hz: float | None = None
    relative_tolerance: float | None = None

    def __post_init__(self) -> None:
        self.low_hz = float(self.low_hz)
        self.high_hz = float(self.high_hz)
        if self.low_hz < 0 or self.high_hz < 0:
            raise ValueError("resonance band frequencies must be non-negative")
        if self.low_hz > self.high_hz:
            raise ValueError("resonance band low_hz must be <= high_hz")
        if self.target_frequency_hz is not None:
            self.target_frequency_hz = abs(float(self.target_frequency_hz))
        if self.tolerance_hz is not None and self.tolerance_hz < 0:
            raise ValueError("tolerance_hz must be non-negative")
        if self.relative_tolerance is not None and self.relative_tolerance < 0:
            raise ValueError("relative_tolerance must be non-negative")

    @property
    def midpoint_hz(self) -> float:
        return 0.5 * (self.low_hz + self.high_hz)

    def contains(self, frequency_hz: float) -> bool:
        frequency = abs(float(frequency_hz))
        return self.low_hz <= frequency <= self.high_hz

    def distance_to_band_hz(self, frequency_hz: float) -> float:
        frequency = abs(float(frequency_hz))
        if self.contains(frequency):
            return 0.0
        return min(abs(frequency - self.low_hz), abs(frequency - self.high_hz))

    def distance_to_target_hz(self, frequency_hz: float) -> float | None:
        if self.target_frequency_hz is None:
            return None
        return abs(abs(float(frequency_hz)) - self.target_frequency_hz)


def build_resonance_bands(
    remove_frequencies_hz: Iterable[float] | None = None,
    tolerance_hz: float | None = None,
    relative_tolerance: float | None = None,
    remove_bands_hz: Iterable[tuple[float, float]] | None = None,
) -> list[ResonanceBand]:
    if relative_tolerance is not None and relative_tolerance < 0:
        raise ValueError("relative_tolerance must be non-negative")
    if tolerance_hz is not None and tolerance_hz < 0:
        raise ValueError("tolerance_hz must be non-negative")

    bands: list[ResonanceBand] = []

    if remove_frequencies_hz is not None:
        for target in remove_frequencies_hz:
            target_value = abs(float(target))
            if relative_tolerance is not None:
                width = target_value * relative_tolerance
                bands.append(
                    ResonanceBand(
                        low_hz=max(0.0, target_value - width),
                        high_hz=target_value + width,
                        target_frequency_hz=target_value,
                        source="relative_tolerance",
                        relative_tolerance=relative_tolerance,
                    )
                )
            else:
                width = float(tolerance_hz or 0.0)
                bands.append(
                    ResonanceBand(
                        low_hz=max(0.0, target_value - width),
                        high_hz=target_value + width,
                        target_frequency_hz=target_value,
                        source="absolute_tolerance",
                        tolerance_hz=width,
                    )
                )

    if remove_bands_hz is not None:
        for low_hz, high_hz in remove_bands_hz:
            bands.append(
                ResonanceBand(
                    low_hz=float(low_hz),
                    high_hz=float(high_hz),
                    source="explicit_band",
                )
            )

    return bands


def annotate_modes_for_resonance_bands(modes: list[Mode], bands: list[ResonanceBand]) -> list[int]:
    if not bands:
        for mode in modes:
            mode.removed = False
            mode.target_frequency_hz = None
            mode.band_low_hz = None
            mode.band_high_hz = None
            mode.distance_to_target_hz = None
            mode.selection_reason = "kept: no resonance band configured"
        return []

    removed_indices: list[int] = []
    for mode in modes:
        matching_band = _best_band_for_mode(mode.frequency_hz, bands, require_inside=True)
        nearest_band = matching_band or _best_band_for_mode(mode.frequency_hz, bands, require_inside=False)
        if nearest_band is None:
            mode.removed = False
            mode.target_frequency_hz = None
            mode.band_low_hz = None
            mode.band_high_hz = None
            mode.distance_to_target_hz = None
            mode.selection_reason = "kept: no resonance band configured"
            continue

        mode.target_frequency_hz = nearest_band.target_frequency_hz
        mode.band_low_hz = nearest_band.low_hz
        mode.band_high_hz = nearest_band.high_hz
        mode.distance_to_target_hz = nearest_band.distance_to_target_hz(mode.frequency_hz)
        mode.removed = matching_band is not None
        mode.selection_reason = _selection_reason(mode, nearest_band, removed=mode.removed)
        if mode.removed:
            removed_indices.append(mode.index)

    return removed_indices


def _best_band_for_mode(
    frequency_hz: float,
    bands: list[ResonanceBand],
    require_inside: bool,
) -> ResonanceBand | None:
    candidates = bands if not require_inside else [band for band in bands if band.contains(frequency_hz)]
    if not candidates:
        return None
    return min(candidates, key=lambda band: _band_sort_key(frequency_hz, band))


def _band_sort_key(frequency_hz: float, band: ResonanceBand) -> tuple[float, float, float]:
    band_distance = band.distance_to_band_hz(frequency_hz)
    target_distance = band.distance_to_target_hz(frequency_hz)
    if target_distance is None:
        target_distance = abs(abs(float(frequency_hz)) - band.midpoint_hz)
    width = band.high_hz - band.low_hz
    return (band_distance, target_distance, width)


def _selection_reason(mode: Mode, band: ResonanceBand, removed: bool) -> str:
    action = "removed" if removed else "kept"
    if band.source == "relative_tolerance" and band.target_frequency_hz is not None:
        return (
            f"{action}: {'within' if removed else 'outside'} resonance band "
            f"{band.low_hz:.6f}-{band.high_hz:.6f} Hz around target "
            f"{band.target_frequency_hz:.6f} Hz (relative tolerance {band.relative_tolerance:.3f})"
        )
    if band.source == "absolute_tolerance" and band.target_frequency_hz is not None:
        return (
            f"{action}: {'within' if removed else 'outside'} resonance band "
            f"{band.low_hz:.6f}-{band.high_hz:.6f} Hz around target "
            f"{band.target_frequency_hz:.6f} Hz (absolute tolerance {band.tolerance_hz:.6f} Hz)"
        )
    return (
        f"{action}: {'within' if removed else 'outside'} explicit resonance band "
        f"{band.low_hz:.6f}-{band.high_hz:.6f} Hz"
    )
