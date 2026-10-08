r"""Matrix Pencil in einem kleinen, vollstaendig ausfuehrbaren Beispiel.

Start:
    .\.venv\Scripts\python.exe examples\minimal_matrix_pencil.py
"""

from __future__ import annotations

import numpy as np


def matrix_pencil(
    signal: np.ndarray,
    dt: float,
    order: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Liefert kontinuierliche Pole, Koeffizienten und Einzelkomponenten."""
    y = np.asarray(signal, dtype=float)
    columns = min(256, len(y) // 2)

    # 1. Zwei Hankel-Matrizen, um genau einen Messwert verschoben.
    y0 = np.lib.stride_tricks.sliding_window_view(y, columns)[:-1]
    y1 = np.lib.stride_tricks.sliding_window_view(y[1:], columns)

    # 2. SVD: Nur die wichtigsten "order" Signalrichtungen behalten.
    u, singular_values, vh = np.linalg.svd(y0, full_matrices=False)
    rank = min(order, np.count_nonzero(singular_values > singular_values[0] * 1e-12))
    u, singular_values, vh = u[:, :rank], singular_values[:rank], vh[:rank]

    # 3. Eigenwerte der kleinen Matrix sind die diskreten Pole z_i.
    pencil = (u.T @ y1 @ vh.T) / singular_values[:, None]
    discrete_poles = np.linalg.eigvals(pencil)

    # 4. Koeffizienten c_i gemeinsam an y[k] = Summe(c_i * z_i**k) anpassen.
    samples = np.arange(len(y))[:, None]
    vandermonde = discrete_poles[None, :] ** samples
    coefficients = np.linalg.lstsq(vandermonde, y, rcond=None)[0]

    # 5. Pole in Frequenz/Daempfung umrechnen; jede Spalte ist eine Komponente.
    continuous_poles = np.log(discrete_poles.astype(complex)) / dt
    components = vandermonde * coefficients
    return continuous_poles, coefficients, components


def main() -> None:
    dt = 0.01
    time = np.arange(0.0, 8.0, dt)
    mode_224_hz = 10.0 * np.exp(-0.50 * time) * np.cos(2 * np.pi * 2.24 * time + 0.30)
    mode_500_hz = 2.0 * np.exp(-0.20 * time) * np.cos(2 * np.pi * 5.00 * time - 0.40)
    signal = mode_224_hz + mode_500_hz

    poles, coefficients, components = matrix_pencil(signal, dt, order=4)
    frequencies = np.abs(poles.imag) / (2 * np.pi)

    # Konjugierte Pole gehoeren paarweise zu derselben reellen Schwingung.
    for pole, coefficient in sorted(
        zip(poles[poles.imag > 0], coefficients[poles.imag > 0]),
        key=lambda item: item[0].imag,
    ):
        print(
            f"f={pole.imag / (2 * np.pi):.3f} Hz, "
            f"Daempfung={pole.real:.3f} 1/s, Amplitude={2 * abs(coefficient):.3f}"
        )

    # Beispiel fuer die Filterung: beide Pole im Band 1,76 bis 2,64 Hz abziehen.
    selected = (frequencies >= 1.76) & (frequencies <= 2.64)
    removed = components[:, selected].sum(axis=1).real
    filtered = signal - removed
    reconstruction = components.sum(axis=1).real
    print(f"Relativer Rekonstruktionsfehler: {np.linalg.norm(signal - reconstruction) / np.linalg.norm(signal):.2e}")
    print(f"Fehler nach Entfernung der 2,24-Hz-Mode: {np.linalg.norm(filtered - mode_500_hz):.2e}")


if __name__ == "__main__":
    main()
