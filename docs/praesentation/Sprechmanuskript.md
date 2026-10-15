# Sprechmanuskript: Schwingungsanalyse mit Matrix Pencil

Zu den 26 Folien der Projektpräsentation. Der Fließtext ist zum Sprechen gedacht. Die Zeigehinweise dienen zur Orientierung und werden nicht vorgelesen.

Das Manuskript umfasst rund 4.200 Wörter. Bei ruhigem Sprechen und kurzen Pausen sind etwa 35 bis 45 Minuten einzuplanen.

In der PowerPoint-Datei steht der Sprechtext auch in den Notizen jeder Folie. Die Bezeichnung „P pos“ im Sprechtext entspricht dem Messkanal `P_pos`.

## Folie 01: Schwingungsanalyse mit Matrix Pencil

**Zeigehinweis:** Auf den Titel zeigen; die beiden Messdatenarten gleich zu Beginn unterscheiden.

Elektrische Messsignale können nach einer Änderung des Betriebszustands pendeln. Ein Messwert steigt und fällt dann wiederholt, bevor sich der Verlauf beruhigt. Diese Projektarbeit untersucht, wie sich solche Schwingungen aus einer aufgezeichneten Kurve bestimmen und beschreiben lassen. Dazu wird das mathematische Verfahren Matrix Pencil verwendet.

Das Ziel ist zunächst eine Beschreibung der Messung: Wie schnell schwingen einzelne Anteile, wie stark sind sie und wie verändern sie sich mit der Zeit? Anschließend wird geprüft, ob sich ausgewählte Anteile rechnerisch abziehen lassen. Dabei müssen die Erkennung einer Schwingung und ihre Entfernung getrennt beurteilt werden.

Ich führe deshalb zuerst von der Messkurve zum Modell und erkläre die einzelnen Rechenschritte. Danach folgen die Ergebnisse. Die Anwendung beginnt mit unseren Projektmessungen der Leistung. Ein eigener Abschnitt behandelt anschließend externe Netzfrequenzmessungen aus Mexiko. Diese beiden Fälle zeigen unterschiedliche Messgrößen und werden entsprechend getrennt besprochen.

## Folie 02: Schwingungen in elektrischen Messsignalen

**Zeigehinweis:** Zuerst die Fragestellung nennen, dann die wiederkehrenden Wellen im konkreten Diagramm zeigen.

Wenn sich der Zustand eines elektrischen Systems ändert, muss sich der gemessene Wert nicht sofort auf einem neuen Niveau einpendeln. Er kann zunächst darüber und darunter schwanken. Eine solche wiederkehrende Änderung bezeichnen wir hier als Schwingung oder Pendelung. Ihre Stärke kann dabei mit der Zeit abnehmen.

Wir möchten diese Bewegung mit wenigen Eigenschaften beschreiben: mit ihrer Frequenz, also der Anzahl vollständiger Schwingungen pro Sekunde, mit ihrer Stärke und mit ihrem Abklingen. Falls ein bestimmter Anteil entfernt werden soll, müssen wir außerdem prüfen, ob seine mathematische Beschreibung dafür ausreichend zuverlässig ist.

Das Diagramm zeigt ein konkretes Beispiel aus unseren Projektmessungen: den Leistungskanal P pos nach einem negativen Frequenzsprung. Die sichtbare Leistungspendelung liegt bei etwa 2,27 Hertz. Der Leistungswert schwingt also ungefähr 2,27-mal pro Sekunde. Die Netzfrequenz dieses Datensatzes liegt dagegen in der Nähe von 50 Hertz. Diese beiden Frequenzen beschreiben unterschiedliche Vorgänge. Im nächsten Schritt ordne ich ein, wie aus dieser Messkurve eine geprüfte Filterausgabe entsteht.

## Folie 03: Überblick: von der Messung zur Filterausgabe

**Zeigehinweis:** Die vier Schritte von oben nach unten verfolgen und bei der Prüfung die Verbindung zurück zur Messung hervorheben.

Die gesamte Auswertung lässt sich in vier Schritte gliedern. Zuerst wählen wir aus der Messung eine bestimmte Größe und einen passenden Zeitabschnitt aus. Damit steht fest, welche Kurve wir überhaupt erklären wollen.

Im zweiten Schritt bildet das Verfahren ein Modell. Ein Modell ist hier eine berechnete Kurve, die sich aus mehreren einfachen Anteilen zusammensetzt. Dazu gehören Schwingungen und Übergänge, die ohne regelmäßiges Hin und Her abklingen. Ihre Summe soll den beobachteten Verlauf möglichst gut beschreiben.

Im dritten Schritt prüfen wir diese Beschreibung. Wir vergleichen die Modellkurve mit den Messwerten und ziehen bekannte Vergleichswerte heran, soweit solche verfügbar sind. Erst danach folgt der vierte Schritt: Ausgewählte Anteile werden abgezogen, sofern die festgelegten Prüfregeln erfüllt sind. Das Ergebnis ist die gefilterte Ausgabe.

Diese Abfolge gilt für beide Anwendungen. Zuerst betrachten wir die Leistung aus unseren Projektmessungen. Später folgt als eigener Vergleichsfall die Netzfrequenzmessung aus Mexiko. Die Methode ist dieselbe, die untersuchte Messgröße ist jeweils eine andere.

## Folie 04: Projektmessungen: Frequenz und Leistung

**Zeigehinweis:** Erst den Frequenzsprung bei ungefähr einer Sekunde, danach die zugehörige Leistungsantwort zeigen.

Hier sehen wir die beiden Projektmessungen genauer. Jede Datei enthält einen Frequenzkanal und den Leistungskanal P pos, jeweils mit einer eigenen Zeitspalte. Die Frequenz beginnt ungefähr bei 50 Hertz. Bei etwa einer Sekunde erfolgt eine Änderung nach oben oder nach unten. Darauf beziehen sich die Bezeichnungen positiver und negativer Sprung.

Die Leistung reagiert darauf mit einem ausgeprägten Übergang und einer überlagerten Pendelung. Genau diesen Leistungskanal analysieren wir mit Matrix Pencil. Der Frequenzverlauf zeigt hier vor allem, wann und in welche Richtung die Anregung erfolgt. Die Sprungrichtung beschreibt also nicht unmittelbar die Richtung der Leistungsänderung.

Eine Grenze der Dokumentation muss dabei sichtbar bleiben: In den Dateien sind weder die physikalische Einheit von P pos noch Messgerät und Versuchsaufbau eindeutig angegeben. Die Achse wurde lediglich zur besseren Lesbarkeit durch eine Million geteilt. Daraus lässt sich keine Einheit wie Megawatt ableiten. Unsere Aussagen beziehen sich deshalb auf die aufgezeichneten Signalverläufe und ihre mathematische Auswertung.

## Folie 05: Vom Messverlauf zum Analyseabschnitt

**Zeigehinweis:** Vom ausgewählten Zeitabschnitt zur Vereinfachung auf 100 Werte pro Sekunde gehen; danach auf die Ausgabe mit den ursprünglichen Messwerten verweisen.

Für die Analyse verwenden wir nicht wahllos die ganze Datei. Zuerst werden jedem Leistungswert der passende Zeitpunkt und der richtige Kanal zugeordnet. Dann wählen wir den Abschnitt von einer bis sieben Sekunden aus. Er beginnt ungefähr am Frequenzsprung. Der Mittelwert wird zunächst abgezogen, damit sich die Berechnung auf die Veränderungen um diesen Grundwert konzentriert.

Die Dateien enthalten ungefähr 4000 Werte pro Sekunde. Für die Bestimmung der Schwingungseigenschaften werden daraus 100 Werte pro Sekunde. Vorher begrenzt ein Tiefpass schnelle Signaländerungen. Das verhindert, dass beim Ausdünnen hohe Frequenzen fälschlich als langsamere Schwingungen erscheinen. Die Zahlen 4000 und 100 geben also die Abtastrate an: wie viele Werte pro Sekunde vorliegen.

Die gefundenen Schwingungsformen werden anschließend an die ursprünglichen, dichter liegenden Werte angepasst. Auch der Signalabzug erfolgt dort. Die Messwerte vor einer Sekunde bleiben unverändert. Für die Prüfung des Modellfehlers verwendet das Programm dagegen die aufbereiteten Daten mit 100 Werten pro Sekunde.

## Folie 06: Modell eines Schwingungsanteils

**Zeigehinweis:** Die Formel anhand der vier Parameter in der Tabelle erklären, ohne sie vollständig vorzulesen.

Ein einzelner Schwingungsanteil wird hier als regelmäßige Welle mit einer veränderlichen Hüllkurve beschrieben. Die Frequenz f bestimmt, wie viele vollständige Schwingungen pro Sekunde auftreten. Die Amplitude A beschreibt die Stärke zu Beginn des untersuchten Ausschnitts. Die Phase legt fest, an welcher Stelle der Welle der Ausschnitt beginnt, also beispielsweise nahe einem Maximum oder einem Nulldurchgang.

Sigma beschreibt, wie sich die Hüllkurve mit der Zeit verändert. Ist Sigma negativ, werden die Ausschläge kleiner. Bei Sigma gleich null bleibt die Stärke konstant. Ein positives Sigma würde im Modell ein Anwachsen beschreiben. Die Zeit in der Formel beginnt am Anfang des ausgewählten Analyseabschnitts.

Eine gemessene Kurve besteht meist nicht aus nur einer solchen Welle. Das Gesamtmodell setzt mehrere Anteile zusammen und ergänzt den zuvor abgezogenen Grundwert. Zusätzlich sind Verläufe möglich, die ohne Hin-und-her-Schwingen abklingen und beispielsweise einen Übergang beschreiben. Erst die Summe dieser Modellanteile wird mit den tatsächlichen Messwerten verglichen.

## Folie 07: Messfolge und verschobene Datenmatrizen

**Zeigehinweis:** Oben x[0] und x[1] zu den Zeiten zuordnen; anschließend die erste Zeile von H0 und H1 vergleichen.

Jetzt kommt der Schritt von der Messkurve zu den Matrizen. Oben steht eine Folge aufbereiteter Signalwerte. Der Mittelwert wurde bereits abgezogen und das Signal nach einer Tiefpassfilterung auf 100 Werte pro Sekunde reduziert. Zwischen zwei Werten liegen deshalb 0,01 Sekunden. x in eckiger Klammer null bezeichnet den ersten Wert bei einer Sekunde, x in Klammer eins den nächsten Wert. Die Zahl in der Klammer ist eine laufende Nummer und nicht die Größe des Messwerts.

Links werden jeweils drei benachbarte Werte in eine Zeile geschrieben. In der nächsten Zeile beginnt derselbe Ausschnitt einen Wert später. Deshalb erscheinen manche Werte mehrfach. Sie werden nicht mehrfach gemessen, sondern in mehreren überlappenden Ausschnitten verwendet. Diese Anordnung heißt Hankelmatrix.

Die rechte Matrix entsteht genauso, beginnt aber überall einen Schritt später. Beide Matrizen enthalten also dieselbe Messkurve, gegeneinander um 0,01 Sekunden verschoben. Das gezeigte Beispiel ist bewusst klein. In der tatsächlichen Auswertung der negativen Sprungantwort besitzt jede Matrix 345 Zeilen und 256 Spalten. Aus der Beziehung zwischen den beiden Matrizen werden anschließend die Schwingungseigenschaften bestimmt.

## Folie 08: Warum die Zeitverschiebung hilft

**Zeigehinweis:** Den Übergang vom einzelnen Anteil links zur Überlagerung rechts zeigen, dann die drei Rechenschritte unten verfolgen.

Warum hilft diese Verschiebung um einen Messschritt? Für einen einzelnen exponentiellen Modellanteil ist die Änderung von einem Schritt zum nächsten immer gleich: Man erhält den nächsten Wert, indem man mit demselben Faktor z multipliziert. Bei einer Schwingung ist dieser Faktor eine komplexe Zahl. Er enthält gleichzeitig die Änderung der Stärke und den Fortschritt innerhalb der Schwingung.

In einer Messung sind mehrere Anteile überlagert. Jeder hat seinen eigenen Faktor. Deshalb kann man nicht einfach zwei benachbarte Messwerte dividieren und daraus alle Schwingungen ablesen. Stattdessen wird die Beziehung zwischen den beiden großen Datenmatrizen gemeinsam ausgewertet.

Die Singulärwertzerlegung, kurz SVD, bildet dafür eine reduzierte Beschreibung. Mit der hier gewählten Ordnung zwölf bleibt eine Beschreibung mit zwölf Dimensionen. Daraus entsteht die kleinere Matrix B mit zwölf Zeilen und zwölf Spalten. Die Eigenwertberechnung liefert dann die gesuchten Faktoren z, auch Pole genannt. Vereinfacht sucht sie Änderungen, bei denen eine bestimmte Modellform erhalten bleibt und sich nur ihre Stärke und Phase verändern. Ordnung zwölf bedeutet dabei nicht automatisch zwölf reale Schwingungen: Eine reale schwingende Komponente wird gewöhnlich durch ein Paar komplexer Pole beschrieben.

## Folie 09: Betrag und Winkel des berechneten Pols

**Zeigehinweis:** Bei z beginnen; anschließend den Betrag links und den Winkel rechts als zwei Eigenschaften derselben Zahl erklären.

Hier sehen wir einen konkreten Pol aus der Leistungsantwort auf den negativen Frequenzsprung. Die Eigenwertberechnung liefert ungefähr 0,988 plus 0,142 mal i. Diese Werte wurden aus der Messung geschätzt. Sie wurden dem Verfahren nicht als erwartete Schwingung vorgegeben.

Eine komplexe Zahl lässt sich als Punkt in einer Ebene vorstellen. Der Realteil ist die waagerechte Koordinate, der Imaginärteil die senkrechte. Der Betrag r ist der Abstand dieses Punktes vom Ursprung. Er wird mit dem Satz des Pythagoras aus beiden Koordinaten berechnet. Hier beträgt er ungefähr 0,998084. Bei jedem Zeitschritt bleiben deshalb rund 99,8084 Prozent der Amplitude erhalten. Weil der Faktor etwas kleiner als eins ist, klingt dieser Anteil langsam ab.

Theta ist der Winkel zur positiven waagerechten Achse. Die Funktion atan2 berechnet ihn aus beiden Koordinaten und berücksichtigt dabei, in welchem der vier Quadranten der Punkt liegt. Hier beträgt der Winkel ungefähr 0,1425 Radiant oder 8,16 Grad. Das ist der Phasenfortschritt innerhalb von 0,01 Sekunden. Der Winkel ist also nicht die Anfangsphase der Schwingung. Betrag und Winkel beschreiben zusammen, wie sich dieser Modellanteil von einem Abtastschritt zum nächsten verändert. Daraus folgen auf der nächsten Folie Frequenz und Abklingrate.

## Folie 10: Frequenz und Dämpfung aus dem Pol

**Zeigehinweis:** Zuerst auf die beiden Umrechnungen links zeigen, anschließend auf die abklingende Kurve rechts.

Aus dem Pol der Leistungsmessung zum negativen Frequenzsprung kennen wir jetzt den Betrag r und den Winkel Theta. Beide beschreiben zunächst nur die Veränderung von einem Abtastschritt zum nächsten. Ein solcher Schritt dauert hier eine Hundertstelsekunde. Für eine verständliche Aussage müssen wir diese Veränderung auf eine Sekunde beziehen.

Der Winkel beträgt ungefähr 0,1425 Radiant pro Schritt. Eine vollständige Schwingung entspricht zwei Pi Radiant. Wir teilen deshalb zuerst durch zwei Pi und anschließend durch die Schrittdauer. So erhalten wir ungefähr 2,268 Hertz: Der Anteil im Leistungssignal schwingt etwas mehr als zweimal pro Sekunde. Das ist nicht die elektrische Netzfrequenz, die im zusätzlich aufgezeichneten Frequenzkanal bei etwa 50 Hertz liegt.

Der Betrag r liegt mit ungefähr 0,9981 knapp unter eins. Die Amplitude wird deshalb mit jedem Schritt etwas kleiner. Aus dem natürlichen Logarithmus von r, geteilt durch die Schrittdauer, folgt Sigma gleich ungefähr minus 0,192 pro Sekunde. Nach einer Sekunde beträgt die Amplitude noch etwa 82,6 Prozent ihres Anfangswerts. Rechts ist dieser einzelne Modellanteil dargestellt: waagerecht die Zeit seit Beginn des Analyseabschnitts, senkrecht sein Signalbeitrag in Tausendern der Dateieinheit. Die Anfangsphase bestimmt, wo die Kurve startet. Theta bestimmt ihren Fortschritt. Wie viele solcher Anteile das Modell zulässt, regelt die Modellordnung.

## Folie 11: Modellordnung

**Zeigehinweis:** Bei Ordnung 12 auf die erste Tabellenzeile zeigen und vier Paare mal zwei plus vier reelle Anteile abzählen.

Die Modellordnung ist eine Vorgabe dafür, wie viele exponentielle Anteile zur Beschreibung des Signals zur Verfügung stehen. Ordnung zwölf bedeutet deshalb weder zwölf Hertz noch automatisch zwölf Schwingungen.

Eine reelle Schwingung entsteht mathematisch aus zwei zusammengehörenden komplexen Polen. Diese nennt man ein konjugiertes Polpaar. In der ersten Tabellenzeile sehen wir bei Ordnung zwölf vier solche Paare und vier reelle Anteile. Vier mal zwei plus vier ergibt zwölf. Die reellen Anteile beschreiben Verläufe ohne periodisches Hin und Her. Beim später betrachteten ROMA-Datensatz verteilt sich dieselbe Ordnung anders: fünf Paare und zwei reelle Anteile. Der separat berücksichtigte Mittelwert zählt dabei nicht mit.

Eine höhere Ordnung gibt dem Modell mehr Möglichkeiten, die Messkurve nachzubilden. Damit kann aber auch Rauschen oder eine nur im gewählten Zeitfenster auftretende Besonderheit angepasst werden. Die kleinste Abweichung allein entscheidet deshalb nicht über die beste Ordnung. Entscheidend ist auch, ob Frequenzen und Dämpfungen bei leicht veränderten Einstellungen ähnlich bleiben. Zunächst betrachten wir, wie das Programm die Rekonstruktion und einen möglichen Filterabzug bewertet.

## Folie 12: Rekonstruktion und Filterentscheidung

**Zeigehinweis:** Den Zähler als Modellabweichung und den Nenner als Schwankung um den Mittelwert erläutern; danach zur Filterausgabe unten wechseln.

Hier sind zwei Rechenschritte zu unterscheiden. Für die Rekonstruktion werden alle geschätzten Anteile und der Grundwert zusammengesetzt. Diese Modellkurve wird dann mit der Messung verglichen. Erst danach wird entschieden, welche einzelnen Anteile entfernt werden dürfen.

In der Formel ist x die Messung und x mit Dach die Modellkurve. Im Zähler steht ihre Abweichung über sämtliche betrachteten Zeitpunkte. Dazu werden die Differenzen quadriert, addiert und anschließend wird die Wurzel gezogen. Der Nenner macht genau dasselbe mit der Messung nach Abzug ihres Mittelwerts. Dadurch wird die Modellabweichung an der Größe der gemessenen Schwankung gemessen. Es werden also Signalwerte verglichen, keine Frequenzdifferenzen.

Im Programm muss dieser relative Fehler höchstens zehn Prozent betragen. Diese Zahl ist eine heuristische Prüfgrenze. Eine wissenschaftliche Kalibrierung ist nicht dokumentiert. Für unsere Leistungsmessungen muss der ausgewählte Anteil im Zielband von 1,76 bis 2,64 Hertz liegen und darf nicht wachsen. Die relative Dämpfung berücksichtigt sowohl das Abklingen als auch die Schwingungsfrequenz. Zugelassen sind Werte bis 0,3. Auch die Norm des gesamten Abzugs ist begrenzt: auf das 1,25-Fache der Norm der mittelwertbereinigten Messung.

Wenn die Prüfungen bestanden sind, entsteht die Filterausgabe durch Messung minus ausgewählte Modellanteile. Das ist eine rechnerische Freigabe, noch kein unabhängiger Nachweis der physikalischen Richtigkeit. Mit einer bekannten Sollkurve lässt sich der Ablauf gezielt überprüfen.

## Folie 13: Prüfung mit einer bekannten Sollkurve

**Zeigehinweis:** Zunächst die bekannte Filteraufgabe erläutern, dann auf die blaue Filterausgabe und die orange gestrichelte Sollkurve zeigen.

Wie lässt sich prüfen, ob der Filter tatsächlich den gewünschten Anteil entfernt? Dafür braucht man ein Beispiel, bei dem die Bestandteile vorher bekannt sind. Dieses künstlich erzeugte Signal enthält einen Grundwertsprung und zwei Schwingungen: eine bei 2,24 Hertz und eine bei fünf Hertz. Entfernt werden soll nur die erste. Die Sollkurve ist das erwartete Signal nach dieser Entfernung. Sie enthält also weiterhin den Grundwert und die Fünf-Hertz-Schwingung.

Das Diagramm zeigt die Zeit in Sekunden und den Signalwert in willkürlichen Einheiten. Grau ist das Eingangssignal. Blau ist die berechnete Filterausgabe, orange gestrichelt die bekannte Sollkurve. Die beiden letzten Kurven liegen praktisch übereinander. Ihre verbleibenden Wellen sind erwünscht: Der Fünf-Hertz-Anteil soll erhalten bleiben.

Über alle 1.200 Werte bleibt die größte Abweichung zur Sollkurve unter drei mal zehn hoch minus dreizehn. Der vollständige Rechenablauf funktioniert damit für dieses rauschfreie Beispiel sehr genau. Die nächste Prüfung vergleicht die geschätzten Modellwerte mit unabhängig veröffentlichten Vergleichswerten.

## Folie 14: NIST: Vergleich mit bekannten Modellwerten

**Zeigehinweis:** Erst die Definition der Referenzparameter nennen; danach die orangefarbenen Datenpunkte mit der blauen Modellkurve vergleichen.

Hier wird geprüft, ob Matrix Pencil die Werte eines bekannten Modells wiederfindet. Diese veröffentlichten Vergleichswerte heißen Referenzparameter. Ein Parameter ist dabei eine Zahl, die einen Bestandteil des Modells festlegt. In diesem Beispiel sind das die Anfangsgewichte und die Abklingraten von drei Exponentialanteilen.

Der Datensatz Lanczos1 stammt vom amerikanischen Normungsinstitut NIST. Er enthält 24 künstlich erzeugte Werte. Die drei zugrunde liegenden Anteile klingen nur ab. Sie pendeln nicht. Als Abklingraten sind eins, drei und fünf pro x-Einheit angegeben. In einer Schreibweise mit negativem Exponenten stehen entsprechend minus eins, minus drei und minus fünf im Exponenten vor x. Das sind keine Schwingungsfrequenzen.

Die orangefarbenen Punkte zeigen die NIST-Daten, die blaue Linie das angepasste Modell. Für die Achsen sind keine physikalischen Einheiten angegeben. Die geschätzten Anfangsgewichte und Abklingraten stimmen innerhalb der festgelegten Prüftoleranz mit den bekannten Werten überein. Anders als beim späteren Mexiko-Vergleich sind diese Referenzwerte Bestandteile eines bekannten künstlichen Modells, keine Vergleichsschätzungen aus einer Messung. Nach diesen kontrollierten Prüfungen folgen die Leistungsmessungen.

## Folie 15: Schwingungsparameter der Sprungantworten

**Zeigehinweis:** Die beiden Datenspalten zeilenweise vergleichen: zuerst Frequenz, dann Abklingen, Modellfehler und Zahl der entfernten Paare.

Die Tabelle fasst unsere Auswertung der beiden bereitgestellten Leistungsmessungen zusammen. Sie enthalten die Antworten auf einen positiven und einen negativen Frequenzsprung. Positiv und negativ bezeichnen die Richtung des Frequenzsprungs um 50 Hertz. Analysiert wird jeweils das Leistungssignal P pos, mit Ordnung zwölf von einer bis sieben Sekunden.

In beiden Leistungssignalen liegt die dominante geschätzte Schwingung bei ungefähr 2,268 Hertz. Diese Pendelfrequenz ist von der elektrischen Netzfrequenz zu unterscheiden. Die Dämpfung ist beim negativen Sprung stärker negativ. Der geschätzte Anteil klingt dort deshalb schneller ab.

Die Fehler von 0,763 und 0,594 Prozent gelten für die Rekonstruktion dieser Leistungsmessungen im Schätzraster mit 100 Werten pro Sekunde. Sie gehören nicht zum späteren Mexiko-Beispiel. Beide Filterungen werden zugelassen: negativ ein Schwingungspaar, positiv zwei. Der zweite positive Anteil liegt bei etwa 2,480 Hertz ebenfalls im Zielband. Eine ähnlich kleine Gesamtabweichung bedeutet also nicht dieselbe Zerlegung. Als Nächstes sehen wir den Abzug in den Leistungskurven.

## Folie 16: Filterung der negativen Sprungantwort

**Zeigehinweis:** Links den vollständigen Verlauf einordnen, rechts im vergrößerten Ausschnitt Messung und Filterausgabe vergleichen.

Diese Folie zeigt die negative Frequenzsprungantwort. Blau ist die Messung, Orange die Filterausgabe. Links sehen wir den gesamten Verlauf. Rechts ist der Zeitraum von vier bis sieben Sekunden vergrößert. In beiden Diagrammen steht auf der waagerechten Achse die Zeit in Sekunden. Die senkrechte Achse zeigt den Kanal P pos, geteilt durch eine Million. Da die physikalische Einheit in der Datei nicht dokumentiert ist, wird hier bewusst nur die Dateieinheit genannt.

Entfernt wird der geschätzte Schwingungsanteil bei ungefähr 2,268 Hertz. Das Programm zieht diesen Anteil punktweise von der ursprünglichen Messung ab. Im rechten Ausschnitt wird die Verringerung der Pendelung gut sichtbar. Der große Übergang im linken Diagramm würde diesen Unterschied optisch verdecken.

Vor einer Sekunde bleiben sämtliche Werte unverändert. Nach dem Analysebeginn ist die Differenz zwischen Messung und Ausgabe genau der berechnete Abzugsanteil. Eine unabhängig bekannte bereinigte Sollkurve fehlt hier allerdings. Die Darstellung belegt daher den rechnerischen Eingriff, aber keine vollständig abgesicherte physikalische Bereinigung. Die positive Sprungantwort zeigt eine etwas andere Zerlegung.

## Folie 17: Filterung der positiven Sprungantwort

**Zeigehinweis:** Im rechten Ausschnitt auf die verbleibende orange Kurve zeigen und betonen, dass zwei Modellanteile abgezogen wurden.

Auch hier ist die Messung blau und die Filterausgabe orange dargestellt. Links steht der vollständige Verlauf, rechts der Ausschnitt von vier bis sieben Sekunden. Die Zeitachse ist in Sekunden angegeben. Die Werte des Kanals P pos sind wieder durch eine Million geteilt und tragen die nicht näher dokumentierte Dateieinheit.

Beim positiven Frequenzsprung werden zwei Schwingungsanteile abgezogen: der dominante Anteil bei ungefähr 2,268 Hertz und ein weiterer bei ungefähr 2,480 Hertz. Der zweite Anteil klingt deutlich schneller ab. Die orange Kurve entsteht deshalb aus der Messung minus der Summe beider Anteile. Sie zeigt nicht nur die Entfernung einer einzigen Frequenz.

Wie zuvor bleiben die Werte vor einer Sekunde erhalten. Das Gesamtmodell passt in dieser Einstellung mit weniger als einem Prozent Fehler gut zur Messkurve. Daraus folgt aber noch nicht, dass beide geschätzten Anteile eindeutig reale Vorgänge beschreiben. Die nächsten Folien betrachten einen externen Vergleichsfall. Dafür ist zunächst wichtig, seine Messgröße von unseren Leistungsmessungen zu unterscheiden.

## Folie 18: Leistungsmessungen und Mexiko im Vergleich

**Zeigehinweis:** Zuerst links die Projektdateien mit dem Leistungssignal einordnen, dann rechts den externen Mexiko-Fall mit der Netzfrequenz gegenüberstellen.

Bevor wir zum Mexiko-Beispiel wechseln, trenne ich die beiden Datengrundlagen. Links stehen die bereitgestellten Projektdateien. Dort wurde der Kanal P pos nach einem positiven beziehungsweise negativen Frequenzsprung ausgewertet. Der zusätzlich aufgezeichnete Frequenzkanal liegt im Bereich von 50 Hertz. Die ungefähr 2,268 Hertz beschreiben hingegen die Pendelung im Leistungssignal. Für P pos ist keine physikalische Einheit belegt. Das Ziel war, diese Pendelung zu bestimmen und den ausgewählten Modellanteil abzuziehen.

Rechts steht ein externer, veröffentlichter FNET-Datensatz aus Mexiko. Hier ist die ausgewertete Messgröße die Netzfrequenz selbst. Sie liegt um 60 Hertz und zeigt darüber langsame zeitliche Schwankungen. Gesucht werden die Schwingungsanteile dieser Frequenzabweichung. Diese können mit den veröffentlichten ROMA-Ergebnissen verglichen werden.

Die gemeinsame Grundlage ist die Matrix-Pencil-Methode. Messgröße, Ereignis und Referenzlage unterscheiden sich jedoch. Die ermittelten Frequenzen und Modellfehler lassen sich deshalb nicht unmittelbar von einem Fall auf den anderen übertragen. Als Nächstes betrachten wir den Verlauf der Netzfrequenz in Mexiko.

## Folie 19: Mexiko: aufgezeichnete Netzfrequenz

**Zeigehinweis:** Den Wechsel zum externen Referenzfall ausdrücklich ankündigen, danach die beiden Diagrammachsen zeigen.

Damit ist die Auswertung unserer beiden Leistungsmessungen abgeschlossen. Jetzt wechseln wir zu einem externen Referenzdatensatz aus Mexiko. Die bisherigen Dateien enthalten den Leistungskanal P pos und den Netzfrequenzkanal f. Analysiert haben wir dort die Leistung P pos. Hier ist die untersuchte Messgröße dagegen die Netzfrequenz selbst, angegeben in Hertz.

Die veröffentlichte Aufzeichnung gehört zu einem Netzereignis vom 28. Dezember 2020. Der Messkanal wird Mazatlán zugeordnet. Wir haben diese Messung nicht selbst durchgeführt. Der Zweck ihrer Auswertung ist der Vergleich mit den veröffentlichten ROMA-Ergebnissen.

Links sehen wir 301 Netzfrequenzwerte über 30 Sekunden, mit jeweils einer Zehntelsekunde Abstand. Waagerecht steht die Zeit, senkrecht die Netzfrequenz nahe 60 Hertz. Eine erkannte Mode von etwa 0,317 Hertz beschreibt die langsame Schwankung dieser Netzfrequenz. Sie ist also von der elektrischen Grundfrequenz um 60 Hertz zu unterscheiden. Die Ausschläge werden insgesamt kleiner. An dieser veröffentlichten Zeitreihe untersuchen wir nun, ob unsere Schwingungsparameter zu den Angaben der Autoren passen.

## Folie 20: Mexiko: Vergleich mit veröffentlichten Schätzwerten

**Zeigehinweis:** Zuerst den Zweck des Vergleichs erklären, dann die Frequenzspalten der ersten Zeile und rechts die Abklingraten zeigen.

Zunächst prüfen wir, ob unsere Methode zu ähnlichen Schwingungsparametern kommt wie eine bereits veröffentlichte Auswertung derselben mexikanischen Zeitreihe. Dafür verwenden wir die Angaben anderer Autoren im ROMA-Handbuch. Diese Vergleichswerte heißen hier Referenzparameter: Gemeint sind die Frequenz und die Abklingrate einer Schwingung. Die Autoren haben sie mit der ERA-Methode geschätzt. Wir verwenden Matrix Pencil mit Ordnung zwölf.

In der Tabelle steht links die veröffentlichte Frequenz und daneben unser Ergebnis. Die erste Zeile nennt 0,317 Hertz bei den Autoren und ungefähr 0,316823 Hertz bei Matrix Pencil. Die nächste Spalte zeigt die relative Differenz: rund 0,056 Prozent. Auch die beiden anderen Frequenzdifferenzen liegen unter 0,06 Prozent. Rechts werden die Abklingraten Sigma verglichen. Negative Werte bedeuten, dass die Schwingung mit der Zeit kleiner wird.

Die Übereinstimmung spricht dafür, dass beide Verfahren ähnliche Schwingungsanteile erkennen. Die gerundeten Autorenwerte sind jedoch Schätzungen und keine bekannten physikalischen Wahrheitswerte. Auf der nächsten Folie folgt eine andere Prüfung: Wie gut bildet die Summe aller Modellanteile die gesamte Messkurve nach?

## Folie 21: Mexiko: Rekonstruktion und Restabweichung

**Zeigehinweis:** Oben die blaue und orange Kurve vergleichen; um 240 bis 243 Sekunden nach unten zur Restkurve zeigen.

Oben sehen wir den Vergleich zwischen mexikanischer Netzfrequenzmessung und Rekonstruktion. Blau ist die gemessene Schwankung, Orange die Summe aller geschätzten Modellanteile. Zur besseren Darstellung wurde der Mittelwert von ungefähr 59,773 Hertz abgezogen. Die senkrechte Achse zeigt deshalb Abweichungen in Millihertz. Ein Millihertz ist ein Tausendstel Hertz.

Über große Bereiche liegen beide Kurven dicht zusammen. Zwischen ungefähr 240 und 243 Sekunden treten jedoch schnelle Änderungen auf, die das Modell sichtbar schlechter nachbildet. Unten ist der verbleibende Rest dargestellt: Für jeden Zeitpunkt wurde der Modellwert vom Messwert abgezogen. Eine perfekte Rekonstruktion würde dort durchgehend null ergeben.

Der auffällige Abschnitt trägt etwa 55 Prozent zur gesamten Fehlerquadratsumme bei. Damit wissen wir, wo ein großer Teil des Fehlers entsteht. Seine Ursache bleibt offen. Zusätzliche Dynamik, Messartefakte oder Grenzen des Modells sind mögliche Erklärungen, aber hier nicht nachgewiesen. Die orange Kurve ist zunächst unsere Rekonstruktion. Ob tatsächlich ein Anteil aus der Messung entfernt wird, entscheidet erst die anschließende Filterprüfung.

## Folie 22: Mexiko: Modellfehler von 17,05 %

**Zeigehinweis:** Erst die beiden Tabellenwerte, dann die Division darunter zeigen; dabei auf den Vergleich gleicher Zeitpunkte verweisen.

Die 17,05 Prozent beschreiben ausschließlich diesen mexikanischen Referenzfall. Sie fassen die Abweichung zwischen gemessener Netzfrequenz und Modellkurve in einer Zahl zusammen. Dafür vergleichen wir die Signalwerte an genau denselben 301 Zeitpunkten. An jedem Zeitpunkt bilden wir Messwert minus Modellwert. Diese Differenzen werden quadriert, gemittelt und anschließend wird die Wurzel gezogen. Das ist der RMSE, also die Wurzel aus dem mittleren Fehlerquadrat.

In der ersten Tabellenzeile steht das Ergebnis: Die typische Größe der Modellabweichung beträgt nach diesem Maß etwa 5,565 Millihertz. Um diesen Wert einordnen zu können, brauchen wir eine Bezugsgröße. Dafür verwenden wir die gemessene Schwankung nach Abzug ihres Mittelwerts. Ihr quadratischer Mittelwert mit anschließender Wurzel, kurz RMS, beträgt etwa 32,646 Millihertz.

Unten teilen wir 5,565 durch 32,646 und multiplizieren mit hundert. Daraus entstehen die 17,05 Prozent. Bezogen wird der Fehler also auf die Stärke der gemessenen Schwankung. Die Netzfrequenz von ungefähr 60 Hertz ist hier keine Bezugsgröße. Auch werden für diese Rechnung keine erkannten Modenfrequenzen voneinander abgezogen. Deshalb können die Frequenzen in der vorherigen Tabelle sehr gut übereinstimmen, während das gesamte Signalmodell noch einen deutlichen Fehler hat.

## Folie 23: Mexiko: Filterentscheidung bei Ordnung 12

**Zeigehinweis:** Die drei Tabellenzeilen nacheinander durchgehen und anschließend die Gleichheit von Filterausgabe und Eingangssignal betonen.

Jetzt folgt die Filterentscheidung für die mexikanische Netzfrequenzmessung bei Ordnung zwölf. Die erste Tabellenzeile prüft die Frequenz. Die erkannte Mode bei ungefähr 0,316823 Hertz liegt im gewünschten Zielband. Diese Bedingung ist erfüllt.

Die zweite Zeile prüft die Qualität des gesamten Modells. Im Programm ist dafür eine Grenze von zehn Prozent eingestellt. Unser Fehler beträgt 17,05 Prozent und überschreitet diese Grenze. Deshalb blockiert der Code den Abzug. Die Ausgabe des Filters ist in diesem Fall exakt das ursprüngliche Eingangssignal. Diese Blockierung betrifft den ROMA-Fall. Bei unseren beiden Leistungsmessungen wird mit der Standardkonfiguration tatsächlich gefiltert.

Die zehn Prozent sind eine heuristische Schutzregel des Prototyps. Sie sollen den Abzug bei unzureichender Rekonstruktion verhindern. Die Zahl stammt weder aus der ROMA-Veröffentlichung noch aus einem allgemeinen physikalischen Gesetz. Ihre geeignete Wahl müsste anhand weiterer Versuche begründet werden. Damit stellt sich die nächste Frage: Verbessert eine höhere Modellordnung die Rekonstruktion ausreichend, und bleiben dabei die einzelnen Schwingungsparameter plausibel?

## Folie 24: Mexiko: Einfluss der Modellordnung

**Zeigehinweis:** Links den Fehlerverlauf und die Zehn-Prozent-Linie zeigen; anschließend rechts die drei Amplituden vergleichen.

Auch diese Ordnungsstudie betrifft die mexikanische Netzfrequenzmessung. Links steht waagerecht die Modellordnung und senkrecht der relative Anpassungsfehler. Mit zunehmender Ordnung stehen mehr Exponentialanteile zur Verfügung. In diesem Beispiel kann sich die Modellkurve dadurch immer genauer an die Messwerte anpassen.

Bei Ordnung zwölf beträgt der Fehler 17,05 Prozent, bei Ordnung vierundzwanzig 12,83 Prozent und bei Ordnung sechsunddreißig 8,76 Prozent. Der letzte Wert liegt unter der gestrichelten Zehn-Prozent-Linie. Die Fehlerbedingung des Filters wäre damit erfüllt.

Rechts sehen wir jedoch, weshalb der Kurvenfehler allein nicht ausreicht. Für die Mode nahe 0,72 Hertz nennen die Autoren eine Amplitude von ungefähr 0,004 Hertz. Ordnung zwölf liefert etwa 0,0045 Hertz. Bei Ordnung sechsunddreißig steigt der Wert auf ungefähr 0,0213 Hertz. Obwohl die Gesamtkurve besser passt, verändert sich also die Zerlegung in einzelne Anteile deutlich. Mehr Modellanteile garantieren deshalb keine bessere physikalische Beschreibung. Zusätzlich betrachten wir nun, wie sich die Modelle an Messpunkten verhalten, die beim Anpassen ausgelassen wurden.

## Folie 25: Mexiko: Prüfung an ausgelassenen Messpunkten

**Zeigehinweis:** Blau als verwendete Punkte und Orange als ausgelassene Zwischenpunkte erklären; dann Ordnung 36 und 72 vergleichen.

Für diese Prüfung der mexikanischen Zeitreihe wird zunächst nur jeder zweite Messwert verwendet. Aus diesen 151 Punkten werden die Modelle geschätzt. Die 150 dazwischenliegenden Werte bleiben bei der Anpassung unbenutzt. Anschließend prüfen wir, wie gut das jeweilige Modell auch diese Zwischenpunkte trifft.

Die blaue Linie zeigt den Fehler auf den verwendeten Punkten. Er sinkt mit steigender Ordnung stark ab. Orange zeigt den Fehler auf den ausgelassenen Zwischenpunkten. Bei Ordnung sechsunddreißig liegen die beiden Fehler bei etwa 4,72 und 10,13 Prozent. Bei Ordnung zweiundsiebzig verbessert sich der blaue Wert auf etwa 0,36 Prozent. Der orange Wert steigt jedoch auf ungefähr 13,99 Prozent. Das ist ein Hinweis auf Überanpassung: Die zusätzlichen Modellanteile helfen zunehmend vor allem bei den bereits verwendeten Punkten.

Diese Prüfung bleibt innerhalb derselben Aufzeichnung. Benachbarte Messwerte hängen häufig zusammen. Eine unabhängige Validierung ist das daher nicht. Für die Ordnungswahl betrachten wir gemeinsam den Kurvenfehler und die Stabilität der Schwingungsparameter. Eine weitere, unabhängig dokumentierte Messung wäre ein stärkerer Nachweis.

## Folie 26: Diskussion und Schlussfolgerungen

**Zeigehinweis:** Linke Spalte mit den Leistungsmessungen und rechte Spalte mit Mexiko getrennt vortragen; danach die Aussage zur Filterfreigabe betonen.

Die Schlussfolgerungen lassen sich anhand der beiden Datengruppen zusammenfassen. Links stehen unsere Projektmessungen. Untersucht wurde der Leistungskanal P pos nach einem positiven beziehungsweise negativen Frequenzsprung. Mit der verwendeten Einstellung werden beide Sprungantworten tatsächlich gefiltert. Die betrachtete Leistungspendelung liegt bei ungefähr 2,268 Hertz. Der relative Modellfehler beträgt rund 0,763 Prozent beim positiven und 0,594 Prozent beim negativen Sprung.

Rechts steht der externe Referenzfall aus Mexiko. Hier wird die Netzfrequenz untersucht. Die ausgewählten Schwingungsfrequenzen stimmen gut mit den veröffentlichten ROMA-Werten überein. Gleichzeitig beträgt der Fehler des Gesamtmodells bei Ordnung zwölf 17,05 Prozent. Damit überschreitet er die eingestellte Schutzgrenze, und der Filterabzug bleibt blockiert.

Daraus folgt: Frequenzübereinstimmung und Filterfreigabe sind getrennt zu bewerten. Eine gut erkannte Frequenz allein bestätigt noch keine ausreichende Rekonstruktion. Auch eine ausgeführte Filterung beweist noch keine physikalisch korrekte Bereinigung. Für die realen Messungen fehlt eine unabhängig bekannte, saubere Referenzkurve. Diese Grenze muss bei der Bewertung der Ergebnisse berücksichtigt werden.

## Quellen und Datengrundlage

- Projektmessungen: `data/Frequenz_Leistungs_Pendelung.XLS` und `data/Frequenz_Leistungs_Pendelung_negativer_Sprung.XLS`.
- Projektcode und Messdaten: [Stand 9d54cc7](https://github.com/relaytoroot/prony_matrix_pencil_filter/tree/9d54cc7c45fbe1613cebd26e4ccbb65d9c3c774f).
- [NIST Lanczos1](https://www.itl.nist.gov/div898/strd/nls/data/lanczos1.shtml).
- [ROMA User Guide](https://github.com/wamsmx/cict/blob/0c397eb5f139bd765179f70868c04ce460343229/User_guides/ROMA/ROMA%20-%20User%20guide.pdf), Tabelle 2.1, Kanal med_1422.

Die Notizen der PowerPoint-Datei enthalten ergänzende fachliche Erläuterungen und Quellen zu den einzelnen Folien.
