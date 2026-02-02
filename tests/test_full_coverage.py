import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import timedelta
from aiohttp import ClientError
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util

from custom_components.solarprognose_de_community.coordinator import SolarPrognoseCoordinator
from custom_components.solarprognose_de_community.sensor import SENSOR_TYPES, SolarSensor
from custom_components.solarprognose_de_community import async_unload_entry
from custom_components.solarprognose_de_community.const import DOMAIN

@pytest.mark.asyncio
async def test_sensor_graph_logic_hardcore(hass: HomeAssistant):
    """Zwingt den Sensor dazu, die Graphen-Schleife zu betreten."""
    entry = MagicMock()
    entry.entry_id = "test_entry"
    entry.options = {}
    
    coordinator = SolarPrognoseCoordinator(hass, api_key="test")
    
    # TRICK: Wir nehmen den Beginn des heutigen Tages in LOKALZEIT
    # Das ist exakt der Ankerpunkt, den sensor.py nutzt.
    now_local = dt_util.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    data = {}
    # Wir füllen Daten für 48 Stunden
    for i in range(48): 
        ts = now_local + timedelta(hours=i)
        # Wir speichern den Wert unter BEIDEN Schlüsseln (Lokal und UTC),
        # um sicherzugehen, dass der Sensor ihn findet, egal wie er rechnet.
        data[ts] = 50.0
        data[dt_util.as_utc(ts)] = 50.0
        
    coordinator.data = data
    coordinator.api_count_today = 10
    coordinator.api_status = 0

    # Nur Sensoren mit "production" im Key haben Graphen
    graph_sensors = [s for s in SENSOR_TYPES if "production" in s.key]
    
    for desc in graph_sensors:
        sensor = SolarSensor(coordinator, entry, "Solar", desc)
        sensor.hass = hass
        
        # Zugriff auf Attribute triggert die Berechnung
        attrs = sensor.extra_state_attributes
        
        # Assertion: Es MUSS etwas generiert worden sein
        assert attrs is not None
        # Prüfe, ob Listen für ApexCharts generiert wurden (das beweist, dass der Loop lief)
        # Wir suchen nach Values, die Listen sind (z.B. 'forecasts': [...])
        has_list = any(isinstance(v, list) for v in attrs.values())
        assert has_list, f"Keine Graphen-Daten für {desc.key} generiert! Loop nicht betreten."

@pytest.mark.asyncio
async def test_coordinator_scheduling_logic(hass: HomeAssistant):
    """Testet die Zeit-Planung im Coordinator im Detail."""
    coordinator = SolarPrognoseCoordinator(hass, api_key="test")
    
    # 1. Test: preferredNextApiRequestAt in der Zukunft
    # Wir simulieren einen Zeitpunkt in 2 Stunden
    next_ts = int((dt_util.now() + timedelta(hours=2)).timestamp())
    
    mock_res = {
        "status": 0,
        "preferredNextApiRequestAt": {"epochTimeUtc": next_ts},
        "data": {}
    }
    
    with patch("custom_components.solarprognose_de_community.coordinator.async_get_clientsession") as mock_session_fac, \
         patch("custom_components.solarprognose_de_community.coordinator.async_call_later") as mock_timer:
        
        session = MagicMock()
        response = AsyncMock()
        response.json.return_value = mock_res
        response.__aenter__.return_value = response
        session.get.return_value = response
        mock_session_fac.return_value = session
        
        await coordinator._async_update_data()
        
        # Timer muss gesetzt sein
        assert mock_timer.called
        # Check delay (sollte ca. 7200 Sekunden sein)
        delay = mock_timer.call_args[0][1]
        assert delay > 7000

@pytest.mark.asyncio
async def test_init_unload_coverage(hass: HomeAssistant):
    """Testet das Entladen der Integration."""
    entry = MagicMock()
    entry.entry_id = "test_entry"
    
    # FIX: Wir simulieren, dass die Integration geladen ist, damit .pop() klappt
    hass.data[DOMAIN] = {entry.entry_id: {"coordinator": MagicMock()}}
    
    # Mock ConfigEntries
    with patch("homeassistant.config_entries.ConfigEntries.async_unload_platforms", return_value=True) as mock_unload:
        result = await async_unload_entry(hass, entry)
        
        assert result is True
        assert mock_unload.called
        
    # Prüfen, ob der Eintrag aus hass.data entfernt wurde
    assert entry.entry_id not in hass.data[DOMAIN]