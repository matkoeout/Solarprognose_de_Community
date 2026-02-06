import pytest
from datetime import timedelta
from unittest.mock import MagicMock, patch
from homeassistant.util import dt as dt_util
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import State
from pytest_homeassistant_custom_component.common import mock_restore_cache

from custom_components.solarprognose_de_community.sensor import SENSOR_TYPES, SolarSensor

@pytest.fixture
def coordinator_with_data(hass):
    """Coordinator mit vollem Datensatz."""
    from custom_components.solarprognose_de_community.coordinator import SolarPrognoseCoordinator
    coord = SolarPrognoseCoordinator(hass, api_key="test")
    
    now = dt_util.now().replace(minute=0, second=0, microsecond=0)
    
    # Daten für Heute und Morgen erzeugen
    data = {}
    for i in range(48):
        t = now.replace(hour=0) + timedelta(hours=i)
        data[t] = 1.0 # 1 kWh/kW pro Stunde
    
    coord.data = data
    coord.api_count_today = 5
    coord.api_status = 0
    
    # FIX: Setze diese Werte explizit, damit Sensoren nicht None liefern
    coord.next_api_request = now + timedelta(hours=1)
    coord.last_api_success = now - timedelta(hours=1)
    coord.api_message = "OK"
    
    return coord

@pytest.mark.asyncio
async def test_all_sensor_values(hass, coordinator_with_data):
    """Iteriert über ALLE Sensortypen und prüft, ob die Lambdas crashen."""
    entry = MagicMock()
    entry.entry_id = "test"
    
    for desc in SENSOR_TYPES:
        sensor = SolarSensor(coordinator_with_data, entry, "Solar", desc)
        sensor.hass = hass
        
        # Prüfe Wert
        val = sensor.native_value
        assert val is not None, f"Sensor {desc.key} lieferte None"
        
        # Prüfe Attribute (wichtig für Forecast Graph)
        attrs = sensor.extra_state_attributes
        if desc.key == "forecast":
            assert "forecast" in attrs
            assert len(attrs["forecast"]) > 0

@pytest.mark.asyncio
async def test_restore_state_api_count(hass):
    """Testet spezifisch das Wiederherstellen des API-Counters."""
    desc = next(d for d in SENSOR_TYPES if d.key == "api_count")
    
    mock_restore_cache(hass, [
        State(f"sensor.solar_api_count", "42")
    ])
    
    entry = MagicMock(entry_id="test")
    coord = MagicMock()
    coord.api_count_today = 0 # Ist beim Start 0
    coord.data = {}
    
    sensor = SolarSensor(coord, entry, "Solar", desc)
    sensor.entity_id = "sensor.solar_api_count"
    sensor.hass = hass
    
    # Simuliere Add to Hass
    with patch.object(SensorEntity, "async_added_to_hass"):
        await sensor.async_added_to_hass()
    
    # Coordinator muss aktualisiert worden sein
    coord.set_api_count.assert_called_with(42)

@pytest.mark.asyncio
async def test_restore_forecast_data(hass):
    """Testet das Wiederherstellen der Forecast-Daten (wichtigster Restore-Test)."""
    desc = next(d for d in SENSOR_TYPES if d.key == "forecast")
    
    # Wir simulieren alte Forecast-Daten im Attribut
    now_iso = dt_util.now().isoformat()
    mock_restore_cache(hass, [
        State(f"sensor.solar_forecast", "100", attributes={
            "forecast": [{"datetime": now_iso, "energy": 50.5}]
        })
    ])
    
    entry = MagicMock(entry_id="test")
    coord = MagicMock()
    coord.data = None # Leer beim Start
    
    sensor = SolarSensor(coord, entry, "Solar", desc)
    sensor.entity_id = "sensor.solar_forecast"
    sensor.hass = hass
    
    with patch.object(SensorEntity, "async_added_to_hass"):
        await sensor.async_added_to_hass()
    
    # Der Coordinator muss mit den Daten befüllt worden sein
    assert coord.async_set_updated_data.called
    args = coord.async_set_updated_data.call_args[0][0]
    assert len(args) == 1
    assert list(args.values())[0] == 50.5