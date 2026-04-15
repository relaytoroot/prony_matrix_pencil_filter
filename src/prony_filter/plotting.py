from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from .filtering import FilterResult


def save_comparison_plot(result: FilterResult, path: str | Path, title: str = "Original vs. gefiltert") -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(result.time, result.original, label="Original", linewidth=1.2)
    ax.plot(result.time, result.filtered, label="Bereinigt", linewidth=1.2)
    ax.set_title(title)
    ax.set_xlabel("Zeit")
    ax.set_ylabel("Signal")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path

