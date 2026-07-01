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
python -m pip install geopandas matplotlib numpy pandas requests xlrd
```

### R dependencies

```.r
install.packages(c("readxl", "sf", "tidyverse"))
```


### Grafische Bedienung (Frontend)

Das Repository enthält zusätzlich ein Tkinter-Frontend, mit dem die PLZ-Flächen ohne direkte Anpassung des Python-Skripts erzeugt und exportiert werden können.

1. Installieren Sie zuerst die Python-Abhängigkeiten wie oben beschrieben. Starten Sie die grafische Oberfläche anschließend aus dem Repository-Verzeichnis mit:

   ```.ps1
   python frontend.py
   ```

2. Tragen Sie die Download-Adresse der Statistik-Austria-Gemeindegeometrien im Feld **Download-URL Gemeindegeometrien** ein. Das Feld ist mit der im Backend hinterlegten URL vorbelegt, kann aber überschrieben werden.

3. Geben Sie den passenden Shapefile-Layer im Feld **Layer-Name Gemeindegeometrien** an, falls die heruntergeladene ZIP-Datei einen anderen Layer-Namen verwendet. Der Layer-Name muss zum Namen der `.shp`-Datei im entpackten Statistik-Austria-Archiv passen, z. B. `STATISTIK_AUSTRIA_GEM_20230101` für das bisherige Archiv.

4. Wählen Sie unter **Exportformat** das gewünschte Ausgabeformat. Unterstützt werden:
   - **GeoJSON (`.geojson`)**
   - **CSV mit WKT-Geometrie (`.csv`)**

5. Für **Qlik Geo Tools** wird der Export als **CSV mit WKT-Geometrie** empfohlen, da die Geometriespalte als WKT-Text weiterverarbeitet werden kann.

6. Beispiel für eine Statistik-Austria-Gemeindegeometrie-URL:

   ```.text
   https://data.statistik.gv.at/data/OGDEXT_GEM_1_STATISTIK_AUSTRIA_20230101.zip
   ```

7. Hinweis: Die bisher fest hinterlegte URL `OGDEXT_GEM_1_STATISTIK_AUSTRIA_20230101.zip` kann veraltet sein. Prüfen Sie auf der Statistik-Austria-Seite, ob eine aktuellere Gemeindegeometrie verfügbar ist, und ersetzen Sie die URL im Frontend bei Bedarf durch die aktuelle Download-URL.

## See also

[Statistik Austria - Regionale Gliederungen](https://www.statistik.at/services/tools/services/regionales/regionale-gliederungen/)

[Statistik Austria - Division of Austria into Municipalities (Shapefile)](https://data.statistik.gv.at/web/meta.jsp?dataset=OGDEXT_GEM_1)
