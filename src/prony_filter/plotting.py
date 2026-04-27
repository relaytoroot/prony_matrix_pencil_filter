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
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(result.time, result.original, label=f"Original ({signal_label})", linewidth=1.2)
    ax.plot(result.time, result.removed_component, label="Entfernte Komponente", linewidth=1.2)
    ax.plot(result.time, result.filtered, label=f"Bereinigt ({signal_label})", linewidth=1.2)
    ax.set_title(title or f"{signal_label}: Original, entfernte Komponente und bereinigtes Signal")
    ax.set_xlabel("Zeit [s]")
    ax.set_ylabel(signal_label)
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def save_fft_plot(result: FFTSpectrumResult, path: str | Path, title: str = "FFT-Spektrum") -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(result.frequencies_hz, result.magnitudes, linewidth=1.2, label="FFT magnitude")
    if result.peaks:
        peak_frequencies = [peak.frequency_hz for peak in result.peaks]
        peak_magnitudes = [peak.magnitude for peak in result.peaks]
        ax.scatter(peak_frequencies, peak_magnitudes, color="tab:red", label="Dominant peaks", zorder=3)
    ax.set_title(title)
    ax.set_xlabel("Frequenz [Hz]")
    ax.set_ylabel("Magnitude")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path
