import pytest
from unittest.mock import patch, MagicMock
from custom_components.solarprognose_de_community import async_setup_entry, async_unload_entry
from custom_components.solarprognose_de_community.const import DOMAIN
from pytest_homeassistant_custom_component.common import MockConfigEntry

@pytest.mark.asyncio
async def test_setup_and_unload(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"api_key": "key"})
    entry.add_to_hass(hass)
    
    # Setup
    with patch("custom_components.solarprognose_de_community.coordinator.SolarPrognoseCoordinator.async_setup"), \
         patch("homeassistant.config_entries.ConfigEntries.async_forward_entry_setups", return_value=True):
        
        assert await async_setup_entry(hass, entry)
        assert DOMAIN in hass.data
    
    # Unload
    with patch("homeassistant.config_entries.ConfigEntries.async_unload_platforms", return_value=True):
        assert await async_unload_entry(hass, entry)
        assert entry.entry_id not in hass.data[DOMAIN]