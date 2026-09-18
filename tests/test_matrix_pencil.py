from __future__ import annotations

import numpy as np
import pytest

from prony_filter.matrix_pencil import matrix_pencil, matrix_pencil_rayleigh


def test_matrix_pencil_detects_synthetic_frequency() -> None:
    dt = 0.01
    time = np.arange(0, 8, dt)
    frequency = 1.8
    damping = -0.25
    signal = 2.0 * np.exp(damping * time) * np.cos(2 * np.pi * frequency * time + 0.4)

    result = matrix_pencil(signal, dt=dt, model_order=4)
    frequencies = np.array([mode.frequency_hz for mode in result.modes])

    assert np.min(np.abs(frequencies - frequency)) < 0.05
    assert len(result.modes) <= result.model_order
    assert np.linalg.norm(result.reconstruction - signal) / np.linalg.norm(signal) < 1e-10


@pytest.mark.parametrize("dt", [float('nan'), float('inf'), 0.0])
def test_matrix_pencil_rejects_invalid_time_step(dt):
    with pytest.raises(ValueError, match='dt'):
        matrix_pencil(np.ones(20), dt, 4)


def test_matrix_pencil_keeps_complex_log_for_negative_real_pole():
    values = (-0.8) ** np.arange(100)
    result = matrix_pencil(values, dt=0.01, model_order=2)
    assert len(result.modes) == 1
    assert result.modes[0].frequency_hz == pytest.approx(50.0)
    assert np.isfinite(result.modes[0].damping)


def test_matrix_pencil_rayleigh_finds_mode_near_initial_guess() -> None:
    dt = 0.01
    time = np.arange(0, 8, dt)
    frequency = 2.24
    damping = -0.5
    signal = 10.0 * np.exp(damping * time) * np.cos(2 * np.pi * frequency * time + 0.3)

    result = matrix_pencil_rayleigh(
        signal,
        dt=dt,
        model_order=4,
        initial_frequencies_hz=[2.2],
        initial_damping=0.0,
    )
    frequencies = np.array([mode.frequency_hz for mode in result.modes])
    dampings = np.array([mode.damping for mode in result.modes])

    assert len(result.modes) == 2
    assert np.min(np.abs(frequencies - frequency)) < 0.02
    assert np.min(np.abs(dampings - damping)) < 0.03


def test_matrix_pencil_recovers_pdf_style_impulse_modes() -> None:
    dt = 0.01
    time = np.arange(0.0, 8.0, dt)
    reference_modes = [
        (2.24, -0.50, 10.0, 0.30),
        (3.05, -0.80, 2.5, -0.60),
        (5.00, -0.35, 1.4, 1.10),
    ]
    signal = np.zeros_like(time)
    for frequency, damping, amplitude, phase in reference_modes:
        signal += amplitude * np.exp(damping * time) * np.cos(2 * np.pi * frequency * time + phase)
    signal = signal / np.max(np.abs(signal))

    result = matrix_pencil(signal, dt=dt, model_order=8, pencil_parameter=256)

    for frequency, damping, _, _ in reference_modes:
        closest = min(result.modes, key=lambda mode: abs(mode.frequency_hz - frequency))
        assert abs(closest.frequency_hz - frequency) < 0.01
        assert abs(closest.damping - damping) < 0.03
