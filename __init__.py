import logging
import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from .const import DOMAIN, CONF_LOGIN_ENDPOINT, CONF_CONSUMPTION_ENDPOINT
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
        username = entry.data[CONF_USERNAME]
        password = entry.data[CONF_PASSWORD]
        login_endpoint = entry.data[CONF_LOGIN_ENDPOINT]
        consumption_endpoint = entry.data[CONF_CONSUMPTION_ENDPOINT]

        # Validate that all required values are strings
        if not all(isinstance(x, str) for x in [username, password, login_endpoint, consumption_endpoint]):
            _LOGGER.error("All configuration values must be strings")
            return False

        # Initialize storage for API data
        hass.data[DOMAIN] = {
            "username": username,
            "auth_token": None,
            "login_profile": None,
            "consumption_data": None
        }

        # Create an aiohttp session for API calls
        async with aiohttp.ClientSession() as session:
            try:
                # Step 1: Login to the electricity provider
                login_payload = {
                    "username": username,
                    "password": password
                }

                _LOGGER.info("Firing call to CLP Login API...")
                async with session.post(login_endpoint, json=login_payload) as login_response:
                    if login_response.status == 200:
                        login_data = await login_response.json()
                        res_data = login_data.get("data", {})
                        if not res_data:
                            _LOGGER.error("No profile return from login API")
                            return False
                            
                        token = res_data.get("access_token")
                        if not token:
                            _LOGGER.error("No token found in login response")
                            return False

                        hass.data[DOMAIN]["auth_token"] = token
                        hass.data[DOMAIN]["login_profile"] = res_data
                        _LOGGER.info("Successfully logged in to CLP")
                    else:
                        _LOGGER.error(f"Login failed with status: {login_response.status}")
                        return False

                # Step 2: Fetch electricity consumption using the token
                _LOGGER.info("Firing call to CLP consumption API...")
                headers = {"authorization": token}
                async with session.get(consumption_endpoint, headers=headers) as consumption_response:
                    if consumption_response.status == 200:
                        consumption_data = await consumption_response.json()
                        res_data = consumption_data.get("data", {})
                        if not res_data:
                            _LOGGER.error("No data return from consumption API")
                            return False

                        hass.data[DOMAIN]["consumption_data"] = res_data
                        _LOGGER.info("Successfully fetched electricity consumption")
                    else:
                        _LOGGER.error(f"Failed to fetch consumption: {consumption_response.status}")
                        return False

            except aiohttp.ClientError as err:
                _LOGGER.error(f"Network error during API calls: {err}")
                return False
            except Exception as err:
                _LOGGER.error(f"Error during API calls: {err}")
                return False

        return True
    except KeyError as err:
        _LOGGER.error(f"Missing required configuration key: {err}")
        return False
    except Exception as err:
        _LOGGER.error(f"Unexpected error during setup: {err}")
        return False