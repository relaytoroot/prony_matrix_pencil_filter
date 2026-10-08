"""Stellt vorhandene Analyseergebnisse als Signal- und Frequenzdiagramme dar."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from .filtering import FilterResult
from .spectral import FFTSpectrumResult


def save_comparison_plot(
    result: FilterResult,
    path: str | Path,
    signal_label: str,
    title: str | None = None,
) -> Path:
    """Speichert Gesamtverlauf, vergrößerten Ausschnitt und entfernten Signalanteil."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    for ax in axes[:2]:
        ax.plot(result.time, result.original, label="Original", linewidth=1.1)
        ax.plot(result.time, result.filtered, label="Bereinigt", linewidth=1.1)
    axes[0].set_title(title or f"{signal_label}: Sprungantwort und Bereinigung")
    # Die spätere Schwingung vergrößert zeigen, damit sie neben dem großen Sprung sichtbar bleibt.
    zoom_start = result.segment_time[0] + 0.5 * (result.segment_time[-1] - result.segment_time[0])
    zoom = (result.time >= zoom_start) & (result.time <= result.segment_time[-1])
    axes[1].set_xlim(zoom_start, result.segment_time[-1])
    low = min(result.original[zoom].min(), result.filtered[zoom].min())
    high = max(result.original[zoom].max(), result.filtered[zoom].max())
    margin = max((high - low) * 0.1, abs(low) * 1e-9, 1e-9)
    axes[1].set_ylim(low - margin, high + margin)
    axes[1].set_title("Detail: zweite Hälfte des Analysefensters")
    axes[2].plot(result.time, result.removed_component, color="tab:orange", label="Entfernte Schwingungen")
    for ax in axes:
        ax.set_xlabel("Zeit [s]")
        ax.set_ylabel(signal_label)
        ax.grid(True, alpha=0.3)
        ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def save_fft_plot(result: FFTSpectrumResult, path: str | Path, title: str = "FFT-Spektrum") -> Path:
    """Speichert das FFT-Betragsspektrum und markiert die ausgewählten Spitzen."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(result.frequencies_hz, result.magnitudes, linewidth=1.2, label="FFT-Betrag")
    if result.peaks:
        peak_frequencies = [peak.frequency_hz for peak in result.peaks]
        peak_magnitudes = [peak.magnitude for peak in result.peaks]
        ax.scatter(peak_frequencies, peak_magnitudes, color="tab:red", label="Dominante Spektralspitzen", zorder=3)
    ax.set_title(title)
    ax.set_xlabel("Frequenz [Hz]")
    ax.set_ylabel("Normierter FFT-Betrag")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path
