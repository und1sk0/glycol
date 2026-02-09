# Changelog

All notable changes to Glycol will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-02-08

### Added

#### Aircraft Type Code Filtering
- **ICAO24 → Type Code Mapping** - Integrated ADS-B Exchange aircraft database with 488,320+ type code mappings
- **Type Group Filter** - Filter aircraft by type groups (passenger, cargo, military, etc.) or individual type codes
- **Automatic Database Download** - Aircraft database downloaded automatically on first run
- **Smart Type Resolution** - Resolves type group names to lists of type codes (e.g., "passenger" → 26 aircraft types)
- **Mixed Filter Support** - Combine type groups and individual codes (e.g., "passenger,F22,B738")

#### Enhanced Aircraft Filter
- **Tail Number → ICAO24 Conversion** - Automatically converts registration numbers to ICAO24 for API filtering
- **REG_TO_ICAO24 Mapping** - 613,253 registration-to-ICAO24 mappings from ADS-B Exchange
- **Intelligent Filter Resolution** - Detects ICAO24 hex codes, tail numbers, and callsigns automatically
- **API Filter Optimization** - Only sends ICAO24 codes to OpenSky API, filters callsigns locally

### Changed

#### Code Refactoring & Clarity
- **Filter Mode Naming** - Removed cryptic MODE_A/B/C in favor of clear names:
  - `None` (all traffic)
  - `"aircraft"` (specific aircraft)
  - `"type_group"` (aircraft types)
- **Terminology Standardization** - "Group" → "Type Group" throughout UI and documentation to avoid confusion with OpenSky API fields
- **Module Organization** - New `aircraft.py` module for aircraft data management
- **Type Hints Improved** - Better type annotations for filter modes and parameters

### Fixed
- **Download User-Agent** - Added User-Agent header to ADS-B Exchange downloads to prevent 403 errors
- **Filter Resolution** - Proper separation of API filters (ICAO24 only) vs. local filters (ICAO24 + callsigns)

### Technical Details

#### New Files
- `glycol/aircraft.py` - Aircraft database management and lookups
- `glycol/data/basic-ac-db.json.gz` - ADS-B Exchange aircraft database (auto-downloaded)

#### Updated Files
- `glycol/monitor.py` - Refactored filter modes, added type code filtering
- `glycol/ui.py` - Type group resolution, improved filter logic
- `glycol/main.py` - Updated mode naming
- `README.md` - Updated terminology and documentation

#### Database Statistics
- **613,253** registration → ICAO24 mappings
- **488,320** ICAO24 → type code mappings
- **100+** aircraft types in glossary
- **8** pre-defined type groups

## [1.1.2] - 2026-02-08

### Added
- **`--interval` CLI Flag** - Set polling interval from command line (5-120 seconds)
- **UI Poll Control** - Adjustable poll interval via GUI spinbox
- **Default Changed** - Poll interval default changed from 10s to 30s

## [1.1.1] - 2026-02-08

### Fixed
- `glycol.sh -h` does not launch into the background; it prints the help docstring and exits
- Changelog version drift corrected

## [1.1.0] - 2026-02-08

### Changed
- **Improved Filter Mode Terminology** - Made filtering modes more intuitive in UI and CLI
- **Enhanced Mode Selection** - Better display names for filter types in GUI dropdown
- **Documentation Updates** - Clarified filter mode usage in README and release notes

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

- **CLI mode** for scripting and automation
- Features:
  - Numeric or text-based menu selection
  - Confirmation prompts for destructive operations
  - Visual feedback (✓/✗ symbols)
  - Category switching for POI
  - Search functionality for glossary
  - Group and aircraft type management

## [0.1.1] - 2026-02-08

### Fixed
- Documentation files that weren't committed in initial release

## [0.1.0] - 2026-02-08

### Added
- Initial OpenSky airport monitor implementation
- Support for 2000+ US airports from OurAirports dataset
- 1500ft altitude ceiling filter for ground traffic
- Basic GUI with aircraft table and event log
- OAuth2 authentication
- CSV event export
- Project README and documentation

---

## Release Information

**Version:** 1.2.0
**Release Date:** February 8, 2026
**Status:** Stable

**Contributors:**
- Initial development and feature implementation

**Special Thanks:**
- OpenSky Network for providing free API access
- OurAirports for comprehensive airport database
- ADS-B Exchange for aircraft database

---

For questions, issues, or feature requests, please visit the project repository.
