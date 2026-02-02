import pytest
from unittest.mock import patch, MagicMock
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.solarprognose_de_community.const import DOMAIN
from custom_components.solarprognose_de_community import async_setup_entry, async_unload_entry

@pytest.mark.asyncio
async def test_setup_unload_entry_direct(hass: HomeAssistant):
    """Testet async_setup_entry direkt und fängt den 5s Timer ab."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"name": "Test Anlage", "api_key": "test_key"},
        entry_id="test_entry_123"
    )
    entry.add_to_hass(hass)

    # mocken 'async_call_later', damit kein "Lingering Timer" entsteht
    with patch("custom_components.solarprognose_de_community.async_call_later") as mock_call_later, \
         patch("homeassistant.config_entries.ConfigEntries.async_forward_entry_setups", return_value=True) as mock_forward:
        
        result = await async_setup_entry(hass, entry)
        
        assert result is True
        assert entry.entry_id in hass.data[DOMAIN]
        
        # Prüfen, ob Sensor-Plattform geladen wurde
        assert mock_forward.called
        
        # Prüfen, ob der verzoegerte Setup-Task (5s) geplant wurde
        assert mock_call_later.called
        # Optional: Pruefen, ob es wirklich 5 Sekunden sind
        assert mock_call_later.call_args[0][1] == 5

    # Teste Unload
    with patch("homeassistant.config_entries.ConfigEntries.async_unload_platforms", return_value=True):
        unload_result = await async_unload_entry(hass, entry)
        assert unload_result is True
        assert entry.entry_id not in hass.data[DOMAIN]