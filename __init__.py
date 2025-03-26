import logging
import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from .const import DOMAIN, CONF_LOGIN_ENDPOINT, CONF_CONSUMPTION_ENDPOINT
from .hk_clp import HkClp
from .util import format_date_range, extract_consumption_data
import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up is called when Home Assistant is loading our component."""
    return True
    
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the component by logging in and fetching electricity consumption."""
    _LOGGER.info("Setting up hk_clp_consumption component..")

    try:
        # Extract configuration values from the entry
        _hk_clp = HkClp(
            username=entry.data[CONF_USERNAME],
            password=entry.data[CONF_PASSWORD],
            login_endpoint=entry.data[CONF_LOGIN_ENDPOINT],
            consumption_endpoint=entry.data[CONF_CONSUMPTION_ENDPOINT],
        )

        # Initialize storage for API data
        hass.data[DOMAIN] = {
            "client": _hk_clp,
            "username": entry.data[CONF_USERNAME],
        }

        # Create an aiohttp session for API calls
        async with aiohttp.ClientSession() as session:
            try:
                # Step 1: Login to the electricity provider
                if not await _hk_clp.login_by_password(session):
                    return False

                # Step 2: Fetch electricity consumption using the token
                from_date, to_date = format_date_range()
                _LOGGER.info(f"Fetching consumption data from {from_date} to {to_date}")
                
                if not await _hk_clp.fetch_electricity_consumption(
                    session=session,
                    from_date=from_date,
                    to_date=to_date,
                    mode="Daily",
                    data_type="Unit",
                ):
                    return False

                # Step 3: Extract and process consumption data
                extract_consumption_data(_hk_clp.consumption_data)

                return True

            except aiohttp.ClientError as err:
                _LOGGER.error(f"Network error during API calls: {err}")
                return False
            except Exception as err:
                _LOGGER.error(f"Error during API calls: {err}")
                return False

    except KeyError as err:
        _LOGGER.error(f"Missing required configuration key: {err}")
        return False
    except Exception as err:
        _LOGGER.error(f"Unexpected error during setup: {err}")
        return False