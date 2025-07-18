import requests
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import async_generate_entity_id
import logging
import time

from .const import (
    DEFAULT_NAME,
    CONF_ID,
    CONF_NAME,
    CONF_NUM,
    CONF_GROUP,
    CONF_STOPS,
)

ENTITY_ID_FORMAT = "sensor.mpk_lodz_{}"
SCAN_INTERVAL = timedelta(minutes=1)
REQUEST_TIMEOUT = 10  # Timeout in seconds
MAX_RETRIES = 3
RETRY_DELAY = 1  # Delay between retries in seconds

_LOGGER = logging.getLogger(__name__)

# Track last error to prevent repeated logging
_LAST_ERROR_TIME = {}
_ERROR_LOG_INTERVAL = 300  # 5 minutes between repeated error logs

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up MPK Łódź sensor from a config entry."""
    config = entry.data
    name = config.get(CONF_NAME, DEFAULT_NAME)
    stops = config.get(CONF_STOPS, [])

    entities = []
    for stop_cfg in stops:
        stop_id = str(stop_cfg.get(CONF_ID, "0"))
        stop_num = str(stop_cfg.get(CONF_NUM, "0"))
        stop_group = str(stop_cfg.get(CONF_GROUP, "0"))
        
        options_used = sum(1 for x in [stop_id, stop_num, stop_group] if x != "0")
        if options_used != 1:
            _log_error(
                f"Please configure exactly one option: stop ID ({stop_id}), stop number ({stop_num}), "
                f"or stop group ({stop_group}). Currently {options_used} options are set."
            )
            continue

        use_stop_num = stop_num != "0"
        use_group = stop_group != "0"
        stop = stop_num if use_stop_num else stop_group if use_group else stop_id

        try:
            real_stop_name = await hass.async_add_executor_job(
                get_stop_name, stop, use_stop_num, use_group
            )

            if real_stop_name is None:
                _log_error(f"Could not find stop with the given parameters. Please check if the configured stop exists.")
                continue

            departures = await hass.async_add_executor_job(
                get_departures, stop, use_stop_num, use_group
            )

            stop_type = "num" if use_stop_num else "group" if use_group else "id"
            
            for i in range(min(10, len(departures))):
                sanitized_stop_name = real_stop_name.lower().replace(' ', '_')
                entity_id = async_generate_entity_id(
                    ENTITY_ID_FORMAT, 
                    f"{stop_type}_{stop}_{sanitized_stop_name}_{i}", 
                    hass=hass
                )
                sensor = MpkLodzDepartureSensor(
                    entity_id, real_stop_name, stop, i, departures[i], use_stop_num, use_group
                )
                entities.append(sensor)
        except Exception as e:
            _log_error(f"Error setting up stop {stop}: {str(e)}")
            continue

    async_add_entities(entities, True)

class MpkLodzDepartureSensor(SensorEntity):
    def __init__(self, entity_id, stop_name, stop, index, departure, use_stop_num, use_group):
        self.entity_id = entity_id
        self._stop_name = stop_name
        self._stop = stop
        self._index = index
        self._departure = departure
        self._use_stop_num = use_stop_num
        self._use_group = use_group
        self._name = f"{stop_name} {index}"
        self._available = True
        
        stop_type = "num" if use_stop_num else "group" if use_group else "id"
        self._attr_unique_id = f"mpk_lodz_{stop_type}_{stop}_{index}"
        self._attr_should_poll = True

    @property
    def name(self):
        return self._name

    @property
    def icon(self):
        return "mdi:bus-clock"

    @property
    def available(self):
        return self._available

    @property
    def state(self):
        return self._departure.get("departure_time") if self._available else None

    @property
    def extra_state_attributes(self):
        if not self._available:
            return {}

        features = ""
        if self._departure.get("low_floor") and self._departure.get("air_conditioned"):
            features = '<span style="color: orange;"><ha-icon icon="mdi:wheelchair"></ha-icon><span style="color: lightblue;"><ha-icon icon="mdi:snowflake"></ha-icon>'
        elif self._departure.get("low_floor"):
            features = '<span style="color: orange;"><ha-icon icon="mdi:wheelchair"></ha-icon>'
        elif self._departure.get("air_conditioned"):
            features = '<span style="color: lightblue;"><ha-icon icon="mdi:snowflake"></ha-icon>'

        attributes = {
            "line": self._departure.get("line", "N/A"),
            "direction": self._departure.get("direction", "N/A"),
            "time": self._departure.get("departure_time", "N/A"),
            "features": features,
            "stop_name": self._stop_name,
        }

        if self._index == 0:
            attributes.update({
                "current_time": self._departure.get("current_time", "N/A"),
                "alert": self._departure.get("alert", " "),
            })

        return attributes

    async def async_update(self):
        """Fetch new state data for the sensor."""
        try:
            departures = await self.hass.async_add_executor_job(
                get_departures,
                self._stop,
                self._use_stop_num,
                self._use_group
            )
            
            if len(departures) > self._index:
                self._departure = departures[self._index]
                self._available = True
            else:
                self._available = False
                _log_error(f"No departure data available for {self.entity_id}")
        except Exception as e:
            _log_error(f"Error updating sensor {self.entity_id}: {str(e)}")
            self._available = False

def _log_error(message):
    """
    Log an error, but prevent repeated logging of the same error 
    within a short time frame.
    """
    current_time = time.time()
    
    # Use full error message as key to track unique errors
    if message not in _LAST_ERROR_TIME or \
       current_time - _LAST_ERROR_TIME.get(message, 0) > _ERROR_LOG_INTERVAL:
        _LOGGER.error(message)
        _LAST_ERROR_TIME[message] = current_time

def get_stop_name(stop, use_stop_num, use_group):
    data = get_data(stop, use_stop_num, use_group)
    if data is None:
        return None
    return data[0].attrib["name"]

def get_departures(stop, use_stop_num, use_group):
    data = get_data(stop, use_stop_num, use_group)
    if data is None:
        return []

    # Safely get current time and alert, defaulting to empty strings
    current_time = data.attrib.get('time', '')
    alert = data[0].attrib.get('ds', ' ')

    try:
        # Find the Day element which contains the departures
        # Sometimes there's an <A> element first, sometimes not
        day_element = None
        for child in data[0]:
            if child.tag == 'Day':
                day_element = child
                break
        
        if day_element is None:
            _log_error(f"No Day element found for stop {stop}")
            return []
            
        departures = day_element  # The Day element contains the R (departure) elements
    except (IndexError, AttributeError) as e:
        _log_error(f"Unable to parse departures for stop {stop}: {str(e)}")
        return []

    parsed_departures = []

    for departure in departures:
        try:
            # Skip if not an R element (departure)
            if departure.tag != 'R':
                continue
                
            line = departure.attrib.get("nr", "N/A")
            direction = departure.attrib.get("dir", "N/A")

            features = departure.attrib.get("vuw", "")
            low_floor = "N" in features
            air_conditioned = "K" in features

            # Get the first S element (schedule) from this departure
            schedule_element = departure.find('S')
            if schedule_element is not None:
                departure_time = schedule_element.attrib.get('t', 'Unknown')
            else:
                departure_time = 'Unknown'

            parsed_departures.append({
                "line": line,
                "direction": direction,
                "departure_time": departure_time,
                "current_time": current_time,
                "alert": alert,
                "low_floor": low_floor,
                "air_conditioned": air_conditioned
            })
        except Exception as e:
            _log_error(f"Error parsing individual departure: {str(e)}")

    return parsed_departures

def get_data(stop, use_stop_num, use_group):
    if not use_stop_num and not use_group:
        address = f"http://rozklady.lodz.pl/Home/GetTimeTableReal?busStopId={stop}"
    elif use_stop_num:
        address = f"http://rozklady.lodz.pl/Home/GetTimeTableReal?busStopNum={stop}"
    elif use_group:
        address = f"http://rozklady.lodz.pl/Home/getTimeTableReal?busStopGroupId={stop}"

    headers = {
        'referer': address,
    }

    session = requests.Session()
    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(
                address, 
                headers=headers, 
                timeout=REQUEST_TIMEOUT
            )
            if response.status_code == 200 and response.content:
                return ET.fromstring(response.text)
            _log_error(f"Failed to get data, status code: {response.status_code}")
            return None
        except requests.Timeout:
            if attempt < MAX_RETRIES - 1:
                _log_error(f"Request timed out, attempt {attempt + 1} of {MAX_RETRIES}")
                time.sleep(RETRY_DELAY)
            else:
                _log_error("Max retries exceeded, request timed out")
                return None
        except Exception as e:
            _log_error(f"Error fetching data: {str(e)}")
            return None
    return None
