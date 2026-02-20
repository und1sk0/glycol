#!/usr/bin/env python3
"""
Glycol Web Server

Launch the web-based version of Glycol for browser access.
"""
import argparse
import logging
import os
from pathlib import Path

from glycol.main import setup_logging
from glycol.web import run_web_app


def main():
    parser = argparse.ArgumentParser(description="Glycol Web Server")
    parser.add_argument(
        "--host",
        default=os.getenv("HOST", "127.0.0.1"),
        help="Host to bind to (default: from HOST env or 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", "8666")),
        help="Port to bind to (default: from PORT env or 8666)",
    )
    parser.add_argument(
        "--log",
        dest="log_file",
        default=None,
        help="Log file name (defaults to timestamped file in logs/)",
    )
    parser.add_argument(
        "--logs-dir",
        dest="logs_dir",
        default=None,
        help="Directory for log files (defaults to logs/)",
    )
    parser.add_argument(
        "--data-dir",
        dest="data_dir",
        default=None,
        help="Directory for data files (defaults to glycol/data/)",
    )
    parser.add_argument(
        "--poll-interval",
        dest="poll_interval",
        type=int,
        default=None,
        help="Poll interval in seconds (default: from POLL_INTERVAL env or 10)",
    )
    parser.add_argument(
        "--radius-nm",
        dest="radius_nm",
        type=float,
        default=None,
        help="Radius in nautical miles from airport (default: from RADIUS_NM env or 5)",
    )
    parser.add_argument(
        "--ceiling-ft",
        dest="ceiling_ft",
        type=float,
        default=None,
        help="Altitude ceiling in feet (default: from CEILING_FT env or 1500)",
    )
    args = parser.parse_args()

    # Set up logging
    log_path = setup_logging(args.log_file, args.logs_dir)
    logging.info(f"Glycol Web Server starting - logging to {log_path}")
    logging.info(f"Server will be available at http://{args.host}:{args.port}")

    # Run the web app
    run_web_app(
        host=args.host,
        port=args.port,
        data_dir=args.data_dir,
        logs_dir=args.logs_dir,
        poll_interval=args.poll_interval,
        radius_nm=args.radius_nm,
        ceiling_ft=args.ceiling_ft,
    )


if __name__ == "__main__":
    main()
