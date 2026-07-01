"""Tkinter GUI for building Austrian postal-code shapefiles."""

from pathlib import Path
from queue import Empty, Queue
from threading import Thread
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPORT_FORMATS = {
    "GeoJSON (.geojson)": ("geojson", ".geojson"),
    "CSV mit WKT (.csv)": ("csv", ".csv"),
}
from subapps import backend


class AtShapefileGui(tk.Tk):
    """Small GUI wrapper around the reusable shapefile build function."""

    def __init__(self):
        super().__init__()
        self.backend = backend
        self.log_queue = Queue()
        self.worker = None

        self.title("AT Shapefile Export")
        self.geometry("780x520")
        self.columnconfigure(1, weight=1)
        self.rowconfigure(10, weight=1)

        self.url_var = tk.StringVar(value=self.backend.SHAPEFILE_ZIP_URL)
        self.layer_var = tk.StringVar(value=self.backend.SHAPEFILE_LAYER)
        self.shapefile_dir_var = tk.StringVar(
            value=str(
                self.backend.get_shapefile_data_dir(self.backend.SHAPEFILE_ZIP_URL)
            )
        )
        self.export_var = tk.StringVar(
            value=str(PROJECT_ROOT / "data" / "processed" / "at_postal_codes.geojson")
        )
        self.simplified_export_enabled_var = tk.BooleanVar(value=False)
        self.simplified_export_path_var = tk.StringVar(
            value=str(
                PROJECT_ROOT
                / "data"
                / "processed"
                / "at_postal_codes.qlik.geojson"
            )
        )
        self.simplify_tolerance_var = tk.StringVar(value="50")
        self.coordinate_precision_var = tk.StringVar(value="6")
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

        ttk.Label(self, text="Zielordner Gemeindegeometrien").grid(
            row=2, column=0, sticky="w", **padding
        )
        ttk.Entry(self, textvariable=self.shapefile_dir_var).grid(
            row=2, column=1, sticky="ew", **padding
        )
        ttk.Button(
            self, text="Durchsuchen...", command=self._choose_shapefile_dir
        ).grid(row=2, column=2, sticky="ew", **padding)

        ttk.Label(self, text="Exportziel").grid(row=3, column=0, sticky="w", **padding)
        ttk.Entry(self, textvariable=self.export_var).grid(
            row=3, column=1, sticky="ew", **padding
        )
        ttk.Button(self, text="Durchsuchen...", command=self._choose_export_path).grid(
            row=3, column=2, sticky="ew", **padding
        )

        ttk.Label(self, text="Exportformat").grid(
            row=4, column=0, sticky="w", **padding
        )
        format_box = ttk.Combobox(
            self,
            textvariable=self.format_var,
            values=list(EXPORT_FORMATS),
            state="readonly",
        )
        format_box.grid(row=4, column=1, columnspan=2, sticky="ew", **padding)
        format_box.bind(
            "<<ComboboxSelected>>", lambda _event: self._sync_export_suffix()
        )

        self.process_button = ttk.Button(
            self,
            text="PLZ-Flächen erzeugen",
            command=self._start_processing,
        )
        ttk.Checkbutton(
            self,
            text="Zusätzlichen vereinfachten Qlik-Export erzeugen",
            variable=self.simplified_export_enabled_var,
        ).grid(row=5, column=0, columnspan=3, sticky="w", **padding)

        ttk.Label(self, text="Vereinfachter Exportpfad").grid(
            row=6, column=0, sticky="w", **padding
        )
        ttk.Entry(self, textvariable=self.simplified_export_path_var).grid(
            row=6, column=1, sticky="ew", **padding
        )
        ttk.Button(
            self,
            text="Durchsuchen...",
            command=self._choose_simplified_export_path,
        ).grid(row=6, column=2, sticky="ew", **padding)

        ttk.Label(self, text="Vereinfachungstoleranz (Meter)").grid(
            row=7, column=0, sticky="w", **padding
        )
        ttk.Entry(self, textvariable=self.simplify_tolerance_var).grid(
            row=7, column=1, columnspan=2, sticky="ew", **padding
        )

        ttk.Label(self, text="Koordinatenpräzision").grid(
            row=8, column=0, sticky="w", **padding
        )
        ttk.Entry(self, textvariable=self.coordinate_precision_var).grid(
            row=8, column=1, columnspan=2, sticky="ew", **padding
        )

        self.process_button.grid(row=9, column=0, columnspan=3, sticky="ew", **padding)

        self.log_text = tk.Text(self, height=16, state="disabled", wrap="word")
        self.log_text.grid(row=10, column=0, columnspan=3, sticky="nsew", **padding)
        ttk.Label(self, textvariable=self.status_var).grid(
            row=11, column=0, columnspan=3, sticky="w", **padding
        )

    def _choose_shapefile_dir(self):
        path = filedialog.askdirectory(
            title="Zielordner für Gemeindegeometrien auswählen",
            initialdir=self.shapefile_dir_var.get() or str(PROJECT_ROOT),
        )
        if path:
            self.shapefile_dir_var.set(path)

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

    def _choose_simplified_export_path(self):
        path = filedialog.asksaveasfilename(
            title="Vereinfachten Qlik-Export auswählen",
            defaultextension=".geojson",
            filetypes=[
                ("GeoJSON (.geojson)", "*.geojson"),
                ("JSON (.json)", "*.json"),
                ("Alle Dateien", "*.*"),
            ],
        )
        if path:
            self.simplified_export_path_var.set(path)

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
        shapefile_dir = self.shapefile_dir_var.get().strip()
        export_path = self.export_var.get().strip()
        simplified_export_enabled = self.simplified_export_enabled_var.get()
        simplified_export_path = self.simplified_export_path_var.get().strip()
        simplify_tolerance_text = self.simplify_tolerance_var.get().strip()
        coordinate_precision_text = self.coordinate_precision_var.get().strip()
        output_format, _extension = EXPORT_FORMATS[self.format_var.get()]

        if (
            not shapefile_url
            or not shapefile_layer
            or not shapefile_dir
            or not export_path
        ):
            messagebox.showerror(
                "Fehlende Eingabe",
                "Bitte URL, Layer-Name, Zielordner und Exportziel ausfüllen.",
            )
            return

        simplify_tolerance = None
        coordinate_precision = None
        if simplified_export_enabled:
            if not simplified_export_path:
                messagebox.showerror(
                    "Fehlende Eingabe",
                    "Bitte einen Pfad für den vereinfachten Export angeben.",
                )
                return
            try:
                simplify_tolerance = float(simplify_tolerance_text)
            except ValueError:
                messagebox.showerror(
                    "Ungültige Toleranz",
                    "Die Vereinfachungstoleranz muss eine Zahl sein.",
                )
                return
            if simplify_tolerance < 0:
                messagebox.showerror(
                    "Ungültige Toleranz",
                    "Die Vereinfachungstoleranz darf nicht negativ sein.",
                )
                return

            if coordinate_precision_text:
                try:
                    coordinate_precision = int(coordinate_precision_text)
                except ValueError:
                    messagebox.showerror(
                        "Ungültige Präzision",
                        "Die Koordinatenpräzision muss eine ganze Zahl sein.",
                    )
                    return
                if coordinate_precision < 0:
                    messagebox.showerror(
                        "Ungültige Präzision",
                        "Die Koordinatenpräzision darf nicht negativ sein.",
                    )
                    return
        else:
            simplified_export_path = None

        default_shapefile_dir = str(
            self.backend.get_shapefile_data_dir(self.backend.SHAPEFILE_ZIP_URL)
        )
        if shapefile_dir == default_shapefile_dir:
            shapefile_dir = str(self.backend.get_shapefile_data_dir(shapefile_url))
            self.shapefile_dir_var.set(shapefile_dir)

        self.process_button.configure(state="disabled")
        self.status_var.set("Verarbeitung läuft...")
        self._append_log("Starte Verarbeitung...")
        self._append_log(f"Normaler Exportpfad: {export_path}")
        if simplified_export_enabled:
            self._append_log(f"Vereinfachter Exportpfad: {simplified_export_path}")
            self._append_log(f"Vereinfachungstoleranz: {simplify_tolerance} m")
            if coordinate_precision is not None:
                self._append_log(f"Koordinatenpräzision: {coordinate_precision}")
        else:
            self._append_log("Kein vereinfachter Export aktiviert.")

        self.worker = Thread(
            target=self._run_processing,
            kwargs={
                "shapefile_url": shapefile_url,
                "shapefile_layer": shapefile_layer,
                "shapefile_dir": shapefile_dir,
                "export_path": export_path,
                "output_format": output_format,
                "simplified_export_path": simplified_export_path,
                "simplify_tolerance": simplify_tolerance,
                "coordinate_precision": coordinate_precision,
            },
            daemon=True,
        )
        self.worker.start()

    def _run_processing(
        self,
        shapefile_url,
        shapefile_layer,
        shapefile_dir,
        export_path,
        output_format,
        simplified_export_path,
        simplify_tolerance,
        coordinate_precision,
    ):
        try:
            self.backend.build_and_export_postal_code_geometries(
                shapefile_url=shapefile_url,
                shapefile_layer=shapefile_layer,
                shapefile_dir=shapefile_dir,
                export_path=export_path,
                export_format=output_format,
                plot=False,
                log_callback=self.log_queue.put,
                simplify_tolerance=simplify_tolerance,
                simplified_export_path=simplified_export_path,
                coordinate_precision=coordinate_precision,
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


def main():
    """Start the graphical shapefile export app."""
    AtShapefileGui().mainloop()


if __name__ == "__main__":
    main()
