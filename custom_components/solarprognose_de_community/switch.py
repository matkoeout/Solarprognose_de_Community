import logging

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    custom_name = entry.data.get("name", "Solarprognose")
    async_add_entities([SolarPollingSwitch(coordinator, entry, custom_name)])


class SolarPollingSwitch(CoordinatorEntity, RestoreEntity, SwitchEntity):
    """Schiebeschalter zum Aktivieren/Deaktivieren des automatischen Pollings."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:autorenew"

    entity_description = SwitchEntityDescription(
        key="enable_automatic_polling",
        translation_key="enable_automatic_polling",
    )

    def __init__(self, coordinator, entry, custom_name):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_enable_automatic_polling"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": custom_name,
            "manufacturer": "Solarprognose.de (Community)",
            "model": "WebAPI v1",
        }

    async def async_added_to_hass(self) -> None:
        """Stellt den letzten Zustand wieder her. Default ist EIN."""
        await super().async_added_to_hass()

        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state in ("on", "off"):
            self.coordinator.enable_automatic_polling = (last_state.state == "on")
        # Kein gespeicherter Zustand vorhanden -> Coordinator-Default (True) bleibt erhalten

    @property
    def is_on(self) -> bool:
        return self.coordinator.enable_automatic_polling

    async def async_turn_on(self, **kwargs) -> None:
        self.coordinator.enable_automatic_polling = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        self.coordinator.enable_automatic_polling = False
        self.async_write_ha_state()
