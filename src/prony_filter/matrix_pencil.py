"""Mathematischer Kern: Schwingungsparameter aus diskreten Messwerten schätzen.

Lesereihenfolge: matrix_pencil() -> _build_pencil_matrix() ->
estimate_coefficients() -> modes_from_poles() -> reconstruct_from_poles().
Das Modell lautet y[k] = Summe(c_i * z_i**k). Ein konjugiert komplexes
Polpaar beschreibt eine reelle, gegebenenfalls gedämpfte Kosinusschwingung.

Begriffe im Code: signal = Messwerte, dt = Abtastabstand in Sekunden,
poles = diskrete Pole z_i, coefficients = komplexe Koeffizienten c_i,
model_order = maximale Anzahl komplexer Exponentialanteile. Eine reelle
Kosinusschwingung benötigt normalerweise zwei dieser Anteile.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(slots=True)
class Mode:
    """Ein Exponentialanteil mit Pol, Koeffizient und abgeleiteten Parametern.

    damping ist der Exponent d in 1/s: d < 0 bedeutet Abklingen.
    amplitude ist |c| eines einzelnen Pols; oscillation_amplitude liefert
    für ein konjugiertes Paar die Kosinusamplitude 2*|c|.
    phase_rad ist die Phase des Koeffizienten in Radiant. Amplitude und
    Phase beziehen sich auf den ersten Messwert des Analyseabschnitts.
    removed und selection_reason dokumentieren die Filterentscheidung.
    """

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
        """Dimensionsloses Dämpfungsverhältnis: zeta = -d / sqrt(d² + (2*pi*f)²)."""
        natural_frequency = np.hypot(self.damping, 2.0 * np.pi * self.frequency_hz)
        return float(-self.damping / natural_frequency) if natural_frequency else 0.0

    @property
    def oscillation_amplitude(self) -> float:
        """Kosinusamplitude eines Polpaars bzw. Amplitude eines reellen Pols."""
        return self.amplitude * (2.0 if abs(self.pole.imag) > 1e-12 else 1.0)


@dataclass(slots=True)
class MatrixPencilResult:
    """Moden, rekonstruiertes Signal und Angaben zur Schätzgenauigkeit.

    reconstruction enthält die Summe aller geschätzten Signalanteile.
    estimation_dt bezeichnet den Abtastabstand bei der Polschätzung;
    decimation_factor ist der Faktor der Abtastratenverringerung.
    relative_fit_error ist die relative Abweichung zwischen Modell und Signal.
    """

    modes: list[Mode]
    dt: float
    model_order: int
    reconstruction: np.ndarray
    estimation_dt: float | None = None
    decimation_factor: int = 1
    relative_fit_error: float = 0.0

    @property
    def estimation_rate_hz(self) -> float:
        """Abtastrate der Polschätzung in Hz, also 1 / estimation_dt."""
        return 1.0 / (self.estimation_dt or self.dt)

    def as_table(self) -> list[dict[str, object]]:
        """Einzelne Pole für Tabellen aufbereiten; Spaltenschlüssel bleiben stabil."""
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
    """Schätzt komplexe Exponentialanteile mit dem Matrix-Pencil-Verfahren.

    Eingabe: eindimensionale Messwerte, Abtastabstand dt und Modellordnung.
    Das diskrete Modell lautet

        y[k] = sum_i c_i * z_i**k

    mit den kontinuierlichen Polen s_i = log(z_i) / dt.
    Ausgabe: Pole und Schwingungsparameter sowie die rekonstruierte Zeitreihe.
    """
    # 1. Messwerte in zwei verschobene Matrizen eintragen und per SVD reduzieren.
    y, pencil_matrix, rank = _build_pencil_matrix(signal, dt, model_order, pencil_parameter)

    # 2. Die Eigenwerte der reduzierten Matrix sind die diskreten Pole z_i.
    poles = np.linalg.eigvals(pencil_matrix)
    poles = _clean_poles(poles)
    if len(poles) == 0:
        raise ValueError("no stable finite poles were estimated")

    # 3. Alle Koeffizienten gemeinsam an die Messwerte anpassen.
    coefficients = estimate_coefficients(y, poles)
    # 4. Modell auswerten; konjugierte Anteile ergeben zusammen reelle Werte.
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
    """Sucht einzelne Pole nahe vorgegebenen Frequenzen mit der Rayleigh-Iteration.

    Die Startfrequenzen und die Anfangsschätzung der Dämpfung bestimmen die
    Startpole. Diese Variante berechnet nicht alle Eigenwerte und ist von
    den Startwerten abhängig. Der Filterablauf ergänzt deshalb eine vollständige
    Eigenwertberechnung für die gemeinsame Anpassung aller Signalanteile.
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
    """Nähert einen Eigenwert durch wiederholtes Lösen verschobener Gleichungen an.

    matrix ist die quadratische Eigenwertmatrix, initial_vector der Startvektor
    und initial_value die anfängliche Eigenwertschätzung. In jedem Schritt
    werden (B - mu*I)*w = v gelöst, w normiert und mu per Rayleigh-Quotient
    aktualisiert. Abbruch nach erreichter Toleranz oder maximaler Schrittzahl.
    """
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
    """Baut die Hankel-Matrizen auf und reduziert das Eigenwertproblem per SVD.

    N = Anzahl der Messwerte, L = pencil_parameter = Anzahl der Spalten.
    Y0 und Y1 haben jeweils (N-L) Zeilen und L Spalten; Y1 ist um einen
    Abtastwert verschoben. Rückgabe: Messwerte, reduzierte Matrix B und Rang r.
    """
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

    # Y0[i,j] = y[i+j], Y1[i,j] = y[i+j+1]: dieselben Daten, um einen Wert versetzt.
    y0 = _hankel(signal=y, rows=rows, columns=l_value, offset=0)
    y1 = _hankel(signal=y, rows=rows, columns=l_value, offset=1)
    # Singulärwertzerlegung: Y0 = U*S*V^H. Kleine Richtungen werden abgeschnitten.
    u_matrix, singular_values, vh_matrix = np.linalg.svd(y0, full_matrices=False)
    rank = min(model_order, np.count_nonzero(singular_values > singular_values[0] * 1e-12))
    if rank < 1:
        raise ValueError("could not determine a numerical rank for the signal")

    u_rank = u_matrix[:, :rank]
    s_rank = singular_values[:rank]
    vh_rank = vh_matrix[:rank, :]
    # B = S_r^-1 * U_r^H * Y1 * V_r hat nur r x r Einträge.
    # Die zeilenweise Division durch s_rank entspricht S_r^-1.
    # Das volle L-x-L-Problem hätte zusätzliche Nulleigenwerte, aus denen
    # durch Rundung künstliche Moden entstehen könnten.
    pencil_matrix = (u_rank.conj().T @ y1 @ vh_rank.conj().T) / s_rank[:, None]
    return y, pencil_matrix, rank


def estimate_coefficients(signal: np.ndarray, poles: np.ndarray) -> np.ndarray:
    """Bestimmt c_i durch kleinste Quadrate: minimiere ||V*c - y||.

    Die Vandermonde-Matrix enthält V[k,i] = z_i**k. Alle Pole werden gemeinsam
    angepasst, damit ihre Beiträge nicht mehrfach demselben Messwertanteil
    zugeordnet werden. |c_i| und arg(c_i) liefern Amplitude und Anfangsphase
    des einzelnen komplexen Anteils.
    """
    y = np.asarray(signal, dtype=float)
    sample_index = np.arange(len(y), dtype=float)
    vandermonde = np.power(poles[np.newaxis, :], sample_index[:, np.newaxis])
    if not np.all(np.isfinite(vandermonde)):
        raise ValueError("estimated modes overflow on the analysis window; shorten the window or reduce the order")
    # Spalten normieren, damit stark wachsende oder rasch abklingende Anteile
    # kleine, länger anhaltende Schwingungen bei der Anpassung nicht verdrängen.
    scales = np.max(np.abs(vandermonde), axis=0)
    coefficients, *_ = np.linalg.lstsq(vandermonde / scales, y, rcond=None)
    coefficients = coefficients / scales
    return coefficients


def reconstruct_from_poles(poles: np.ndarray, coefficients: np.ndarray, n_samples: int) -> np.ndarray:
    """Wertet y_hat[k] = Summe(c_i * z_i**k) für k = 0 bis n_samples-1 aus.

    Die Rückgabe ist komplex. Bei konjugierten Polpaaren verwendet der Aufrufer
    den Realteil; kleine imaginäre Rundungsreste werden dabei verworfen.
    """
    sample_index = np.arange(n_samples, dtype=float)
    vandermonde = np.power(poles[np.newaxis, :], sample_index[:, np.newaxis])
    return vandermonde @ coefficients


def _hankel(signal: np.ndarray, rows: int, columns: int, offset: int) -> np.ndarray:
    """Ordnet Messwerte so an, dass jede Gegendiagonale denselben Wert enthält."""
    return np.column_stack([signal[offset + column : offset + column + rows] for column in range(columns)])


def _clean_poles(poles: np.ndarray) -> np.ndarray:
    """Entfernt nicht endliche, nahezu null große und extrem wachsende Pole.

    Dies ist eine numerische Vorauswahl. Die Prüfung auf abklingende Moden
    für die tatsächliche Entfernung erfolgt später in resonance.py.
    """
    poles = np.asarray(poles, dtype=complex)
    finite = poles[np.isfinite(poles)]
    finite = finite[np.abs(finite) > 1e-12]
    # Sehr stark wachsende Pole sind hier meist numerische Artefakte.
    return finite[np.abs(finite) < 1.5]


def _deduplicate_poles(poles: np.ndarray, tolerance: float = 1e-8) -> np.ndarray:
    """Fasst mehrfach gefundene Pole innerhalb der angegebenen Toleranz zusammen."""
    unique: list[complex] = []
    for pole in poles:
        if not any(abs(pole - existing) <= tolerance for existing in unique):
            unique.append(complex(pole))
    return np.asarray(unique, dtype=complex)


def modes_from_poles(poles: np.ndarray, coefficients: np.ndarray, dt: float) -> list[Mode]:
    """Rechnet diskrete Pole und Koeffizienten in Schwingungsparameter um.

    Wie in der Handrechnung: ln(z) = ln(|z|) + j*arg(z).
    Daraus folgen d = ln(|z|)/dt und f = |arg(z)|/(2*pi*dt).
    Der Polwinkel beschreibt den Phasenzuwachs je Abtastschritt; der Winkel
    des Koeffizienten beschreibt die Anfangsphase des jeweiligen Anteils.
    """
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
