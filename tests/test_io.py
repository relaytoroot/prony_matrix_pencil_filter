from __future__ import annotations

from uuid import uuid4
from pathlib import Path

import numpy as np
import pandas as pd

from prony_filter.filtering import filter_known_modes
from prony_filter.io import (
    build_report_tables,
    export_results,
    extract_time_signal,
    guess_time_column_for_signal,
    guess_time_signal_columns,
)
from prony_filter.spectral import analyze_fft_spectrum, build_resonance_comparison_rows


def test_signal_column_selects_nearest_time_column() -> None:
    frame = pd.DataFrame(
        {
            "Unnamed: 0": [0.0, 0.1, 0.2, 0.3],
            "f": [50.0, 50.1, 50.0, 49.9],
            "Unnamed: 2": [1.0, 1.1, 1.2, 1.3],
            "P_pos": [100.0, 105.0, 102.0, 101.0],
        }
    )

    assert guess_time_column_for_signal(frame, "P_pos") == "Unnamed: 2"
    assert guess_time_signal_columns(frame) == ("Unnamed: 2", "P_pos")

    time, signal, time_column, signal_column = extract_time_signal(frame, signal_column="P_pos")

    assert time_column == "Unnamed: 2"
    assert signal_column == "P_pos"
    assert time.tolist() == [1.0, 1.1, 1.2, 1.3]
    assert signal.tolist() == [100.0, 105.0, 102.0, 101.0]


def test_export_results_default_writes_only_result_xlsx() -> None:
    result, fft_result, resonance_comparison = _build_example_result()
    report = build_report_tables(
        result,
        input_path="input.xlsx",
        signal_column="P_pos",
        t0=1.0,
        fft_result=fft_result,
        resonance_comparison_rows=resonance_comparison,
    )
    output_dir = Path("test_artifacts") / f"default_export_{uuid4().hex}"
    output_dir.mkdir(parents=True, exist_ok=True)

    written = export_results(
        result,
        output_dir=output_dir,
        input_path="input.xlsx",
        signal_column="P_pos",
        t0=1.0,
        fft_result=fft_result,
        resonance_comparison_rows=resonance_comparison,
        report=report,
    )

    assert set(written) == {"result_xlsx"}
    assert (output_dir / "result.xlsx").exists()
    assert not (output_dir / "filtered_signal.csv").exists()
    assert not (output_dir / "modes.csv").exists()
    assert not (output_dir / "fft_spectrum.csv").exists()
    assert not (output_dir / "fft_peaks.csv").exists()
    assert not (output_dir / "resonance_comparison.csv").exists()


def test_report_tables_provide_summary_modes_and_signal_sheets() -> None:
    result, fft_result, resonance_comparison = _build_example_result()
    report = build_report_tables(
        result,
        input_path="input.xlsx",
        signal_column="P_pos",
        t0=1.0,
        fft_result=fft_result,
        resonance_comparison_rows=resonance_comparison,
    )

    assert report.summary_frame["Field"].tolist() == [
        "Eingabedatei",
        "Analysiertes Signal",
        "Sprungzeitpunkt t0",
        "Analysefenster",
        "Zielresonanz",
        "Resonanzband",
        "Staerkster FFT-Peak im Resonanzband",
        "Ausgewaehlte Matrix-Pencil-Mode",
        "Daempfung",
        "Amplitude",
        "Entscheidung",
        "Warnungen",
    ]
    assert list(report.modes_frame.columns) == [
        "Frequenz [Hz]",
        "Daempfung [1/s]",
        "Amplitude",
        "Phase [rad]",
        "Abstand zur Zielresonanz [Hz]",
        "Entfernt",
        "Auswahlgrund",
    ]
    assert list(report.signal_frame.columns) == ["time", "original", "removed_component", "filtered"]
    assert not report.modes_frame.empty


def _build_example_result():
    dt = 0.01
    time = np.arange(0, 10, dt)
    step_time = 1.0
    clean = np.ones_like(time) * 10.0
    response_time = np.maximum(0.0, time - step_time)
    oscillation = 1.5 * np.exp(-0.3 * response_time) * np.cos(2 * np.pi * 2.0 * response_time)
    values = clean + np.where(time >= step_time, oscillation, 0.0)

    result = filter_known_modes(
        time=time,
        values=values,
        t0=step_time,
        remove_frequencies_hz=[2.0],
        tolerance_hz=0.15,
        model_order=6,
    )
    fft_result = analyze_fft_spectrum(result.residual, dt=result.analysis.dt, peak_count=20)
    resonance_comparison = build_resonance_comparison_rows(
        result.selection_bands,
        result.analysis.modes,
        fft_result,
    )
    return result, fft_result, resonance_comparison
