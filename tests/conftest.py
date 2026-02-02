##
##  cls && pytest --cov=custom_components.solarprognose_de_community tests/
##
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# Windows-Socket-Fix (Neutralisiert das blockierende Plugin)
try:
    import pytest_socket
    pytest_socket.disable_socket = lambda *args, **kwargs: None
    pytest_socket.SocketBlockedError = Exception 
except ImportError:
    pass

@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(hass):
    """Vollständiger asynchroner Patch für das Integration-Objekt."""
    mock_integration = MagicMock()
    mock_integration.domain = "solarprognose_de_community"
    mock_integration.disabled = False
    
    mock_integration.resolve_dependencies = AsyncMock(return_value=True)
    mock_integration.async_get_component = AsyncMock(return_value=MagicMock())
    mock_integration.async_get_platform = AsyncMock(return_value=MagicMock())
    
    mock_integration.platforms_exists = MagicMock(return_value=False)
    
    with patch("homeassistant.loader.async_get_integration", return_value=mock_integration), \
         patch("homeassistant.setup.async_process_deps_reqs", return_value=True), \
         patch("homeassistant.helpers.translation.async_load_integrations", AsyncMock()):
        
        hass.data["integrations"] = {"solarprognose_de_community": mock_integration}
        yield