from __future__ import annotations

import numpy as np

from .matrix_pencil import MatrixPencilResult, matrix_pencil


def prony_like_analysis(signal: np.ndarray, dt: float, model_order: int) -> MatrixPencilResult:
    """Compatibility wrapper for a Prony-style workflow.

    The current prototype intentionally uses Matrix Pencil internally. This keeps the
    API aligned with the FNN/Prony wording while retaining a numerically robust first
    implementation.
    """
    return matrix_pencil(signal=signal, dt=dt, model_order=model_order)

