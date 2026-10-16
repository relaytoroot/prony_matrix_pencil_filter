# Prony Matrix Pencil Filter

## Projekt und Zusammenarbeit

- Antworte auf Deutsch und erklaere technische Zusammenhaenge schrittweise.
- Dieses Python-Projekt schaetzt und subtrahiert gedaempfte Schwingungsanteile
  aus Zeitreihen. Der implementierte Kern ist Matrix Pencil; eine eigenstaendige
  klassische Prony-Implementierung ist nicht vorhanden.
- Aktuelle Aufgabe: die vorhandene Praesentation gemeinsam Folie fuer Folie
  nachvollziehen und ausbauen. Pro Gespraechsschritt genau eine Folie behandeln.
- Publikum: technisch, mit Grundlagen in linearer Algebra.
- Der Nutzer moechte insbesondere Matrixaufbau, SVD, Eigenwerte, Normen sowie
  Herkunft, Einheiten und Skalierung aller Diagrammachsen selbst verstehen.
- Zu jeder Folie die Leitfrage, Daten- oder Codequelle, Rechenschritte,
  Folienaussage und einen kurzen Sprechtext erarbeiten. Bei Diagrammen Zeitbezug,
  Achsenwerte, Darstellungsfaktor und sichtbaren Ausschnitt getrennt erklaeren.
- Bestehende Aenderungen erhalten. Rohmessungen als Eingabedaten behandeln.
  Ueberarbeitete Praesentationen zunaechst als eigene Arbeitsfassung speichern.

## Einstieg und Dateien

1. `examples/minimal_matrix_pencil.py`: ueberschaubare reine Mathematik.
2. `src/prony_filter/matrix_pencil.py`: produktiver mathematischer Kern.
3. `src/prony_filter/filtering.py`: Vorbereitung, Polschaetzung, gemeinsame
   Koeffizientenanpassung auf dem Messraster und Filterentscheidung.
4. `src/prony_filter/io.py`: Messdateien und passende Zeitspalten einlesen.
5. `docs/PRONY_VORSTELLUNG.md`: fachlicher Ueberblick; Stand 18.09.2026.
6. `docs/praesentation/README.md` und `Sprechmanuskript.md`: Aufbau und Erklaerungen
   der vorhandenen Praesentation mit 26 Folien; Stand 15.10.2026.

Unter `docs/praesentation/` liegen die Originaldateien:

- `Projektarbeit_Schwingungsanalyse_Matrix_Pencil_mit_Sprechtext.pptx`
- `Projektarbeit_Schwingungsanalyse_Matrix_Pencil.pdf`
- `Sprechmanuskript.md` und `Sprechmanuskript.pdf`

`examples/presentation_demo.py` fuehrt beide lokalen Sprungmessungen aus.
Tests stehen unter `tests/`; Abhaengigkeiten und Paketdefinition in `pyproject.toml`.

## Lokale Umgebung und Befehle

Windows-Projektordner: `C:\Sevgi\projects\prony_matrix_pencil_filter`.
Eine `.venv` ist bereits vorhanden. Nutze ihren Interpreter.

PowerShell, jeweils im Projektordner:

```powershell
.\.venv\Scripts\python.exe examples\minimal_matrix_pencil.py
.\.venv\Scripts\python.exe examples\slide_02_measurement.py
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

In Git Bash lautet der Interpreterpfad `./.venv/Scripts/python.exe`.
Falls eine neue Umgebung erforderlich ist:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
```

Erzeugte Ergebnisse gehoeren unter `outputs/` und sind nicht versioniert.
Pruefe mathematische Aenderungen mit den passenden vorhandenen Tests.
Fuer reine Erklaerungs- oder Darstellungsanpassungen genuegt die gezielte
Ausfuehrung und Sichtpruefung des betroffenen Beispiels.

## Fachliche Konventionen

- Modell: `y[k] = sum(c_i * z_i**k)`, `s_i = log(z_i) / dt`.
  Frequenz `abs(Im(s_i))/(2*pi)`; Abklingrate `Re(s_i)` in 1/s.
- Ein konjugiertes Polpaar bildet eine reelle Kosinusschwingung.
  Ihre Anfangsamplitude ist `2*abs(c_i)`; Anfangsphase und Amplitude beziehen
  sich auf den Anfang des Analyseabschnitts.
- Hankel-Matrizen: `H0[i,j] = y[i+j]`, `H1[i,j] = y[i+j+1]`.
  Bei N Messwerten und L Spalten hat jede Matrix die Form `(N-L, L)`.
- SVD: `H0 = U @ Sigma @ V.T` fuer reelle Daten. Nach dem Abschneiden auf r
  Richtungen entsteht `B = Sigma_r^-1 @ U_r.T @ H1 @ V_r` mit Form `(r,r)`.
  Die Eigenwerte von B schaetzen die diskreten Pole.
- r ist das Minimum aus gewuenschter Ordnung und numerischem Rang.
  Die produktive Berechnung verwendet die konjugierte Transposition.
- Das Minimalbeispiel besitzt 800 Werte, L=256, zwei rauschfreie Schwingungen
  bei 2,24 und 5 Hz und Rang 4. H0/H1 sind 544x256, B ist 4x4. Auch bei
  angeforderter Ordnung 12 behaelt dieses Beispiel nur vier Richtungen.
- Die Folien zur negativen Sprungantwort nennen H0/H1 mit 345x256 und B mit
  12x12. Diese Groessen gehoeren zu diesem Analyseabschnitt und dieser Ordnung.
- Die Projektdateien enthalten `f` mit Zeitspalte `Unnamed: 0` und `P_pos`
  mit eigener Zeitspalte `Unnamed: 2`. Diese Zeitspalten nicht vertauschen.
- Analysiert wird hier `P_pos`. Seine physikalische Einheit ist nicht
  dokumentiert. Eine Division durch 10^6 begruendet keine Einheit MW.
- Die Leistungspendelung um 2,27 Hz und die Netzfrequenz um 50 Hz sind
  unterschiedliche Groessen. Der externe Mexiko-Fall analysiert dagegen
  Schwankungen der Netzfrequenz um 60 Hz.
- Norm auf Folie 12: euklidische Vektornorm, Wurzel aus der Quadratsumme.
  `e_rel = ||x - x_hat||_2 / ||x - mean(x)||_2` gilt fuer die dort verwendete
  Mittelwertbereinigung. Im Code wird der Fehler auf dem Schaetzraster geprueft;
  andere Vorverarbeitungen muessen entsprechend beruecksichtigt werden.
- Fitfehlergrenze 10 %, Abzugsnorm maximal 1,25-mal Residualnorm und maximale
  relative Daempfung 0,3 sind implementierte Pruefregeln. Eine Filterfreigabe
  oder ein kleiner Fitfehler beweist keine physikalisch eindeutige Zerlegung.

## Uebergabestand am 16.10.2026

- Folie 1 wurde besprochen. Vorschlag fuer den Untertitel:
  "Von der Messkurve zu Schwingungsparametern und gezieltem Signalabzug".
  Dieser Vorschlag wurde noch nicht in die Original-PowerPoint eingearbeitet.
- Aktuelle Folie ist 2: "Schwingungen in elektrischen Messsignalen".
  Besprochen wurden die negative Sprungantwort, Zeitfenster 2 bis 7 s,
  Anzeigewerte `P_pos / 1_000_000` und y-Achsengrenzen 6,85 bis 7,00.
  Skalierungsfaktor und vergroesserter Achsenausschnitt getrennt erklaeren.
- `examples/slide_02_measurement.py` wurde in dieser Sitzung hinzugefuegt und
  erfolgreich ausgefuehrt. Es erzeugt PNG und SVG unter `outputs/folienaufbau/`.
  Die Kurve verwendet unveraenderte Messwerte mit reiner Anzeigeskalierung.
- Die 2153 gespeicherten Diagrammpunkte der Originalfolie 2 wurden gegen die
  XLS-Messwerte abgeglichen: Zeitpunkte und skalierte Werte stimmen bis auf
  Rundung der gespeicherten Dezimalzahlen ueberein. Das neue Beispiel zeigt
  alle 20001 Messpunkte des Abschnitts.
- Nachtrag Claude Code: Die y-Teilstriche des Beispiels lagen zunaechst bei
  6,87 bis 6,99, weil `MultipleLocator(0.03)` ab null zaehlt. Das PPTX-Diagramm
  verwendet Minimum 6,85, Maximum 7,00 und Hauptschritt 0,03; das Beispiel
  setzt jetzt dieselben Teilstriche und gibt Zeitraster und Wertebereich aus.
- Originalfolien 1 und 2 wurden aus dem vorhandenen PDF als Bilder gerendert:
  `outputs/folienaufbau/originalfolien/folie_01.png` und `folie_02.png`.
- Eine ChatGPT-Pages-Ansicht dieser beiden Bilder wurde angelegt. Sie ist kein
  lokaler Teil des Projekts; fuer Claude die lokalen PDF-/PPTX-Dateien oder
  die gerenderten Bilder verwenden.
- Die Original-PPTX und das Manuskript wurden in dieser Sitzung nicht geaendert.
- Achsen und Skalierung von Folie 2 wurden in Claude Code getrennt erklaert:
  Zeitbezug (Frequenzsprung bei etwa 1,0 s), Achsenwerte, Faktor 10^6 und
  vergroesserter Ausschnitt.
- Naechster Schritt: Rueckfragen zu Folie 2 klaeren; bei "weiter" mit Folie 3
  fortfahren.
- Diese Datei uebertraegt den Arbeitskontext, nicht den vollstaendigen Chat.

## Claude Code

Claude Desktop ist lokal installiert unter
`C:\Users\sevgi\AppData\Local\AnthropicClaude\claude.exe`.
Der Nutzer moechte diese vorhandene Installation verwenden. In der Desktop-App
den Bereich Code, die Umgebung Local und den bestehenden Projektordner waehlen.
Ein separater `claude`-Terminalbefehl wurde bei der Uebergabe nicht gefunden.

`CLAUDE.md` im Projektordner wird von Claude Code als Projektkontext geladen.
Offizielle Referenz: https://code.claude.com/docs/en/memory
Desktop-Anleitung: https://code.claude.com/docs/en/desktop
