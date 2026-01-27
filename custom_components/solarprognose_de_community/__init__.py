from __future__ import annotations
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

from .coordinator import SolarPrognoseCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    # Nutze Optionen falls vorhanden, sonst Basis-Daten
    api_url = entry.options.get("api_url", entry.data.get("api_url"))
    api_key = entry.options.get("api_key", entry.data.get("api_key"))

    coordinator = SolarPrognoseCoordinator(hass, api_url, api_key)

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as ex:
        raise ConfigEntryNotReady(f"Solarprognose API nicht erreichbar: {ex}") from ex

    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

    # Service-Handler definieren
    async def handle_update_service(call: ServiceCall):
        """Extrahiert Geräte-IDs oder aktualisiert alle, falls keine ID angegeben wurde."""
        device_ids = call.data.get("device_id", [])
        
        # Falls kein Target/Gerät im Dashboard gewählt wurde: Alles aktualisieren
        if not device_ids:
            _LOGGER.info("Update für alle Solarprognose-Instanzen ausgelöst")
            for data in hass.data[DOMAIN].values():
                # Korrigiert: async_refresh() statt async_request_refresh()
                await data["coordinator"].async_refresh()
            return

        # Falls ein Target gewählt wurde: Gezielt filtern
        if isinstance(device_ids, str):
            device_ids = [device_ids]

        dev_reg = dr.async_get(hass)
        for entry_id, data in hass.data[DOMAIN].items():
            for dev_id in device_ids:
                device = dev_reg.async_get(dev_id)
                if device and entry_id in device.config_entries:
                    _LOGGER.info("Manuelles Update für %s ausgelöst", device.name)
                    # Korrigiert: async_refresh() statt async_request_refresh()
                    await data["coordinator"].async_refresh()

    # Service nur einmal registrieren
    if not hass.services.has_service(DOMAIN, "update"):
        hass.services.async_register(
            DOMAIN, 
            "update", 
            handle_update_service
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True

async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok