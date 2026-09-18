from __future__ import annotations

import numpy as np
import pytest

from prony_filter.filtering import filter_known_modes


def test_high_sample_rate_recovers_mode_and_preserves_out_of_band_signal():
    time = np.arange(0, 7, 1 / 4000)
    tau = np.maximum(time - 1, 0)
    target = np.where(time >= 1, 2 * np.exp(-0.2 * tau) * np.cos(2 * np.pi * 2.24 * tau + .3), 0)
    other = np.where(time >= 1, .7 * np.exp(-0.1 * tau) * np.cos(2 * np.pi * 5 * tau), 0)
    # 102.24 Hz would alias onto the target after naive downsampling to 100 Hz.
    interference = np.where(time >= 1, .6 * np.cos(2 * np.pi * 102.24 * tau), 0)
    values = 10 + target + other + interference
    result = filter_known_modes(time, values, 1, [2.24], model_order=10)
    accepted = [m for m in result.modes if m.removed]
    assert accepted
    best = min(accepted, key=lambda m: abs(m.frequency_hz - 2.24))
    assert best.frequency_hz == pytest.approx(2.24, abs=.01)
    assert best.damping == pytest.approx(-.2, abs=.03)
    assert best.oscillation_amplitude == pytest.approx(2, abs=.06)
    assert result.analysis.decimation_factor == 40
    assert result.analysis.dt == pytest.approx(1 / 4000)
    assert len(result.filtered) == len(time)
    assert np.array_equal(result.filtered[time < 1], values[time < 1])
    assert np.linalg.norm(result.filtered - (10 + other + interference)) / np.linalg.norm(target) < .03


def test_growing_oscillation_is_reported_but_not_subtracted():
    time = np.arange(0, 4, .01)
    values = np.exp(.2 * time) * np.cos(2 * np.pi * 2 * time)
    result = filter_known_modes(time, values, 0, [2], model_order=4, detrend='none')
    assert not any(mode.removed for mode in result.modes)
    assert np.array_equal(result.filtered, values)
    assert any('growing' in mode.selection_reason for mode in result.modes)


def test_short_window_and_offset_axis_preserve_data_outside_window():
    time = np.arange(10, 18, .01)
    values = 3 + np.cos(2 * np.pi * 2 * (time - 10))
    result = filter_known_modes(time, values, 11, [2], model_order=4, window_length_s=3)
    outside = (time < 11) | (time > 14)
    assert np.array_equal(result.filtered[outside], values[outside])
    assert np.max(np.abs(result.filtered[~outside] - 3)) < 1e-6


def test_analysis_rate_must_resolve_requested_band():
    time = np.arange(0, 4, .001)
    with pytest.raises(ValueError, match='analysis rate'):
        filter_known_modes(time, np.cos(2*np.pi*20*time), 0, [20], analysis_rate_hz=50)


def test_native_rate_can_resolve_a_mode_below_nyquist_without_decimation():
    time = np.arange(0, 4, .02)
    result = filter_known_modes(time, np.cos(2*np.pi*20*time), 0, [20], model_order=4)
    assert any(mode.removed for mode in result.modes)
    assert result.analysis.decimation_factor == 1
    assert np.max(np.abs(result.filtered)) < 1e-6


def test_poor_fit_blocks_subtraction_and_explains_why():
    time = np.arange(0, 4, .01)
    values = np.exp(-.5*time) * np.cos(2*np.pi*2*time) + .3 * np.random.default_rng(42).normal(size=len(time))
    result = filter_known_modes(time, values, 0, [2], model_order=4)
    assert result.analysis.relative_fit_error > .1
    assert any('reconstruction error' in mode.selection_reason for mode in result.modes)
    assert not any(mode.removed for mode in result.modes)
    assert np.array_equal(result.filtered, values)


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
