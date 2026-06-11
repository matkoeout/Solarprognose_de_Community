from __future__ import annotations
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.event import async_call_later

from .coordinator import SolarPrognoseCoordinator
from .const import DOMAIN, CONF_ENABLE_AUTOMATIC_POLLING, DEFAULT_ENABLE_AUTOMATIC_POLLING

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setzt die Integration ueber einen Config Entry auf."""
    hass.data.setdefault(DOMAIN, {})

    # Nutze Optionen falls vorhanden, sonst Basis-Daten
    api_url = entry.options.get("api_url", entry.data.get("api_url"))
    api_key = entry.options.get("api_key", entry.data.get("api_key"))
    enable_automatic_polling = entry.options.get(
        CONF_ENABLE_AUTOMATIC_POLLING,
        entry.data.get(CONF_ENABLE_AUTOMATIC_POLLING, DEFAULT_ENABLE_AUTOMATIC_POLLING),
    )

    # Coordinator initialisieren (noch kein API-Aufruf)
    coordinator = SolarPrognoseCoordinator(hass, api_url, api_key, enable_automatic_polling)
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

    # 1. Plattformen (Sensoren) laden
    # Dies wird nun direkt ausgeführt, um den Watchdog zu beruhigen.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # 2. Den Coordinator-Setup-Prozess verzoegert starten
    # Dies gibt den Sensoren Zeit fuer RestoreEntity, ohne den Import zu blockieren.
    async def _delayed_setup(_):
        await coordinator.async_setup()

    entry.async_on_unload(async_call_later(hass, 5, _delayed_setup))

    # Service-Handler definieren
    async def handle_update_service(call: ServiceCall):
        """Extrahiert Geraete-IDs oder aktualisiert alle, falls keine ID angegeben wurde."""
        device_ids = call.data.get("device_id", [])
        
        if not device_ids:
            _LOGGER.info("Update fuer alle Solarprognose-Instanzen ausgelöst")
            for data in hass.data[DOMAIN].values():
                await data["coordinator"].async_refresh()
            return

        if isinstance(device_ids, str):
            device_ids = [device_ids]

        dev_reg = dr.async_get(hass)
        for entry_id, data in hass.data[DOMAIN].items():
            for dev_id in device_ids:
                device = dev_reg.async_get(dev_id)
                if device and entry_id in device.config_entries:
                    _LOGGER.info("Manuelles Update fuer %s ausgelöst", device.name)
                    await data["coordinator"].async_refresh()

    # Service nur einmal registrieren
    if not hass.services.has_service(DOMAIN, "update"):
        hass.services.async_register(DOMAIN, "update", handle_update_service)

    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True

async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Wird aufgerufen, wenn Optionen aktualisiert werden."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Entlaedt einen Config Entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok