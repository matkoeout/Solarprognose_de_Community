import voluptuous as vol
import aiohttp
import async_timeout
import logging
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def validate_input(hass, data):
    """
    Versucht die Validierung, ignoriert aber Fehler, 
    damit das Geraet trotz API-Limit angelegt werden kann.
    """
    api_key = data.get("api_key")
    url = data.get("api_url") or (
        "https://www.solarprognose.de/web/solarprediction/api/v1"
        f"?access-token={api_key}&type=hourly&_format=json"
    )

    try:
        async with async_timeout.timeout(10):
            session = async_get_clientsession(hass)
            async with session.get(url) as response:
                res = await response.json()
                api_status = res.get("status")
                if api_status != 0:
                    _LOGGER.warning("Validierung fehlgeschlagen (Status %s), Setup wird trotzdem erlaubt", api_status)
    except Exception as err:
        _LOGGER.warning("Server nicht erreichbar (%s), Setup wird trotzdem erlaubt", err)

    # Wir geben IMMER None zurueck, um das Anlegen zu erzwingen
    return None

class SolarPrognoseConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Behandelt den Setup-Prozess."""
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input:
            if not user_input.get("api_key") and not user_input.get("api_url"):
                errors["base"] = "missing_api"
            else:
                await validate_input(self.hass, user_input)
                return self.async_create_entry(
                    title=user_input.get("name", "Solarprognose"), 
                    data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("name", default="Solarprognose"): str,
                vol.Optional("api_key"): str,
                vol.Optional("api_url"): str,
            }),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SolarPrognoseOptionsFlowHandler()

class SolarPrognoseOptionsFlowHandler(config_entries.OptionsFlow):
    """Behandelt Aenderungen in den Optionen."""
    async def async_step_init(self, user_input=None) -> FlowResult:
        if user_input:
            await validate_input(self.hass, user_input)
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    "api_key", 
                    default=self.config_entry.options.get(
                        "api_key", self.config_entry.data.get("api_key", "")
                    )
                ): str,
                vol.Optional(
                    "api_url", 
                    default=self.config_entry.options.get(
                        "api_url", self.config_entry.data.get("api_url", "")
                    )
                ): str,
            }),
        )