from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from prony_filter.matrix_pencil import MatrixPencilResult, matrix_pencil


@dataclass(frozen=True, slots=True)
class ReferenceMode:
    frequency_hz: float
    damping: float
    amplitude: float
    phase_rad: float


REFERENCE_MODES = [
    ReferenceMode(frequency_hz=2.24, damping=-0.50, amplitude=10.0, phase_rad=0.30),
    ReferenceMode(frequency_hz=3.05, damping=-0.80, amplitude=2.5, phase_rad=-0.60),
    ReferenceMode(frequency_hz=5.00, damping=-0.35, amplitude=1.4, phase_rad=1.10),
]


def main() -> int:
    output_dir = Path("outputs") / "pdf_impulse_matrix_pencil"
    output_dir.mkdir(parents=True, exist_ok=True)

    dt = 0.01
    duration_s = 8.0
    time = np.arange(0.0, duration_s, dt)
    clean_impulse = build_impulse_response(time, REFERENCE_MODES)
    noisy_impulse = clean_impulse + 0.02 * np.random.default_rng(1087).normal(size=len(time))

    clean_result = matrix_pencil(clean_impulse, dt=dt, model_order=8, pencil_parameter=256)
    noisy_result = matrix_pencil(noisy_impulse, dt=dt, model_order=12, pencil_parameter=256)

    pd.DataFrame({"time": time, "clean_impulse": clean_impulse, "noisy_impulse": noisy_impulse}).to_csv(
        output_dir / "impulse_signal.csv",
        index=False,
    )
    pd.DataFrame(clean_result.as_table()).to_csv(output_dir / "clean_estimated_modes.csv", index=False)
    pd.DataFrame(noisy_result.as_table()).to_csv(output_dir / "noisy_estimated_modes.csv", index=False)

    clean_matches = build_match_table(clean_result)
    noisy_matches = build_match_table(noisy_result)
    pd.DataFrame(clean_matches).to_csv(output_dir / "clean_reference_matches.csv", index=False)
    pd.DataFrame(noisy_matches).to_csv(output_dir / "noisy_reference_matches.csv", index=False)

    save_impulse_plot(time, clean_impulse, noisy_impulse, clean_result, noisy_result, output_dir / "impulse_reconstruction.png")
    write_summary(output_dir / "summary.md", clean_matches, noisy_matches)

    print("Reference vs Matrix-Pencil estimates, clean impulse:")
    print(pd.DataFrame(clean_matches).to_string(index=False))
    print("\nReference vs Matrix-Pencil estimates, noisy impulse:")
    print(pd.DataFrame(noisy_matches).to_string(index=False))
    print(f"\nWritten PDF-style impulse example to {output_dir}")
    return 0


def build_impulse_response(time: np.ndarray, modes: list[ReferenceMode]) -> np.ndarray:
    signal = np.zeros_like(time, dtype=float)
    for mode in modes:
        signal += mode.amplitude * np.exp(mode.damping * time) * np.cos(
            2.0 * np.pi * mode.frequency_hz * time + mode.phase_rad
        )
    max_abs = float(np.max(np.abs(signal)))
    if max_abs > 0:
        signal = signal / max_abs
    return signal


def build_match_table(result: MatrixPencilResult) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    estimated_modes = [mode for mode in result.modes if mode.frequency_hz > 0.05]
    for reference in REFERENCE_MODES:
        closest = min(
            estimated_modes,
            key=lambda mode: (
                abs(mode.frequency_hz - reference.frequency_hz),
                abs(mode.damping - reference.damping),
                mode.index,
            ),
        )
        rows.append(
            {
                "reference_frequency_hz": reference.frequency_hz,
                "estimated_frequency_hz": closest.frequency_hz,
                "frequency_error_hz": closest.frequency_hz - reference.frequency_hz,
                "reference_damping_1_per_s": reference.damping,
                "estimated_damping_1_per_s": closest.damping,
                "damping_error_1_per_s": closest.damping - reference.damping,
                "estimated_amplitude": closest.amplitude,
                "estimated_phase_rad": closest.phase_rad,
            }
        )
    return rows


def save_impulse_plot(
    time: np.ndarray,
    clean_impulse: np.ndarray,
    noisy_impulse: np.ndarray,
    clean_result: MatrixPencilResult,
    noisy_result: MatrixPencilResult,
    path: Path,
) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    axes[0].plot(time, clean_impulse, label="Clean synthetic impulse", linewidth=1.1)
    axes[0].plot(time, clean_result.reconstruction, label="Matrix-Pencil reconstruction", linewidth=1.0)
    axes[0].set_title("Clean impulse response")
    axes[0].set_ylabel("Normalized amplitude")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    axes[1].plot(time, noisy_impulse, label="Noisy synthetic impulse", linewidth=1.1)
    axes[1].plot(time, noisy_result.reconstruction, label="Matrix-Pencil reconstruction", linewidth=1.0)
    axes[1].set_title("Noisy impulse response")
    axes[1].set_xlabel("Time [s]")
    axes[1].set_ylabel("Normalized amplitude")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()

    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def write_summary(path: Path, clean_matches: list[dict[str, float]], noisy_matches: list[dict[str, float]]) -> None:
    lines = [
        "# PDF-Style Impulse Matrix-Pencil Example",
        "",
        "The synthetic impulse response is built as a sum of damped cosine modes:",
        "",
        "`h(t) = sum_j A_j exp(d_j t) cos(2*pi*f_j*t + phi_j)`",
        "",
        "This mirrors the modal impulse-response idea from `001087.pdf`: resonant frequencies and damping",
        "coefficients are encoded as complex eigenvalues and are then estimated from the sampled response.",
        "",
        "## Reference Modes",
        "",
        "| frequency [Hz] | damping [1/s] | amplitude | phase [rad] |",
        "| ---: | ---: | ---: | ---: |",
    ]
    for mode in REFERENCE_MODES:
        lines.append(f"| {mode.frequency_hz:.6f} | {mode.damping:.6f} | {mode.amplitude:.6f} | {mode.phase_rad:.6f} |")
    lines.extend(["", "## Clean Estimate", ""])
    lines.extend(_match_lines(clean_matches))
    lines.extend(["", "## Noisy Estimate", ""])
    lines.extend(_match_lines(noisy_matches))
    path.write_text("\n".join(lines), encoding="utf-8")


def _match_lines(matches: list[dict[str, float]]) -> list[str]:
    lines = [
        "| reference frequency [Hz] | estimated frequency [Hz] | frequency error [Hz] | reference damping [1/s] | estimated damping [1/s] | damping error [1/s] |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in matches:
        lines.append(
            f"| {row['reference_frequency_hz']:.6f} | {row['estimated_frequency_hz']:.6f} | "
            f"{row['frequency_error_hz']:.6f} | {row['reference_damping_1_per_s']:.6f} | "
            f"{row['estimated_damping_1_per_s']:.6f} | {row['damping_error_1_per_s']:.6f} |"
        )
    return lines


if __name__ == "__main__":
    raise SystemExit(main())
