"""Top-level starter for the Austrian shapefile app."""

import argparse

from subapps import backend


def start_gui():
    """Import and start the Tkinter GUI only when it is requested."""
    try:
        from subapps.gui import main as gui_main
    except ModuleNotFoundError as exc:
        if exc.name != "tkinter":
            raise
        raise SystemExit(
            "Tkinter is not installed in this Python environment. "
            "Install the Tkinter package for your Python distribution "
            "(for example, 'python3-tk' on Debian/Ubuntu) or run "
            "'python at-shapefile.py --cli' to use the command-line export."
        ) from exc

    gui_main()


def main():
    """Start the GUI by default or run the backend CLI workflow."""
    parser = argparse.ArgumentParser(description="Build Austrian postal-code shapefiles.")
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run the default command-line export instead of opening the GUI.",
    )
    parser.add_argument(
        "--export-path",
        help="Write the full postal-code export to this path.",
    )
    parser.add_argument(
        "--export-format",
        help="Export format for the full postal-code export (defaults to the output suffix).",
    )
    parser.add_argument(
        "--simplified-export-path",
        help="Also write a simplified postal-code export to this path.",
    )
    parser.add_argument(
        "--simplify-tolerance",
        type=float,
        help="Simplification tolerance in meters for the simplified export.",
    )
    parser.add_argument(
        "--coordinate-precision",
        type=int,
        help="Decimal places to keep for GeoJSON coordinates.",
    )
    args = parser.parse_args()

    if args.cli:
        backend.main(
            export_path=args.export_path,
            export_format=args.export_format,
            simplified_export_path=args.simplified_export_path,
            simplify_tolerance=args.simplify_tolerance,
            coordinate_precision=args.coordinate_precision,
        )
    else:
        start_gui()


if __name__ == "__main__":
    main()
