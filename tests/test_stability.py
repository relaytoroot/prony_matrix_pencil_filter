from __future__ import annotations

import numpy as np

from prony_filter.stability import run_stability_scan


def test_stability_scan_tracks_mode_inside_resonance_band() -> None:
    dt = 0.01
    time = np.arange(0, 10, dt)
    t0 = 1.0
    tau = np.maximum(0.0, time - t0)
    values = 10.0 + np.where(
        time >= t0,
        1.5 * np.exp(-0.25 * tau) * np.cos(2 * np.pi * 2.24 * tau),
        0.0,
    )

    result = run_stability_scan(
        time=time,
        values=values,
        t0=t0,
        model_orders=[8, 10, 12],
        t0_offsets_s=[-0.02, 0.0, 0.02],
        remove_frequencies_hz=[2.2],
        relative_tolerance=0.2,
    )

    assert (result["error"] == "").all()
    assert (result["band_match_count"] >= 1).all()
    assert result["representative_removed"].all()
