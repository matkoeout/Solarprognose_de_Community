import logging
import async_timeout
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util
from homeassistant.helpers.event import async_call_later
from homeassistant.core import callback, HomeAssistant

from .const import DOMAIN, NIGHT_START_HOUR, NIGHT_END_HOUR, CONF_ENABLE_AUTOMATIC_POLLING

_LOGGER = logging.getLogger(__name__)
MIN_UPDATE_INTERVAL = timedelta(minutes=30)

class SolarPrognoseCoordinator(DataUpdateCoordinator):
    """Zentrale Instanz zum Abrufen und Aufbereiten der Prognosedaten."""
    
    def __init__(self, hass: HomeAssistant, api_url=None, api_key=None, enable_automatic_polling: bool = True):
        # Falls keine fertige URL geliefert wurde, bauen wir sie aus dem API-Key zusammen
        self.api_url = api_url or (
            "https://www.solarprognose.de/web/solarprediction/api/v1"
            f"?access-token={api_key}&type=hourly&_format=json"
        )
        
        self._enable_automatic_polling = enable_automatic_polling
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=None)
        
        self.api_status = None
        self.api_message = ""
        self.next_api_request = None
        self.last_api_success = None
        self.api_count_today = 0
        self.last_reset_day = dt_util.now().date()
        self._unsub_next_update = None

    async def async_setup(self):
        """Initiales Setup: Berücksichtigt die Nachtruhe auch beim Systemstart."""
        if not self._enable_automatic_polling:
            _LOGGER.info("Automatisches Polling deaktiviert. Kein automatischer Abruf.")
            return

        now = dt_util.now()
        
        # 1. Prüfen, ob wir uns aktuell in der Nachtruhe befinden
        if now.hour >= NIGHT_START_HOUR or now.hour < NIGHT_END_HOUR:
            target = now.replace(hour=NIGHT_END_HOUR, minute=5, second=0, microsecond=0)
            if now.hour >= NIGHT_START_HOUR:
                target += timedelta(days=1)
            
            delay = target - now
            _LOGGER.info(
                "Systemstart während der Nachtruhe. Update verzögert bis %s.", 
                target.strftime("%H:%M")
            )
            self.next_api_request = target
            self._schedule_next_update(delay)
            return

        # 2. Falls keine Nachtruhe: Prüfen, ob ein zukünftiger Zeitpunkt bekannt ist
        if self.next_api_request and self.next_api_request > now:
            delay = self.next_api_request - now
            _LOGGER.info(
                "Neustart erkannt. Warte bis %s für das nächste API-Update.", 
                self.next_api_request.strftime("%H:%M")
            )
            self._schedule_next_update(delay)
            return

        # 3. Ansonsten: Sofortiges Update
        await self.async_refresh()

    async def _async_update_data(self):
        """Daten von der API abrufen und verarbeiten."""
        now = dt_util.now()
        
        # Damit springt der Sensor in HA um Mitternacht sofort auf 0.
        if now.date() > self.last_reset_day:
            self.api_count_today = 0
            self.last_reset_day = now.date()

        # Wenn es zwischen 21:00 und 03:00 ist, brechen wir hier ab.
        if now.hour >= NIGHT_START_HOUR or now.hour < NIGHT_END_HOUR:
            
            # plant das Aufwachen kurz nach 03:00 Uhr (z.B. 03:05)
            target = now.replace(hour=NIGHT_END_HOUR, minute=5, second=0, microsecond=0)
            
            # Falls es jetzt z.B. 22:00 Uhr ist, muss das Ziel morgen sein
            if now.hour >= NIGHT_START_HOUR:
                target += timedelta(days=1)
            
            # Falls Ziel in der Vergangenheit liegt (Randfall), +1 Tag
            if target <= now:
                target += timedelta(days=1)
                
            delay = target - now
            _LOGGER.info("Nachtruhe: reset, aber API pausiert bis %s", target.strftime("%H:%M"))
            
            # Update planen, aber KEINE API anfragen
            self.next_api_request = target
            self._schedule_next_update(delay)
            
            # Wir geben die alten Daten zurück. 
            # Da sich api_count_today oben geändert hat, wird HA diesen neuen Wert (0) trotzdem anzeigen!
            return self.data or {}

        try:
            async with async_timeout.timeout(20):
                session = async_get_clientsession(self.hass)
                async with session.get(self.api_url) as response:
                    res = await response.json()
                    self.api_status = res.get("status")
                    self.api_message = res.get("message", "")
                    
                    # Status 0 bedeutet bei Solarprognose.de "Erfolg"
                    if self.api_status != 0:
                        _LOGGER.warning("API Fehler: %s. Versuche es in 60 Min erneut.", self.api_message)
                        self._schedule_next_update(timedelta(minutes=60))
                        return self.data or {}
                    # Zähler und Zeitpunkt nur bei OK
                    if self.api_status == 0:
                        self.api_count_today += 1
                        self.last_api_success = now

                    # Empfehlung der API für den naechsten optimalen Abrufzeitpunkt speichern
                    # 1. Basis-Verzögerung berechnen
                    delay_seconds = 150 * 60
                    if next_req := res.get("preferredNextApiRequestAt"):
                        ts_seconds = int(next_req.get("epochTimeUtc", 0))
                        if ts_seconds > 0:
                            req_time_utc = dt_util.utc_from_timestamp(ts_seconds)
                            # Berechne Sekunden bis zum Zielzeitpunkt
                            delay_seconds = (req_time_utc - dt_util.utcnow()).total_seconds()
                    
                    # 2. Nacht-Logik anwenden
                    next_planned = now + timedelta(seconds=max(60, delay_seconds))
                    
                    if next_planned.hour >= NIGHT_START_HOUR or next_planned.hour < NIGHT_END_HOUR:
                        # Ziel auf heute 03:00 Uhr
                        target = now.replace(hour=NIGHT_END_HOUR, minute=5, second=0, microsecond=0)
                        
                        # Wenn es bereits nach 03:00 Uhr ist (also wir sind im Bereich 21:00 - 23:59),
                        # muss das Ziel auf morgen 03:00 Uhr gesetzt werden.
                        if now.hour >= NIGHT_START_HOUR:
                            target += timedelta(days=1)
                        
                        # Wichtig: Falls target aus irgendeinem Grund in der Vergangenheit liegt (z.B. Punkt 02:59:59),
                        # stellen wir sicher, dass wir mindestens bis NIGHT_END_HOUR warten.
                        if target <= now:
                            target += timedelta(days=1)
                    
                        new_delay = (target - now).total_seconds()
                        _LOGGER.info("Nachtruhe aktiv. Nächste Abfrage geplant für: %s", target.strftime("%H:%M"))
                        
                        delay = timedelta(seconds=new_delay)
                        self.next_api_request = target
                    else:
                        delay = timedelta(seconds=max(60, delay_seconds))
                        self.next_api_request = next_planned                    
                    
                    self._schedule_next_update(delay)

                    # Rohdaten verarbeiten
                    processed_data = {}
                    for ts, v in res.get("data", {}).items():
                        local_dt = dt_util.as_local(dt_util.utc_from_timestamp(int(ts)))
                        processed_data[local_dt] = float(v[0])
                        
                    return processed_data

        except Exception as err:
            _LOGGER.error("Verbindungsfehler: %s. Retry in 60 Min.", err)
            self._schedule_next_update(timedelta(minutes=60))
            raise UpdateFailed(f"Verbindungsfehler zur API: {err}") from err

    def _schedule_next_update(self, delay: timedelta):
        """Plant das naechste Update."""
        if not self._enable_automatic_polling:
            return

        # Mindestintervall als Schutz vor unerwarteten kurzfristigen Empfehlungen
        delay = max(delay, MIN_UPDATE_INTERVAL)

        if self._unsub_next_update:
            self._unsub_next_update()

        @callback
        def _fire_refresh(_):
            self.hass.async_create_task(self.async_refresh())

        self._unsub_next_update = async_call_later(
            self.hass, 
            delay.total_seconds(), 
            _fire_refresh
        )

    def set_api_count(self, count: int):
        self.api_count_today = count

    def set_next_update(self, next_time):
        if self.next_api_request is None or next_time > dt_util.now():
            self.next_api_request = next_time

    def async_set_updated_data(self, data):
        self.data = data