// Glycol Web App JavaScript

const state = {
    isPolling: false,
    eventSource: null,
    aircraftData: [],
    events: []
};

// DOM elements
const airportInput = document.getElementById('airport');
const filterModeSelect = document.getElementById('filter-mode');
const filterValueGroup = document.getElementById('filter-value-group');
const filterValueInput = document.getElementById('filter-value');
const intervalInput = document.getElementById('interval');
const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const exportBtn = document.getElementById('export-btn');
const aircraftTbody = document.getElementById('aircraft-tbody');
const eventLog = document.getElementById('event-log');
const statusAuth = document.getElementById('status-auth');
const statusPolling = document.getElementById('status-polling');
const statusRateLimit = document.getElementById('status-rate-limit');
const statusEvents = document.getElementById('status-events');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadStatus();
    setupEventListeners();
});

function setupEventListeners() {
    filterModeSelect.addEventListener('change', () => {
        const mode = filterModeSelect.value;
        if (mode === 'all') {
            filterValueGroup.style.display = 'none';
        } else {
            filterValueGroup.style.display = 'flex';
            filterValueInput.placeholder = mode === 'aircraft'
                ? 'e.g., A1B2C3, N456CD'
                : 'e.g., passenger, cargo';
        }
    });

    startBtn.addEventListener('click', startMonitoring);
    stopBtn.addEventListener('click', stopMonitoring);
    exportBtn.addEventListener('click', exportCSV);

    // Allow Enter key to start
    airportInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !state.isPolling) {
            startMonitoring();
        }
    });
}

async function loadStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        statusAuth.textContent = data.authenticated ? '✓ Authenticated' : '✗ Not authenticated';
        statusAuth.style.color = data.authenticated ? '#28a745' : '#dc3545';

        if (data.polling) {
            state.isPolling = true;
            startBtn.disabled = true;
            stopBtn.disabled = false;
            statusPolling.textContent = `Monitoring: ${data.airport}`;
            airportInput.value = data.airport;
            connectEventStream();
        }

        updateEventCount(data.event_count);
    } catch (error) {
        console.error('Failed to load status:', error);
    }
}

async function startMonitoring() {
    const airport = airportInput.value.trim().toUpperCase();
    if (!airport) {
        alert('Please enter an airport code');
        return;
    }

    const filterMode = filterModeSelect.value;
    const filterValue = filterValueInput.value.trim();
    const interval = parseInt(intervalInput.value);

    const filterValues = filterMode !== 'all' && filterValue
        ? filterValue.split(',').map(v => v.trim())
        : [];

    try {
        const response = await fetch('/api/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                airport,
                filter_mode: filterMode,
                filter_values: filterValues,
                interval
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to start monitoring');
        }

        state.isPolling = true;
        startBtn.disabled = true;
        stopBtn.disabled = false;
        statusPolling.textContent = `Monitoring: ${data.airport_name || airport}`;

        connectEventStream();
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

async function stopMonitoring() {
    try {
        await fetch('/api/stop', { method: 'POST' });

        state.isPolling = false;
        startBtn.disabled = false;
        stopBtn.disabled = true;
        statusPolling.textContent = 'Idle';

        if (state.eventSource) {
            state.eventSource.close();
            state.eventSource = null;
        }
    } catch (error) {
        console.error('Failed to stop monitoring:', error);
    }
}

function connectEventStream() {
    if (state.eventSource) {
        state.eventSource.close();
    }

    state.eventSource = new EventSource('/api/stream');

    state.eventSource.onmessage = (event) => {
        try {
            const message = JSON.parse(event.data);
            handleServerEvent(message);
        } catch (error) {
            console.error('Failed to parse event:', error);
        }
    };

    state.eventSource.onerror = (error) => {
        console.error('EventSource error:', error);
        if (!state.isPolling) {
            state.eventSource.close();
            state.eventSource = null;
        }
    };
}

function handleServerEvent(message) {
    switch (message.type) {
        case 'aircraft_update':
            updateAircraftTable(message.data.aircraft);
            break;
        case 'new_events':
            addEvents(message.data.events);
            break;
        case 'rate_limit':
            updateRateLimit(message.data.remaining);
            break;
    }
}

function updateAircraftTable(aircraft) {
    state.aircraftData = aircraft;

    if (aircraft.length === 0) {
        aircraftTbody.innerHTML = '<tr><td colspan="5" class="no-data">No aircraft in range</td></tr>';
        return;
    }

    aircraftTbody.innerHTML = aircraft.map(ac => {
        const status = ac.on_ground ? 'On Ground' : 'Airborne';
        const statusClass = ac.on_ground ? 'on-ground' : 'airborne';
        const altitude = ac.altitude !== null ? ac.altitude.toLocaleString() : 'N/A';
        const velocity = ac.velocity !== null ? ac.velocity.toLocaleString() : 'N/A';

        return `
            <tr>
                <td><span class="clickable" onclick="openADSB('${ac.icao24}')">${ac.icao24}</span></td>
                <td>${ac.callsign || 'N/A'}</td>
                <td><span class="${statusClass}">${status}</span></td>
                <td>${altitude}</td>
                <td>${velocity}</td>
            </tr>
        `;
    }).join('');
}

function addEvents(events) {
    if (state.events.length === 0 && eventLog.querySelector('.no-data')) {
        eventLog.innerHTML = '';
    }

    events.forEach(event => {
        state.events.unshift(event);

        const eventDiv = document.createElement('div');
        eventDiv.className = `event-item ${event.event_type}`;

        const timestamp = new Date(event.timestamp).toLocaleTimeString();
        const eventType = event.event_type === 'takeoff' ? '🛫 Takeoff' : '🛬 Landing';
        const altitude = event.altitude_ft !== null ? `${event.altitude_ft.toLocaleString()} ft` : 'N/A';
        const airportStr = event.airport ? ` @ ${event.airport}` : '';

        eventDiv.innerHTML = `
            <div class="event-time">${timestamp} - ${eventType}${airportStr}</div>
            <div class="event-details">
                <span class="clickable" onclick="openADSB('${event.icao24}')">${event.icao24}</span>
                ${event.callsign ? `(${event.callsign})` : ''} - Altitude: ${altitude}
            </div>
        `;

        eventLog.insertBefore(eventDiv, eventLog.firstChild);
    });

    updateEventCount(state.events.length);
}

function updateEventCount(count) {
    statusEvents.textContent = `Events: ${count}`;
}

function updateRateLimit(remaining) {
    if (remaining !== null) {
        statusRateLimit.textContent = `Rate Limit: ${remaining} remaining`;
        statusRateLimit.style.color = remaining < 10 ? '#dc3545' : '#28a745';
    }
}

function openADSB(icao24) {
    const url = `https://globe.adsbexchange.com/?icao=${icao24}`;
    window.open(url, '_blank');
}

async function exportCSV() {
    try {
        const response = await fetch('/api/export_csv');
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `glycol_events_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    } catch (error) {
        alert(`Export failed: ${error.message}`);
    }
}
