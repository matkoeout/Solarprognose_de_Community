import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from homeassistant.core import HomeAssistant
from custom_components.solarprognose_de_community.const import DOMAIN
from custom_components.solarprognose_de_community import async_setup_entry

@pytest.mark.asyncio
async def test_manual_update_service_coverage(hass: HomeAssistant):
    """Testet den Service-Aufruf und durchläuft echten Setup-Code."""
    
    # 1. Setup Entry Mock
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.data = {"api_key": "test", "name": "Test"}
    entry.options = {}
    
    # 2. Coordinator Mock
    coordinator = MagicMock()
    coordinator.async_refresh = AsyncMock()
    coordinator.async_config_entry_first_refresh = AsyncMock()
    
    # 3. WICHTIG: Wir patchen die KLASSE, nicht die Funktion async_setup_entry
    # Dadurch läuft der Code in __init__.py wirklich ab!
    with patch("custom_components.solarprognose_de_community.SolarPrognoseCoordinator") as mock_coord_cls, \
         patch("custom_components.solarprognose_de_community.async_call_later") as mock_timer, \
         patch("homeassistant.config_entries.ConfigEntries.async_forward_entry_setups", return_value=True):
        
        mock_coord_cls.return_value = coordinator
        
        # Echter Aufruf von async_setup_entry
        result = await async_setup_entry(hass, entry)
        assert result is True
        
        # Jetzt existiert der Service. Wir rufen ihn auf.
        await hass.services.async_call(DOMAIN, "update", {}, blocking=True)
        
        # Prüfen
        assert coordinator.async_refresh.called