## AT Shapefile
# Last update: 2026-01-21

"""Austrian shapefile creation and manipulation using GeoPandas."""

from io import BytesIO
from pathlib import Path
import re
from zipfile import ZIP_DEFLATED, ZipFile

import geopandas as gpd
from matplotlib import pyplot
import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).resolve().parent
SHAPEFILE_DATA_DIR = (
    PROJECT_ROOT / "data" / "raw" / "OGDEXT_GEM_1_STATISTIK_AUSTRIA_20230101"
)
POSTLEXIKON_URL = "https://www.post.at/g/c/postlexikon"
MUNICIPALITIES_URL = (
    "https://www.statistik.at/verzeichnis/reglisten/gemliste_knz_en.csv"
)
POLITICAL_DISTRICTS_URL = (
    "http://www.statistik.at/verzeichnis/reglisten/polbezirke_en.csv"
)
LOCALITIES_URL = "http://www.statistik.at/verzeichnis/reglisten/ortsliste.csv"
SHAPEFILE_ZIP_URL = (
    "https://data.statistik.gv.at/data/OGDEXT_GEM_1_STATISTIK_AUSTRIA_20230101.zip"
)
SHAPEFILE_LAYER = "STATISTIK_AUSTRIA_GEM_20230101"

AUSTRIAN_STATES_MAPPING = {
    "W": "Vienna",
    "N": "Lower Austria",
    "B": "Burgenland",
    "O": "Upper Austria",
    "Sa": "Salzburg",
    "T": "Tyrol",
    "V": "Vorarlberg",
    "St": "Styria",
}


def safe_extract(zip_file, target_dir):
    """Extract a zip archive while preventing path traversal."""
    target_dir = Path(target_dir).resolve()

    for member in zip_file.infolist():
        target_path = Path(target_dir, member.filename).resolve()
        if target_path != target_dir and target_dir not in target_path.parents:
            raise ValueError(
                f"Unsafe zip entry outside target directory: {member.filename}"
            )

    zip_file.extractall(path=target_dir)


def get_latest_postal_code_url():
    """Return the latest Post AG PLZ Verzeichnis XLSX URL."""
    page_source = requests.get(
        url=POSTLEXIKON_URL,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=5,
        verify=True,
    ).content.decode("utf-8")

    plz_verzeichnis = [
        line
        for line in page_source.split(sep="\n")
        if 'title="PLZ Verzeichnis"' in line
    ][0]
    return re.sub(
        pattern=r"^.*href=\"(.*\.xlsx)?.*$",
        repl=r"\1",
        string=plz_verzeichnis,
        flags=0,
    )


def load_postal_codes():
    """Download and normalize Austrian postal codes from Post AG."""
    plz_verzeichnis = get_latest_postal_code_url()

    return (
        pd.read_excel(
            io=BytesIO(
                initial_bytes=requests.get(
                    url=plz_verzeichnis,
                    headers={"User-Agent": "Mozilla"},
                    timeout=5,
                    verify=True,
                ).content,
            ),
            sheet_name=0,
            header=0,
            index_col=None,
            skiprows=0,
            skipfooter=0,
            dtype=None,
            engine="openpyxl",
        )
        .rename(columns={"PLZ": "postal_code", "Ort": "city", "Bundesland": "state"})
        .astype(dtype={"postal_code": "str"})
        .assign(country="AT")
        .query(expr='adressierbar == "Ja"')
        .filter(items=["country", "postal_code", "state", "city"])
        .assign(
            state=lambda row: row["state"].replace(
                to_replace=AUSTRIAN_STATES_MAPPING,
                regex=True,
            ),
        )
        .sort_values(by=["country", "postal_code"], ignore_index=True)
    )


def load_municipalities():
    """Download and normalize the Statistik Austria municipality list."""
    return (
        pd.read_csv(
            filepath_or_buffer=MUNICIPALITIES_URL,
            sep=";",
            header=0,
            index_col=None,
            skiprows=2,
            skipfooter=1,
            dtype=None,
            engine="python",
            encoding="utf-8",
            keep_default_na=True,
        )
        .rename(
            columns={
                "Municipality Name": "municipality",
                "Municipality Code": "municipality_code",
                "Postal Code of the Municipal": "postal_code",
            },
        )
        .astype(dtype={"municipality_code": "str", "postal_code": "str"})
        .filter(items=["municipality_code", "municipality", "postal_code"])
        .sort_values(by=["municipality_code"], ignore_index=True)
    )


def load_political_districts():
    """Download and normalize Austrian political districts."""
    return (
        pd.read_csv(
            filepath_or_buffer=POLITICAL_DISTRICTS_URL,
            sep=";",
            header=0,
            index_col=None,
            skiprows=2,
            skipfooter=1,
            dtype=None,
            engine="python",
            encoding="utf-8",
            keep_default_na=True,
        )
        .rename(
            columns={
                "Federal Province": "state",
                "Political District": "political_district",
                "Pol. District Code": "political_district_code",
            },
        )
        .astype(dtype={"political_district_code": "str"})
        .filter(items=["political_district_code", "political_district", "state"])
        .sort_values(by=["political_district_code"], ignore_index=True)
    )


def load_localities(political_districts):
    """Download localities and join them with political districts."""
    return (
        pd.read_csv(
            filepath_or_buffer=LOCALITIES_URL,
            sep=";",
            header=0,
            index_col=None,
            skiprows=2,
            skipfooter=1,
            dtype=None,
            engine="python",
            encoding="utf-8",
            keep_default_na=True,
        )
        .rename(
            columns={
                "Gemeindekennziffer": "gemeindekennziffer",
                "Gemeindename": "municipality",
                "Ortschaftsname": "city",
                "Postleitzahl": "postal_code",
            },
        )
        .astype(dtype={"gemeindekennziffer": "str", "postal_code": "str"})
        .assign(
            political_district_code=lambda row: row["gemeindekennziffer"].str.slice(
                start=0,
                stop=3,
            ),
        )
        .assign(
            postal_code=lambda row: row["postal_code"].str.split(pat=" ", expand=False)
        )
        .explode(column=["postal_code"])
        .filter(items=["political_district_code", "postal_code"])
        .drop_duplicates(subset=None, keep="first", ignore_index=True)
        .merge(
            right=political_districts,
            how="left",
            on=["political_district_code"],
            indicator=False,
        )
        .filter(
            items=[
                "state",
                "political_district_code",
                "political_district",
                "postal_code",
            ]
        )
        .sort_values(by=["political_district_code", "postal_code"], ignore_index=True)
    )


def download_shapefile(target_dir=SHAPEFILE_DATA_DIR, url=SHAPEFILE_ZIP_URL):
    """Download and extract the Statistik Austria municipality shapefile."""
    with ZipFile(
        file=BytesIO(
            initial_bytes=requests.get(
                url=url,
                headers=None,
                timeout=5,
                verify=True,
            ).content,
        ),
        mode="r",
        compression=ZIP_DEFLATED,
    ) as zip_file:
        target_dir.mkdir(parents=True, exist_ok=True)
        safe_extract(zip_file=zip_file, target_dir=target_dir)


def load_shapefile(
    municipalities,
    postal_codes,
    shapefile_dir=SHAPEFILE_DATA_DIR,
    shapefile_layer=SHAPEFILE_LAYER,
):
    """Load the extracted shapefile and join municipality and postal code data."""
    return (
        gpd.read_file(
            filename=shapefile_dir / f"{shapefile_layer}.shp",
            layer=shapefile_layer,
            include_fields=["g_id", "g_name", "geometry"],
            driver=None,
            encoding="utf-8",
        )
        .rename(columns={"g_id": "municipality_code", "g_name": "municipality"})
        .astype(dtype={"municipality_code": "str"})
        .merge(
            right=municipalities.filter(items=["municipality_code", "postal_code"]),
            how="left",
            on=["municipality_code"],
            indicator=False,
        )
        .merge(right=postal_codes, how="left", on=["postal_code"], indicator=False)
        .filter(
            items=[
                "country",
                "state",
                "municipality_code",
                "municipality",
                "city",
                "postal_code",
                "geometry",
            ],
        )
        .sort_values(by=["country", "postal_code"], ignore_index=True)
    )


def plot_shapefile_levels(at_shapefile):
    """Plot Austrian shapefile dissolves at state, municipality, and postal-code levels."""
    (
        at_shapefile.filter(items=["state", "geometry"])
        .dissolve(by="state", as_index=False, sort=True, dropna=True)
        .plot()
    )
    pyplot.show()

    (
        at_shapefile.filter(items=["state", "municipality", "geometry"])
        .dissolve(by="municipality", as_index=False, sort=True, dropna=True)
        .plot()
    )
    pyplot.show()

    (
        at_shapefile.filter(items=["postal_code", "geometry"])
        .dissolve(by="postal_code", as_index=False, sort=True, dropna=True)
        .plot()
    )
    pyplot.show()


def export_shapefile(at_shapefile, export_path, export_format=None):
    """Export the generated GeoDataFrame to the selected file format."""
    export_path = Path(export_path)
    export_path.parent.mkdir(parents=True, exist_ok=True)
    export_format = (export_format or export_path.suffix.lstrip(".")).lower()

    if export_format in {"geojson", "json"}:
        at_shapefile.to_file(export_path, driver="GeoJSON")
    elif export_format in {"gpkg", "geopackage"}:
        at_shapefile.to_file(export_path, driver="GPKG")
    elif export_format in {"shp", "shapefile"}:
        at_shapefile.to_file(export_path, driver="ESRI Shapefile")
    elif export_format == "csv":
        at_shapefile.drop(columns="geometry").to_csv(export_path, index=False)
    else:
        raise ValueError(f"Unsupported export format: {export_format}")


def build_at_shapefile(
    shapefile_url=SHAPEFILE_ZIP_URL,
    shapefile_layer=SHAPEFILE_LAYER,
    shapefile_dir=SHAPEFILE_DATA_DIR,
    export_path=None,
    export_format=None,
    plot=False,
    log_callback=None,
):
    """Build Austrian postal-code areas and optionally export or plot the result."""

    def log(message):
        if log_callback is not None:
            log_callback(message)

    log("Loading postal codes...")
    postal_codes = load_postal_codes()
    log("Loading municipalities...")
    municipalities = load_municipalities()
    log("Loading political districts...")
    political_districts = load_political_districts()
    log("Loading localities...")
    localities = load_localities(political_districts)

    duplicate_localities = localities.loc[
        localities.duplicated(subset=["postal_code"], keep=False)
    ].sort_values(by=["postal_code"], ignore_index=True)
    if not duplicate_localities.empty:
        log(f"Found {len(duplicate_localities)} duplicate locality postal-code rows.")

    log("Downloading and extracting municipality geometries...")
    download_shapefile(target_dir=shapefile_dir, url=shapefile_url)
    log("Building joined shapefile data...")
    at_shapefile = load_shapefile(
        municipalities=municipalities,
        postal_codes=postal_codes,
        shapefile_dir=shapefile_dir,
        shapefile_layer=shapefile_layer,
    )

    if export_path:
        export_label = export_format or Path(export_path).suffix.lstrip(".")
        log(f"Exporting {export_label} to {export_path}...")
        export_shapefile(
            at_shapefile=at_shapefile,
            export_path=export_path,
            export_format=export_format,
        )
        log("Export completed successfully.")

    if plot:
        log("Plotting shapefile levels...")
        plot_shapefile_levels(at_shapefile)

    return at_shapefile


def main():
    """Build and plot Austrian shapefile data."""
    build_at_shapefile(plot=True, log_callback=print)


if __name__ == "__main__":
    main()
