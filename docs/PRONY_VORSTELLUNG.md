# Prony-/Matrix-Pencil-Analyse vorstellen

Stand: 18.09.2026. Die Umsetzung verwendet **Matrix Pencil**, keine eigenständige klassische Prony-Implementierung.

## Erklärung in einer Minute

> Wir zerlegen die Antwort nach einem Sprung in gedämpfte Schwingungen. Die FFT zeigt zuerst, in welchem Frequenzbereich Schwingungen liegen. Matrix Pencil schätzt zusätzlich Dämpfung, Amplitude und Phase. Zugelassene Schwingungen im gewünschten Band werden rekonstruiert und vom Original abgezogen. Die Sprungantwort und die übrigen Signalanteile bleiben als Rest erhalten. An synthetischen Signalen kennen wir die richtige Antwort; bei Messdaten prüfen wir zusätzlich die Empfindlichkeit gegenüber den Auswerteparametern.

Das Modell lautet:

`y(t) = Summe A_i * exp(d_i * t) * cos(2*pi*f_i*t + phi_i)`

- `f_i`: Frequenz in Hz; `d_i < 0`: abklingende Schwingung.
- `A_i`: Kosinusamplitude am Anfang des Analysefensters; `phi_i`: Phase.
- Diskret: `y[k] = Summe c_i * z_i**k`; kontinuierlicher Pol: `s_i = log(z_i)/dt`.
- Frequenz: `abs(Im(s_i))/(2*pi)`; Dämpfung: `Re(s_i)`.
- Zwei komplex konjugierte Pole bilden eine reale Schwingung. Ihre Kosinusamplitude ist `2*abs(c_i)`. Der Excel-Bericht fasst das Paar zusammen; die Diagnose-CSV zeigt einzelne Pole.

## Minimaler Codepfad

Zum Nachvollziehen der Mathematik reicht zuerst eine Datei:
[examples/minimal_matrix_pencil.py](../examples/minimal_matrix_pencil.py).
Sie enthaelt ein kuenstliches Signal mit bekannten Moden und direkt darunter
die fuenf Rechenschritte: Hankel-Matrizen, SVD, Eigenwerte, Koeffizienten und
Rekonstruktion beziehungsweise Subtraktion. Start:

```powershell
.\.venv\Scripts\python.exe examples\minimal_matrix_pencil.py
```

Die produktive Umsetzung bleibt umfangreicher, weil sie Messdateien,
Anti-Aliasing, ungleichmaessige Zeitraster, Auswahlgrenzen und Exporte absichert.

## Vollstaendiger Produktionspfad

| Datei / Funktion | Was passiert dort? |
|---|---|
| [examples/presentation_demo.py](../examples/presentation_demo.py), `main()` | Überschaubarer Gesamtweg: Daten laden, filtern, FFT vergleichen, Ergebnisse exportieren. |
| [filtering.py](../src/prony_filter/filtering.py), `prepare_signal_segment()` | Passende Messwerte ab `t0` auswählen, Zeitraster vereinheitlichen und Offset/Trend behandeln. |
| [filtering.py](../src/prony_filter/filtering.py), `_prepare_estimation_signal()` | Überabtastete Messwerte mit Anti-Aliasing-Filter für die Polschätzung reduzieren. |
| [matrix_pencil.py](../src/prony_filter/matrix_pencil.py), `_build_pencil_matrix()` | Zwei um einen Messwert versetzte Hankel-Matrizen bilden. SVD trennt den beibehaltenen Signalunterraum ab. Eigenwertproblem auf die Modellordnung reduzieren. |
| [matrix_pencil.py](../src/prony_filter/matrix_pencil.py), `matrix_pencil()` | Eigenwerte als diskrete Pole bestimmen; daraus Frequenz und Dämpfung berechnen. |
| [filtering.py](../src/prony_filter/filtering.py), `analyze_prepared_segment()` | Pole auf das ursprüngliche Zeitraster übertragen und alle Koeffizienten gemeinsam per kleinste Quadrate anpassen. |
| [resonance.py](../src/prony_filter/resonance.py), `annotate_modes_for_resonance_bands()` | Bandzugehörigkeit, Wachstum und Dämpfungsgrenze prüfen; Auswahl begründen. |
| [filtering.py](../src/prony_filter/filtering.py), `filter_known_modes()` | Ausgewählte Komponenten abziehen: `filtered = original - removed_component`. Vor `t0` und nach einem begrenzten Fenster bleibt das Original erhalten. |
| [tests/test_filtering.py](../tests/test_filtering.py) | Referenzprüfung mit 4.000 Hz, bekannter 2,24-Hz-Mode, anderer Schwingung und einer möglichen Aliasing-Störung. |

Die zentrale SVD-Reduktion ist `S_r^-1 @ U_r.H @ Y1 @ V_r`. Das Ergebnis hat nur `r x r` Einträge. Die frühere `L x L`-Matrix enthielt zusätzlich einen Nullraum, dessen numerisch kleine Eigenwerte zu Scheinmoden werden konnten.

## Was wurde verbessert?

1. Eigenwerte werden nur im beibehaltenen Signalunterraum berechnet.
2. Bei der 2,2-Hz-Analyse werden 4.000 Hz auf 100 Hz für die Polschätzung reduziert. Ein Pencil mit 256 Abtastwerten umfasst dadurch 2,56 s statt 64 ms. Kurze Fenster begrenzen die Pencil-Größe zusätzlich auf die halbe Datenlänge.
3. Amplituden werden auf den Originalwerten angepasst; das exportierte Signal wird nicht pauschal tiefpassgefiltert.
4. Wachsende Moden und standardmäßig Dämpfungsverhältnisse `zeta > 0.3` werden nicht subtrahiert. `zeta = -d/sqrt(d²+(2*pi*f)²)`; die Grenze ist über `--max-damping-ratio` einstellbar.
5. Ein Fitfehler über 10 % auf dem Schätzraster oder eine entfernte Komponente mit mehr als dem 1,25-Fachen der Residualnorm blockiert die Bereinigung. Das sind Auswahlregeln, keine physikalische Zertifizierung.
6. Das Excel-Summary enthält beide Abtastraten und den Fitfehler. Konjugierte Pole erzeugen keine doppelte Kandidatenwarnung mehr. Der Plot zeigt die große Sprungantwort, eine vergrößerte spätere Phase und die entfernte Schwingung getrennt.

## Reproduzierbare Vorstellung

Im Projektordner ausführen (die beiden XLS-Messdateien werden unter `data/` mitgeliefert):

```powershell
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
.\.venv\Scripts\python.exe examples\presentation_demo.py
```

Die Begrenzung der BLAS-Threads vermeidet auf diesem Rechner unnötigen Verwaltungsaufwand bei kleinen Matrizen; sie ändert nicht die Methode.

Ausgabe: `outputs/presentation_demo/positive/` und `negative/`, jeweils mit Excel, Vergleichsplot und Diagnose-CSV. `outputs/presentation_demo/summary.json` enthält die Kennzahlen. Die zusätzliche spektrale Kontrolle verwendet **für beide Signale denselben Abschnitt 4–7 s**, lineare Trendbereinigung und ein Hann-Fenster. Verglichen wird die Energie der FFT-Stützstellen im Band 1,76–2,64 Hz. Diese Kennzahl belegt die Abschwächung im Band, aber nicht die physikalische Richtigkeit jeder entfernten Mode.

Einzelanalyse:

```powershell
.\.venv\Scripts\python.exe -m prony_filter.cli --file data\Frequenz_Leistungs_Pendelung.XLS --signal-column P_pos --t0 1 --remove 2.2 --rel-tol 0.2 --output-dir outputs\vorstellung
```

Tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

## Nachgewiesener Stand und Grenzen

Mit Ordnung 12 und dem gesamten verfügbaren Abschnitt ab 1 s:

| Messdatei | Dominante Mode | Dämpfung |
|---|---:|---:|
| `Frequenz_Leistungs_Pendelung.XLS` | 2,268418 Hz | -0,106929 1/s |
| `Frequenz_Leistungs_Pendelung_negativer_Sprung.XLS` | 2,267978 Hz | -0,191769 1/s |

Der FFT-Peak im Band liegt in diesem gesamten Abschnitt bei 2,333236 Hz. FFT-Maximum und modale Frequenz sind unterschiedliche Schätzgrößen; Sprunganteil und Fenster beeinflussen das FFT-Spektrum.

Die neuen Stabilitätsberichte liegen unter `outputs/validation_20260918_positive/` und `outputs/validation_20260918_negative/`. Je Datei werden 45 Kombinationen untersucht: Ordnungen 8/10/12/14/16, Startzeiten 0,98/1,00/1,02 s, angeforderte Fenster 3/5/7 s. Fenster enden spätestens mit den Messdaten; ein angefordertes 7-s-Fenster ist hier also kürzer als 7 s.

- Negative Sprungmessung: **45/45** mit zugelassener Bandmode; repräsentative Frequenzen **2,263865–2,273155 Hz**.
- Positive Sprungmessung: **37/45** mit zugelassener Bandmode. Alle 30 Kombinationen mit angeforderten Fenstern von 5 oder 7 s haben eine zugelassene Mode; 3-s-Fenster bleiben deutlich empfindlicher.
- Ein zugelassener Bandtreffer ist noch kein Stabilitätsnachweis. Auch mehrere benachbarte Moden und abweichende Dämpfungen kommen vor. Das ist insbesondere bei der positiven Sprungmessung weiter fachlich zu bewerten.
- Die Auswahlgrenzen sind sichtbar und dokumentiert. Es wird keine Modellordnung automatisch so lange angepasst, bis die gewünschte Frequenz erscheint.

## Fachliche Quellen

- Hua und Sarkar, [Matrix Pencil Method for Estimating Parameters of Exponentially Damped/Undamped Sinusoids in Noise](https://www.math.ucdavis.edu/~saito/data/sonar/HuaSarkarPencilMethod.pdf), 1990.
- SciPy, [resample_poly](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.resample_poly.html): polyphasige Abtastratenumsetzung mit Tiefpassfilter; hier mit linearer Randfortsetzung.
