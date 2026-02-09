# Glycol 1.0.0 Release Notes

**Release Date:** February 8, 2026

We're excited to announce the first stable release of Glycol, a real-time airport flight monitoring system built on the OpenSky Network API.

## 🎯 What is Glycol?

Glycol tracks aircraft around any of 2000+ US airports, automatically detects takeoff and landing events, and provides comprehensive database management for planes of interest and aircraft type groups.

## ✨ Key Features

### Real-Time Flight Monitoring
- Track aircraft within 5 NM radius of any US airport
- Automatic takeoff and landing event detection
- Three filtering modes: ICAO24/callsign, category code, or all traffic
- Live Tkinter GUI with aircraft table and event log
- CSV export of recorded events
- 1500ft altitude ceiling filter for ground traffic

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
```bash
# Foreground
python -m glycol --airport KSFO

# Background
./glycol.sh --airport KJFK

# With filtering
python -m glycol --airport KORD --mode A --filter "ABC123,DEF456"
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
- tkinter (usually pre-installed)
- Internet connection

## 📚 Documentation

- **README.md** - Comprehensive usage guide
- **CHANGELOG.md** - Detailed version history
- Inline code documentation throughout

## 🗄️ Database Files

All databases are stored in `glycol/data/`:
- `us_airports.json` - 2000+ US airports
- `planes_of_interest.json` - POI database
- `groups.json` - Aircraft groups and glossary
- `credentials.json` - Your OAuth2 credentials (create this)

## 🎯 Use Cases

- **Aviation Enthusiasts** - Track specific aircraft and monitor local airports
- **Researchers** - Collect and analyze flight pattern data
- **Spotters** - Get notified of interesting aircraft movements
- **Developers** - Build on Glycol's APIs and databases

## 🔧 What's Next?

Future enhancements being considered:
- Web-based UI
- Notification system (email, SMS, webhooks)
- Historical data analysis
- Custom alert rules
- International airport support
- Enhanced filtering options

## 🙏 Acknowledgments

- **OpenSky Network** - Free flight data API
- **OurAirports** - Comprehensive airport database
- Aviation community for aircraft type information

## 📝 License

MIT License (if applicable)

---

**Questions or issues?** Visit the project repository or open an issue.

**Want to contribute?** Pull requests welcome!

**Enjoying Glycol?** Star the repository and share with fellow aviation enthusiasts!

---

*Version 1.0.0 - First Stable Release*
