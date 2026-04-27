from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from prony_filter.filtering import filter_known_modes
from prony_filter.io import export_results
from prony_filter.plotting import save_comparison_plot, save_fft_plot
from prony_filter.spectral import analyze_fft_spectrum, build_resonance_comparison_rows


def main() -> int:
    dt = 0.01
    time = np.arange(0, 12, dt)
    t0 = 1.0
    tau = np.maximum(0.0, time - t0)
    base = 100.0 + np.where(time >= t0, 20.0, 0.0)
    resonance = 3.0 * np.exp(-0.25 * tau) * np.cos(2 * np.pi * 2.24 * tau + 0.2)
    signal = base + np.where(time >= t0, resonance, 0.0)

    result = filter_known_modes(
        time=time,
        values=signal,
        t0=t0,
        remove_frequencies_hz=[2.2],
        relative_tolerance=0.2,
        model_order=8,
    )
    fft_result = analyze_fft_spectrum(result.residual, dt=result.analysis.dt)
    resonance_comparison = build_resonance_comparison_rows(result.selection_bands, result.analysis.modes, fft_result)

    output_dir = Path("outputs") / "example"
    export_results(
        result,
        output_dir=output_dir,
        input_path="synthetic_example.csv",
        signal_column="P_pos",
        t0=t0,
        debug=True,
        fft_result=fft_result,
        resonance_comparison_rows=resonance_comparison,
    )
    save_comparison_plot(result, output_dir / "comparison_plot.png", signal_label="P_pos")
    save_fft_plot(fft_result, output_dir / "fft_plot.png")
    print(pd.DataFrame(resonance_comparison).to_string(index=False))
    print(f"Example written to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
