"""Tools for Prony and Matrix-Pencil based oscillation filtering."""

from .filtering import FilterResult, filter_known_modes
from .matrix_pencil import Mode, MatrixPencilResult, matrix_pencil
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
    "ResonanceBand",
    "run_stability_scan",
]
