from __future__ import annotations

import pandas as pd

from prony_filter.io import extract_time_signal, guess_time_column_for_signal


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

    time, signal, time_column, signal_column = extract_time_signal(frame, signal_column="P_pos")

    assert time_column == "Unnamed: 2"
    assert signal_column == "P_pos"
    assert time.tolist() == [1.0, 1.1, 1.2, 1.3]
    assert signal.tolist() == [100.0, 105.0, 102.0, 101.0]
