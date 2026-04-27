from __future__ import annotations

import numpy as np

from prony_filter.filtering import analyze_prepared_segment, filter_known_modes, prepare_signal_segment
from prony_filter.matrix_pencil import matrix_pencil


def test_matrix_pencil_recovers_single_clean_mode() -> None:
    dt = 0.01
    time = np.arange(0.0, 8.0, dt)
    f_true = 2.24
    d_true = -0.5
    amplitude_true = 10.0
    phase_true = 0.3
    signal = amplitude_true * np.exp(d_true * time) * np.cos(2.0 * np.pi * f_true * time + phase_true)

    result = matrix_pencil(signal, dt=dt, model_order=4)
    best_mode = min(result.modes, key=lambda mode: abs(mode.frequency_hz - f_true))
    reconstruction_error = np.linalg.norm(result.reconstruction - signal) / np.linalg.norm(signal)
    phase_error = min(_wrapped_distance(best_mode.phase_rad, phase_true), _wrapped_distance(best_mode.phase_rad, -phase_true))

    assert abs(best_mode.frequency_hz - f_true) < 0.02
    assert abs(best_mode.damping - d_true) < 0.03
    assert abs(2.0 * best_mode.amplitude - amplitude_true) < 0.2
    assert phase_error < 0.05
    assert reconstruction_error < 1e-10


def test_matrix_pencil_recovers_single_noisy_mode() -> None:
    rng = np.random.default_rng(123)
    dt = 0.01
    time = np.arange(0.0, 8.0, dt)
    f_true = 2.24
    d_true = -0.5
    signal = 10.0 * np.exp(d_true * time) * np.cos(2.0 * np.pi * f_true * time + 0.3)
    signal = signal + 1.5
    signal = signal + 0.12 * rng.normal(size=len(time))

    prepared = prepare_signal_segment(
        time=time,
        values=signal,
        t0=0.0,
        detrend="constant",
        model_order=10,
    )
    segment_analysis = analyze_prepared_segment(
        prepared=prepared,
        model_order=10,
        remove_frequencies_hz=[f_true],
        tolerance_hz=0.2,
    )
    best_mode = min(segment_analysis.analysis.modes, key=lambda mode: abs(mode.frequency_hz - f_true))
    reconstruction_error = (
        np.linalg.norm(segment_analysis.analysis.reconstruction - prepared.residual)
        / np.linalg.norm(prepared.residual)
    )

    assert abs(best_mode.frequency_hz - f_true) < 0.08
    assert abs(best_mode.damping - d_true) < 0.15
    assert reconstruction_error < 0.08


def test_filtering_removes_only_selected_band() -> None:
    time, values, primary_mode, secondary_mode, step_time = _two_mode_step_signal()
    result = filter_known_modes(
        time=time,
        values=values,
        t0=step_time,
        remove_frequencies_hz=[2.2],
        relative_tolerance=0.2,
        model_order=10,
        detrend="constant",
    )

    post_step = time >= step_time
    expected_filtered = 10.0 + secondary_mode
    relative_error = np.linalg.norm(result.filtered[post_step] - expected_filtered[post_step]) / np.linalg.norm(primary_mode[post_step])
    removed_frequencies = [mode.frequency_hz for mode in result.modes if mode.removed]

    assert removed_frequencies
    assert all(1.76 <= frequency <= 2.64 for frequency in removed_frequencies)
    assert relative_error < 0.35


def test_signal_before_t0_unchanged() -> None:
    time, values, _, _, step_time = _two_mode_step_signal()
    result = filter_known_modes(
        time=time,
        values=values,
        t0=step_time,
        remove_frequencies_hz=[2.2],
        relative_tolerance=0.2,
        model_order=10,
        detrend="constant",
    )

    pre_step = time < step_time
    assert np.allclose(result.filtered[pre_step], values[pre_step])
    assert np.allclose(result.removed_component[pre_step], 0.0)


def test_filtered_equals_original_minus_removed_after_t0() -> None:
    time, values, _, _, step_time = _two_mode_step_signal()
    result = filter_known_modes(
        time=time,
        values=values,
        t0=step_time,
        remove_frequencies_hz=[2.2],
        relative_tolerance=0.2,
        model_order=10,
        detrend="constant",
    )

    post_step = time >= step_time
    assert np.allclose(
        result.filtered[post_step],
        result.original[post_step] - result.removed_component[post_step],
    )


def _two_mode_step_signal() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    dt = 0.01
    time = np.arange(0.0, 10.0, dt)
    step_time = 1.0
    tau = np.maximum(0.0, time - step_time)
    primary_mode = np.where(
        time >= step_time,
        1.5 * np.exp(-0.25 * tau) * np.cos(2.0 * np.pi * 2.24 * tau + 0.2),
        0.0,
    )
    secondary_mode = np.where(
        time >= step_time,
        0.7 * np.exp(-0.12 * tau) * np.cos(2.0 * np.pi * 5.0 * tau - 0.3),
        0.0,
    )
    values = 10.0 + primary_mode + secondary_mode
    return time, values, primary_mode, secondary_mode, step_time


def _wrapped_distance(value: float, reference: float) -> float:
    return abs(np.angle(np.exp(1j * (value - reference))))
