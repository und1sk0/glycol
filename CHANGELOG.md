# Changelog

All notable changes to Glycol will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2026-02-19

### Added
- **Configurable Monitoring Parameters** - All core monitoring parameters now configurable via Helm chart
  - `config.pollInterval` - API polling interval in seconds (default: 10)
  - `config.radiusNm` - Monitoring radius in nautical miles from airport (default: 5)
  - `config.ceilingFt` - Altitude ceiling in feet for tracking aircraft (default: 1500)
  - Environment variables: `POLL_INTERVAL`, `RADIUS_NM`, `CEILING_FT`
  - Command-line arguments: `--poll-interval`, `--radius-nm`, `--ceiling-ft`

### Changed
- **Port Standardization** - All remaining port 5000 references updated to 8666
  - Updated `web_server.py` default port to 8666
  - Updated `glycol/web.py` default port to 8666
  - Updated `start_web.sh` default port to 8666
  - Updated all documentation (WEB_README.md, DOCKER.md, charts/glycol/README.md)

### Improved
- **Environment Variable Support** - Web server now reads configuration from environment variables
  - `HOST` and `PORT` now read from environment with proper defaults
  - All monitoring parameters configurable via environment or CLI args
  - Enables runtime configuration without code changes

## [2.1.2] - 2026-02-19

### Changed
- **Helm Chart Consolidation** - Removed raw Kubernetes manifests (`k8s/` directory) in favor of Helm-only deployment
  - Helm chart is now the canonical deployment method
  - Updated README to reference only Helm deployment
  - Renamed deployment examples to use `charts/` path

### Improved
- **Fully Templatized Helm Chart** - All hard-coded values moved to `values.yaml`
  - Added `credentials.mountPath` for configurable credential file path
  - Added `persistence.mountPath` for configurable log directory path
  - Added `strategy.type` and `strategy.rollingUpdate` for configurable deployment strategy
  - Secret name now uses `glycol.secretName` helper consistently
  - PVC name now uses `glycol.pvcName` helper consistently
  - Removed redundant if/else blocks in deployment template

### Fixed
- **Credentials Format Bug** - Fixed secret template to use `clientId`/`clientSecret` (camelCase) instead of `client_id`/`client_secret` (snake_case)
  - This bug prevented authentication in Kubernetes deployments
  - App expects camelCase keys per OpenSky API requirements
- **Helm Chart Version** - Updated `Chart.yaml` appVersion from 2.1.0 to 2.1.1
- **Deployment Scripts** - Updated `charts/deploy-helm.sh` to use correct image version (2.1.1) and port (8666)

### Removed
- **Raw Kubernetes Manifests** - Deleted `k8s/` directory and all raw YAML files
  - `k8s/deployment.yaml`
  - `k8s/service.yaml`
  - `k8s/ingress.yaml`
  - `k8s/secret.yaml`
  - `k8s/namespace.yaml`
  - `k8s/deploy.sh`
  - `k8s/README.md`

## [2.1.1] - 2026-02-16

### Added
- **Airport code in event log** - Each takeoff/landing event now includes the monitored airport code
  - Desktop GUI event log shows `[KSFO]` tag in each event line
  - Web UI event log shows `@ KSFO` next to the event type (e.g. `🛫 Takeoff @ KSFO`)
  - Airport code included in event dicts from `AircraftMonitor.process_states()` and serialized through the web API

## [2.1.0] - 2026-02-14

### Added

#### Docker Support
- **Multi-Stage Dockerfile** - Optimized Alpine Linux build for minimal image size (~240MB)
  - Stage 1: Build dependencies with compilation tools
  - Stage 2: Runtime-only environment with stripped-down image
  - Non-root user execution (glycol, UID 1000)
  - Default port: 8666 (configurable via environment variables)
- **Docker Compose Configuration** - Simple deployment with `docker compose up`
- **Health Check Endpoints** - Kubernetes/Docker-ready probes
  - `/healthz/live` - Liveness probe (returns 200 if app is running)
  - `/healthz/ready` or `/healthz` - Readiness probe (returns 200 if authenticated, 503 if not)
- **Comprehensive Documentation** - `DOCKER.md` with deployment guides
  - Docker run examples with volume mounts
  - Docker Compose usage
  - Kubernetes deployment manifests with liveness/readiness probes
  - Security best practices (non-root, read-only credentials)
  - Production deployment considerations

#### Kubernetes Support
- **Helm Chart** - Production-ready Helm chart in `charts/glycol/`
  - Configurable credentials (inline or existing secret)
  - Optional ingress with TLS support
  - Horizontal Pod Autoscaling (HPA)
  - Persistent volume support for logs
  - ServiceAccount with configurable permissions
  - Resource limits and requests
  - Pod security contexts
- **Kubernetes Manifests** - Raw manifests in `k8s/` directory
  - Namespace isolation
  - Deployment with rolling updates
  - Service (ClusterIP)
  - Ingress example
  - Secret management
  - Deployment scripts
- **Kubernetes Documentation** - `k8s/README.md` with deployment guides
  - Minikube, kind, and k3s examples
  - Production deployment best practices
  - Troubleshooting guide

#### New Files
- `Dockerfile` - Multi-stage Alpine build with health checks
- `.dockerignore` - Optimized build context
- `docker-compose.yml` - Simple deployment configuration
- `DOCKER.md` - Comprehensive Docker and Kubernetes documentation
- `charts/glycol/Chart.yaml` - Helm chart metadata
- `charts/glycol/values.yaml` - Default Helm values
- `charts/glycol/templates/*` - Helm templates (deployment, service, ingress, etc.)
- `charts/glycol/README.md` - Helm chart documentation
- `charts/deploy-helm.sh` - Automated Helm deployment script
- `k8s/namespace.yaml` - Kubernetes namespace
- `k8s/deployment.yaml` - Kubernetes deployment
- `k8s/service.yaml` - Kubernetes service
- `k8s/ingress.yaml` - Kubernetes ingress example
- `k8s/secret.yaml` - Kubernetes secret template
- `k8s/deploy.sh` - Automated Kubernetes deployment script
- `k8s/README.md` - Kubernetes deployment documentation

#### Features
- **Containerized Deployment** - Run Glycol web interface in Docker/Kubernetes
- **Health Monitoring** - Built-in liveness and readiness probes
- **Minimal Image Size** - Alpine-based build (~240MB vs ~1GB standard Python)
- **Security Hardening** - Non-root execution, read-only credential mounts
- **Port Standardization** - Consistent port 8666 for all external access
- **Production Ready** - Helm chart with HPA, ingress, and resource management
- **Flexible Secret Management** - Support for inline credentials, existing secrets, or External Secrets Operator

### Changed
- **Web Server** - Added health check endpoints for container orchestration
- **Port Configuration** - Standardized on port 8666 for external access (was 5000)
  - Container runs on 8666
  - Service exposes 8666
  - Port-forward uses 8666:8666
  - Docker uses -p 8666:8666
- **Import Structure** - Made tkinter import lazy to support headless container environments
  - Moved UI import from module level to function level in `glycol/main.py`
  - Prevents ImportError when running web server in containers without GUI libraries

### Fixed
- **Container Compatibility** - Fixed tkinter import error in headless Docker environments

## [2.0.0] - 2026-02-13

### Added

#### Web Interface
- **Browser-Based UI** - Modern web interface as alternative to Tkinter GUI
  - Flask web server with Server-Sent Events for real-time updates
  - Responsive HTML/CSS/JavaScript design with gradient purple theme
  - Accessible from any device with a web browser on the network
  - Real-time aircraft table updates without page refresh
  - Live event log showing takeoffs and landings as they happen
  - All features from desktop GUI available in web interface

#### New Files
- `glycol/web.py` - Flask application with SSE streaming (315 lines)
- `glycol/templates/index.html` - Web interface template (97 lines)
- `glycol/static/style.css` - Responsive styling (297 lines)
- `glycol/static/app.js` - Client-side JavaScript (267 lines)
- `web_server.py` - Web server launcher script (63 lines)
- `start_web.sh` - Quick start shell script (22 lines)
- `WEB_README.md` - Comprehensive web interface documentation (186 lines)

#### Features
- **Real-Time Updates** - Server-Sent Events push updates to browser
- **No Authentication Required** - Web UI uses backend credentials automatically
- **Network Accessible** - Run with `--host 0.0.0.0` to access from other devices
- **CSV Export** - Download event logs directly from browser
- **Clickable ICAO24 Links** - Open aircraft on ADSB-Exchange with one click
- **Status Bar** - Shows authentication, monitoring status, rate limits, and event count
- **All Filtering Options** - Aircraft filter, type group filter, and all traffic modes
- **Port Configuration** - Customizable port via `--port` flag (default: 5000)

### Changed
- **README.md** - Updated to highlight both web and desktop interfaces
- **requirements.txt** - Added Flask dependency

### Fixed
- Multiple interface compatibility issues during development:
  - Corrected `get_states()` to accept bbox as tuple, not unpacked arguments
  - Fixed `AircraftMonitor` method calls (using `process_states()` not `update()`)
  - Fixed `EventStore` method calls (using `record_event()` not `add_event()`)
  - Removed invalid `data_dir` parameters from `get_bounding_box()` and `airport_name()`
  - Corrected event dictionary key mappings (`"type"` → `"event_type"`, `"altitude_m"` → `"altitude_ft"`)

### Technical Details

#### Architecture
- **Backend**: Flask with threading for concurrent API polling and SSE broadcasting
- **Frontend**: Vanilla JavaScript (no frameworks) with EventSource for SSE
- **Real-Time**: Server-Sent Events for push updates from server to browser
- **Polling**: Background thread queries OpenSky API at configured interval
- **Broadcasting**: Events pushed to all connected browser clients via SSE

#### API Endpoints
- `GET /` - Main web interface
- `POST /api/start` - Start monitoring an airport
- `POST /api/stop` - Stop monitoring
- `GET /api/status` - Get current status (auth, polling, events, rate limit)
- `GET /api/events` - Get all recorded events as JSON
- `GET /api/export_csv` - Download events as CSV file
- `GET /api/groups` - Get available aircraft type groups
- `GET /api/stream` - Server-Sent Events stream for real-time updates

#### Event Types (SSE)
- `aircraft_update` - Updated aircraft list and count
- `new_events` - New takeoff/landing events detected
- `rate_limit` - API rate limit status update

### Breaking Changes
- None - Web interface is an addition, existing CLI and GUI remain unchanged

## [1.3.1] - 2026-02-10

### Fixed
- **Glossary Search** - Fixed `manage.py glossary search` command that was returning no results due to database file mismatch
- **Database Naming** - Renamed `groups.json` to `type_groups.json` to avoid confusion with OpenSky API's "groups" field

## [1.3.0] - 2026-02-09

### Added
- **Clickable ICAO24 Links** - ICAO24 identifiers in both the aircraft table and event log are now clickable
  - Double-click aircraft table rows to open in ADSB-Exchange
  - Single-click blue underlined ICAO24 links in event log
  - Right-click context menu with options for both OpenSky Network and ADSB-Exchange
  - Hover cursor feedback (hand pointer) on ICAO24 column
  - Status bar hints when hovering over clickable ICAO24s
- **Direct ADSB-Exchange Integration** - Quick access to live aircraft tracking on ADSB-Exchange globe view

### Changed
- **Simplified Link Behavior** - Default click action opens ADSB-Exchange directly without dialog prompt
- **Improved Visual Feedback** - ICAO24 numbers styled as blue underlined links in event log with hover effects

## [1.2.2] - 2026-02-08

### Fixed
- **Log File Location** - Fixed regression where log files were written to package installation directory instead of `./logs` in current working directory
- **Event CSV Location** - Fixed event CSV files being written to current directory instead of `./logs` directory

## [1.2.1] - 2026-02-09

### Added
- **Type Code Display in Event Log** - Aircraft type codes now shown in event log entries (e.g., "A320", "B738")

### Fixed
- **UI Initialization Bug** - Fixed `AttributeError` when launching with `--group` filter due to `mode_var` being used before initialization

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

**Version:** 2.2.0
**Release Date:** February 19, 2026
**Status:** Stable

**Contributors:**
- Initial development and feature implementation

**Special Thanks:**
- OpenSky Network for providing free API access
- OurAirports for comprehensive airport database
- ADS-B Exchange for aircraft database

---

For questions, issues, or feature requests, please visit the project repository.
