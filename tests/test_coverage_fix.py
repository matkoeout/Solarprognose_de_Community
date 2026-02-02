import pytest
from datetime import timedelta
from unittest.mock import MagicMock
from homeassistant.util import dt as dt_util
from custom_components.solarprognose_de_community.sensor import SENSOR_TYPES, SolarSensor

@pytest.mark.asyncio
async def test_trigger_all_lambdas(hass):
    """Triggert alle Sensortypen für 100% Coverage in sensor.py."""
    entry = MagicMock()
    entry.entry_id = "test_entry"
    coordinator = MagicMock()
    now = dt_util.now().replace(minute=0, second=0, microsecond=0)
    
    coordinator.data = {
        now: 1.0, 
        now.replace(hour=12): 2.0,
        (now + timedelta(days=1)): 3.0
    }
    coordinator.api_count_today = 5
    coordinator.api_status = 0

    for desc in SENSOR_TYPES:
        sensor = SolarSensor(coordinator, entry, "Solar", desc)
        _ = sensor.native_value
        _ = sensor.extra_state_attributes