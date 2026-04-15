from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(slots=True)
class Mode:
    index: int
    pole: complex
    coefficient: complex
    frequency_hz: float
    damping: float
    amplitude: float
    phase_rad: float
    removed: bool = False


@dataclass(slots=True)
class MatrixPencilResult:
    modes: list[Mode]
    dt: float
    model_order: int
    reconstruction: np.ndarray

    def as_table(self) -> list[dict[str, float | int | bool]]:
        return [
            {
                "index": mode.index,
                "frequency_hz": mode.frequency_hz,
                "damping": mode.damping,
                "amplitude": mode.amplitude,
                "phase_rad": mode.phase_rad,
                "removed": mode.removed,
            }
            for mode in self.modes
        ]


def matrix_pencil(
    signal: np.ndarray,
    dt: float,
    model_order: int,
    pencil_parameter: int | None = None,
) -> MatrixPencilResult:
    """Estimate damped complex exponential modes with the Matrix Pencil method.

    The discrete model is

        y[k] = sum_i c_i * z_i**k

    with continuous poles s_i = log(z_i) / dt.
    """
    y = np.asarray(signal, dtype=float)
    if y.ndim != 1:
        raise ValueError("signal must be one-dimensional")
    if len(y) < 8:
        raise ValueError("signal must contain at least 8 samples")
    if dt <= 0:
        raise ValueError("dt must be positive")
    if model_order < 1:
        raise ValueError("model_order must be at least 1")

    n_samples = len(y)
    l_value = pencil_parameter or n_samples // 2
    l_value = int(np.clip(l_value, model_order + 1, n_samples - 2))
    rows = n_samples - l_value
    if rows <= model_order:
        raise ValueError("model_order is too high for the selected data length")

    y0 = _hankel(signal=y, rows=rows, columns=l_value, offset=0)
    y1 = _hankel(signal=y, rows=rows, columns=l_value, offset=1)

    u_matrix, singular_values, vh_matrix = np.linalg.svd(y0, full_matrices=False)
    rank = min(model_order, np.count_nonzero(singular_values > singular_values[0] * 1e-12))
    if rank < 1:
        raise ValueError("could not determine a numerical rank for the signal")

    u_rank = u_matrix[:, :rank]
    s_rank = singular_values[:rank]
    vh_rank = vh_matrix[:rank, :]
    y0_pinv_rank = vh_rank.conj().T @ np.diag(1.0 / s_rank) @ u_rank.conj().T
    pencil_matrix = y0_pinv_rank @ y1
    poles = np.linalg.eigvals(pencil_matrix)
    poles = _clean_poles(poles)
    if len(poles) == 0:
        raise ValueError("no stable finite poles were estimated")

    coefficients = estimate_coefficients(y, poles)
    reconstruction = reconstruct_from_poles(poles, coefficients, n_samples).real
    modes = _modes_from_poles(poles, coefficients, dt)
    return MatrixPencilResult(modes=modes, dt=dt, model_order=rank, reconstruction=reconstruction)


def estimate_coefficients(signal: np.ndarray, poles: np.ndarray) -> np.ndarray:
    y = np.asarray(signal, dtype=float)
    sample_index = np.arange(len(y), dtype=float)
    vandermonde = np.power(poles[np.newaxis, :], sample_index[:, np.newaxis])
    coefficients, *_ = np.linalg.lstsq(vandermonde, y, rcond=None)
    return coefficients


def reconstruct_from_poles(poles: np.ndarray, coefficients: np.ndarray, n_samples: int) -> np.ndarray:
    sample_index = np.arange(n_samples, dtype=float)
    vandermonde = np.power(poles[np.newaxis, :], sample_index[:, np.newaxis])
    return vandermonde @ coefficients


def _hankel(signal: np.ndarray, rows: int, columns: int, offset: int) -> np.ndarray:
    return np.column_stack([signal[offset + column : offset + column + rows] for column in range(columns)])


def _clean_poles(poles: np.ndarray) -> np.ndarray:
    finite = poles[np.isfinite(poles)]
    finite = finite[np.abs(finite) > 1e-12]
    # Extremely explosive poles are usually numerical artifacts for this filtering use case.
    return finite[np.abs(finite) < 1.5]


def _modes_from_poles(poles: np.ndarray, coefficients: np.ndarray, dt: float) -> list[Mode]:
    modes: list[Mode] = []
    for index, (pole, coefficient) in enumerate(zip(poles, coefficients)):
        continuous_pole = np.log(pole) / dt
        frequency_hz = abs(float(np.imag(continuous_pole) / (2.0 * np.pi)))
        damping = float(np.real(continuous_pole))
        modes.append(
            Mode(
                index=index,
                pole=complex(pole),
                coefficient=complex(coefficient),
                frequency_hz=frequency_hz,
                damping=damping,
                amplitude=float(abs(coefficient)),
                phase_rad=float(np.angle(coefficient)),
                removed=False,
            )
        )
    return modes

