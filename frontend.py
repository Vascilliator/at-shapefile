"""Tkinter GUI for building Austrian postal-code shapefiles."""

from importlib import util
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_PATH = PROJECT_ROOT / "at-shapefile.py"
EXPORT_FORMATS = {
    "GeoJSON (.geojson)": ("geojson", ".geojson"),
    "GeoPackage (.gpkg)": ("gpkg", ".gpkg"),
    "ESRI Shapefile (.shp)": ("shp", ".shp"),
    "CSV ohne Geometrie (.csv)": ("csv", ".csv"),
}


def load_backend():
    """Load the hyphenated backend script as an importable module."""
    spec = util.spec_from_file_location("at_shapefile_backend", BACKEND_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load backend from {BACKEND_PATH}")

    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AtShapefileGui(tk.Tk):
    """Small GUI wrapper around the reusable shapefile build function."""

    def __init__(self):
        super().__init__()
        self.backend = load_backend()
        self.log_queue = Queue()
        self.worker = None

        self.title("AT Shapefile Export")
        self.geometry("780x520")
        self.columnconfigure(1, weight=1)
        self.rowconfigure(5, weight=1)

        self.url_var = tk.StringVar(value=self.backend.SHAPEFILE_ZIP_URL)
        self.layer_var = tk.StringVar(value=self.backend.SHAPEFILE_LAYER)
        self.export_var = tk.StringVar(
            value=str(PROJECT_ROOT / "data" / "processed" / "at_postal_codes.geojson")
        )
        self.format_var = tk.StringVar(value="GeoJSON (.geojson)")
        self.status_var = tk.StringVar(value="Bereit.")

        self._build_form()
        self.after(100, self._drain_log_queue)

    def _build_form(self):
        padding = {"padx": 8, "pady": 6}

        ttk.Label(self, text="Download-URL Gemeindegeometrien").grid(
            row=0, column=0, sticky="w", **padding
        )
        ttk.Entry(self, textvariable=self.url_var).grid(
            row=0, column=1, columnspan=2, sticky="ew", **padding
        )

        ttk.Label(self, text="Layer-Name Gemeindegeometrien").grid(
            row=1, column=0, sticky="w", **padding
        )
        ttk.Entry(self, textvariable=self.layer_var).grid(
            row=1, column=1, columnspan=2, sticky="ew", **padding
        )

        ttk.Label(self, text="Exportziel").grid(row=2, column=0, sticky="w", **padding)
        ttk.Entry(self, textvariable=self.export_var).grid(
            row=2, column=1, sticky="ew", **padding
        )
        ttk.Button(self, text="Durchsuchen...", command=self._choose_export_path).grid(
            row=2, column=2, sticky="ew", **padding
        )

        ttk.Label(self, text="Exportformat").grid(
            row=3, column=0, sticky="w", **padding
        )
        format_box = ttk.Combobox(
            self,
            textvariable=self.format_var,
            values=list(EXPORT_FORMATS),
            state="readonly",
        )
        format_box.grid(row=3, column=1, columnspan=2, sticky="ew", **padding)
        format_box.bind(
            "<<ComboboxSelected>>", lambda _event: self._sync_export_suffix()
        )

        self.process_button = ttk.Button(
            self,
            text="PLZ-Flächen erzeugen",
            command=self._start_processing,
        )
        self.process_button.grid(row=4, column=0, columnspan=3, sticky="ew", **padding)

        self.log_text = tk.Text(self, height=16, state="disabled", wrap="word")
        self.log_text.grid(row=5, column=0, columnspan=3, sticky="nsew", **padding)
        ttk.Label(self, textvariable=self.status_var).grid(
            row=6, column=0, columnspan=3, sticky="w", **padding
        )

    def _choose_export_path(self):
        export_format, extension = EXPORT_FORMATS[self.format_var.get()]
        path = filedialog.asksaveasfilename(
            title="Exportziel auswählen",
            defaultextension=extension,
            filetypes=[
                (self.format_var.get(), f"*{extension}"),
                ("Alle Dateien", "*.*"),
            ],
        )
        if path:
            self.export_var.set(path)
            self.format_var.set(self._format_label_for_path(path, export_format))

    def _format_label_for_path(self, path, fallback_format):
        suffix = Path(path).suffix.lower().lstrip(".")
        for label, (export_format, _extension) in EXPORT_FORMATS.items():
            if (
                suffix == export_format
                or suffix == "json"
                and export_format == "geojson"
            ):
                return label
        for label, (export_format, _extension) in EXPORT_FORMATS.items():
            if export_format == fallback_format:
                return label
        return self.format_var.get()

    def _sync_export_suffix(self):
        path = Path(self.export_var.get())
        _export_format, extension = EXPORT_FORMATS[self.format_var.get()]
        if path.suffix and path.suffix.lower() != extension:
            self.export_var.set(str(path.with_suffix(extension)))

    def _start_processing(self):
        if self.worker and self.worker.is_alive():
            return

        shapefile_url = self.url_var.get().strip()
        shapefile_layer = self.layer_var.get().strip()
        export_path = self.export_var.get().strip()
        export_format, _extension = EXPORT_FORMATS[self.format_var.get()]

        if not shapefile_url or not shapefile_layer or not export_path:
            messagebox.showerror(
                "Fehlende Eingabe", "Bitte URL, Layer-Name und Exportziel ausfüllen."
            )
            return

        self.process_button.configure(state="disabled")
        self.status_var.set("Verarbeitung läuft...")
        self._append_log("Starte Verarbeitung...")

        self.worker = Thread(
            target=self._run_processing,
            kwargs={
                "shapefile_url": shapefile_url,
                "shapefile_layer": shapefile_layer,
                "export_path": export_path,
                "export_format": export_format,
            },
            daemon=True,
        )
        self.worker.start()

    def _run_processing(
        self, shapefile_url, shapefile_layer, export_path, export_format
    ):
        try:
            self.backend.build_at_shapefile(
                shapefile_url=shapefile_url,
                shapefile_layer=shapefile_layer,
                export_path=export_path,
                export_format=export_format,
                plot=False,
                log_callback=self.log_queue.put,
            )
        except Exception as exc:  # noqa: BLE001 - show unexpected backend failures in the GUI log.
            self.log_queue.put(("error", f"Fehler: {exc}"))
        else:
            self.log_queue.put(
                ("done", f"Export erfolgreich abgeschlossen: {export_path}")
            )

    def _drain_log_queue(self):
        try:
            while True:
                item = self.log_queue.get_nowait()
                if isinstance(item, tuple):
                    event, message = item
                    self._append_log(message)
                    if event == "done":
                        self.status_var.set("Fertig.")
                        self.process_button.configure(state="normal")
                        messagebox.showinfo("Export fertig", message)
                    elif event == "error":
                        self.status_var.set("Fehler.")
                        self.process_button.configure(state="normal")
                        messagebox.showerror("Fehler", message)
                else:
                    self._append_log(item)
        except Empty:
            pass
        finally:
            self.after(100, self._drain_log_queue)

    def _append_log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")


if __name__ == "__main__":
    AtShapefileGui().mainloop()
