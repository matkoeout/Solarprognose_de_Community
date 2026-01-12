from __future__ import annotations

import logging
from homeassistant.core import HomeAssistant
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_get_solar_forecast(
    hass: HomeAssistant, config_entry_id: str
) -> dict:

    entry_data = hass.data.get(DOMAIN, {}).get(config_entry_id)
    if not entry_data:
        return {}

    coordinator = entry_data["coordinator"]

    if not coordinator.data:
        return {}

    return {
        "wh_hours": {
            dt.isoformat(): round(val * 1000, 2)
            for dt, val in coordinator.data.items()
        }
    }
