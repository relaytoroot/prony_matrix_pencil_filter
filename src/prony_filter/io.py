from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Iterable

import numpy as np
import pandas as pd

from .filtering import FilterResult
from .resonance import ResonanceBand, modes_in_resonance_bands

if TYPE_CHECKING:
    from .spectral import FFTPeak, FFTSpectrumResult


TIME_KEYWORDS = ("time", "zeit", "t ", "t[s]", "t_s", "seconds", "sec")
SIGNAL_KEYWORDS = ("leistung", "power", "frequency", "frequenz", "p ", "p_", "q ", "signal", "y")
PREFERRED_SIGNAL_COLUMNS = ("P_pos",)


@dataclass(slots=True)
class ReportTables:
    summary_frame: pd.DataFrame
    modes_frame: pd.DataFrame
    signal_frame: pd.DataFrame
    all_modes_frame: pd.DataFrame
    fft_spectrum_frame: pd.DataFrame | None
    fft_peaks_frame: pd.DataFrame | None
    resonance_comparison_frame: pd.DataFrame | None
    summary_items: dict[str, str]
    warnings: list[str]


def read_table(path: str | Path, sheet_name: str | int | None = 0) -> pd.DataFrame:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(file_path)
    suffix = file_path.suffix.lower()
    if suffix in {".xls", ".xlsx", ".xlsm"}:
        return pd.read_excel(file_path, sheet_name=sheet_name)
    if suffix in {".csv", ".txt"}:
        return pd.read_csv(file_path)
    raise ValueError(f"Unsupported file type: {suffix}")


def list_columns(frame: pd.DataFrame) -> list[str]:
    return [str(column) for column in frame.columns]


def numeric_columns(frame: pd.DataFrame) -> list[str]:
    result: list[str] = []
    for column in frame.columns:
        values = pd.to_numeric(frame[column], errors="coerce")
        if values.notna().sum() >= 3:
            result.append(str(column))
    return result


def guess_time_signal_columns(frame: pd.DataFrame) -> tuple[str, str]:
    numeric = numeric_columns(frame)
    if len(numeric) < 2:
        raise ValueError("Could not find at least two numeric columns")

    time_column = _find_by_keywords(numeric, TIME_KEYWORDS) or numeric[0]
    signal_candidates = [column for column in numeric if column != time_column]
    signal_column = (
        _find_preferred_column(signal_candidates, PREFERRED_SIGNAL_COLUMNS)
        or _find_by_keywords(signal_candidates, SIGNAL_KEYWORDS)
        or signal_candidates[0]
    )
    linked_time_column = _guess_time_column_left_of_signal(frame, signal_column)
    if linked_time_column is not None:
        time_column = linked_time_column
    return time_column, signal_column


def extract_time_signal(
    frame: pd.DataFrame,
    time_column: str | None = None,
    signal_column: str | None = None,
) -> tuple[np.ndarray, np.ndarray, str, str]:
    if time_column is None and signal_column is not None:
        time_column = guess_time_column_for_signal(frame, signal_column)
    if time_column is None or signal_column is None:
        guessed_time, guessed_signal = guess_time_signal_columns(frame)
        time_column = time_column or guessed_time
        signal_column = signal_column or guessed_signal

    time_label = _resolve_column_label(frame, time_column)
    signal_label = _resolve_column_label(frame, signal_column)
    time_values = pd.to_numeric(frame[time_label], errors="coerce").to_numpy(dtype=float)
    signal_values = pd.to_numeric(frame[signal_label], errors="coerce").to_numpy(dtype=float)
    return time_values, signal_values, str(time_label), str(signal_label)


def guess_time_column_for_signal(frame: pd.DataFrame, signal_column: str) -> str:
    """Guess the matching time column for a selected signal column.

    Some exported XLS files contain multiple time/signal pairs, for example
    ``Unnamed: 0`` + ``f`` and ``Unnamed: 2`` + ``P_pos``. In that layout the
    most useful default is the numeric column immediately left of the selected
    signal.
    """
    columns = [str(column) for column in frame.columns]
    if signal_column not in columns:
        raise KeyError(
            f"Unknown signal column: {signal_column}. Available columns: {', '.join(columns)}"
        )
    candidate = _guess_time_column_left_of_signal(frame, signal_column)
    if candidate is not None:
        return candidate

    guessed_time, _ = guess_time_signal_columns(frame)
    return guessed_time


def build_signal_frame(result: FilterResult) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "time": result.time,
            "original": result.original,
            "removed_component": result.removed_component,
            "filtered": result.filtered,
        }
    )


def build_modes_frame(result: FilterResult) -> pd.DataFrame:
    return pd.DataFrame(result.analysis.as_table())


def build_resonance_modes_frame(result: FilterResult) -> pd.DataFrame:
    columns = [
        "Frequenz [Hz]",
        "Daempfung [1/s]",
        "Amplitude",
        "Phase [rad]",
        "Abstand zur Zielresonanz [Hz]",
        "Entfernt",
        "Auswahlgrund",
    ]
    rows = []
    for mode in modes_in_resonance_bands(result.analysis.modes, result.selection_bands):
        rows.append(
            {
                "Frequenz [Hz]": mode.frequency_hz,
                "Daempfung [1/s]": mode.damping,
                "Amplitude": mode.amplitude,
                "Phase [rad]": mode.phase_rad,
                "Abstand zur Zielresonanz [Hz]": mode.distance_to_target_hz,
                "Entfernt": "ja" if mode.removed else "nein",
                "Auswahlgrund": mode.selection_reason,
            }
        )
    return pd.DataFrame(rows, columns=columns)


def build_report_tables(
    result: FilterResult,
    input_path: str | Path,
    signal_column: str,
    t0: float,
    fft_result: FFTSpectrumResult | None = None,
    resonance_comparison_rows: Iterable[dict[str, object]] | None = None,
) -> ReportTables:
    signal_frame = build_signal_frame(result)
    all_modes_frame = build_modes_frame(result)
    modes_frame = build_resonance_modes_frame(result)
    fft_spectrum_frame = None if fft_result is None else pd.DataFrame(fft_result.spectrum_table())
    fft_peaks_frame = None if fft_result is None else pd.DataFrame(fft_result.peaks_table())
    resonance_comparison_frame = None
    if resonance_comparison_rows is not None:
        resonance_comparison_frame = pd.DataFrame(list(resonance_comparison_rows))

    band_summaries = _build_band_summaries(result.selection_bands, result.analysis.modes, fft_result)
    warnings = _collect_warnings(result, t0=t0, band_summaries=band_summaries)
    summary_items = _build_summary_items(
        input_path=input_path,
        signal_column=signal_column,
        result=result,
        t0=t0,
        band_summaries=band_summaries,
        warnings=warnings,
    )
    summary_frame = pd.DataFrame(
        {
            "Field": list(summary_items.keys()),
            "Value": list(summary_items.values()),
        }
    )
    return ReportTables(
        summary_frame=summary_frame,
        modes_frame=modes_frame,
        signal_frame=signal_frame,
        all_modes_frame=all_modes_frame,
        fft_spectrum_frame=fft_spectrum_frame,
        fft_peaks_frame=fft_peaks_frame,
        resonance_comparison_frame=resonance_comparison_frame,
        summary_items=summary_items,
        warnings=warnings,
    )


def export_results(
    result: FilterResult,
    output_dir: str | Path,
    input_path: str | Path,
    signal_column: str,
    t0: float,
    write_excel: bool = True,
    debug: bool = False,
    fft_result: FFTSpectrumResult | None = None,
    resonance_comparison_rows: Iterable[dict[str, object]] | None = None,
    report: ReportTables | None = None,
) -> dict[str, Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    report_tables = report or build_report_tables(
        result,
        input_path=input_path,
        signal_column=signal_column,
        t0=t0,
        fft_result=fft_result,
        resonance_comparison_rows=resonance_comparison_rows,
    )

    written: dict[str, Path] = {}
    if write_excel:
        excel_path = output_path / "result.xlsx"
        with pd.ExcelWriter(excel_path) as writer:
            report_tables.summary_frame.to_excel(writer, sheet_name="Summary", index=False)
            report_tables.modes_frame.to_excel(writer, sheet_name="Modes", index=False)
            report_tables.signal_frame.to_excel(writer, sheet_name="Signal", index=False)
        written["result_xlsx"] = excel_path

    if debug:
        signal_csv_path = output_path / "filtered_signal.csv"
        modes_csv_path = output_path / "modes.csv"
        report_tables.signal_frame.to_csv(signal_csv_path, index=False)
        report_tables.all_modes_frame.to_csv(modes_csv_path, index=False)
        written["filtered_csv"] = signal_csv_path
        written["modes_csv"] = modes_csv_path
        if report_tables.fft_spectrum_frame is not None:
            fft_spectrum_path = output_path / "fft_spectrum.csv"
            report_tables.fft_spectrum_frame.to_csv(fft_spectrum_path, index=False)
            written["fft_spectrum_csv"] = fft_spectrum_path
        if report_tables.fft_peaks_frame is not None:
            fft_peaks_path = output_path / "fft_peaks.csv"
            report_tables.fft_peaks_frame.to_csv(fft_peaks_path, index=False)
            written["fft_peaks_csv"] = fft_peaks_path
        if report_tables.resonance_comparison_frame is not None:
            comparison_path = output_path / "resonance_comparison.csv"
            report_tables.resonance_comparison_frame.to_csv(comparison_path, index=False)
            written["resonance_comparison_csv"] = comparison_path

    return written


def _build_summary_items(
    input_path: str | Path,
    signal_column: str,
    result: FilterResult,
    t0: float,
    band_summaries: list[dict[str, object]],
    warnings: list[str],
) -> dict[str, str]:
    if len(result.segment_time) == 0:
        analysis_window = f"ab t0={t0:.6f} s"
    else:
        analysis_window = f"{result.segment_time[0]:.6f} s bis {result.segment_time[-1]:.6f} s"

    if band_summaries:
        target_resonance = _format_band_lines(band_summaries, _target_text)
        resonance_band = _format_band_lines(band_summaries, _band_text)
        strongest_peak = _format_band_lines(band_summaries, _peak_text)
        selected_mode = _format_band_lines(band_summaries, _mode_text)
        damping = _format_band_lines(band_summaries, _damping_text)
        amplitude = _format_band_lines(band_summaries, _amplitude_text)
        decision = _format_band_lines(band_summaries, _decision_text)
    else:
        target_resonance = "nicht konfiguriert"
        resonance_band = "nicht konfiguriert"
        strongest_peak = "keine Resonanzbaender konfiguriert"
        selected_mode = "keine Resonanzbaender konfiguriert"
        damping = "n/a"
        amplitude = "n/a"
        decision = "nicht entfernt"

    return {
        "Eingabedatei": str(Path(input_path)),
        "Analysiertes Signal": signal_column,
        "Sprungzeitpunkt t0": f"{t0:.6f} s",
        "Analysefenster": analysis_window,
        "Zielresonanz": target_resonance,
        "Resonanzband": resonance_band,
        "Staerkster FFT-Peak im Resonanzband": strongest_peak,
        "Ausgewaehlte Matrix-Pencil-Mode": selected_mode,
        "Daempfung": damping,
        "Amplitude": amplitude,
        "Entscheidung": decision,
        "Warnungen": "\n".join(warnings) if warnings else "-",
    }


def _build_band_summaries(
    bands: list[ResonanceBand],
    modes: list,
    fft_result: FFTSpectrumResult | None,
) -> list[dict[str, object]]:
    peaks = [] if fft_result is None else list(fft_result.peaks)
    summaries: list[dict[str, object]] = []
    for band in bands:
        modes_in_band = [mode for mode in modes if band.contains(mode.frequency_hz)]
        selected_mode = None
        if modes_in_band:
            selected_mode = min(
                modes_in_band,
                key=lambda mode: (
                    _target_distance_or_midpoint(mode.frequency_hz, band),
                    mode.index,
                ),
            )
        peak_in_band = None
        peaks_in_band = [peak for peak in peaks if band.contains(peak.frequency_hz)]
        if peaks_in_band:
            peak_in_band = max(peaks_in_band, key=lambda peak: peak.magnitude)
        summaries.append(
            {
                "band": band,
                "selected_mode": selected_mode,
                "candidate_count": len(modes_in_band),
                "peak_in_band": peak_in_band,
            }
        )
    return summaries


def _collect_warnings(result: FilterResult, t0: float, band_summaries: list[dict[str, object]]) -> list[str]:
    warnings: list[str] = []
    if not result.selection_bands:
        warnings.append("Keine Resonanzbaender konfiguriert.")

    for summary in band_summaries:
        band = summary["band"]
        selected_mode = summary["selected_mode"]
        peak_in_band = summary["peak_in_band"]
        candidate_count = int(summary["candidate_count"])
        band_label = f"{band.low_hz:.6f}-{band.high_hz:.6f} Hz"

        if peak_in_band is None:
            warnings.append(f"Kein FFT-Peak im Resonanzband {band_label}.")
        if selected_mode is None:
            warnings.append(f"Keine Matrix-Pencil-Mode im Resonanzband {band_label}.")
        if candidate_count > 1:
            warnings.append(
                f"Mehrere Matrix-Pencil-Kandidaten im Resonanzband {band_label}: {candidate_count}."
            )
        if peak_in_band is not None and selected_mode is None:
            warnings.append(
                f"Inkonsistenz im Resonanzband {band_label}: FFT-Peak vorhanden, aber keine Matrix-Pencil-Mode."
            )
        if peak_in_band is not None and selected_mode is not None:
            frequency_gap = abs(peak_in_band.frequency_hz - selected_mode.frequency_hz)
            threshold = max(0.05, 0.5 * (band.high_hz - band.low_hz))
            if frequency_gap > threshold:
                warnings.append(
                    f"Inkonsistenz im Resonanzband {band_label}: FFT-Peak {peak_in_band.frequency_hz:.6f} Hz "
                    f"und Matrix-Pencil-Mode {selected_mode.frequency_hz:.6f} Hz liegen weit auseinander."
                )

    warnings.extend(_validate_signal_consistency(result, t0=t0))
    return _unique_messages(warnings)


def _validate_signal_consistency(result: FilterResult, t0: float) -> list[str]:
    warnings: list[str] = []
    before_mask = result.time < t0
    after_mask = result.time >= t0

    if before_mask.any() and not np.allclose(result.filtered[before_mask], result.original[before_mask]):
        warnings.append("Vor t0 weicht filtered vom Original ab.")
    if before_mask.any() and not np.allclose(result.removed_component[before_mask], 0.0):
        warnings.append("Vor t0 ist removed_component nicht null.")
    if after_mask.any() and not np.allclose(
        result.filtered[after_mask],
        result.original[after_mask] - result.removed_component[after_mask],
    ):
        warnings.append("Nach t0 gilt filtered != original - removed_component.")
    if not any(mode.removed for mode in result.analysis.modes) and not np.allclose(result.filtered, result.original):
        warnings.append("Es wurde keine Mode entfernt, aber filtered weicht vom Original ab.")
    return warnings


def _resolve_column_label(frame: pd.DataFrame, requested: str | None) -> object:
    if requested is None:
        raise KeyError("Column name must not be None")
    for column in frame.columns:
        if str(column) == requested:
            return column
    available = ", ".join(list_columns(frame))
    raise KeyError(f"Unknown column: {requested}. Available columns: {available}")


def _find_by_keywords(columns: Iterable[str], keywords: tuple[str, ...]) -> str | None:
    for column in columns:
        normalized = f" {column.lower()} "
        if any(keyword in normalized for keyword in keywords):
            return column
    return None


def _find_preferred_column(columns: Iterable[str], preferred_names: tuple[str, ...]) -> str | None:
    normalized_map = {column.lower(): column for column in columns}
    for preferred_name in preferred_names:
        match = normalized_map.get(preferred_name.lower())
        if match is not None:
            return match
    return None


def _looks_like_time_column(series: pd.Series) -> bool:
    values = pd.to_numeric(series, errors="coerce").dropna().to_numpy(dtype=float)
    if len(values) < 3:
        return False
    diffs = np.diff(values)
    if np.any(diffs <= 0):
        return False
    median_dt = float(np.median(diffs))
    if median_dt <= 0:
        return False
    return bool(np.allclose(diffs, median_dt, rtol=1e-2, atol=max(1e-12, median_dt * 1e-4)))


def _guess_time_column_left_of_signal(frame: pd.DataFrame, signal_column: str) -> str | None:
    columns = [str(column) for column in frame.columns]
    if signal_column not in columns:
        return None
    signal_index = columns.index(signal_column)
    numeric = set(numeric_columns(frame))
    for candidate in reversed(columns[:signal_index]):
        if candidate in numeric and _looks_like_time_column(frame[_resolve_column_label(frame, candidate)]):
            return candidate
    return None


def _format_band_lines(
    band_summaries: list[dict[str, object]],
    formatter,
) -> str:
    values: list[str] = []
    multi_band = len(band_summaries) > 1
    for index, summary in enumerate(band_summaries, start=1):
        text = formatter(summary)
        if multi_band:
            text = f"Band {index}: {text}"
        values.append(text)
    return "\n".join(values)


def _target_text(summary: dict[str, object]) -> str:
    band = summary["band"]
    if band.target_frequency_hz is None:
        return "nicht explizit angegeben"
    return f"{band.target_frequency_hz:.6f} Hz"


def _band_text(summary: dict[str, object]) -> str:
    band = summary["band"]
    return f"{band.low_hz:.6f} bis {band.high_hz:.6f} Hz"


def _peak_text(summary: dict[str, object]) -> str:
    peak = summary["peak_in_band"]
    if peak is None:
        return "kein Peak im Band"
    return f"{peak.frequency_hz:.6f} Hz (Magnitude {peak.magnitude:.6f})"


def _mode_text(summary: dict[str, object]) -> str:
    selected_mode = summary["selected_mode"]
    if selected_mode is None:
        return "keine Mode im Band"
    return f"{selected_mode.frequency_hz:.6f} Hz"


def _damping_text(summary: dict[str, object]) -> str:
    selected_mode = summary["selected_mode"]
    if selected_mode is None:
        return "n/a"
    return f"{selected_mode.damping:.6f} 1/s"


def _amplitude_text(summary: dict[str, object]) -> str:
    selected_mode = summary["selected_mode"]
    if selected_mode is None:
        return "n/a"
    return f"{selected_mode.amplitude:.6f}"


def _decision_text(summary: dict[str, object]) -> str:
    selected_mode = summary["selected_mode"]
    if selected_mode is None or not selected_mode.removed:
        return "nicht entfernt"
    return "entfernt"


def _target_distance_or_midpoint(frequency_hz: float, band: ResonanceBand) -> float:
    target_distance = band.distance_to_target_hz(frequency_hz)
    if target_distance is not None:
        return target_distance
    return abs(abs(float(frequency_hz)) - band.midpoint_hz)


def _unique_messages(messages: Iterable[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for message in messages:
        if not message or message in seen:
            continue
        seen.add(message)
        unique.append(message)
    return unique
