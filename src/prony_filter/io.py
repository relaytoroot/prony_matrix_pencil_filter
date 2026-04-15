from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from .filtering import FilterResult


TIME_KEYWORDS = ("time", "zeit", "t ", "t[s]", "t_s", "seconds", "sec")
SIGNAL_KEYWORDS = ("leistung", "power", "frequency", "frequenz", "p ", "q ", "signal", "y")


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
    signal_column = _find_by_keywords(signal_candidates, SIGNAL_KEYWORDS) or signal_candidates[0]
    return time_column, signal_column


def extract_time_signal(
    frame: pd.DataFrame,
    time_column: str | None = None,
    signal_column: str | None = None,
) -> tuple[np.ndarray, np.ndarray, str, str]:
    if time_column is None or signal_column is None:
        guessed_time, guessed_signal = guess_time_signal_columns(frame)
        time_column = time_column or guessed_time
        signal_column = signal_column or guessed_signal
    time_values = pd.to_numeric(frame[time_column], errors="coerce").to_numpy(dtype=float)
    signal_values = pd.to_numeric(frame[signal_column], errors="coerce").to_numpy(dtype=float)
    return time_values, signal_values, time_column, signal_column


def export_results(result: FilterResult, output_dir: str | Path, write_excel: bool = True) -> dict[str, Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    signal_frame = pd.DataFrame(
        {
            "time": result.time,
            "original": result.original,
            "filtered": result.filtered,
            "removed_component": result.removed_component,
        }
    )
    modes_frame = pd.DataFrame(result.analysis.as_table())

    written = {
        "filtered_csv": output_path / "filtered_signal.csv",
        "modes_csv": output_path / "modes.csv",
    }
    signal_frame.to_csv(written["filtered_csv"], index=False)
    modes_frame.to_csv(written["modes_csv"], index=False)
    if write_excel:
        excel_path = output_path / "results.xlsx"
        with pd.ExcelWriter(excel_path) as writer:
            signal_frame.to_excel(writer, sheet_name="filtered_signal", index=False)
            modes_frame.to_excel(writer, sheet_name="modes", index=False)
        written["excel"] = excel_path
    return written


def _find_by_keywords(columns: Iterable[str], keywords: tuple[str, ...]) -> str | None:
    for column in columns:
        normalized = f" {column.lower()} "
        if any(keyword in normalized for keyword in keywords):
            return column
    return None

