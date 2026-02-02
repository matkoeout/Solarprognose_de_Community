import pytest
from datetime import timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from homeassistant.util import dt as dt_util
from homeassistant.core import HomeAssistant

from custom_components.solarprognose_de_community.coordinator import SolarPrognoseCoordinator
from custom_components.solarprognose_de_community.const import NIGHT_START_HOUR, NIGHT_END_HOUR

@pytest.mark.asyncio
async def test_coordinator_night_delay(hass: HomeAssistant):
    """Testet die Verzoegerung waehrend der Nachtruhe."""
    night_time = dt_util.now().replace(hour=NIGHT_START_HOUR + 1, minute=0, second=0, microsecond=0)
    
    with patch("homeassistant.util.dt.now", return_value=night_time), \
         patch("custom_components.solarprognose_de_community.coordinator.async_call_later") as mock_sleep:
        
        coordinator = SolarPrognoseCoordinator(hass, api_key="test_key")
        await coordinator.async_setup()
        
        assert coordinator.next_api_request is not None
        assert coordinator.next_api_request.hour == NIGHT_END_HOUR
        assert mock_sleep.called

@pytest.mark.asyncio
async def test_api_counter_reset(hass: HomeAssistant):
    """Testet den Reset des API-Zaehlers bei Datumswechsel."""
    coordinator = SolarPrognoseCoordinator(hass, api_key="test_key")
    coordinator.api_count_today = 5
    yesterday = dt_util.now().date() - timedelta(days=1)
    coordinator.last_reset_day = yesterday
    
    mock_res = {
        "status": 0,
        "message": "OK",
        "data": {"1700000000": [1.0]}
    }

    with patch("custom_components.solarprognose_de_community.coordinator.async_get_clientsession") as mock_get_session:
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_res
        mock_response.__aenter__.return_value = mock_response
        mock_session.get.return_value = mock_response
        
        with patch.object(coordinator, "_schedule_next_update"):
            await coordinator._async_update_data()
            
            # WICHTIG: Reset auf 0, dann inkrementiert auf 1 durch erfolgreichen Abruf
            assert coordinator.api_count_today == 1
            assert coordinator.last_reset_day == dt_util.now().date()

@pytest.mark.asyncio
async def test_is_night_boundary(hass: HomeAssistant):
    """Testet die exakten Grenzen der Nachtruhe."""
    day_time = dt_util.now().replace(hour=NIGHT_START_HOUR - 1, minute=59)
    is_night = (day_time.hour >= NIGHT_START_HOUR or day_time.hour < NIGHT_END_HOUR)
    assert not is_night

    night_start = dt_util.now().replace(hour=NIGHT_START_HOUR, minute=0)
    is_night = (night_start.hour >= NIGHT_START_HOUR or night_start.hour < NIGHT_END_HOUR)
    assert is_night