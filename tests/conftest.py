import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from homeassistant.util import dt as dt_util

@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(hass):
    """Aktiviert die Custom Integration in HA."""
    mock_integration = MagicMock()
    mock_integration.domain = "solarprognose_de_community"
    mock_integration.disabled = False
    
    with patch("homeassistant.loader.async_get_integration", return_value=mock_integration), \
         patch("homeassistant.setup.async_process_deps_reqs", return_value=True):
        yield

@pytest.fixture
def mock_api_client():
    """Mockt die aiohttp ClientSession für alle Tests."""
    with patch("custom_components.solarprognose_de_community.coordinator.async_get_clientsession") as mock_session_cls, \
         patch("custom_components.solarprognose_de_community.config_flow.async_get_clientsession") as mock_flow_session_cls:
        
        session = MagicMock()
        response = AsyncMock()
        response.status = 200
        # Default Antwort
        response.json.return_value = {"status": 0, "data": {}, "preferredNextApiRequestAt": None}
        response.__aenter__.return_value = response
        
        session.get.return_value = response
        
        mock_session_cls.return_value = session
        mock_flow_session_cls.return_value = session
        
        yield session, response

@pytest.fixture
def mock_coordinator(hass):
    """Erstellt einen Coordinator mit gemocktem Timer."""
    from custom_components.solarprognose_de_community.coordinator import SolarPrognoseCoordinator
    
    # Timer patchen, damit wir nicht warten müssen
    with patch("custom_components.solarprognose_de_community.coordinator.async_call_later") as mock_timer:
        coord = SolarPrognoseCoordinator(hass, api_key="test_key")
        coord._schedule_next_update = MagicMock(wraps=coord._schedule_next_update)
        # Den echten Timer-Mock an den Coordinator hängen, um Assertions zu machen
        coord.mock_timer = mock_timer
        yield coord