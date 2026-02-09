import argparse
import json
import logging
import os
import secrets
from datetime import datetime
from pathlib import Path

from glycol.ui import run_app


class JsonFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records as JSON.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add any extra fields from the log record
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


def setup_logging(log_file: str = None, logs_dir: str = None) -> str:
    """
    Set up logging to file. Returns the log file path.

    Args:
        log_file: Optional custom log file name. If None, generates a timestamped name.
        logs_dir: Optional directory for log files. If None, uses default logs/ directory.

    Returns:
        The full path to the log file.
    """
    # Create logs directory if it doesn't exist
    if logs_dir is None:
        logs_dir = Path(__file__).parent.parent / "logs"
    else:
        logs_dir = Path(logs_dir)

    logs_dir.mkdir(parents=True, exist_ok=True)

    # Generate log file name if not provided
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d:%H:%M")
        random_hex = secrets.token_hex(4)
        log_file = f"glycol-{timestamp}-{random_hex}.log"

    # Add logs/ prefix if the log file doesn't contain a path separator
    if os.sep not in log_file and "/" not in log_file:
        log_path = logs_dir / log_file
    else:
        log_path = Path(log_file)

    # Configure logging with JSON formatter for file, standard format for console
    json_formatter = JsonFormatter()
    console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    file_handler = logging.FileHandler(log_path, mode="a")
    file_handler.setFormatter(json_formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)

    logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])

    return str(log_path)


def main():
    parser = argparse.ArgumentParser(description="Glycol - OpenSky Airport Monitor")
    parser.add_argument(
        "--airport",
        default="",
        help="ICAO airport code to monitor (e.g. KSFO)",
    )

    # Mutually exclusive filter options
    filter_group = parser.add_mutually_exclusive_group()
    filter_group.add_argument(
        "--aircraft",
        dest="aircraft_filter",
        default="",
        help="Filter by ICAO24 or tail number",
    )
    filter_group.add_argument(
        "--group",
        dest="group_filter",
        default="",
        help="Filter by aircraft group name",
    )

    parser.add_argument(
        "--interval",
        dest="poll_interval",
        default=30,
        help="Polling interval seconds (default: 30)",
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

    # Determine mode and filter from new flags
    if args.aircraft_filter:
        mode = "A"
        filter_text = args.aircraft_filter
    elif args.group_filter:
        mode = "B"
        filter_text = args.group_filter
    else:
        mode = "C"
        filter_text = ""

    # Set up logging
    log_path = setup_logging(args.log_file, args.logs_dir)
    logging.info(f"Glycol starting - logging to {log_path}")
    if args.aircraft_filter:
        logging.info(
            f"Airport: {args.airport or 'Not set'}, Filter: aircraft={args.aircraft_filter}"
        )
    elif args.group_filter:
        logging.info(
            f"Airport: {args.airport or 'Not set'}, Filter: group={args.group_filter}"
        )
    else:
        logging.info(f"Airport: {args.airport or 'Not set'}, Filter: all traffic")
    if args.data_dir:
        logging.info(f"Data directory: {args.data_dir}")
    if args.logs_dir:
        logging.info(f"Logs directory: {args.logs_dir}")

    run_app(
        airport=args.airport,
        data_dir=args.data_dir,
        filter_text=filter_text,
        logs_dir=args.logs_dir,
        mode=mode,
        poll_interval=args.poll_interval,
    )


if __name__ == "__main__":
    main()
