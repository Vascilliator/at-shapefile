"""Top-level starter for the Austrian shapefile app."""

import argparse

from subapps import backend
from subapps.gui import main as start_gui


def main():
    """Start the GUI by default or run the backend CLI workflow."""
    parser = argparse.ArgumentParser(description="Build Austrian postal-code shapefiles.")
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run the default command-line export instead of opening the GUI.",
    )
    args = parser.parse_args()

    if args.cli:
        backend.main()
    else:
        start_gui()


if __name__ == "__main__":
    main()
