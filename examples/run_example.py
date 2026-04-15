from __future__ import annotations

from pathlib import Path

import numpy as np

from prony_filter.filtering import filter_known_modes
from prony_filter.io import export_results
from prony_filter.plotting import save_comparison_plot


def main() -> int:
    dt = 0.01
    time = np.arange(0, 12, dt)
    t0 = 1.0
    tau = np.maximum(0.0, time - t0)
    base = 100.0 + np.where(time >= t0, 20.0, 0.0)
    resonance = 3.0 * np.exp(-0.25 * tau) * np.cos(2 * np.pi * 1.8 * tau + 0.2)
    signal = base + np.where(time >= t0, resonance, 0.0)

    result = filter_known_modes(
        time=time,
        values=signal,
        t0=t0,
        remove_frequencies_hz=[1.8],
        tolerance_hz=0.2,
        model_order=8,
    )

    output_dir = Path("outputs") / "example"
    export_results(result, output_dir=output_dir)
    save_comparison_plot(result, output_dir / "comparison_plot.png")
    print(f"Example written to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

