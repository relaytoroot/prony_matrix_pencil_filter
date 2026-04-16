from __future__ import annotations

import pytest

from prony_filter.matrix_pencil import Mode
from prony_filter.resonance import annotate_modes_for_resonance_bands, build_resonance_bands


def test_relative_tolerance_builds_resonance_band() -> None:
    bands = build_resonance_bands(remove_frequencies_hz=[2.2], relative_tolerance=0.2)

    assert len(bands) == 1
    assert bands[0].target_frequency_hz == pytest.approx(2.2)
    assert bands[0].low_hz == pytest.approx(1.76)
    assert bands[0].high_hz == pytest.approx(2.64)
    assert bands[0].source == "relative_tolerance"


def test_mode_is_removed_when_inside_relative_resonance_band() -> None:
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

    removed_indices = annotate_modes_for_resonance_bands([mode], bands)

    assert removed_indices == [0]
    assert mode.removed is True
    assert mode.target_frequency_hz == pytest.approx(2.2)
    assert mode.band_low_hz == pytest.approx(1.76)
    assert mode.band_high_hz == pytest.approx(2.64)
    assert mode.distance_to_target_hz == pytest.approx(abs(2.2 - 1.921094))
    assert "relative tolerance" in mode.selection_reason
