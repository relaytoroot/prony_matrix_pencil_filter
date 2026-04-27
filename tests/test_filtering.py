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


def test_filter_known_modes_without_matching_targets_keeps_signal_for_offset_time_axis() -> None:
    dt = 0.01
    time = np.arange(10, 18, dt)
    step_time = 11.0
    response_time = np.maximum(0.0, time - step_time)
    values = 4.0 + np.where(
        time >= step_time,
        0.8 * np.exp(-0.4 * response_time) * np.cos(2 * np.pi * 1.5 * response_time),
        0.0,
    )

    result = filter_known_modes(
        time=time,
        values=values,
        t0=step_time,
        remove_frequencies_hz=[],
        tolerance_hz=0.1,
        model_order=6,
    )

    assert np.allclose(result.filtered, values)
    assert np.allclose(result.removed_component, 0.0)


def test_filter_result_matches_original_minus_removed_component_after_t0() -> None:
    time = np.array(
        [
            0.0,
            0.11,
            0.19,
            0.31,
            0.42,
            0.55,
            0.68,
            0.77,
            0.85,
            0.94,
            1.02,
            1.11,
            1.21,
            1.32,
            1.44,
            1.57,
            1.71,
            1.86,
            2.02,
            2.19,
            2.37,
            2.56,
        ]
    )
    step_time = 0.77
    response_time = np.maximum(0.0, time - step_time)
    values = 3.0 + np.where(
        time >= step_time,
        1.1 * np.exp(-0.5 * response_time) * np.cos(2 * np.pi * 1.8 * response_time),
        0.0,
    )

    result = filter_known_modes(
        time=time,
        values=values,
        t0=step_time,
        remove_frequencies_hz=[1.8],
        tolerance_hz=0.2,
        model_order=3,
    )

    before_mask = time < step_time
    after_mask = time >= step_time

    assert np.allclose(result.filtered[before_mask], values[before_mask])
    assert np.allclose(result.removed_component[before_mask], 0.0)
    assert np.allclose(
        result.filtered[after_mask],
        result.original[after_mask] - result.removed_component[after_mask],
    )
