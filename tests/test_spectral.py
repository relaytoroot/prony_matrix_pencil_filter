from __future__ import annotations

import numpy as np

from prony_filter.matrix_pencil import Mode
from prony_filter.resonance import annotate_modes_for_resonance_bands, build_resonance_bands
from prony_filter.spectral import analyze_fft_spectrum, build_resonance_comparison_rows


def test_fft_detects_peak_near_known_frequency() -> None:
    dt = 0.01
    time = np.arange(0, 8, dt)
    signal = np.cos(2 * np.pi * 2.24 * time)

    result = analyze_fft_spectrum(signal, dt=dt, peak_count=3)

    assert result.peaks
    assert abs(result.peaks[0].frequency_hz - 2.24) < 0.05


def test_fft_and_matrix_pencil_comparison_uses_resonance_band() -> None:
    dt = 0.01
    time = np.arange(0, 8, dt)
    signal = np.cos(2 * np.pi * 2.24 * time)
    fft_result = analyze_fft_spectrum(signal, dt=dt, peak_count=3)

    mode = Mode(
        index=0,
        pole=1 + 0j,
        coefficient=1 + 0j,
        frequency_hz=1.921094,
        damping=-10.0,
        amplitude=1.0,
        phase_rad=0.0,
    )
    bands = build_resonance_bands(remove_frequencies_hz=[2.2], relative_tolerance=0.2)
    annotate_modes_for_resonance_bands([mode], bands)

    rows = build_resonance_comparison_rows(bands, [mode], fft_result)

    assert len(rows) == 1
    assert rows[0]["fft_peak_in_band"] is True
    assert rows[0]["mode_in_band"] is True
    assert rows[0]["removed"] is True
    assert "removed:" in str(rows[0]["decision"])
