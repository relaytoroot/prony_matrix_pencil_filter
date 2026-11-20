"""Versuche, Messkanäle und Quellenangaben für das lokale Matrix-Pencil-Labor."""

from __future__ import annotations

import json
import sysconfig
from functools import lru_cache
from pathlib import Path


ARCHIVE = Path(__file__).with_name("labor_data")
_XLS = {
    "positive": "Frequenz_Leistungs_Pendelung.XLS",
    "negative": "Frequenz_Leistungs_Pendelung_negativer_Sprung.XLS",
}


@lru_cache(maxsize=1)
def catalog() -> dict[str, dict]:
    """Einträge sind nach Versuchsgruppe geordnet. Frequenzparameter stehen in Hz."""
    legacy_limits = dict(target=2.2, tolerance=0.44, minTarget=0.5, maxTarget=10,
                         minTolerance=0.05, maxTolerance=1)
    generator = dict(
        id="synthetic", title="Eigene Schwingungen erzeugen", group="Signalgenerator",
        description="Beginne mit einem einzelnen Ton, mische eine zweite Schwingung hinzu und vergleiche die Schätzung mit deinen Vorgaben.",
        signalLabel="Amplitude", unit="a. E.", sampleRate=100, t0=0, order=2,
        sourceName="Signalgenerator im Projekt", processing="800 berechnete Werte in acht Sekunden.",
        target=3, tolerance=0.35, minTarget=0.1, maxTarget=40, minTolerance=0.01, maxTolerance=5,
    )
    entries = {generator["id"]: generator}
    for source, name in _XLS.items():
        titel = "Positiver Frequenzsprung" if source == "positive" else "Negativer Frequenzsprung"
        entries[source] = dict(
            id=source, title=titel, group="Sprungtests im Projekt",
            description="Leistungsantwort nach dem Frequenzsprung bei einer Sekunde. "
                        "Vergleiche die gefundene Pendelung mit der des anderen Sprungtests.",
            signalLabel="Leistung P_pos", unit="Dateieinheit", sampleRate=4000, t0=1, order=12,
            sourceName=name, processing="Messkanal P_pos mit eigener Zeitspalte. Die Datei nennt keine physikalische Einheit.",
            **legacy_limits,
        )
    for folder in ("ereignisse", "netzbetrieb", "mechanik", "akustik"):
        manifest = ARCHIVE / folder / "manifest.json"
        for entry in json.loads(manifest.read_text(encoding="utf-8-sig")):
            source = entry["id"]
            if source in entries:
                raise ValueError(f"Doppelte Versuchskennung im Katalog: {source}")
            rate = entry["sampleRate"]
            filename = entry.pop("file")
            if Path(filename).name != filename or not filename.endswith(".csv"):
                raise ValueError(f"Ungültiger Messdateiname für {source}")
            # Selbst das breiteste einstellbare Band bleibt unter der Nyquistfrequenz.
            entry.update(
                csvPath=manifest.parent / filename, csvUrl=f"/api/data/{source}.csv",
                minTarget=min(rate / 1000, 0.05, entry["target"]),
                minTolerance=min(rate / 10000, 0.01, entry["tolerance"]),
                maxTarget=round(rate * 0.40, 9), maxTolerance=round(rate * 0.09, 9),
            )
            entries[source] = entry
    return entries


def public_catalog() -> dict:
    experiments = [{key: value for key, value in entry.items() if key != "csvPath"}
                   for entry in catalog().values()]
    return {"experiments": experiments}


def xls_path(source: str) -> Path:
    filename = _XLS[source]
    project_file = Path(__file__).resolve().parents[2] / "data" / filename
    if project_file.is_file():
        return project_file
    return Path(sysconfig.get_path("data")) / "share" / "prony-filter" / filename
