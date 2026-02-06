import pytest
from datetime import timedelta
from unittest.mock import patch, AsyncMock, MagicMock
from homeassistant.util import dt as dt_util
from homeassistant.helpers.update_coordinator import UpdateFailed
from custom_components.solarprognose_de_community.const import NIGHT_START_HOUR, NIGHT_END_HOUR

# Wir setzen eine Standard-Zeit (Mittag), damit die Tests nicht in die Nachtruhe laufen
@pytest.fixture
def mock_now_daytime():
    now = dt_util.now().replace(hour=12, minute=0, second=0, microsecond=0)
    with patch("homeassistant.util.dt.now", return_value=now):
        yield now

@pytest.mark.asyncio
async def test_initial_setup_daytime(hass, mock_coordinator, mock_now_daytime):
    """Setup am Tag: Soll sofort refreshen."""
    mock_coordinator.async_refresh = AsyncMock()
    await mock_coordinator.async_setup()
    mock_coordinator.async_refresh.assert_called_once()

@pytest.mark.asyncio
async def test_initial_setup_nighttime(hass, mock_coordinator):
    """Setup in der Nacht: Soll warten bis 3 Uhr."""
    # 22:00 Uhr
    now = dt_util.now().replace(hour=22, minute=0)
    with patch("homeassistant.util.dt.now", return_value=now):
        mock_coordinator.async_refresh = AsyncMock()
        await mock_coordinator.async_setup()
        
        # KEIN Refresh, sondern warten
        mock_coordinator.async_refresh.assert_not_called()
        assert mock_coordinator.next_api_request is not None
        assert mock_coordinator.next_api_request.hour == NIGHT_END_HOUR

@pytest.mark.asyncio
async def test_update_success_and_data_parsing(hass, mock_coordinator, mock_api_client, mock_now_daytime):
    """Testet erfolgreiches Update, API Counter und Daten-Parsing."""
    _, mock_response = mock_api_client
    
    # Mock Daten: Ein Wert heute, ein Wert morgen
    ts_now = int(mock_now_daytime.timestamp())
    mock_response.json.return_value = {
        "status": 0,
        "data": {
            str(ts_now): [12.34],
            str(ts_now + 3600): [56.78]
        }
    }
    
    data = await mock_coordinator._async_update_data()
    
    assert len(data) == 2
    assert mock_coordinator.api_count_today == 1

@pytest.mark.asyncio
async def test_update_api_error(hass, mock_coordinator, mock_api_client, mock_now_daytime):
    """Testet Fehlerbehandlung bei Status != 0."""
    _, mock_response = mock_api_client
    mock_response.json.return_value = {"status": 1, "message": "Limit reached"}
    
    data = await mock_coordinator._async_update_data()
    
    assert mock_coordinator.api_status == 1
    assert data == {} # Leeres Dict zurückgeben
    # Sollte 60 Minuten warten
    args, _ = mock_coordinator.mock_timer.call_args
    assert args[1] == 3600  # 60 min * 60 sec

@pytest.mark.asyncio
async def test_smart_scheduling_logic(hass, mock_coordinator, mock_api_client, mock_now_daytime):
    """Testet die komplexe Logik für preferredNextApiRequestAt."""
    _, mock_response = mock_api_client
    
    # Fall 1: API sagt "komm in 2 Stunden wieder"
    target_time = mock_now_daytime + timedelta(hours=2)
    mock_response.json.return_value = {
        "status": 0,
        "preferredNextApiRequestAt": {"epochTimeUtc": int(target_time.timestamp())}
    }
    
    await mock_coordinator._async_update_data()
    
    # Timer prüfen
    delay = mock_coordinator.mock_timer.call_args[0][1]
    # Toleranz für Laufzeit (delay sollte ca 7200s sein)
    assert 7000 < delay < 7300

@pytest.mark.asyncio
async def test_night_reset_logic(hass, mock_coordinator):
    """Testet, ob um Mitternacht der Counter resettet wird."""
    # Wir simulieren 01:00 Uhr nachts (in der Sperrzeit)
    now = dt_util.now().replace(hour=1, minute=0, second=0, microsecond=0)
    
    # Wir setzen last_reset_day auf gestern
    mock_coordinator.last_reset_day = (now - timedelta(days=1)).date()
    mock_coordinator.api_count_today = 10
    
    with patch("homeassistant.util.dt.now", return_value=now):
        await mock_coordinator._async_update_data()
        
        # 1. Reset muss erfolgt sein
        assert mock_coordinator.api_count_today == 0
        assert mock_coordinator.last_reset_day == now.date()
        
        # 2. Es darf KEIN API Call rausgehen (wir sind noch in der Sperrzeit 21-03)
        target_hour = NIGHT_END_HOUR # 3
        # Zeit bis 3 Uhr: 2 Stunden = 7200 Sekunden
        # Da wir um 01:00:00 starten und target 03:05:00 ist
        expected_delay = 2 * 3600 + 300 # 2h + 5min
        
        delay = mock_coordinator.mock_timer.call_args[0][1]
        assert (expected_delay - 10) < delay < (expected_delay + 10)

@pytest.mark.asyncio
async def test_exception_handling(hass, mock_coordinator, mock_api_client, mock_now_daytime):
    """Testet Netzwerkfehler."""
    session, _ = mock_api_client
    session.get.side_effect = Exception("Connection lost")
    
    with pytest.raises(UpdateFailed):
        await mock_coordinator._async_update_data()
    
    # Sollte Retry planen (60 min)
    args, _ = mock_coordinator.mock_timer.call_args
    assert args[1] == 3600