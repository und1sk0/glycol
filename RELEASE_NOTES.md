# Glycol 2.0.0 Release Notes

**Release Date:** February 13, 2026

We're excited to announce Glycol 2.0.0, featuring a brand-new **browser-based web interface** alongside the existing desktop GUI. This major release brings modern web technology to Glycol's real-time airport flight monitoring capabilities.

## 🎯 What is Glycol?

Glycol tracks aircraft around any of 2000+ US airports, automatically detects takeoff and landing events, and provides comprehensive database management for planes of interest and aircraft type groups.

## ✨ What's New in 2.0.0

### 🌐 Web Interface (NEW!)

The star feature of v2.0.0 is the **browser-based web interface** - a modern alternative to the desktop GUI:

- **Real-Time Updates** - Server-Sent Events (SSE) push updates to your browser instantly
- **Network Accessible** - Access from any device on your network with `--host 0.0.0.0`
- **No Authentication Required** - Web UI uses your backend credentials automatically
- **Responsive Design** - Beautiful purple gradient theme that works on desktop and mobile
- **Live Aircraft Table** - See all aircraft in the area with automatic updates
- **Live Event Log** - Watch takeoffs and landings happen in real-time
- **CSV Export** - Download event logs directly from your browser
- **Clickable ICAO24 Links** - One-click access to aircraft on ADSB-Exchange
- **All Filtering Options** - Aircraft filter, type group filter, and all traffic modes available

#### Quick Start (Web Interface)
```bash
# Start the web server
./start_web.sh --airport KSFO

# Or with Python
python web_server.py --airport KSFO --port 8080

# Access from other devices on your network
python web_server.py --airport KJFK --host 0.0.0.0
```

Then open your browser to `http://localhost:8080`

#### New Files
- `glycol/web.py` - Flask application with SSE streaming (315 lines)
- `glycol/templates/index.html` - Web interface template (97 lines)
- `glycol/static/style.css` - Responsive styling (297 lines)
- `glycol/static/app.js` - Client-side JavaScript (267 lines)
- `web_server.py` - Web server launcher script (63 lines)
- `start_web.sh` - Quick start shell script (22 lines)
- `WEB_README.md` - Comprehensive web interface documentation (186 lines)

#### Technical Architecture
- **Backend**: Flask with threading for concurrent API polling and SSE broadcasting
- **Frontend**: Vanilla JavaScript (no frameworks) with EventSource for SSE
- **Real-Time**: Server-Sent Events for push updates from server to browser
- **Polling**: Background thread queries OpenSky API at configured interval
- **Broadcasting**: Events pushed to all connected browser clients simultaneously

## ✨ Core Features

### Real-Time Flight Monitoring
- Track aircraft within 5 NM radius of any US airport
- Automatic takeoff and landing event detection
- Three filtering options: aircraft (ICAO24/tail), type group, or all traffic
- **Two User Interfaces**: Modern web UI or classic Tkinter desktop GUI
- CSV export of recorded events
- 1500ft altitude ceiling filter for ground traffic
- Clickable ICAO24 links to ADSB-Exchange for live tracking

### Background Operations
- Daemonized execution with `glycol.sh` launcher
- Automatic virtual environment activation
- Timestamped JSON log files for easy parsing

### Structured Logging
- Machine-readable JSON logs in `logs/` directory
- Human-readable console output
- Easy analysis with `jq` and other tools
- Separate log levels for debugging

### Database Management

#### Planes of Interest (POI)
- Track specific aircraft with custom metadata
- Multi-category organization (default, example, custom)
- Store tail number, name, ICAO24, make/model, notes
- Automatic format migration

#### Aircraft Type Filtering
- **ICAO24 → Type Code Mapping** - 488,320+ aircraft type mappings from ADS-B Exchange
- **Tail Number → ICAO24 Conversion** - 613,253 registration-to-ICAO24 mappings
- **Type Group Filter** - Filter by aircraft categories (passenger, cargo, military, etc.)
- **Mixed Filter Support** - Combine type groups and individual codes

#### Aircraft Groups & Glossary
- 8 pre-populated aircraft groups:
  - **Passenger** (26 types) - A380, 777, 737, A320, etc.
  - **Cargo** (10 types) - 747F, MD-11F, etc.
  - **Military Fighter** (10 types) - F-16, F-15, F-22, F-35
  - **Military Transport** (10 types) - C-130, C-17, KC-135
  - **Coast Guard** (5 types)
  - **Business Jet** (13 types) - Gulfstream, Falcon, Citation
  - **General Aviation** (10 types) - Cessna, Piper, Cirrus
  - **Helicopter** (12 types) - Robinson, Bell, Sikorsky

- Comprehensive glossary with 100+ aircraft type codes
- Full make, model, and notes for each type
- Searchable by code, manufacturer, or keyword

#### Interactive Management
- Menu-driven interface: `python manage.py`
- CLI mode for scripting and automation
- CRUD operations for POI, groups, and glossary
- Search, browse, and manage all databases

## 🚀 Quick Start

### Installation
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running Glycol

#### Web Interface (Recommended)
```bash
# Quick start
./start_web.sh --airport KSFO

# Custom port
python web_server.py --airport KJFK --port 8080

# Network accessible
python web_server.py --airport KORD --host 0.0.0.0

# With filtering
python web_server.py --airport KSEA --aircraft "ABC123,DEF456"
python web_server.py --airport KDFW --group passenger
```

#### Desktop GUI
```bash
# Foreground
python -m glycol --airport KSFO

# Background
./glycol.sh --airport KJFK

# With filtering
python -m glycol --airport KORD --aircraft "ABC123,DEF456"
python -m glycol --airport KSEA --group passenger,cargo
```

### Managing Databases
```bash
# Interactive mode
python manage.py

# CLI examples
python manage.py poi list
python manage.py groups view passenger
python manage.py glossary search "Boeing"
```

### Analyzing Logs
```bash
# View errors
cat logs/glycol-*.log | jq 'select(.level == "ERROR")'

# Extract messages
cat logs/glycol-*.log | jq -r '.message'
```

## 📋 Requirements

- Python 3.10+
- OpenSky Network account (free)
- tkinter (for desktop GUI, usually pre-installed)
- Flask (for web interface, installed via requirements.txt)
- Internet connection

## 📚 Documentation

- **README.md** - Comprehensive usage guide
- **WEB_README.md** - Web interface documentation
- **CHANGELOG.md** - Detailed version history
- Inline code documentation throughout

## 🗄️ Database Files

All databases are stored in `glycol/data/`:
- `us_airports.json` - 2000+ US airports
- `planes_of_interest.json` - POI database
- `type_groups.json` - Aircraft groups and glossary
- `credentials.json` - Your OAuth2 credentials (create this)
- `basic-ac-db.json.gz` - ADS-B Exchange aircraft database (auto-downloaded)

## 🎯 Use Cases

- **Aviation Enthusiasts** - Track specific aircraft and monitor local airports
- **Researchers** - Collect and analyze flight pattern data
- **Spotters** - Get notified of interesting aircraft movements
- **Developers** - Build on Glycol's APIs and databases
- **Remote Monitoring** - Access from any device on your network via web browser

## 🔧 What's Next?

Future enhancements being considered:
- Notification system (email, SMS, webhooks)
- Historical data analysis
- Custom alert rules
- International airport support
- Enhanced filtering options
- Mobile app integration
- Multi-airport monitoring

## 🙏 Acknowledgments

- **OpenSky Network** - Free flight data API
- **OurAirports** - Comprehensive airport database
- **ADS-B Exchange** - Aircraft database with type codes and registrations
- Aviation community for aircraft type information

## 📝 License

MIT License

---

**Questions or issues?** Visit the project repository or open an issue.

**Want to contribute?** Pull requests welcome!

**Enjoying Glycol?** Star the repository and share with fellow aviation enthusiasts!

---

*Version 2.0.0 - Web Interface Release*
