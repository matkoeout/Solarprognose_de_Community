import pytest
from unittest.mock import patch
from homeassistant import data_entry_flow
from custom_components.solarprognose_de_community.config_flow import SolarPrognoseConfigFlow, SolarPrognoseOptionsFlowHandler
from custom_components.solarprognose_de_community.const import DOMAIN
from pytest_homeassistant_custom_component.common import MockConfigEntry

@pytest.mark.asyncio
async def test_flow_user_success(hass, mock_api_client):
    """Erfolgreiches Setup."""
    flow = SolarPrognoseConfigFlow()
    flow.hass = hass

    result = await flow.async_step_user(user_input={
        "name": "Test",
        "api_key": "123"
    })

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "Test"
    assert result["data"]["api_key"] == "123"

@pytest.mark.asyncio
async def test_flow_user_error_but_pass(hass, mock_api_client):
    """Fehler bei Validierung erlaubt trotzdem Setup (Feature)."""
    _, mock_response = mock_api_client
    mock_response.json.return_value = {"status": -1} # Fehler
    
    flow = SolarPrognoseConfigFlow()
    flow.hass = hass
    
    result = await flow.async_step_user(user_input={
        "name": "Test",
        "api_key": "123"
    })
    
    # Soll trotzdem angelegt werden
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY

@pytest.mark.asyncio
async def test_options_flow(hass):
    """Optionen Flow."""
    entry = MockConfigEntry(domain=DOMAIN, data={"api_key": "old"})
    entry.add_to_hass(hass)
    
    flow = SolarPrognoseOptionsFlowHandler()
    flow.hass = hass
    flow._config_entry = entry # Interner Hack für Test
    
    # Init Step
    result = await flow.async_step_init()
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    
    # Save Step
    with patch("custom_components.solarprognose_de_community.config_flow.async_get_clientsession"):
        result2 = await flow.async_step_init(user_input={"api_key": "new"})
    
    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["data"]["api_key"] == "new"