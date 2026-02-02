import pytest
from unittest.mock import MagicMock, patch
from homeassistant.core import HomeAssistant, State
from homeassistant.components.sensor import SensorEntity
from pytest_homeassistant_custom_component.common import mock_restore_cache
from custom_components.solarprognose_de_community.sensor import SENSOR_TYPES, SolarSensor

@pytest.mark.asyncio
async def test_sensor_restore_state(hass: HomeAssistant):
    description = next(desc for desc in SENSOR_TYPES if desc.key == "today_total")
    entity_id = f"sensor.solarprognose_{description.key}"
    
    mock_restore_cache(hass, [
        State(entity_id, "123.45", attributes={"unit_of_measurement": "kWh"})
    ])

    entry = MagicMock()
    entry.entry_id = "test_entry"
    coordinator = MagicMock()
    coordinator.data = None
    
    sensor = SolarSensor(coordinator, entry, "Solar", description)
    sensor.entity_id = entity_id
    sensor.hass = hass 
    
    with patch.object(SensorEntity, "async_added_to_hass"): 
        await sensor.async_added_to_hass()
    
    assert sensor.native_value == 123.45