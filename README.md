# Prony Matrix Pencil Filter

Prototype zur Analyse und Filterung von Frequenz- und Leistungspendelungen nach einem Sprungtest.

Ziel ist eine bereinigte Zeitreihe aus `Y(t)`, nachdem bekannte gedämpfte Schwingungen erkannt, rekonstruiert und vom Signal abgezogen wurden.

## Fachlicher Hintergrund

Nach einem Sprungtest kann die Antwort des Systems näherungsweise als Summe gedämpfter Schwingungen modelliert werden:

```text
y(t) = Sum_i A_i * exp(d_i * t) * cos(2*pi*f_i*t + phi_i)
```

Dabei sind:

- `f_i`: Frequenz der Mode in Hz
- `d_i`: Dämpfung als Realteil des kontinuierlichen Pols
- `A_i`: Amplitude
- `phi_i`: Phase

Fachlich wird oft von Prony-Analyse gesprochen. Intern nutzt dieses Projekt aktuell Matrix Pencil als robustes Kernverfahren. `prony.py` bleibt als Wrapper erhalten, damit später bei Bedarf ein klassisches Prony-Verfahren ergänzt werden kann.

## FFT und Matrix Pencil

Die neue Arbeitslogik ist bewusst zweistufig:

1. FFT als Voranalyse: zeigt dominante Frequenzanteile im gewählten Analysefenster.
2. Matrix Pencil / Prony-artige Analyse: bestimmt gedämpfte Moden mit Frequenz, Dämpfung, Amplitude und Phase.
3. Resonanzband festlegen: nicht als exakter Einzelwert, sondern als fachlich plausibles Band.
4. Matrix-Pencil-Mode im Band auswählen, rekonstruieren und vom Signal abziehen.

Wichtig:

- Die FFT filtert nicht direkt heraus.
- Die FFT liefert nur einen Hinweis für ein plausibles Resonanzband.
- Die eigentliche Bereinigung erfolgt über die rekonstruierten Matrix-Pencil-Moden.

Im aktuellen Testfall zeigt die FFT einen dominanten Peak bei ungefähr `2.24 Hz`. Die Matrix-Pencil-Analyse findet im selben Setup eine entfernbare Mode bei ungefähr `1.921 Hz`. Diese Mode liegt innerhalb des Resonanzbands `2.2 Hz +/- 20 %`, also `1.76 Hz bis 2.64 Hz`.

## Resonanzband statt Punktziel

Mechanische Resonanzen sollen in diesem Tool nicht nur als exakter Zielwert betrachtet werden. Deshalb gibt es jetzt drei Auswahlwege:

- Exakter Zielwert mit absoluter Toleranz:

```powershell
.\.venv\Scripts\python.exe -m prony_filter.cli --file data\Frequenz_Leistungs_Pendelung.XLS --signal-column P_pos --t0 1.0 --remove 2.2 --tol 0.2
```

- Exakter Zielwert mit relativer Toleranz:

```powershell
.\.venv\Scripts\python.exe -m prony_filter.cli --file data\Frequenz_Leistungs_Pendelung.XLS --signal-column P_pos --t0 1.0 --remove 2.2 --rel-tol 0.2
```

- Explizites Resonanzband:

```powershell
.\.venv\Scripts\python.exe -m prony_filter.cli --file data\Frequenz_Leistungs_Pendelung.XLS --signal-column P_pos --t0 1.0 --remove-band 1.76 2.64
```

Bei `--remove 2.2 --rel-tol 0.2` ergibt sich automatisch das Band `1.76 Hz bis 2.64 Hz`.

## Projektstruktur

```text
prony_matrix_pencil_filter/
  README.md
  pyproject.toml
  src/
    prony_filter/
      __init__.py
      cli.py
      filtering.py
      io.py
      matrix_pencil.py
      plotting.py
      prony.py
      resonance.py
      spectral.py
      stability.py
  examples/
    run_example.py
    stability_scan.py
  notebooks/
    01_explore_data.ipynb
  tests/
  data/
  outputs/
```

## Installation

```powershell
cd C:\Sevgi\projects\prony_matrix_pencil_filter
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
```

In Git Bash:

```bash
cd /c/Sevgi/projects/prony_matrix_pencil_filter
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -e ".[dev]"
```

## Mitgelieferte Unterlagen

Die ZIP-Unterlagen liegen lokal unter `data/`. Dieser Ordner ist absichtlich in Git ignoriert, damit Messdaten und PDFs nicht versehentlich auf GitHub landen.

Erkannte XLS-Struktur:

- `Frequenz_Leistungs_Pendelung.XLS`
- `Frequenz_Leistungs_Pendelung_negativer_Sprung.XLS`
- Frequenzsignal: Zeitspalte `Unnamed: 0`, Signalspalte `f`
- Leistungssignal: Zeitspalte `Unnamed: 2`, Signalspalte `P_pos`

## Spalten anzeigen

```powershell
.\.venv\Scripts\python.exe -m prony_filter.cli --file data\Frequenz_Leistungs_Pendelung.XLS --list-columns
```

## Analyse ausführen

Leistungssignal mit relativer Resonanzband-Auswahl:

```powershell
.\.venv\Scripts\python.exe -m prony_filter.cli --file data\Frequenz_Leistungs_Pendelung.XLS --signal-column P_pos --t0 1.0 --remove 2.2 --rel-tol 0.2 --order 12 --pencil 256 --output-dir outputs\leistung_resonanzband
```

Leistungssignal mit explizitem Resonanzband:

```powershell
.\.venv\Scripts\python.exe -m prony_filter.cli --file data\Frequenz_Leistungs_Pendelung.XLS --signal-column P_pos --t0 1.0 --remove-band 1.76 2.64 --order 12 --pencil 256 --output-dir outputs\leistung_band --no-excel
```

Standardmaessig wird fuer die fachliche Auswertung das Wirkleistungssignal `P_pos` verwendet. Dazu erkennt der Import automatisch die direkt links stehende Zeitspalte `Unnamed: 2`.

`--pencil 256` hält die Matrix-Pencil-Rechnung bei großen Messdateien handlich. Ohne Angabe nutzt das Tool ebenfalls einen begrenzten, sicheren Default.

## Output

Ein normaler CLI-Lauf erzeugt im gewählten Output-Ordner nur zwei Dateien:

- `result.xlsx`
- `comparison_plot.png`

`result.xlsx` enthält drei Sheets:

- `Summary`: Eingabedatei, analysiertes Signal, Resonanzband, staerkster FFT-Peak im Band, ausgewaehlte Matrix-Pencil-Mode, Entscheidung und Warnungen
- `Modes`: nur Moden im Resonanzband
- `Signal`: `time`, `original`, `removed_component`, `filtered`

Mit `--debug` werden zusaetzlich Diagnose-Dateien wie `filtered_signal.csv`, `modes.csv`, `fft_spectrum.csv`, `fft_peaks.csv`, `resonance_comparison.csv` und `fft_plot.png` erzeugt.

Der fachliche Vergleich im Summary folgt weiterhin dieser Logik:

```text
FFT-Peak: ca. 2.24 Hz
vorgegebene Resonanz: 2.2 Hz
verwendetes Band: 1.76 bis 2.64 Hz
Matrix-Pencil-Mode: 1.921094 Hz
Entscheidung: entfernt, weil im Resonanzband
```

## Stabilitätstest

Für die Robustheitsprüfung gibt es ein kleines Scan-Skript:

```powershell
.\.venv\Scripts\python.exe examples\stability_scan.py --file data\Frequenz_Leistungs_Pendelung.XLS --signal-column P_pos --t0 1.0 --remove 2.2 --rel-tol 0.2
```

Das Skript testet standardmäßig:

- Modellordnungen `8, 10, 12, 14, 16`
- `t0`-Variationen von `-0.02 s` bis `+0.02 s`
- optional auch verschiedene Analysefenster über `--window-seconds`

Die Ergebnisse landen in `stability_report.csv` und `stability_summary.md`.

## Validierung

Fuer die fachliche Validierung gibt es jetzt einen eigenen Report-Lauf. Er erzeugt synthetische Referenztests, den FFT-vs-Matrix-Pencil-Vergleich auf demselben Signalabschnitt und einen Stabilitaetsscan in einem gemeinsamen Ordner:

```powershell
.\.venv\Scripts\python.exe -m prony_filter.validation --file data\Frequenz_Leistungs_Pendelung.XLS --signal-column P_pos --t0 1.0
```

Der Ordner `validation_report/` enthaelt unter anderem:

- `synthetic_clean_modes.csv`
- `synthetic_noisy_modes.csv`
- `real_fft_peaks.csv`
- `real_modes_in_band.csv`
- `real_resonance_comparison.csv`
- `stability_report.csv`
- `stability_summary.md`
- `summary.md`

Mit `--debug` werden zusaetzlich die grossen Diagnoseartefakte wie synthetische Plot-PNGs, `real_modes.csv`, `real_fft_spectrum.csv` und `real_fft_plot.png` geschrieben.

Interpretation:

- Reines synthetisches Einzelsignal: Matrix Pencil sollte die vorgegebene Frequenz direkt wiederfinden.
- Simulierte oder echt gemessene Sprungantwort: FFT-Peak und Matrix-Pencil-Mode koennen voneinander abweichen, weil Sprunganteil, Daempfung, Offset, weitere Moden, Fensterwahl und Modellordnung eine Rolle spielen.

## Tests und Beispiele

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe examples\run_example.py
.\.venv\Scripts\python.exe examples\stability_scan.py --file data\Frequenz_Leistungs_Pendelung.XLS --signal-column P_pos --t0 1.0
.\.venv\Scripts\python.exe -m prony_filter.validation --file data\Frequenz_Leistungs_Pendelung.XLS --signal-column P_pos --t0 1.0
```

## Grenzen des Prototyps

- Die Modellordnung muss fachlich plausibel gewählt werden.
- `t0` muss zum Sprungtest passen, sonst werden falsche Signalanteile geschätzt.
- Ungleichmäßig abgetastete Daten werden intern auf ein gleichmäßiges Raster interpoliert.
- FFT und Matrix Pencil können unterschiedliche, aber fachlich trotzdem vereinbare Hinweise liefern.
- Der Prototyp ist ein technischer Startpunkt und noch kein Zertifizierungstool.
