# Glycol Web Server

Browser-based version of the Glycol airport monitor. Access the application through your web browser instead of the Tkinter GUI.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the web server:**
   ```bash
   python web_server.py
   ```

3. **Open your browser:**
   Navigate to `http://127.0.0.1:8666`

## Features

- **Real-time updates** via Server-Sent Events (SSE)
- **Interactive controls** for selecting airports and filters
- **Live aircraft table** showing all aircraft in range
- **Event log** with takeoff/landing notifications
- **Clickable ICAO24 links** to ADSB-Exchange for detailed tracking
- **CSV export** of recorded events
- **Responsive design** that works on desktop and mobile

## Usage

### Basic Usage

```bash
# Run on default port (8666)
python web_server.py

# Run on custom port
python web_server.py --port 8080

# Run on all interfaces (accessible from network)
python web_server.py --host 0.0.0.0
```

### Advanced Options

```bash
# Custom log file
python web_server.py --log web-session.log

# Custom directories
python web_server.py --logs-dir /path/to/logs --data-dir /path/to/data
```

## Web Interface

### Controls

1. **Airport ICAO** - Enter a 4-letter airport code (e.g., KSFO, KJFK)
2. **Filter** - Choose from:
   - All Traffic
   - Aircraft (filter by ICAO24/tail number)
   - Type Group (filter by aircraft category)
3. **Value** - Comma-separated filter values
4. **Poll Interval** - How often to check for updates (5-120 seconds)

### Status Bar

- **Authentication** - Shows if credentials are loaded
- **Monitoring** - Current airport being monitored
- **Rate Limit** - OpenSky API rate limit status
- **Events** - Count of recorded events

### Aircraft Table

Displays all aircraft within 5 NM of the airport:
- **ICAO24** - Clickable link to ADSB-Exchange
- **Callsign** - Flight number or tail number
- **Status** - On Ground or Airborne
- **Altitude** - Barometric altitude in feet
- **Speed** - Ground speed in knots

### Event Log

Real-time log of takeoff and landing events:
- 🛫 **Takeoff** - Aircraft leaves the ground
- 🛬 **Landing** - Aircraft touches down

Click any ICAO24 code to view the aircraft on ADSB-Exchange.

## Technical Details

### Architecture

- **Backend:** Flask web server with Server-Sent Events
- **Frontend:** Vanilla JavaScript (no frameworks)
- **Real-time:** SSE for push updates from server to browser
- **Polling:** Background thread queries OpenSky API at configured interval

### API Endpoints

- `GET /` - Main web interface
- `POST /api/start` - Start monitoring an airport
- `POST /api/stop` - Stop monitoring
- `GET /api/status` - Get current status
- `GET /api/events` - Get all recorded events
- `GET /api/export_csv` - Download events as CSV
- `GET /api/groups` - Get available aircraft type groups
- `GET /api/stream` - Server-Sent Events stream for real-time updates

### Event Types

Events sent via SSE:
- `aircraft_update` - Updated aircraft list
- `new_events` - New takeoff/landing events
- `rate_limit` - API rate limit update

## Credentials

On first use, you need OpenSky Network credentials. Create `glycol/data/credentials.json`:

```json
{
  "clientId": "your-client-id",
  "clientSecret": "your-client-secret"
}
```

Get your credentials from: https://opensky-network.org/

## Troubleshooting

### Server won't start

- Check if port is already in use: `lsof -i :8666`
- Try a different port: `python web_server.py --port 8080`

### Not authenticated

- Verify `glycol/data/credentials.json` exists and is valid
- Check logs for authentication errors

### No data showing

- Ensure you clicked "Start" after entering an airport code
- Check browser console for JavaScript errors
- Verify OpenSky API is responding (check server logs)

### Real-time updates not working

- EventSource (SSE) requires modern browser
- Check browser console for connection errors
- Some corporate firewalls block SSE

## Development

### Running in Debug Mode

Edit `web.py` and set `debug=True` in the `run()` call:
```python
app.run(host=host, port=port, debug=True, threaded=True)
```

### File Structure

```
glycol/
  web.py              # Flask application and SSE logic
  templates/
    index.html        # Main web interface
  static/
    style.css         # Styling
    app.js            # Client-side JavaScript
```

## Comparison with GUI Version

| Feature | GUI (Tkinter) | Web Server |
|---------|---------------|------------|
| Interface | Desktop window | Web browser |
| Access | Local only | Network capable |
| Real-time | Polling in GUI thread | SSE push |
| Mobile | No | Yes (responsive) |
| Multi-user | No | Yes (shared events) |

Both versions share the same backend logic for API calls, event detection, and filtering.
