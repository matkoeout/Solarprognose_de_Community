import logging
import json
from datetime import timedelta
from dataclasses import dataclass
from typing import Callable, Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
    SensorEntityDescription,
)
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, NIGHT_START_HOUR, NIGHT_END_HOUR

_LOGGER = logging.getLogger(__name__)

@dataclass(frozen=True)
class SolarSensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[Any], Any] = None
    attr_fn: Callable[[Any], dict[str, Any]] = None

def build_forecast_attrs(coord):
    """Erstellt die Attribute fuer den Forecast-Sensor inkl. evcc-Format."""
    sorted_data = sorted((coord.data or {}).items())
    
    # 1. Die originalen Home Assistant Attribute
    attrs = {
        "forecast": [{"datetime": dt.isoformat(), "energy": val} 
                     for dt, val in sorted_data],
        "integrated_forecast": True
    }
    
    # 2. Das neue evcc Array aufbauen
    # dt ist der Start der Stunde. end ist exakt eine Stunde spaeter.
    # val ist in kWh, daher * 1000 um Watt zu erhalten.
    evcc_list = [
        {
            "start": dt.isoformat(),
            "end": (dt + timedelta(hours=1)).isoformat(),
            "value": int(val * 1000)
        }
        for dt, val in sorted_data
    ]
    
    attrs["evcc_data"] = json.dumps(evcc_list)
    return attrs

SENSOR_TYPES: tuple[SolarSensorEntityDescription, ...] = (
    SolarSensorEntityDescription(
        key="today_total",
        translation_key="today_total",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        # Summiert alle Werte des aktuellen Kalendertages
        value_fn=lambda coord: round(sum(val for dt, val in (coord.data or {}).items() 
            if dt.date() == dt_util.now().date()), 2),
    ),
    SolarSensorEntityDescription(
        key="tomorrow_total",
        translation_key="tomorrow_total",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda coord: round(sum(val for dt, val in (coord.data or {}).items() 
            if dt.date() == (dt_util.now().date() + timedelta(days=1))), 2),
    ),
    SolarSensorEntityDescription(
        key="rest_day",
        translation_key="rest_day",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        # Verhindert Fehler, falls dt_util.now() exakt zwischen zwei Timestamps liegt
        value_fn=lambda coord: round(sum(
            val for dt, val in (coord.data or {}).items() 
            if dt.date() == dt_util.now().date() and dt >= dt_util.now().replace(minute=0, second=0, microsecond=0)
        ), 2),
    ),
    SolarSensorEntityDescription(
        key="current_hour",
        translation_key="current_hour",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda coord: int((coord.data or {}).get(
            dt_util.now().replace(minute=0, second=0, microsecond=0), 0) * 1000),
    ),
    SolarSensorEntityDescription(
        key="next_hour",
        translation_key="next_hour",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda coord: int((coord.data or {}).get(
            (dt_util.now() + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0), 0) * 1000),
    ),
    SolarSensorEntityDescription(
        key="peak_power_today",
        translation_key="peak_power_today",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda coord: int(max([val for dt, val in (coord.data or {}).items() 
            if dt.date() == dt_util.now().date()] or [0]) * 1000),
    ),
    SolarSensorEntityDescription(
        key="peak_time_today",
        translation_key="peak_time_today",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda coord: (
            max([(val, dt) for dt, val in (coord.data or {}).items() if dt.date() == dt_util.now().date()] or [(0, None)])[1]
        ),
    ),
    SolarSensorEntityDescription(
        key="peak_power_tomorrow",
        translation_key="peak_power_tomorrow",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda coord: int(max([val for dt, val in (coord.data or {}).items() 
            if dt.date() == (dt_util.now().date() + timedelta(days=1))] or [0]) * 1000),
    ),
SolarSensorEntityDescription(
        key="forecast",
        translation_key="forecast",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        # Erzeugt den gleitenden Prognose-Wert fuer das HA-Energie-Dashboard
        value_fn=lambda coord: round(sum(val for dt, val in (coord.data or {}).items() 
            if dt.date() == dt_util.now().date() and dt <= dt_util.now()), 2),
        attr_fn=build_forecast_attrs
    ),
    SolarSensorEntityDescription(
        key="peak_time_tomorrow",
        translation_key="peak_time_tomorrow",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda coord: (
            max([(val, dt) for dt, val in (coord.data or {}).items() 
                if dt.date() == (dt_util.now().date() + timedelta(days=1))] or [(0, None)])[1]
        ),
    ),
    SolarSensorEntityDescription(
        key="api_count",
        translation_key="api_count",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:api",
        value_fn=lambda coord: coord.api_count_today,
    ),
    SolarSensorEntityDescription(
        key="api_status",
        translation_key="api_status",
        value_fn=lambda coord: (
            "Schlafend" if (dt_util.now().hour >= NIGHT_START_HOUR or dt_util.now().hour < NIGHT_END_HOUR) 
            else ("OK" if coord.api_status == 0 else "Fehler")
        ),
        attr_fn=lambda coord: {"api_message": coord.api_message},
    ),
    SolarSensorEntityDescription(
        key="next_update", 
        translation_key="next_update", 
        device_class=SensorDeviceClass.TIMESTAMP, 
        value_fn=lambda coord: coord.next_api_request 
    ),
    SolarSensorEntityDescription(
        key="last_update", 
        translation_key="last_update", 
        device_class=SensorDeviceClass.TIMESTAMP, 
        value_fn=lambda coord: coord.last_api_success
    ),
)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    custom_name = entry.data.get("name", "Solarprognose")
    async_add_entities(SolarSensor(coordinator, entry, custom_name, desc) for desc in SENSOR_TYPES)

class SolarSensor(CoordinatorEntity, RestoreEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, custom_name, description):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": custom_name,
            "manufacturer": "Solarprognose.de (Community)",
            "model": "WebAPI v1",
        }

    async def async_added_to_hass(self) -> None:
        """Wird aufgerufen, wenn die Entitaet hinzugefuegt wird."""
        await super().async_added_to_hass()

        # Letzten Zustand aus der Home Assistant Datenbank laden
        last_state = await self.async_get_last_state()
        if not last_state or last_state.state in (None, "unknown", "unavailable"):
            return
    
        try:
            # 1. API-Zaehler wiederherstellen
            if self.entity_description.key == "api_count":
                restored_count = int(last_state.state)
                if restored_count > self.coordinator.api_count_today:
                    self.coordinator.set_api_count(restored_count)
    
            # 2. Naechsten Abrufzeitpunkt an den Coordinator uebergeben
            elif self.entity_description.key == "next_update":
                restored_dt = dt_util.parse_datetime(last_state.state)
                if restored_dt and restored_dt > dt_util.now():
                    _LOGGER.info("Wiederhergestellte Abfragezeit uebernommen: %s", restored_dt)
                    self.coordinator.next_api_request = restored_dt
    
            # 3. Zeitpunkt des letzten Erfolgs wiederherstellen
            elif self.entity_description.key == "last_update":
                self.coordinator.last_api_success = dt_util.parse_datetime(last_state.state)

            # 4. Prognosedaten (Zeitreihe) aus dem forecast-Sensor rekonstruieren
            # Dies befuellt den Coordinator, damit alle anderen Sensoren sofort Daten haben
            elif self.entity_description.key == "forecast":
                if "forecast" in last_state.attributes:
                    restored_data = {}
                    for item in last_state.attributes["forecast"]:
                        # ISO-String zurueck in datetime Objekt umwandeln
                        dt = dt_util.parse_datetime(item["datetime"])
                        if dt:
                            # Lokalzeit-Objekt sicherstellen
                            local_dt = dt_util.as_local(dt)
                            restored_data[local_dt] = float(item["energy"])
                    
                    # Nur befuellen, wenn der Coordinator aktuell leer ist
                    if restored_data and not self.coordinator.data:
                        _LOGGER.info("Prognosedaten erfolgreich aus Cache wiederhergestellt")
                        self.coordinator.async_set_updated_data(restored_data)

            # 5. Fuer alle anderen Sensoren (Ertrag/Leistung) den Wert lokal puffern
            else:
                try:
                    self._attr_native_value = float(last_state.state)
                except ValueError:
                    pass
    
        except (ValueError, TypeError) as err:
            _LOGGER.error("Fehler beim Wiederherstellen von %s: %s", self.entity_description.key, err)

    @property
    def native_value(self):
        """Gibt den aktuellen Status des Sensors zurueck."""
        # 1. Wenn der Coordinator Daten hat, nutzen wir diese (Normalbetrieb)
        if self.coordinator.data:
            return self.entity_description.value_fn(self.coordinator)

        # 2. Wenn der Coordinator leer ist (nach Neustart), 
        # versuchen wir den alten Zustand des Sensors aus dem Cache zu nutzen.
        if getattr(self, "_attr_native_value", None) is not None:
            return self._attr_native_value

        # 3. Fallback fuer administrative Sensoren, die direkt am Coordinator haengen
        allowed_without_data = ["api_count", "api_status", "next_update", "last_update"]
        if self.entity_description.key in allowed_without_data:
            return self.entity_description.value_fn(self.coordinator)

        return None

    @property
    def extra_state_attributes(self):
        """Gibt zusaetzliche Attribute zurueck."""
        # Attribute nur berechnen, wenn Daten vorhanden sind oder es kein Forecast-Sensor ist
        if not self.coordinator.data and self.entity_description.key == "forecast":
            return None
        return self.entity_description.attr_fn(self.coordinator) if self.entity_description.attr_fn else None
