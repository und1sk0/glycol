# Changelog

All notable changes to Glycol will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-08

### Added

#### Core Features
- Real-time airport flight monitoring using OpenSky Network API
- Automatic takeoff and landing event detection within 5 NM radius
- Support for 2000+ US airports (commercial, military, GA, heliports)
- Three filtering options:
  - **Aircraft filter** (`--aircraft`) - Filter by ICAO24 address or tail number
  - **Group filter** (`--group`) - Filter by aircraft group name
  - **All traffic** (default) - Monitor all traffic
- Tkinter GUI with real-time aircraft table and event log
- CSV export of recorded events
- OAuth2 authentication with automatic token refresh
- API rate limit handling with exponential backoff
- Altitude ceiling filter (1500ft) for ground traffic detection

#### Background Operations
- **Background launcher script** (`glycol.sh`) for daemonized execution
- Automatic virtual environment activation
- Process detachment from terminal
- Timestamped log file generation

#### Structured Logging
- **JSON structured logging** for machine-readable output
- Dual output: human-readable console + JSON file logs
- Stored in `logs/` directory with automatic timestamping
- Easy parsing with `jq` for log analysis
- Separate log levels for debugging and production

#### Planes of Interest (POI) Database
- **Multi-category POI system** for tracking specific aircraft
- Store custom metadata: tail number, name, ICAO24, make/model, notes
- Multiple categories for organizing aircraft collections
- Default categories: `default` (empty) and `example` (historical aircraft)
- Automatic migration from legacy list format
- Category switching and management

#### Aircraft Groups & Glossary
- **Pre-populated aircraft type groups**:
  - `passenger` - 26 commercial airliners (A380, 777, 737, A320, etc.)
  - `cargo` - 10 freighter aircraft (747F, MD-11F, etc.)
  - `military_fighter` - 10 fighter jets (F-16, F-15, F-22, F-35, A-10)
  - `military_transport` - 10 military transports (C-130, C-17, KC-135, KC-46)
  - `coast_guard` - 5 Coast Guard aircraft
  - `business_jet` - 13 corporate jets (Gulfstream, Falcon, Citation, Challenger)
  - `general_aviation` - 10 GA aircraft (Cessna, Piper, Cirrus, Beechcraft)
  - `helicopter` - 12 rotary-wing aircraft (Robinson, Bell, Sikorsky, Airbus)

- **Comprehensive aircraft glossary** with 100+ type codes
  - Full make, model, and notes for each aircraft type
  - Examples: B77W (Boeing 777-300ER), A388 (Airbus A380-800), F22 (F-22 Raptor)
  - Searchable by code, make, model, or notes

#### Interactive Database Manager
- **Menu-driven interactive interface** (`python manage.py`)
- Three main sections:
  1. **Planes of Interest** - CRUD operations for tracked aircraft
  2. **Aircraft Groups** - Browse and manage type groups
  3. **Aircraft Glossary** - Search and explore aircraft types

- **CLI mode** for scripting and automation:
  ```bash
  python manage.py poi list
  python manage.py groups view passenger
  python manage.py glossary search "737"
  ```

- Features:
  - Numeric or text-based menu selection
  - Confirmation prompts for destructive operations
  - Visual feedback (✓/✗ symbols)
  - Category switching for POI
  - Search functionality for glossary
  - Group and aircraft type management

### Database Files

- `glycol/data/us_airports.json` - 2000+ US airport database
- `glycol/data/planes_of_interest.json` - POI database with categories
- `glycol/data/groups.json` - Aircraft groups and type glossary
- `glycol/data/credentials.json` - OAuth2 credentials (user-created)

### Project Structure

```
glycol/
  __main__.py            # Entry point
  main.py                # CLI argument parsing and logging setup
  api.py                 # OpenSky REST API client
  auth.py                # OAuth2 token management
  monitor.py             # Takeoff/landing event detection
  airports.py            # Airport database and bounding box math
  ui.py                  # Tkinter GUI
  events.py              # Event storage and CSV export
  poi.py                 # Planes of Interest database management
  groups.py              # Aircraft groups and glossary management
  data/                  # Data files (airports, POI, groups, credentials)

glycol.sh     # Background launcher script
manage.py     # Interactive database manager
logs/         # Application logs (JSON format)
```

### Requirements

- Python 3.10+
- OpenSky Network account with OAuth2 credentials
- tkinter (included with most Python installations)
- Dependencies: requests, requests-oauthlib (see requirements.txt)

### Usage Examples

#### Running Glycol

```bash
# Foreground with GUI
python -m glycol --airport KSFO

# Background with launcher
./glycol.sh --airport KJFK

# Filter by specific aircraft
python -m glycol --airport KORD --aircraft "A1B2C3,N456CD"

# Filter by aircraft group
python -m glycol --airport KLAX --group "passenger"
```

#### Managing Databases

```bash
# Interactive mode
python manage.py

# CLI mode - POI
python manage.py poi list
python manage.py --category example poi list
python manage.py poi add N12345 --name "My Plane"

# CLI mode - Groups
python manage.py groups list
python manage.py groups view passenger

# CLI mode - Glossary
python manage.py glossary search "Boeing"
python manage.py glossary get B77W
```

#### Log Analysis

```bash
# View all ERROR level logs
cat logs/glycol-*.log | jq 'select(.level == "ERROR")'

# Extract just messages
cat logs/glycol-*.log | jq -r '.message'

# Filter by timestamp
cat logs/glycol-*.log | jq 'select(.timestamp > "2026-02-08")'
```

### Documentation

- README.md - Comprehensive usage guide
- CHANGELOG.md - Version history and release notes
- Inline code documentation with docstrings

### Known Limitations

- OpenSky API rate limits (10 requests per 10 seconds for authenticated users)
- 5 NM radius limitation for airport monitoring
- US airports only (ICAO-coded airports in US and territories)
- Requires active internet connection
- Tkinter GUI dependency

### Attribution

- Airport data sourced from [OurAirports](https://ourairports.com/)
- Flight data from [OpenSky Network](https://opensky-network.org/)
- Aircraft type codes based on ICAO standards

---

## Release Information

**Version:** 1.0.0
**Release Date:** February 8, 2026
**Status:** Stable
**License:** MIT (if applicable)

**Contributors:**
- Initial development and feature implementation

**Special Thanks:**
- OpenSky Network for providing free API access
- OurAirports for comprehensive airport database

---

For questions, issues, or feature requests, please visit the project repository.
