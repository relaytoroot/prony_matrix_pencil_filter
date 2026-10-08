"""Öffentliche Schnittstellen zur Schwingungsanalyse und Filterung.

Diese Datei bündelt Importe, etwa ``from prony_filter import filter_known_modes``.
Die mathematischen Berechnungen stehen in den jeweiligen Fachmodulen.
"""

from .filtering import FilterResult, filter_known_modes
from .matrix_pencil import Mode, MatrixPencilResult, matrix_pencil, matrix_pencil_rayleigh, rayleigh_quotient_iteration
from .resonance import ResonanceBand
from .spectral import FFTPeak, FFTSpectrumResult, analyze_fft_spectrum
from .stability import run_stability_scan

__all__ = [
    "analyze_fft_spectrum",
    "FFTPeak",
    "FFTSpectrumResult",
    "FilterResult",
    "Mode",
    "MatrixPencilResult",
    "filter_known_modes",
    "matrix_pencil",
    "matrix_pencil_rayleigh",
    "rayleigh_quotient_iteration",
    "ResonanceBand",
    "run_stability_scan",
]
