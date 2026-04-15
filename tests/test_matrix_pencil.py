from __future__ import annotations

import numpy as np

from prony_filter.matrix_pencil import matrix_pencil


def test_matrix_pencil_detects_synthetic_frequency() -> None:
    dt = 0.01
    time = np.arange(0, 8, dt)
    frequency = 1.8
    damping = -0.25
    signal = 2.0 * np.exp(damping * time) * np.cos(2 * np.pi * frequency * time + 0.4)

    result = matrix_pencil(signal, dt=dt, model_order=4)
    frequencies = np.array([mode.frequency_hz for mode in result.modes])

    assert np.min(np.abs(frequencies - frequency)) < 0.05

