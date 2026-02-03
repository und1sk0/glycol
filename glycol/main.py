import argparse

from glycol.ui import run_app


def main():
    parser = argparse.ArgumentParser(
        description="Glycol - OpenSky Airport Monitor"
    )
    parser.add_argument(
        "--airport",
        default="",
        help="ICAO airport code to monitor (e.g. KSFO)",
    )
    parser.add_argument(
        "--mode",
        choices=["A", "B", "C"],
        default="C",
        help="Filter mode: A=ICAO24/tail, B=category, C=all traffic",
    )
    parser.add_argument(
        "--filter",
        dest="filter_text",
        default="",
        help="Comma-separated filter values (for modes A and B)",
    )
    args = parser.parse_args()
    run_app(airport=args.airport, mode=args.mode, filter_text=args.filter_text)


if __name__ == "__main__":
    main()
