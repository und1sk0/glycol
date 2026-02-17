import datetime
import re
import threading
import tkinter as tk
import webbrowser
from tkinter import ttk, messagebox, filedialog, simpledialog

from glycol.auth import OpenSkyAuth, load_credentials_from_file
from glycol.api import OpenSkyClient
from glycol.aircraft import REG_TO_ICAO24, ICAO24_TO_TYPE
from glycol.airports import get_bounding_box, airport_name
from glycol.monitor import AircraftMonitor
from glycol.events import EventStore
from glycol.groups import GroupsDatabase

_ICAO24_RE = re.compile(r"^[0-9a-fA-F]{6}$")


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

    def __init__(
        self,
        root: tk.Tk,
        airport: str = "",
        mode: str | None = None,
        filter_text: str = "",
        data_dir: str | None = None,
        logs_dir: str | None = None,
        poll_interval: int = 30,
    ):
        self.poll_interval = poll_interval
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
        self.groups_db = GroupsDatabase(data_dir=data_dir)
        self.monitor = AircraftMonitor(filter_mode=None, icao_to_type=ICAO24_TO_TYPE)
        self.store = EventStore(logs_dir=logs_dir)
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

    # -------------------------
    # Filter resolution (FIX)
    # -------------------------

    @staticmethod
    def _dedupe_preserve_order(values: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for v in values:
            if v not in seen:
                seen.add(v)
                out.append(v)
        return out

    def _parse_filter_values(self) -> list[str]:
        return [v.strip() for v in self.filter_var.get().split(",") if v.strip()]

    def _resolve_group_filter(self, raw_values: list[str]) -> list[str]:
        """
        Resolve type group names and individual type codes to a list of type codes.

        Args:
            raw_values: List of type group names and/or type codes (e.g., ["passenger", "B738"])

        Returns:
            List of type codes to filter by (e.g., ["A388", "B738", ...])
        """
        type_codes: list[str] = []

        for value in raw_values:
            value_upper = value.strip().upper()
            if not value_upper:
                continue

            # Check if it's a type group name (e.g., "passenger", "cargo")
            group_types = self.groups_db.get_group(value_upper.lower())
            if group_types:
                # It's a type group - expand to all type codes in the group
                type_codes.extend([t.upper() for t in group_types])
            else:
                # Assume it's an individual type code
                type_codes.append(value_upper)

        return self._dedupe_preserve_order(type_codes)

    def _resolve_aircraft_filter(
        self, raw_values: list[str]
    ) -> tuple[list[str] | None, list[str]]:
        """
        Returns (api_icao24_filter, monitor_filter_values).

        - api_icao24_filter: ONLY ICAO24 hex strings (lowercased) safe to pass to OpenSky.
                            None means "do not API-filter; fetch all in bbox and filter locally."
        - monitor_filter_values: what the monitor should match against (ICAO24 + callsign + reg),
                                 normalized reasonably.
        """
        api_icao24: list[str] = []
        monitor_values: list[str] = []

        for token in raw_values:
            t = token.strip()
            if not t:
                continue

            # 1) ICAO24 hex directly
            if _ICAO24_RE.match(t):
                api_icao24.append(t.lower())
                monitor_values.append(t.lower())
                continue

            # 2) Try registration (tail) -> ICAO24 via local mapping
            reg = t.upper()
            monitor_values.append(reg)

            icao = REG_TO_ICAO24.get(reg)
            if isinstance(icao, str) and icao:
                api_icao24.append(icao.lower())
                monitor_values.append(icao.lower())
                continue

            # 3) Otherwise treat as callsign (matched locally by monitor)
            monitor_values.append(reg)

        api_icao24 = self._dedupe_preserve_order(api_icao24)
        monitor_values = self._dedupe_preserve_order(monitor_values)

        return (api_icao24 or None), monitor_values

    # ---- UI construction ----

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(
            label="Set Credentials...", command=self._prompt_credentials
        )
        file_menu.add_command(label="Save CSV...", command=self._save_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self._on_close)
        menubar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menubar)

    def _build_config_panel(self, airport: str, mode: str | None, filter_text: str):
        frame = ttk.LabelFrame(self.root, text="Configuration", padding=6)
        frame.pack(fill=tk.X, padx=6, pady=(6, 3))

        # Airport
        ttk.Label(frame, text="Airport ICAO:").grid(row=0, column=0, sticky=tk.W)
        self.airport_var = tk.StringVar(value=airport)
        ttk.Entry(frame, textvariable=self.airport_var, width=8).grid(
            row=0, column=1, padx=4
        )

        # Filter Type
        ttk.Label(frame, text="Filter:").grid(
            row=0, column=2, sticky=tk.W, padx=(12, 0)
        )
        # Map internal mode to display value
        mode_display = {None: "All Traffic", "aircraft": "Aircraft", "type_group": "Type Group"}
        self.mode_var = tk.StringVar(value=mode_display.get(mode, "All Traffic"))
        mode_combo = ttk.Combobox(
            frame,
            textvariable=self.mode_var,
            values=["All Traffic", "Aircraft", "Type Group"],
            state="readonly",
            width=12,
        )
        mode_combo.grid(row=0, column=3, padx=4)

        # Filter Value
        ttk.Label(frame, text="Value:").grid(row=0, column=4, sticky=tk.W, padx=(12, 0))
        self.filter_var = tk.StringVar(value=filter_text)
        ttk.Entry(frame, textvariable=self.filter_var, width=30).grid(
            row=0, column=5, padx=4
        )

        # Poll interval
        ttk.Label(frame, text="Poll (s):").grid(
            row=0, column=6, sticky=tk.W, padx=(12, 0)
        )
        self.poll_var = tk.IntVar(value=self.poll_interval)
        ttk.Spinbox(frame, from_=5, to=120, textvariable=self.poll_var, width=5).grid(
            row=0, column=7, padx=4
        )

        # Start / Stop
        self.start_btn = ttk.Button(frame, text="Start", command=self._toggle_polling)
        self.start_btn.grid(row=0, column=8, padx=(12, 0))

    def _build_aircraft_table(self):
        frame = ttk.LabelFrame(self.root, text="Aircraft in Range", padding=4)
        frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=3)

        cols = (
            "icao24",
            "callsign",
            "alt_m",
            "speed_ms",
            "heading",
            "vrate",
            "on_ground",
            "category",
            "country",
        )
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

        # Bind double-click and right-click to open ICAO24 link
        self.tree.bind("<Double-Button-1>", self._on_table_double_click)
        self.tree.bind("<Button-2>", self._on_table_right_click)  # macOS right-click
        self.tree.bind("<Button-3>", self._on_table_right_click)  # Windows/Linux right-click
        self.tree.bind("<Control-Button-1>", self._on_table_right_click)  # macOS ctrl-click
        self.tree.bind("<Motion>", self._on_table_motion)

    def _build_event_log(self):
        frame = ttk.LabelFrame(self.root, text="Event Log", padding=4)
        frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=3)

        self.log_text = tk.Text(frame, height=8, state=tk.DISABLED, wrap=tk.WORD)
        sb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=sb.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure tag for clickable ICAO24 links
        self.log_text.tag_config("icao24_link", foreground="blue", underline=True)
        self.log_text.tag_bind("icao24_link", "<Button-1>", self._on_log_icao_click)
        self.log_text.tag_bind("icao24_link", "<Enter>", lambda e: self.log_text.config(cursor="hand2"))
        self.log_text.tag_bind("icao24_link", "<Leave>", lambda e: self.log_text.config(cursor=""))

    def _build_status_bar(self):
        self.status_var = tk.StringVar(value="Not authenticated")
        bar = ttk.Label(
            self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W
        )
        bar.pack(fill=tk.X, padx=6, pady=(0, 6))

    # ---- ICAO24 Link Handlers ----

    def _open_icao24_link(self, icao24: str):
        """Prompt user to choose which site to open for the ICAO24."""
        icao24_lower = icao24.lower()

        # Create a simple dialog for the user to choose
        choice = messagebox.askquestion(
            "Open ICAO24 Link",
            f"Open {icao24} in:\n\nYes = OpenSky Network\nNo = ADSB-Exchange",
            icon='question'
        )

        if choice == 'yes':
            url = f"https://opensky-network.org/network/explorer?icao24={icao24_lower}"
        else:
            url = f"https://globe.adsbexchange.com/?icao={icao24_lower}"

        webbrowser.open(url)

    def _on_table_double_click(self, event):
        """Handle double-click on aircraft table to open ICAO24 link."""
        item = self.tree.identify_row(event.y)
        if item:
            values = self.tree.item(item, "values")
            if values:
                icao24 = values[0]  # ICAO24 is the first column
                if icao24 and _ICAO24_RE.match(icao24):
                    # Go directly to ADSB-Exchange
                    url = f"https://globe.adsbexchange.com/?icao={icao24.lower()}"
                    webbrowser.open(url)

    def _on_table_right_click(self, event):
        """Handle right-click on aircraft table to show context menu."""
        item = self.tree.identify_row(event.y)
        if item:
            # Select the row
            self.tree.selection_set(item)
            values = self.tree.item(item, "values")
            if values:
                icao24 = values[0]
                if icao24 and _ICAO24_RE.match(icao24):
                    # Create context menu
                    menu = tk.Menu(self.root, tearoff=0)
                    menu.add_command(
                        label=f"Open {icao24} in OpenSky Network",
                        command=lambda: self._open_icao24_direct(icao24, "opensky")
                    )
                    menu.add_command(
                        label=f"Open {icao24} in ADSB-Exchange",
                        command=lambda: self._open_icao24_direct(icao24, "adsbex")
                    )
                    menu.post(event.x_root, event.y_root)

    def _on_table_motion(self, event):
        """Show tooltip when hovering over ICAO24 column."""
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            # Column #0 is the first visible column (ICAO24)
            if column == "#1":
                self.tree.config(cursor="hand2")
                item = self.tree.identify_row(event.y)
                if item:
                    values = self.tree.item(item, "values")
                    if values and values[0]:
                        self._set_status(f"Double-click ICAO24 to open in ADSB-Exchange")
            else:
                self.tree.config(cursor="")
        else:
            self.tree.config(cursor="")

    def _open_icao24_direct(self, icao24: str, site: str):
        """Open ICAO24 link directly to specified site."""
        icao24_lower = icao24.lower()
        if site == "opensky":
            url = f"https://opensky-network.org/network/explorer?icao24={icao24_lower}"
        else:  # adsbex
            url = f"https://globe.adsbexchange.com/?icao={icao24_lower}"
        webbrowser.open(url)

    def _on_log_icao_click(self, event):
        """Handle click on ICAO24 link in event log."""
        # Get the index of the click
        index = self.log_text.index(f"@{event.x},{event.y}")

        # Get all tags at this position
        tags = self.log_text.tag_names(index)

        # Find the ICAO24 tag (format: icao24_XXXXXX)
        for tag in tags:
            if tag.startswith("icao24_") and tag != "icao24_link":
                icao24 = tag.split("_", 1)[1]
                if _ICAO24_RE.match(icao24):
                    # Go directly to ADSB-Exchange
                    url = f"https://globe.adsbexchange.com/?icao={icao24.lower()}"
                    webbrowser.open(url)
                    break

    # ---- Credentials ----

    def _auto_authenticate(self):
        credentials = load_credentials_from_file(data_dir=self.data_dir)
        if credentials:
            client_id, client_secret = credentials
            self.auth = OpenSkyAuth(client_id, client_secret)
            self._set_status("Authenticating with saved credentials...")
            threading.Thread(target=self._do_auth, daemon=True).start()
        else:
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
            threading.Thread(target=self._do_auth, daemon=True).start()

    def _do_auth(self):
        ok = self.auth.authenticate()
        if ok:
            self.client = OpenSkyClient(self.auth)
            self.root.after(0, lambda: self._set_status("Authenticated"))
        else:
            self.root.after(
                0, lambda: self._set_status("Authentication failed - check credentials")
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

        # Map display value to internal filter mode
        mode_display = self.mode_var.get()
        display_to_mode = {"All Traffic": None, "Aircraft": "aircraft", "Type Group": "type_group"}
        filter_mode = display_to_mode.get(mode_display)

        raw_filt = self._parse_filter_values()

        # Compute the API filter and the monitor filter separately.
        api_icao24_filter: list[str] | None = None
        filt_for_monitor: list[str] = raw_filt

        if filter_mode == "aircraft":
            api_icao24_filter, filt_for_monitor = self._resolve_aircraft_filter(
                raw_filt
            )
        elif filter_mode == "type_group":
            # Resolve type group names to type codes
            filt_for_monitor = self._resolve_group_filter(raw_filt)

        self.monitor.set_filter(filter_mode, filt_for_monitor)
        self.monitor.reset()
        self.store = EventStore(airport=airport, logs_dir=self.logs_dir)

        self._polling = True
        self._stop_event.clear()
        self.start_btn.config(text="Stop")
        self._set_status(f"Monitoring {airport_name(airport)} ({airport})")

        if filter_mode == "aircraft":
            self._log(
                f"--- Started monitoring {airport} (Filter: Aircraft={','.join(raw_filt) if raw_filt else 'all'}) ---"
            )
        elif filter_mode == "type_group":
            self._log(
                f"--- Started monitoring {airport} (Filter: Type Group={','.join(raw_filt) if raw_filt else 'all'}) ---"
            )
        else:
            self._log(f"--- Started monitoring {airport} (Filter: All Traffic) ---")

        self._poll_thread = threading.Thread(
            target=self._poll_loop,
            args=(bbox, api_icao24_filter if filter_mode == "aircraft" else None, airport),
            daemon=True,
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

    def _poll_loop(self, bbox, icao24_filter, airport=""):
        while not self._stop_event.is_set():
            try:
                states = self.client.get_states(bbox, icao24_filter=icao24_filter)
                events = self.monitor.process_states(states, airport=airport)

                for ev in events:
                    if ev["type"] in ("takeoff", "landing"):
                        self.store.record_event(ev)

                self.root.after(0, self._update_ui, states, events)
            except Exception as exc:
                self.root.after(0, self._log, f"Poll error: {exc}")

            self._stop_event.wait(timeout=self.poll_var.get())

    # ---- UI updates ----

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
            if not self.monitor._matches_filter(s):
                continue

            self.tree.insert(
                "",
                tk.END,
                values=(
                    s.get("icao24", ""),
                    (s.get("callsign") or "").strip(),
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
        airport = ev.get("airport", "")

        # Look up type code
        type_code = ICAO24_TO_TYPE.get(icao.lower(), "?")

        # Build message with clickable ICAO24
        airport_str = f"  [{airport}]" if airport else ""
        prefix = f"[{tag}] {ts}{airport_str}  {cs} ("
        suffix = f")  {type_code}  alt={alt}m  spd={spd}m/s"

        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, prefix)

        # Insert ICAO24 with clickable tags if valid
        if _ICAO24_RE.match(icao):
            start_idx = self.log_text.index(tk.END + "-1c")
            self.log_text.insert(tk.END, icao)
            end_idx = self.log_text.index(tk.END + "-1c")
            # Apply both the general link style and a unique tag with the ICAO24
            self.log_text.tag_add("icao24_link", start_idx, end_idx)
            self.log_text.tag_add(f"icao24_{icao}", start_idx, end_idx)
        else:
            self.log_text.insert(tk.END, icao)

        self.log_text.insert(tk.END, suffix + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

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
    data_dir: str | None = None,
    filter_text: str = "",
    logs_dir: str | None = None,
    mode: str | None = None,
    poll_interval: int = 30,
):
    root = tk.Tk()
    app = GlycolApp(
        root,
        airport=airport,
        data_dir=data_dir,
        filter_text=filter_text,
        logs_dir=logs_dir,
        mode=mode,
        poll_interval=poll_interval,
    )
    root.protocol("WM_DELETE_WINDOW", app._on_close)
    root.mainloop()
