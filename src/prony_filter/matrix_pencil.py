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
    target_frequency_hz: float | None = None
    band_low_hz: float | None = None
    band_high_hz: float | None = None
    distance_to_target_hz: float | None = None
    selection_reason: str = ""
    removed: bool = False

    @property
    def damping_ratio(self) -> float:
        natural_frequency = np.hypot(self.damping, 2.0 * np.pi * self.frequency_hz)
        return float(-self.damping / natural_frequency) if natural_frequency else 0.0

    @property
    def oscillation_amplitude(self) -> float:
        """Cosine amplitude for a conjugate pair, or amplitude of a real pole."""
        return self.amplitude * (2.0 if abs(self.pole.imag) > 1e-12 else 1.0)


@dataclass(slots=True)
class MatrixPencilResult:
    modes: list[Mode]
    dt: float
    model_order: int
    reconstruction: np.ndarray
    estimation_dt: float | None = None
    decimation_factor: int = 1
    relative_fit_error: float = 0.0

    @property
    def estimation_rate_hz(self) -> float:
        return 1.0 / (self.estimation_dt or self.dt)

    def as_table(self) -> list[dict[str, object]]:
        return [
            {
                "index": mode.index,
                "frequency_hz": mode.frequency_hz,
                "damping": mode.damping,
                "amplitude": mode.amplitude,
                "phase_rad": mode.phase_rad,
                "target_frequency_hz": mode.target_frequency_hz,
                "band_low_hz": mode.band_low_hz,
                "band_high_hz": mode.band_high_hz,
                "distance_to_target_hz": mode.distance_to_target_hz,
                "selection_reason": mode.selection_reason,
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
    y, pencil_matrix, rank = _build_pencil_matrix(signal, dt, model_order, pencil_parameter)

    poles = np.linalg.eigvals(pencil_matrix)
    poles = _clean_poles(poles)
    if len(poles) == 0:
        raise ValueError("no stable finite poles were estimated")

    coefficients = estimate_coefficients(y, poles)
    reconstruction = reconstruct_from_poles(poles, coefficients, len(y)).real
    modes = modes_from_poles(poles, coefficients, dt)
    return MatrixPencilResult(modes=modes, dt=dt, model_order=rank, reconstruction=reconstruction,
                              relative_fit_error=float(np.linalg.norm(reconstruction - y) / max(np.linalg.norm(y), 1e-12)))


def matrix_pencil_rayleigh(
    signal: np.ndarray,
    dt: float,
    model_order: int,
    initial_frequencies_hz: list[float],
    initial_damping: float = 0.0,
    pencil_parameter: int | None = None,
    max_iterations: int = 30,
    tolerance: float = 1e-12,
) -> MatrixPencilResult:
    """Estimate selected modes with Matrix Pencil and Rayleigh quotient iteration.

    Unlike :func:`matrix_pencil`, this does not compute the full eigenvalue set.
    It searches near informed initial frequency guesses, which can reduce
    spurious estimates when the expected resonance region is known.
    """
    if not initial_frequencies_hz:
        raise ValueError("initial_frequencies_hz must contain at least one value")
    if max_iterations < 1:
        raise ValueError("max_iterations must be at least 1")
    if tolerance <= 0:
        raise ValueError("tolerance must be positive")

    y, pencil_matrix, rank = _build_pencil_matrix(signal, dt, model_order, pencil_parameter)
    poles: list[complex] = []
    for frequency_hz in initial_frequencies_hz:
        frequency = abs(float(frequency_hz))
        angular_frequency = 2.0 * np.pi * frequency
        signs = [1.0] if frequency == 0.0 else [1.0, -1.0]
        for sign in signs:
            initial_continuous_pole = complex(initial_damping, sign * angular_frequency)
            initial_discrete_pole = np.exp(initial_continuous_pole * dt)
            initial_vector = initial_discrete_pole ** np.arange(pencil_matrix.shape[0], dtype=float)
            pole = rayleigh_quotient_iteration(
                pencil_matrix,
                initial_vector=initial_vector,
                initial_value=initial_discrete_pole,
                max_iterations=max_iterations,
                tolerance=tolerance,
            )
            poles.append(pole)

    poles_array = _deduplicate_poles(_clean_poles(np.asarray(poles, dtype=complex)))
    if len(poles_array) == 0:
        raise ValueError("no stable finite poles were estimated")

    coefficients = estimate_coefficients(y, poles_array)
    reconstruction = reconstruct_from_poles(poles_array, coefficients, len(y)).real
    modes = modes_from_poles(poles_array, coefficients, dt)
    return MatrixPencilResult(modes=modes, dt=dt, model_order=rank, reconstruction=reconstruction,
                              relative_fit_error=float(np.linalg.norm(reconstruction - y) / max(np.linalg.norm(y), 1e-12)))


def rayleigh_quotient_iteration(
    matrix: np.ndarray,
    initial_vector: np.ndarray,
    initial_value: complex | None = None,
    max_iterations: int = 30,
    tolerance: float = 1e-12,
) -> complex:
    """Return one eigenvalue near an initial guess using Rayleigh quotient iteration."""
    matrix_array = np.asarray(matrix, dtype=complex)
    if matrix_array.ndim != 2 or matrix_array.shape[0] != matrix_array.shape[1]:
        raise ValueError("matrix must be square")
    vector = np.asarray(initial_vector, dtype=complex)
    if vector.ndim != 1 or len(vector) != matrix_array.shape[0]:
        raise ValueError("initial_vector length must match matrix size")
    vector_norm = np.linalg.norm(vector)
    if vector_norm == 0:
        raise ValueError("initial_vector must not be zero")
    if max_iterations < 1:
        raise ValueError("max_iterations must be at least 1")
    if tolerance <= 0:
        raise ValueError("tolerance must be positive")

    vector = vector / vector_norm
    eigenvalue = (
        complex(initial_value)
        if initial_value is not None
        else complex(vector.conj() @ matrix_array @ vector / (vector.conj() @ vector))
    )
    identity = np.eye(matrix_array.shape[0], dtype=complex)
    for _ in range(max_iterations):
        shifted_matrix = matrix_array - eigenvalue * identity
        try:
            next_vector = np.linalg.solve(shifted_matrix, vector)
        except np.linalg.LinAlgError:
            next_vector = np.linalg.lstsq(shifted_matrix, vector, rcond=None)[0]
        next_norm = np.linalg.norm(next_vector)
        if next_norm == 0:
            break
        vector = next_vector / next_norm
        next_eigenvalue = complex(vector.conj() @ matrix_array @ vector / (vector.conj() @ vector))
        if abs(next_eigenvalue - eigenvalue) <= tolerance:
            return next_eigenvalue
        eigenvalue = next_eigenvalue
    return eigenvalue


def _build_pencil_matrix(
    signal: np.ndarray,
    dt: float,
    model_order: int,
    pencil_parameter: int | None,
) -> tuple[np.ndarray, np.ndarray, int]:
    y = np.asarray(signal, dtype=float)
    if y.ndim != 1:
        raise ValueError("signal must be one-dimensional")
    if len(y) < 8:
        raise ValueError("signal must contain at least 8 samples")
    if not np.all(np.isfinite(y)):
        raise ValueError("signal must contain only finite values")
    if not np.isfinite(dt) or dt <= 0:
        raise ValueError("dt must be finite and positive")
    if not isinstance(model_order, (int, np.integer)) or model_order < 1:
        raise ValueError("model_order must be a positive integer")
    if pencil_parameter is not None and (
        not isinstance(pencil_parameter, (int, np.integer)) or pencil_parameter < 1
    ):
        raise ValueError("pencil_parameter must be a positive integer")

    n_samples = len(y)
    default_pencil = min(n_samples // 2, max(model_order * 8, 256))
    l_value = pencil_parameter or default_pencil
    l_value = min(l_value, n_samples // 2)
    if l_value <= model_order:
        raise ValueError("pencil_parameter and half the sample count must exceed model_order")
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
    # Solve only in the retained signal subspace (rank x rank). The full
    # L x L pseudoinverse product has L-rank zero eigenvalues; rounding can
    # turn these into artificial modes and corrupt the amplitude fit.
    pencil_matrix = (u_rank.conj().T @ y1 @ vh_rank.conj().T) / s_rank[:, None]
    return y, pencil_matrix, rank


def estimate_coefficients(signal: np.ndarray, poles: np.ndarray) -> np.ndarray:
    y = np.asarray(signal, dtype=float)
    sample_index = np.arange(len(y), dtype=float)
    vandermonde = np.power(poles[np.newaxis, :], sample_index[:, np.newaxis])
    if not np.all(np.isfinite(vandermonde)):
        raise ValueError("estimated modes overflow on the analysis window; shorten the window or reduce the order")
    # Normalize columns so strongly growing or rapidly decaying nuisance modes
    # do not suppress small, persistent oscillations in the least-squares fit.
    scales = np.max(np.abs(vandermonde), axis=0)
    coefficients, *_ = np.linalg.lstsq(vandermonde / scales, y, rcond=None)
    coefficients = coefficients / scales
    return coefficients


def reconstruct_from_poles(poles: np.ndarray, coefficients: np.ndarray, n_samples: int) -> np.ndarray:
    sample_index = np.arange(n_samples, dtype=float)
    vandermonde = np.power(poles[np.newaxis, :], sample_index[:, np.newaxis])
    return vandermonde @ coefficients


def _hankel(signal: np.ndarray, rows: int, columns: int, offset: int) -> np.ndarray:
    return np.column_stack([signal[offset + column : offset + column + rows] for column in range(columns)])


def _clean_poles(poles: np.ndarray) -> np.ndarray:
    poles = np.asarray(poles, dtype=complex)
    finite = poles[np.isfinite(poles)]
    finite = finite[np.abs(finite) > 1e-12]
    # Extremely explosive poles are usually numerical artifacts for this filtering use case.
    return finite[np.abs(finite) < 1.5]


def _deduplicate_poles(poles: np.ndarray, tolerance: float = 1e-8) -> np.ndarray:
    unique: list[complex] = []
    for pole in poles:
        if not any(abs(pole - existing) <= tolerance for existing in unique):
            unique.append(complex(pole))
    return np.asarray(unique, dtype=complex)


def modes_from_poles(poles: np.ndarray, coefficients: np.ndarray, dt: float) -> list[Mode]:
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
