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
.\.venv\Scripts\python.exe -m pip install -e .[dev]
```

In Git Bash:

```bash
cd /c/Sevgi/projects/prony_matrix_pencil_filter
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -e ".[dev]"
```

## Daten ablegen

Die mitgegebenen Unterlagen konnten beim Anlegen des Projekts lokal nicht automatisch gefunden werden. Lege die Dateien bei Bedarf hier ab:

```text
data/
  Aufgabe.txt
  Pencil_Method.pdf
  vde-fnn-hinweis-netzbildende-eigenschaftenv2-1_ah.pdf
  Frequenz_Leistungs_Pendelung.XLS
  Frequenz_Leistungs_Pendelung_negativer_Sprung.XLS
  Python Implementierung.url
```

## Spalten anzeigen

```powershell
.\.venv\Scripts\python.exe -m prony_filter.cli --file data\Frequenz_Leistungs_Pendelung.XLS --list-columns
```

## Analyse ausführen

```powershell
.\.venv\Scripts\python.exe -m prony_filter.cli --file data\Frequenz_Leistungs_Pendelung.XLS --t0 1.0 --remove 1.8 3.2 --tol 0.2 --order 12 --output-dir outputs
```

Optional mit expliziten Spalten:

```powershell
.\.venv\Scripts\python.exe -m prony_filter.cli --file data\Frequenz_Leistungs_Pendelung.XLS --time-column Zeit --signal-column Wirkleistung --t0 1.0 --remove 1.8 3.2 --tol 0.2 --order 12
```

## Output

Der CLI-Lauf erzeugt:

- `filtered_signal.csv`
- `modes.csv`
- `comparison_plot.png`
- optional `results.xlsx`

Die Modentabelle enthält:

- Frequenz in Hz
- Dämpfung
- Amplitude
- Phase
- entfernt ja/nein

## Grenzen des Prototyps

- Die Modellordnung muss fachlich plausibel gewählt werden.
- Stark verrauschte oder nicht gleichmäßig abgetastete Daten müssen vorher geprüft werden.
- Aktuell wird bei ungleichmäßiger Abtastung auf ein gleichmäßiges Raster interpoliert.
- Die Amplitude wird aus komplexen Exponentialkoeffizienten abgeleitet und ist als technische Kenngröße zu verstehen.

