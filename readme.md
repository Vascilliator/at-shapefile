# Austrian Shapefile

## Description

This repository aims to create and manipulate Austrian shapefile into multiple levels, such as state level (first-level administrative divisions of Austria), municipality level (third-level administrative divisions of Austria) and postal code level. The code was written in both Python and R; both codes are analogous.

## Output

Austrian shapefile - municipality level (third-level administrative divisions of Austria)

<p align="center">
<img src="./media/shapefile_austria_municipality.png" alt="Shapefile Austria" width=650>
</p>

Austrian shapefile - postal code level

<p align="center">
<img src="./media/shapefile_austria_postal_code.png" alt="Shapefile Austria" width=650>
</p>

## Usage

### Python dependencies

```.ps1
python -m pip install -r requirements.txt
```

### R dependencies

```.r
install.packages(c("readxl", "sf", "tidyverse"))
```


### Grafische Bedienung (Frontend)

Das Repository enthält eine schlanke Start-App auf oberster Ebene (`at-shapefile.py`). Die eigentliche GUI- und Backend-Logik liegt im Unterverzeichnis `subapps/`, damit Startpunkt, grafische Oberfläche und Verarbeitung getrennt bleiben.

1. Installieren Sie zuerst die Python-Abhängigkeiten wie oben beschrieben. Starten Sie die grafische Oberfläche anschließend aus dem Repository-Verzeichnis mit:

   ```.ps1
   python at-shapefile.py
   ```

2. Optional können Sie den Standard-Export ohne GUI ausführen. Dieser normale Export bleibt detailgetreu und wird nicht vereinfacht:

   ```.ps1
   python at-shapefile.py --cli
   ```

   Zusätzlich kann ein separater, vereinfachter Export für Qlik erzeugt werden. Der detailgetreue Standard-Export wird dabei weiterhin unverändert geschrieben; die Vereinfachung gilt nur für die Datei unter `--simplified-export-path`. Empfohlene Startwerte sind `--simplify-tolerance 50` für eine moderate Vereinfachung, `--simplify-tolerance 100` für eine stärkere Dateigrößenreduktion und `--coordinate-precision 6` für WGS84-GeoJSON-Ausgaben. Prüfen Sie die visuelle Qualität der vereinfachten Datei anschließend stichprobenartig in Qlik.

   ```.ps1
   python at-shapefile.py --cli `
     --export-path output/at_postal_codes.geojson `
     --simplified-export-path output/at_postal_codes.qlik.geojson `
     --simplify-tolerance 50 `
     --coordinate-precision 6
   ```

3. Tragen Sie die Download-Adresse der Statistik-Austria-Gemeindegeometrien im Feld **Download-URL Gemeindegeometrien** ein. Das Feld ist mit der im Backend hinterlegten URL vorbelegt, kann aber überschrieben werden.

4. Geben Sie den passenden Shapefile-Layer im Feld **Layer-Name Gemeindegeometrien** an, falls die heruntergeladene ZIP-Datei einen anderen Layer-Namen verwendet. Der Layer-Name muss zum Namen der `.shp`-Datei im entpackten Statistik-Austria-Archiv passen, z. B. `STATISTIK_AUSTRIA_GEM_20230101` für das bisherige Archiv.

5. Wählen Sie unter **Exportformat** das gewünschte Ausgabeformat. Unterstützt werden:
   - **GeoJSON (`.geojson`)**
   - **CSV mit WKT-Geometrie (`.csv`)**

6. Für **Qlik Geo Tools** wird der Export als **CSV mit WKT-Geometrie** empfohlen, da die Geometriespalte als WKT-Text weiterverarbeitet werden kann.

7. Wenn zusätzlich eine kleinere Datei für Qlik benötigt wird, aktivieren Sie **Zusätzlichen vereinfachten Qlik-Export erzeugen**. Wählen Sie anschließend unter **Vereinfachter Exportpfad** eine separate Zieldatei, damit der normale detailgetreue Export erhalten bleibt. Tragen Sie als Startwert bei **Vereinfachungstoleranz (Meter)** `50` für eine moderate Vereinfachung oder `100` für eine stärkere Dateigrößenreduktion ein. Für GeoJSON-Ausgaben in WGS84 ist bei **Koordinatenpräzision** der Wert `6` empfohlen. Prüfen Sie die visuelle Qualität der vereinfachten Qlik-Datei nach dem Export stichprobenartig in Qlik.

8. Beispiel für eine Statistik-Austria-Gemeindegeometrie-URL:

   ```.text
   https://data.statistik.gv.at/data/OGDEXT_GEM_1_STATISTIK_AUSTRIA_20230101.zip
   ```

9. Hinweis: Die bisher fest hinterlegte URL `OGDEXT_GEM_1_STATISTIK_AUSTRIA_20230101.zip` kann veraltet sein. Prüfen Sie auf der Statistik-Austria-Seite, ob eine aktuellere Gemeindegeometrie verfügbar ist, und ersetzen Sie die URL im Frontend bei Bedarf durch die aktuelle Download-URL.

## See also

[Statistik Austria - Regionale Gliederungen](https://www.statistik.at/services/tools/services/regionales/regionale-gliederungen/)

[Statistik Austria - Division of Austria into Municipalities (Shapefile)](https://data.statistik.gv.at/web/meta.jsp?dataset=OGDEXT_GEM_1)
