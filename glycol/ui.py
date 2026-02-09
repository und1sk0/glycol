import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import datetime

from glycol.auth import OpenSkyAuth, load_credentials_from_file
from glycol.api import OpenSkyClient
from glycol.airports import get_bounding_box, airport_name, AIRPORTS
from glycol.monitor import AircraftMonitor
from glycol.events import EventStore


class CredentialsDialog(simpledialog.Dialog):
    """Modal dialog to collect OpenSky client_id and client_secret."""

    def body(self, master):
        self.title("OpenSky Credentials")
        tk.Label(master, text="Client ID:").grid(row=0, sticky=tk.W)
        tk.Label(master, text="Client Secret:").grid(row=1, sticky=tk.W)

        self.entry_id = tk.Entry(master, width=40)
        self.entry_secret = tk.Entry(master, width=40, show="*")
        self.entry_id.grid(row=0, column=1, padx=4, pady=2)
        self.entry_secret.grid(row=1, column=1, padx=4, pady=2)
        return self.entry_id

    def apply(self):
        self.result = (self.entry_id.get().strip(), self.entry_secret.get().strip())


class GlycolApp:
    """Main Tkinter application for Glycol airport monitoring."""

    POLL_DEFAULT = 10  # seconds

    def __init__(
        self,
        root: tk.Tk,
        airport: str = "",
        mode: str = "C",
        filter_text: str = "",
        data_dir: str = None,
        logs_dir: str = None,
    ):
        self.root = root
        self.root.title("Glycol - OpenSky Airport Monitor")
        self.root.geometry("960x700")
        self.root.minsize(800, 550)

        # Configuration
        self.data_dir = data_dir
        self.logs_dir = logs_dir

        # State
        self.auth: OpenSkyAuth | None = None
        self.client: OpenSkyClient | None = None
        self.monitor = AircraftMonitor()
        self.store = EventStore()
        self._polling = False
        self._poll_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        self._build_menu()
        self._build_config_panel(airport, mode, filter_text)
        self._build_aircraft_table()
        self._build_event_log()
        self._build_status_bar()

        # Try to load credentials automatically, prompt if not found
        self.root.after(200, self._auto_authenticate)

    # ---- UI construction ----

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Set Credentials...", command=self._prompt_credentials)
        file_menu.add_command(label="Save CSV...", command=self._save_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self._on_close)
        menubar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menubar)

    def _build_config_panel(self, airport: str, mode: str, filter_text: str):
        frame = ttk.LabelFrame(self.root, text="Configuration", padding=6)
        frame.pack(fill=tk.X, padx=6, pady=(6, 3))

        # Airport
        ttk.Label(frame, text="Airport ICAO:").grid(row=0, column=0, sticky=tk.W)
        self.airport_var = tk.StringVar(value=airport)
        ttk.Entry(frame, textvariable=self.airport_var, width=8).grid(
            row=0, column=1, padx=4
        )

        # Filter Type
        ttk.Label(frame, text="Filter:").grid(row=0, column=2, sticky=tk.W, padx=(12, 0))
        self.mode_var = tk.StringVar(value=mode.upper() if mode else "C")
        mode_combo = ttk.Combobox(
            frame,
            textvariable=self.mode_var,
            values=["All Traffic", "Aircraft", "Group"],
            state="readonly",
            width=12,
        )
        # Map mode to display value
        mode_display = {"C": "All Traffic", "A": "Aircraft", "B": "Group"}
        mode_combo.set(mode_display.get(mode.upper() if mode else "C", "All Traffic"))
        mode_combo.grid(row=0, column=3, padx=4)

        # Filter Value
        ttk.Label(frame, text="Value:").grid(
            row=0, column=4, sticky=tk.W, padx=(12, 0)
        )
        self.filter_var = tk.StringVar(value=filter_text)
        ttk.Entry(frame, textvariable=self.filter_var, width=30).grid(
            row=0, column=5, padx=4
        )

        # Poll interval
        ttk.Label(frame, text="Poll (s):").grid(
            row=0, column=6, sticky=tk.W, padx=(12, 0)
        )
        self.poll_var = tk.IntVar(value=self.POLL_DEFAULT)
        ttk.Spinbox(frame, from_=5, to=120, textvariable=self.poll_var, width=5).grid(
            row=0, column=7, padx=4
        )

        # Start / Stop
        self.start_btn = ttk.Button(frame, text="Start", command=self._toggle_polling)
        self.start_btn.grid(row=0, column=8, padx=(12, 0))

    def _build_aircraft_table(self):
        frame = ttk.LabelFrame(self.root, text="Aircraft in Range", padding=4)
        frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=3)

        cols = ("icao24", "callsign", "alt_m", "speed_ms", "heading", "vrate", "on_ground", "category", "country")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=10)
        headings = {
            "icao24": "ICAO24",
            "callsign": "Callsign",
            "alt_m": "Alt (m)",
            "speed_ms": "Spd (m/s)",
            "heading": "Hdg",
            "vrate": "VRate",
            "on_ground": "Ground",
            "category": "Cat",
            "country": "Country",
        }
        widths = {
            "icao24": 70,
            "callsign": 90,
            "alt_m": 70,
            "speed_ms": 70,
            "heading": 55,
            "vrate": 60,
            "on_ground": 55,
            "category": 45,
            "country": 90,
        }
        for c in cols:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=widths[c], anchor=tk.CENTER)

        vsb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def _build_event_log(self):
        frame = ttk.LabelFrame(self.root, text="Event Log", padding=4)
        frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=3)

        self.log_text = tk.Text(frame, height=8, state=tk.DISABLED, wrap=tk.WORD)
        sb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=sb.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

    def _build_status_bar(self):
        self.status_var = tk.StringVar(value="Not authenticated")
        bar = ttk.Label(
            self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W
        )
        bar.pack(fill=tk.X, padx=6, pady=(0, 6))

    # ---- Credentials ----

    def _auto_authenticate(self):
        """Try to load credentials from file, prompt if not found."""
        credentials = load_credentials_from_file(data_dir=self.data_dir)
        if credentials:
            client_id, client_secret = credentials
            self.auth = OpenSkyAuth(client_id, client_secret)
            self._set_status("Authenticating with saved credentials...")
            threading.Thread(target=self._do_auth, daemon=True).start()
        else:
            # No credentials file found, prompt user
            self._prompt_credentials()

    def _prompt_credentials(self):
        dlg = CredentialsDialog(self.root)
        if dlg.result:
            client_id, client_secret = dlg.result
            if not client_id or not client_secret:
                messagebox.showwarning("Credentials", "Both fields are required.")
                return
            self.auth = OpenSkyAuth(client_id, client_secret)
            self._set_status("Authenticating...")
            # Authenticate in a thread to avoid blocking UI
            threading.Thread(target=self._do_auth, daemon=True).start()

    def _do_auth(self):
        ok = self.auth.authenticate()
        if ok:
            self.client = OpenSkyClient(self.auth)
            self.root.after(0, lambda: self._set_status("Authenticated"))
        else:
            self.root.after(
                0,
                lambda: self._set_status("Authentication failed - check credentials"),
            )

    # ---- Polling control ----

    def _toggle_polling(self):
        if self._polling:
            self._stop_polling()
        else:
            self._start_polling()

    def _start_polling(self):
        if not self.client:
            messagebox.showinfo("Glycol", "Please set credentials first.")
            return

        airport = self.airport_var.get().strip().upper()
        if not airport:
            messagebox.showinfo("Glycol", "Enter an airport ICAO code.")
            return

        bbox = get_bounding_box(airport)
        if bbox is None:
            messagebox.showinfo(
                "Glycol",
                f"Unknown airport {airport}. Add it to airports.py or provide lat/lon.",
            )
            return

        # Map display value back to mode
        mode_display = self.mode_var.get()
        mode_map = {"All Traffic": "C", "Aircraft": "A", "Group": "B"}
        mode = mode_map.get(mode_display, "C")

        filt = [v.strip() for v in self.filter_var.get().split(",") if v.strip()]
        self.monitor.set_filter(mode, filt)
        self.monitor.reset()
        self.store = EventStore(airport=airport)

        self._polling = True
        self._stop_event.clear()
        self.start_btn.config(text="Stop")
        self._set_status(f"Monitoring {airport_name(airport)} ({airport})")

        # Log with clearer filter description
        if mode == "A":
            self._log(f"--- Started monitoring {airport} (Filter: Aircraft={','.join(filt) if filt else 'all'}) ---")
        elif mode == "B":
            self._log(f"--- Started monitoring {airport} (Filter: Group={','.join(filt) if filt else 'all'}) ---")
        else:
            self._log(f"--- Started monitoring {airport} (Filter: All Traffic) ---")

        self._poll_thread = threading.Thread(
            target=self._poll_loop, args=(bbox, filt if mode == "A" else None), daemon=True
        )
        self._poll_thread.start()

    def _stop_polling(self):
        self._polling = False
        self._stop_event.set()
        self.start_btn.config(text="Start")
        self._log("--- Stopped ---")
        if len(self.store):
            path = self.store.save_csv()
            self._log(f"Events saved to {path}")

    def _poll_loop(self, bbox, icao24_filter):
        while not self._stop_event.is_set():
            try:
                states = self.client.get_states(bbox, icao24_filter=icao24_filter)
                events = self.monitor.process_states(states)

                # Record significant events
                for ev in events:
                    if ev["type"] in ("takeoff", "landing"):
                        self.store.record_event(ev)

                # Schedule UI update on the main thread
                self.root.after(0, self._update_ui, states, events)
            except Exception as exc:
                self.root.after(0, self._log, f"Poll error: {exc}")

            self._stop_event.wait(timeout=self.poll_var.get())

    # ---- UI updates (called on main thread) ----

    def _update_ui(self, states: list[dict], events: list[dict]):
        self._update_table(states)
        for ev in events:
            self._log_event(ev)
        rl = self.client.rate_limit_remaining if self.client else "?"
        now = datetime.datetime.now().strftime("%H:%M:%S")
        airport = self.airport_var.get().strip().upper()
        self._set_status(
            f"{airport_name(airport)} | Last poll: {now} | "
            f"Aircraft: {len(states)} | Rate limit remaining: {rl} | "
            f"Events recorded: {len(self.store)}"
        )

    def _update_table(self, states: list[dict]):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for s in states:
            # Apply the same filter the monitor uses
            if not self.monitor._matches_filter(s):
                continue
            self.tree.insert(
                "",
                tk.END,
                values=(
                    s.get("icao24", ""),
                    s.get("callsign", ""),
                    _fmt(s.get("baro_altitude")),
                    _fmt(s.get("velocity")),
                    _fmt(s.get("true_track")),
                    _fmt(s.get("vertical_rate")),
                    "Y" if s.get("on_ground") else "N",
                    s.get("category", ""),
                    s.get("origin_country", ""),
                ),
            )

    def _log_event(self, ev: dict):
        etype = ev["type"]
        tag = etype.upper()
        cs = ev.get("callsign") or "?"
        icao = ev.get("icao24") or "?"
        alt = _fmt(ev.get("altitude_m"))
        spd = _fmt(ev.get("velocity_ms"))
        ts = ev.get("timestamp", "")[:19]
        self._log(f"[{tag}] {ts}  {cs} ({icao})  alt={alt}m  spd={spd}m/s")

    def _log(self, text: str):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _set_status(self, text: str):
        self.status_var.set(text)

    # ---- CSV save ----

    def _save_csv(self):
        if len(self.store) == 0:
            messagebox.showinfo("Glycol", "No events to save.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if path:
            self.store.save_csv(path)
            self._log(f"Saved CSV to {path}")

    # ---- Cleanup ----

    def _on_close(self):
        self._stop_polling()
        self.root.destroy()


def _fmt(val) -> str:
    """Format a numeric value for display, returning '-' for None."""
    if val is None:
        return "-"
    if isinstance(val, float):
        return f"{val:.0f}"
    return str(val)


def run_app(
    airport: str = "",
    mode: str = "C",
    filter_text: str = "",
    data_dir: str = None,
    logs_dir: str = None,
):
    root = tk.Tk()
    app = GlycolApp(
        root,
        airport=airport,
        mode=mode,
        filter_text=filter_text,
        data_dir=data_dir,
        logs_dir=logs_dir,
    )
    root.protocol("WM_DELETE_WINDOW", app._on_close)
    root.mainloop()
