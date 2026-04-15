from __future__ import annotations

import numpy as np

from prony_filter.filtering import filter_known_modes


def test_filter_known_modes_reduces_target_oscillation() -> None:
    dt = 0.01
    time = np.arange(0, 10, dt)
    step_time = 1.0
    clean = np.ones_like(time) * 10.0
    response_time = np.maximum(0.0, time - step_time)
    oscillation = 1.5 * np.exp(-0.3 * response_time) * np.cos(2 * np.pi * 2.0 * response_time)
    values = clean + np.where(time >= step_time, oscillation, 0.0)

    result = filter_known_modes(
        time=time,
        values=values,
        t0=step_time,
        remove_frequencies_hz=[2.0],
        tolerance_hz=0.15,
        model_order=6,
    )

    original_energy = np.linalg.norm(values[time >= step_time] - np.mean(values[time >= step_time]))
    filtered_energy = np.linalg.norm(result.filtered[time >= step_time] - np.mean(result.filtered[time >= step_time]))

    assert filtered_energy < original_energy * 0.75
    assert any(mode.removed for mode in result.modes)

