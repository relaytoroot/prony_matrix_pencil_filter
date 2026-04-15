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

Fachlich wird oft von Prony-Analyse gesprochen. Intern kann dafür aber auch das Matrix-Pencil-Verfahren genutzt werden, weil es für verrauschte Messdaten oft robuster und numerisch gut nachvollziehbar ist.

## Prony oder Matrix Pencil?

- Prony ist historisch bekannt und gut erklärbar, kann aber empfindlich auf Rauschen und Modellordnung reagieren.
- Matrix Pencil nutzt eine Hankel-Matrix und eine SVD-basierte Rangreduktion. Das ist für den ersten Prototypen die robustere Standardwahl.
- Dieses Projekt nutzt deshalb Matrix Pencil als Kernverfahren. `prony.py` enthält bewusst einen Wrapper, damit später ein klassisches Prony-Verfahren ergänzt werden kann.

## Projektstruktur

```text
prony_matrix_pencil_filter/
  README.md
  pyproject.toml
  src/
    prony_filter/
      __init__.py
      io.py
      matrix_pencil.py
      prony.py
      filtering.py
      plotting.py
      cli.py
  notebooks/
    01_explore_data.ipynb
  tests/
    test_matrix_pencil.py
    test_filtering.py
  examples/
    run_example.py
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

Frequenzsignal analysieren:

```powershell
.\.venv\Scripts\python.exe -m prony_filter.cli --file data\Frequenz_Leistungs_Pendelung.XLS --time-column "Unnamed: 0" --signal-column f --t0 1.0 --remove 1.8 3.2 --tol 0.2 --order 12 --pencil 256 --output-dir outputs\frequenz_pos --no-excel
```

Leistungssignal analysieren:

```powershell
.\.venv\Scripts\python.exe -m prony_filter.cli --file data\Frequenz_Leistungs_Pendelung.XLS --signal-column P_pos --t0 1.0 --remove 1.8 3.2 --tol 0.2 --order 12 --pencil 256 --output-dir outputs\leistung_pos --no-excel
```

Wenn `--signal-column P_pos` gewählt wird, erkennt der Import automatisch die direkt links stehende Zeitspalte `Unnamed: 2`.

`--pencil 256` hält die Matrix-Pencil-Rechnung bei großen Messdateien handlich. Ohne Angabe nutzt das Tool ebenfalls einen begrenzten, sicheren Default.

## Output

Der CLI-Lauf erzeugt im gewählten Output-Ordner:

- `filtered_signal.csv`: Originalsignal, gefiltertes Signal und entfernte Komponente.
- `modes.csv`: erkannte Moden mit Frequenz, Dämpfung, Amplitude, Phase und Entfernt-Markierung.
- `comparison_plot.png`: Originalsignal gegen bereinigtes Signal.
- `results.xlsx`: optionaler Excel-Export, wenn `--no-excel` nicht gesetzt ist.

Die Modentabelle enthält:

- Frequenz in Hz
- Dämpfung
- Amplitude
- Phase
- entfernt ja/nein

## Tests und Beispiel

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe examples\run_example.py
```

## Grenzen des Prototyps

- Die Modellordnung muss fachlich plausibel gewählt werden.
- `t0` muss zum Sprungtest passen, sonst werden falsche Signalanteile geschätzt.
- Ungleichmäßig abgetastete Daten werden intern auf ein gleichmäßiges Raster interpoliert.
- Der Prototyp ist ein technischer Startpunkt und noch kein Zertifizierungstool.
