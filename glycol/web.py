import json
import logging
import queue
import threading
import time
from pathlib import Path
from typing import Generator

from flask import Flask, render_template, request, jsonify, Response

from glycol.auth import OpenSkyAuth, load_credentials_from_file
from glycol.api import OpenSkyClient
from glycol.aircraft import REG_TO_ICAO24, ICAO24_TO_TYPE
from glycol.airports import get_bounding_box, airport_name, AIRPORTS
from glycol.monitor import AircraftMonitor
from glycol.events import EventStore
from glycol.groups import GroupsDatabase


class GlycolWebApp:
    """Web-based Glycol airport monitor using Flask and SSE."""

    def __init__(self, data_dir: str | None = None, logs_dir: str | None = None):
        self.app = Flask(__name__,
                        template_folder=str(Path(__file__).parent / "templates"),
                        static_folder=str(Path(__file__).parent / "static"))
        self.data_dir = data_dir
        self.logs_dir = logs_dir

        # State
        self.auth: OpenSkyAuth | None = None
        self.client: OpenSkyClient | None = None
        self.groups_db = GroupsDatabase(data_dir=data_dir)
        self.monitor = AircraftMonitor(filter_mode=None, icao_to_type=ICAO24_TO_TYPE)
        self.store = EventStore(logs_dir=logs_dir)

        # Polling state
        self._polling = False
        self._poll_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self.current_airport = ""
        self.poll_interval = 10

        # SSE state - queues for broadcasting updates
        self._event_queues: list[queue.Queue] = []
        self._queues_lock = threading.Lock()

        # Try to authenticate
        self._authenticate()

        # Setup routes
        self._setup_routes()

    def _authenticate(self):
        """Attempt to load credentials and authenticate."""
        try:
            creds = load_credentials_from_file(data_dir=self.data_dir)
            if creds:
                client_id, client_secret = creds
                self.auth = OpenSkyAuth(client_id, client_secret)
                if self.auth.authenticate():
                    self.client = OpenSkyClient(self.auth)
                    logging.info("Authenticated with OpenSky API")
                else:
                    logging.error("Authentication failed")
            else:
                logging.warning("No credentials found")
        except Exception as e:
            logging.error(f"Authentication failed: {e}")

    def _broadcast_event(self, event_type: str, data: dict):
        """Broadcast an event to all SSE clients."""
        message = {
            "type": event_type,
            "data": data,
            "timestamp": time.time()
        }

        with self._queues_lock:
            dead_queues = []
            for q in self._event_queues:
                try:
                    q.put_nowait(message)
                except queue.Full:
                    dead_queues.append(q)

            # Remove dead queues
            for q in dead_queues:
                self._event_queues.remove(q)

    def _poll_loop(self):
        """Background polling loop."""
        logging.info("Starting poll loop")

        while not self._stop_event.is_set():
            try:
                if not self.client or not self.current_airport:
                    time.sleep(1)
                    continue

                # Get bounding box for airport
                bbox = get_bounding_box(self.current_airport)
                if not bbox:
                    logging.warning(f"Airport {self.current_airport} not found")
                    time.sleep(self.poll_interval)
                    continue

                # Query API
                states = self.client.get_states(bbox)

                # Process states
                aircraft_list = []
                events = []

                for state in states:
                    # Check for events
                    event = self.monitor.update(state)
                    if event:
                        self.store.record_event(event)
                        events.append(event)

                    # Build aircraft info
                    icao24 = state.get("icao24", "")
                    callsign = state.get("callsign", "")
                    on_ground = state.get("on_ground", False)
                    altitude = state.get("baro_altitude")
                    velocity = state.get("velocity")

                    aircraft_list.append({
                        "icao24": icao24,
                        "callsign": callsign,
                        "on_ground": on_ground,
                        "altitude": round(altitude / 0.3048) if altitude else None,
                        "velocity": round(velocity * 1.94384) if velocity else None,
                    })

                # Broadcast updates
                self._broadcast_event("aircraft_update", {
                    "aircraft": aircraft_list,
                    "count": len(aircraft_list)
                })

                if events:
                    self._broadcast_event("new_events", {
                        "events": [self._format_event(e) for e in events]
                    })

                # Broadcast rate limit info
                if self.client.rate_limit_remaining is not None:
                    self._broadcast_event("rate_limit", {
                        "remaining": self.client.rate_limit_remaining
                    })

                time.sleep(self.poll_interval)

            except Exception as e:
                logging.error(f"Poll error: {e}", exc_info=True)
                time.sleep(5)

        logging.info("Poll loop stopped")

    def _format_event(self, event: dict) -> dict:
        """Format event for JSON serialization."""
        return {
            "timestamp": event["timestamp"].isoformat() if hasattr(event["timestamp"], "isoformat") else str(event["timestamp"]),
            "icao24": event["icao24"],
            "callsign": event.get("callsign", ""),
            "event_type": event["event_type"],
            "altitude_ft": event.get("altitude_ft"),
        }

    def _setup_routes(self):
        """Setup Flask routes."""

        @self.app.route("/")
        def index():
            airport_codes = sorted(AIRPORTS.keys())
            return render_template("index.html", airports=airport_codes)

        @self.app.route("/api/start", methods=["POST"])
        def start_monitoring():
            data = request.get_json()
            airport = data.get("airport", "").strip().upper()
            self.poll_interval = int(data.get("interval", 10))

            filter_mode = data.get("filter_mode")
            filter_values = data.get("filter_values", [])

            if not airport:
                return jsonify({"error": "Airport code required"}), 400

            if not self.client:
                return jsonify({"error": "Not authenticated"}), 401

            # Update filter
            self.monitor.set_filter(
                filter_mode if filter_mode != "all" else None,
                filter_values if filter_values else None
            )

            # Start polling
            self.current_airport = airport

            if not self._polling:
                self._stop_event.clear()
                self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
                self._poll_thread.start()
                self._polling = True

            airport_info = airport_name(airport)
            return jsonify({
                "status": "started",
                "airport": airport,
                "airport_name": airport_info,
                "interval": self.poll_interval
            })

        @self.app.route("/api/stop", methods=["POST"])
        def stop_monitoring():
            if self._polling:
                self._stop_event.set()
                if self._poll_thread:
                    self._poll_thread.join(timeout=5)
                self._polling = False

            return jsonify({"status": "stopped"})

        @self.app.route("/api/events")
        def get_events():
            df = self.store.get_dataframe()
            events = []
            for _, row in df.iterrows():
                events.append({
                    "timestamp": row["timestamp"].isoformat() if hasattr(row["timestamp"], "isoformat") else str(row["timestamp"]),
                    "icao24": row["icao24"],
                    "callsign": row.get("callsign", ""),
                    "event_type": row["event_type"],
                    "altitude_ft": row.get("altitude_m") * 3.28084 if row.get("altitude_m") else None,
                })
            return jsonify({"events": events})

        @self.app.route("/api/export_csv")
        def export_csv():
            df = self.store.get_dataframe()
            csv_data = df.to_csv(index=False)
            return Response(
                csv_data,
                mimetype="text/csv",
                headers={"Content-Disposition": "attachment;filename=glycol_events.csv"}
            )

        @self.app.route("/api/groups")
        def get_groups():
            groups = list(self.groups_db.groups.keys())
            return jsonify({"groups": groups})

        @self.app.route("/api/status")
        def get_status():
            return jsonify({
                "authenticated": self.client is not None,
                "polling": self._polling,
                "airport": self.current_airport,
                "event_count": len(self.store),
                "rate_limit": self.client.rate_limit_remaining if self.client else None
            })

        @self.app.route("/api/stream")
        def stream():
            """Server-Sent Events endpoint for real-time updates."""
            def event_stream() -> Generator[str, None, None]:
                q: queue.Queue = queue.Queue(maxsize=50)

                with self._queues_lock:
                    self._event_queues.append(q)

                try:
                    while True:
                        try:
                            message = q.get(timeout=30)
                            yield f"data: {json.dumps(message)}\n\n"
                        except queue.Empty:
                            # Send keepalive
                            yield ": keepalive\n\n"
                except GeneratorExit:
                    pass
                finally:
                    with self._queues_lock:
                        if q in self._event_queues:
                            self._event_queues.remove(q)

            return Response(
                event_stream(),
                mimetype="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no"
                }
            )

    def run(self, host="127.0.0.1", port=5000, debug=False):
        """Run the Flask development server."""
        logging.info(f"Starting Glycol web server on http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug, threaded=True)


def create_app(data_dir: str | None = None, logs_dir: str | None = None) -> Flask:
    """Factory function to create Flask app."""
    glycol_app = GlycolWebApp(data_dir=data_dir, logs_dir=logs_dir)
    return glycol_app.app


def run_web_app(host="127.0.0.1", port=5000, data_dir: str | None = None, logs_dir: str | None = None):
    """Convenience function to run the web app."""
    app = GlycolWebApp(data_dir=data_dir, logs_dir=logs_dir)
    app.run(host=host, port=port, debug=False)
