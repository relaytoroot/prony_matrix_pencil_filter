from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .filtering import PreparedSignalSegment, SegmentAnalysisResult, analyze_prepared_segment, prepare_signal_segment
from .io import extract_time_signal, read_table
from .plotting import save_fft_plot
from .spectral import FFTSpectrumResult, analyze_fft_spectrum, build_resonance_comparison_rows
from .stability import build_stability_summary_markdown, run_stability_scan


@dataclass(slots=True)
class SyntheticCaseConfig:
    name: str
    f_true: float = 2.24
    d_true: float = -0.5
    amplitude_true: float = 10.0
    phase_true: float = 0.3
    duration_s: float = 8.0
    dt: float = 0.01
    offset: float = 0.0
    noise_std: float = 0.0
    model_order: int = 6
    detrend: str = "none"
    second_mode: tuple[float, float, float, float] | None = None
    random_seed: int = 123


@dataclass(slots=True)
class SyntheticCaseResult:
    config: SyntheticCaseConfig
    time: np.ndarray
    signal: np.ndarray
    prepared: PreparedSignalSegment
    segment_analysis: SegmentAnalysisResult
    fft_result: FFTSpectrumResult
    recovered_frequency_hz: float
    recovered_damping: float
    recovered_pair_amplitude: float
    recovered_phase_rad: float
    reconstruction_error: float
    modes_frame: pd.DataFrame


@dataclass(slots=True)
class RealSignalValidationResult:
    prepared: PreparedSignalSegment
    segment_analysis: SegmentAnalysisResult
    fft_result: FFTSpectrumResult
    modes_frame: pd.DataFrame
    modes_in_band_frame: pd.DataFrame
    fft_peaks_frame: pd.DataFrame
    comparison_frame: pd.DataFrame


def generate_validation_report(
    file_path: str | Path,
    output_dir: str | Path = "validation_report",
    sheet_name: str | int | None = 0,
    time_column: str | None = None,
    signal_column: str = "P_pos",
    t0: float = 1.0,
    target_frequency_hz: float = 2.2,
    relative_tolerance: float = 0.2,
    model_order: int = 12,
    detrend: str = "constant",
    pencil_parameter: int | None = 256,
    stability_orders: list[int] | None = None,
    stability_t0_values: list[float] | None = None,
    stability_windows_s: list[float] | None = None,
    debug: bool = False,
) -> Path:
    report_dir = Path(output_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    clean_result = run_synthetic_case(SyntheticCaseConfig(name="synthetic_clean", model_order=6, detrend="none"))
    noisy_result = run_synthetic_case(
        SyntheticCaseConfig(
            name="synthetic_noisy",
            offset=1.5,
            noise_std=0.12,
            model_order=10,
            detrend="constant",
            second_mode=(3.05, -0.8, 2.5, -0.6),
        )
    )

    clean_result.modes_frame.to_csv(report_dir / "synthetic_clean_modes.csv", index=False)
    noisy_result.modes_frame.to_csv(report_dir / "synthetic_noisy_modes.csv", index=False)
    if debug:
        _save_synthetic_plot(clean_result, report_dir / "synthetic_clean_plot.png")
        _save_synthetic_plot(noisy_result, report_dir / "synthetic_noisy_plot.png")

    frame = read_table(file_path, sheet_name=sheet_name)
    time, values, used_time_column, used_signal_column = extract_time_signal(
        frame,
        time_column=time_column,
        signal_column=signal_column,
    )
    real_result = analyze_real_signal(
        time=time,
        values=values,
        t0=t0,
        target_frequency_hz=target_frequency_hz,
        relative_tolerance=relative_tolerance,
        model_order=model_order,
        detrend=detrend,
        pencil_parameter=pencil_parameter,
    )

    real_result.modes_in_band_frame.to_csv(report_dir / "real_modes_in_band.csv", index=False)
    real_result.fft_peaks_frame.to_csv(report_dir / "real_fft_peaks.csv", index=False)
    real_result.comparison_frame.to_csv(report_dir / "real_resonance_comparison.csv", index=False)
    if debug:
        real_result.modes_frame.to_csv(report_dir / "real_modes.csv", index=False)
        pd.DataFrame(real_result.fft_result.spectrum_table()).to_csv(report_dir / "real_fft_spectrum.csv", index=False)
        save_fft_plot(real_result.fft_result, report_dir / "real_fft_plot.png", title="Real data FFT spectrum")

    stability_orders = stability_orders or [8, 10, 12, 14, 16]
    stability_t0_values = stability_t0_values or [0.98, 1.00, 1.02]
    stability_windows_s = stability_windows_s or [3.0, 5.0, 7.0]
    stability_result = run_stability_scan(
        time=time,
        values=values,
        t0=t0,
        model_orders=stability_orders,
        t0_offsets_s=[value - t0 for value in stability_t0_values],
        remove_frequencies_hz=[target_frequency_hz],
        tolerance_hz=0.2,
        relative_tolerance=relative_tolerance,
        detrend=detrend,
        pencil_parameter=pencil_parameter,
        window_lengths_s=stability_windows_s,
    )
    stability_result.to_csv(report_dir / "stability_report.csv", index=False)
    stability_summary = build_stability_summary_markdown(stability_result)
    (report_dir / "stability_summary.md").write_text(stability_summary, encoding="utf-8")

    summary_text = build_validation_summary(
        clean_result=clean_result,
        noisy_result=noisy_result,
        real_result=real_result,
        stability_result=stability_result,
        used_time_column=used_time_column,
        used_signal_column=used_signal_column,
        target_frequency_hz=target_frequency_hz,
        relative_tolerance=relative_tolerance,
    )
    (report_dir / "summary.md").write_text(summary_text, encoding="utf-8")
    return report_dir


def analyze_real_signal(
    time: np.ndarray,
    values: np.ndarray,
    t0: float,
    target_frequency_hz: float,
    relative_tolerance: float,
    model_order: int,
    detrend: str,
    pencil_parameter: int | None,
) -> RealSignalValidationResult:
    prepared = prepare_signal_segment(
        time=time,
        values=values,
        t0=t0,
        detrend=detrend,
        model_order=model_order,
    )
    segment_analysis = analyze_prepared_segment(
        prepared=prepared,
        model_order=model_order,
        remove_frequencies_hz=[target_frequency_hz],
        relative_tolerance=relative_tolerance,
        pencil_parameter=pencil_parameter,
    )
    fft_result = analyze_fft_spectrum(prepared.residual, dt=prepared.dt, peak_count=10)
    modes_frame = _sorted_modes_frame(segment_analysis.analysis.as_table())
    modes_in_band_rows = [
        row
        for row in segment_analysis.analysis.as_table()
        if any(band.contains(row["frequency_hz"]) for band in segment_analysis.selection_bands)
    ]
    modes_in_band_frame = _sorted_modes_frame(modes_in_band_rows, empty_columns=modes_frame.columns.tolist())
    fft_peaks_frame = pd.DataFrame(fft_result.peaks_table())
    comparison_frame = pd.DataFrame(
        build_resonance_comparison_rows(
            bands=segment_analysis.selection_bands,
            modes=segment_analysis.analysis.modes,
            fft_result=fft_result,
        )
    )

    return RealSignalValidationResult(
        prepared=prepared,
        segment_analysis=segment_analysis,
        fft_result=fft_result,
        modes_frame=modes_frame,
        modes_in_band_frame=modes_in_band_frame,
        fft_peaks_frame=fft_peaks_frame,
        comparison_frame=comparison_frame,
    )


def run_synthetic_case(config: SyntheticCaseConfig) -> SyntheticCaseResult:
    time = np.arange(0.0, config.duration_s, config.dt)
    signal = _build_synthetic_signal(time, config)
    prepared = prepare_signal_segment(
        time=time,
        values=signal,
        t0=0.0,
        detrend=config.detrend,
        model_order=config.model_order,
    )
    segment_analysis = analyze_prepared_segment(
        prepared=prepared,
        model_order=config.model_order,
        remove_frequencies_hz=[config.f_true],
        tolerance_hz=0.1,
    )
    fft_result = analyze_fft_spectrum(prepared.residual, dt=prepared.dt, peak_count=5)
    best_mode = _closest_mode(segment_analysis.analysis.modes, config.f_true)
    pair_mode = _conjugate_partner(best_mode, segment_analysis.analysis.modes)
    pair_amplitude_estimate = (
        2.0 * best_mode.amplitude
        if pair_mode is None
        else float(best_mode.amplitude + pair_mode.amplitude)
    )
    reconstruction_error = float(
        np.linalg.norm(segment_analysis.analysis.reconstruction - prepared.residual)
        / max(np.linalg.norm(prepared.residual), 1e-12)
    )
    return SyntheticCaseResult(
        config=config,
        time=time,
        signal=signal,
        prepared=prepared,
        segment_analysis=segment_analysis,
        fft_result=fft_result,
        recovered_frequency_hz=best_mode.frequency_hz,
        recovered_damping=best_mode.damping,
        recovered_pair_amplitude=float(pair_amplitude_estimate),
        recovered_phase_rad=best_mode.phase_rad,
        reconstruction_error=reconstruction_error,
        modes_frame=_sorted_modes_frame(segment_analysis.analysis.as_table()),
    )


def build_validation_summary(
    clean_result: SyntheticCaseResult,
    noisy_result: SyntheticCaseResult,
    real_result: RealSignalValidationResult,
    stability_result: pd.DataFrame,
    used_time_column: str,
    used_signal_column: str,
    target_frequency_hz: float,
    relative_tolerance: float,
) -> str:
    prepared = real_result.prepared
    top_peaks = real_result.fft_result.peaks[:5]
    band_low = target_frequency_hz * (1.0 - relative_tolerance)
    band_high = target_frequency_hz * (1.0 + relative_tolerance)
    successful_stability = stability_result[(stability_result["error"] == "") & (stability_result["band_match_count"] > 0)]

    lines = [
        "# Validation Summary",
        "",
        "## 1. Synthetic algorithm check",
        "",
        "- Reines synthetisches Einzelsignal: Matrix Pencil sollte die vorgegebene Frequenz direkt wiederfinden.",
        "- Simulierte oder echt gemessene Sprungantwort: FFT-Peak und Matrix-Pencil-Mode koennen voneinander abweichen, weil Sprunganteil, Daempfung, Offset, weitere Moden, Fensterwahl und Modellordnung eine Rolle spielen.",
        "",
        _synthetic_summary_line("Clean synthetic case", clean_result),
        _synthetic_summary_line("Noisy synthetic case", noisy_result),
        "",
        f"- Conclusion for the pure 2.24 Hz reference: {'passed' if abs(clean_result.recovered_frequency_hz - clean_result.config.f_true) < 0.02 and abs(clean_result.recovered_damping - clean_result.config.d_true) < 0.05 else 'failed'}",
        "",
        "## 2. FFT and Matrix Pencil on the identical real-data segment",
        "",
        f"- Time column: `{used_time_column}`",
        f"- Signal column: `{used_signal_column}`",
        f"- Used time range: `{prepared.segment_time[0]:.6f}` s to `{prepared.segment_time[-1]:.6f}` s",
        f"- Number of samples after preprocessing: `{len(prepared.uniform_time)}`",
        f"- Sampling interval: `{prepared.dt:.9f}` s",
        f"- Sampling rate: `{1.0 / prepared.dt:.6f}` Hz",
        f"- Detrending: `{prepared.detrend}`",
        f"- Target resonance: `{target_frequency_hz:.6f}` Hz",
        f"- Resonance band: `{band_low:.6f}` Hz to `{band_high:.6f}` Hz",
        "",
        "### FFT peaks",
        "",
    ]

    if top_peaks:
        for peak in top_peaks:
            lines.append(f"- Peak {peak.rank}: `{peak.frequency_hz:.6f}` Hz with magnitude `{peak.magnitude:.6f}`")
    else:
        lines.append("- No FFT peaks detected.")
    lines.append("")

    lines.extend(["### Matrix-Pencil modes in the resonance band", ""])
    if real_result.modes_in_band_frame.empty:
        lines.append("- No Matrix-Pencil modes were found inside the resonance band.")
    else:
        lines.append("| index | frequency [Hz] | damping [1/s] | amplitude | phase [rad] | distance to target [Hz] | removed | selection reason |")
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |")
        for row in real_result.modes_in_band_frame.itertuples(index=False):
            target_distance = "-" if pd.isna(row.distance_to_target_hz) else f"{float(row.distance_to_target_hz):.6f}"
            lines.append(
                f"| {int(row.index)} | {float(row.frequency_hz):.6f} | {float(row.damping):.6f} | "
                f"{float(row.amplitude):.6f} | {float(row.phase_rad):.6f} | {target_distance} | "
                f"{bool(row.removed)} | {row.selection_reason} |"
            )
    lines.append("")

    lines.extend(["## 3. Why a mode near 1.92 Hz may have been removed", ""])
    if real_result.modes_in_band_frame.empty:
        lines.append("- In this run no Matrix-Pencil mode was found inside the resonance band.")
    else:
        closest_row = real_result.modes_in_band_frame.iloc[
            real_result.modes_in_band_frame["distance_to_target_hz"].fillna(np.inf).astype(float).argmin()
        ]
        lines.append(
            f"- Closest in-band mode: `{closest_row['frequency_hz']:.6f}` Hz with damping `{closest_row['damping']:.6f}` 1/s "
            f"and distance `{closest_row['distance_to_target_hz']:.6f}` Hz to the target `{target_frequency_hz:.6f}` Hz."
        )
        if any(abs(float(freq) - 1.921094) < 0.05 for freq in real_result.modes_in_band_frame["frequency_hz"]):
            lines.append(
                "- A mode around `1.92 Hz` lies inside the band `2.2 Hz +/- 20 %`, so the current selection logic can remove it even when the strongest FFT peak is closer to `2.24 Hz`."
            )
        lines.append(
            "- This is not automatic proof that `1.92 Hz` is the correct physical drivetrain mode. It only shows that, under the current preprocessing and model order, Matrix Pencil places a damped mode in the expected resonance band there."
        )
    lines.append("")

    lines.extend(["## 4. Stability over t0, window and model order", ""])
    lines.append(f"- Successful parameter combinations with at least one in-band mode: `{len(successful_stability)}` / `{len(stability_result)}`")
    if not successful_stability.empty:
        frequency_series = successful_stability["representative_mode_frequency_hz"].dropna().astype(float)
        lines.append(f"- Frequency range of the representative in-band mode: `{frequency_series.min():.6f}` Hz to `{frequency_series.max():.6f}` Hz")
        lines.append(f"- Frequency mean / std: `{frequency_series.mean():.6f}` Hz / `{frequency_series.std(ddof=0):.6f}` Hz")
        lines.extend(_stability_cluster_lines(frequency_series))
    else:
        lines.append("- No stable resonance-band mode was found in the tested parameter grid.")
    lines.append("")

    lines.extend(
        [
            "## 5. Open questions",
            "",
            "- Should the drivetrain resonance be represented by a single damped mode or by multiple nearby modes inside the same band?",
            "- Should the validation focus on the full post-step window or on a shorter early-time window that emphasizes the oscillatory transient?",
            "- Should order selection be constrained to values that both recover the synthetic benchmark and stay stable on the real step response?",
            "",
        ]
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a validation report for Matrix Pencil and FFT comparison.")
    parser.add_argument("--file", required=True, help="Input XLS/XLSX/CSV file")
    parser.add_argument("--sheet", default=0, help="Excel sheet name or index. Default: 0")
    parser.add_argument("--time-column", help="Name of the time column")
    parser.add_argument("--signal-column", default="P_pos", help="Name of the signal column. Default: P_pos")
    parser.add_argument("--t0", type=float, default=1.0, help="Step time for the analysis segment")
    parser.add_argument("--target-frequency", type=float, default=2.2, help="Target resonance frequency in Hz")
    parser.add_argument("--relative-tolerance", type=float, default=0.2, help="Relative resonance-band tolerance")
    parser.add_argument("--order", type=int, default=12, help="Matrix-Pencil model order for the real-data run")
    parser.add_argument("--pencil", type=int, default=256, help="Optional Matrix-Pencil parameter")
    parser.add_argument(
        "--detrend",
        choices=("none", "constant", "linear"),
        default="constant",
        help="Baseline/trend handling before modal estimation",
    )
    parser.add_argument("--output-dir", default="validation_report", help="Directory for the generated validation report")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Write additional diagnostic plots and full-spectrum exports",
    )
    parser.add_argument("--orders", nargs="*", type=int, default=[8, 10, 12, 14, 16], help="Orders for the stability scan")
    parser.add_argument(
        "--stability-t0",
        nargs="*",
        type=float,
        default=[0.98, 1.00, 1.02],
        help="Absolute t0 values for the stability scan",
    )
    parser.add_argument(
        "--stability-windows",
        nargs="*",
        type=float,
        default=[3.0, 5.0, 7.0],
        help="Window lengths in seconds for the stability scan",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    output_dir = generate_validation_report(
        file_path=args.file,
        output_dir=args.output_dir,
        sheet_name=_parse_sheet(args.sheet),
        time_column=args.time_column,
        signal_column=args.signal_column,
        t0=args.t0,
        target_frequency_hz=args.target_frequency,
        relative_tolerance=args.relative_tolerance,
        model_order=args.order,
        detrend=args.detrend,
        pencil_parameter=args.pencil,
        stability_orders=args.orders,
        stability_t0_values=args.stability_t0,
        stability_windows_s=args.stability_windows,
        debug=args.debug,
    )
    print(f"Validation report written to {output_dir}")
    return 0


def _build_synthetic_signal(time: np.ndarray, config: SyntheticCaseConfig) -> np.ndarray:
    rng = np.random.default_rng(config.random_seed)
    signal = config.amplitude_true * np.exp(config.d_true * time) * np.cos(
        2.0 * np.pi * config.f_true * time + config.phase_true
    )
    if config.second_mode is not None:
        second_frequency, second_damping, second_amplitude, second_phase = config.second_mode
        signal = signal + second_amplitude * np.exp(second_damping * time) * np.cos(
            2.0 * np.pi * second_frequency * time + second_phase
        )
    if config.offset != 0.0:
        signal = signal + config.offset
    if config.noise_std > 0.0:
        signal = signal + config.noise_std * rng.normal(size=len(time))
    return signal


def _closest_mode(modes: list[object], target_frequency_hz: float) -> object:
    return min(modes, key=lambda mode: abs(mode.frequency_hz - target_frequency_hz))


def _conjugate_partner(mode: object, modes: list[object]) -> object | None:
    candidates = [candidate for candidate in modes if candidate.index != mode.index]
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda candidate: (
            abs(candidate.pole - np.conj(mode.pole)),
            abs(candidate.frequency_hz - mode.frequency_hz),
            abs(candidate.damping - mode.damping),
        ),
    )


def _sorted_modes_frame(rows: list[dict[str, object]], empty_columns: list[str] | None = None) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=empty_columns or [])
    frame = pd.DataFrame(rows)
    if "distance_to_target_hz" in frame.columns:
        frame["distance_to_target_hz"] = pd.to_numeric(frame["distance_to_target_hz"], errors="coerce")
    sort_columns = [column for column in ["distance_to_target_hz", "frequency_hz", "damping", "index"] if column in frame.columns]
    if sort_columns:
        frame = frame.sort_values(by=sort_columns, kind="stable", na_position="last")
    return frame.reset_index(drop=True)


def _save_synthetic_plot(result: SyntheticCaseResult, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(result.time, result.signal, label="Synthetic signal", linewidth=1.2)
    ax.plot(
        result.prepared.segment_time,
        result.prepared.baseline + result.prepared.residual,
        label="Preprocessed signal",
        linewidth=1.0,
        alpha=0.8,
    )
    ax.plot(
        result.prepared.segment_time,
        result.prepared.baseline,
        label="Baseline",
        linewidth=1.0,
        alpha=0.7,
    )
    ax.plot(
        result.prepared.segment_time,
        _reconstructed_segment_signal(result),
        label="Matrix-Pencil reconstruction",
        linewidth=1.2,
    )
    ax.set_title(result.config.name.replace("_", " ").title())
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Signal")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _reconstructed_segment_signal(result: SyntheticCaseResult) -> np.ndarray:
    segment_time_relative = result.prepared.segment_time - result.prepared.segment_time[0]
    reconstructed_uniform = result.prepared.baseline + result.segment_analysis.analysis.reconstruction
    return np.interp(
        segment_time_relative,
        result.prepared.uniform_time,
        reconstructed_uniform,
    )


def _synthetic_summary_line(label: str, result: SyntheticCaseResult) -> str:
    return (
        f"- {label}: recovered `{result.recovered_frequency_hz:.6f}` Hz and `{result.recovered_damping:.6f}` 1/s "
        f"(true `{result.config.f_true:.6f}` Hz / `{result.config.d_true:.6f}` 1/s), "
        f"pair amplitude estimate `{result.recovered_pair_amplitude:.6f}`, phase estimate `{result.recovered_phase_rad:.6f}`, "
        f"reconstruction error `{result.reconstruction_error:.6e}`."
    )


def _stability_cluster_lines(frequencies: pd.Series) -> list[str]:
    values = frequencies.to_numpy(dtype=float)
    near_192 = int(np.count_nonzero(np.abs(values - 1.921094) <= 0.08))
    near_224 = int(np.count_nonzero(np.abs(values - 2.24) <= 0.08))
    lines: list[str] = []
    if near_192 > 0:
        lines.append(f"- Parameter combinations near `1.92 Hz`: `{near_192}`")
    if near_224 > 0:
        lines.append(f"- Parameter combinations near `2.24 Hz`: `{near_224}`")
    if near_192 == 0 and near_224 == 0:
        lines.append("- The representative in-band mode does not cluster tightly around either `1.92 Hz` or `2.24 Hz`.")
    return lines


def _parse_sheet(raw_sheet: str) -> str | int:
    try:
        return int(raw_sheet)
    except ValueError:
        return raw_sheet


if __name__ == "__main__":
    raise SystemExit(main())
