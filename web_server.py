#!/usr/bin/env python3
"""
Glycol Web Server

Launch the web-based version of Glycol for browser access.
"""
import argparse
import logging
from pathlib import Path

from glycol.main import setup_logging
from glycol.web import run_web_app


def main():
    parser = argparse.ArgumentParser(description="Glycol Web Server")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to bind to (default: 5000)",
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
    )


if __name__ == "__main__":
    main()
