import logging
from datetime import datetime
from typing import TypedDict, List, Optional, Dict, Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

class Usage(TypedDict):
    """Typed Dict for the daily usage"""
    date: datetime
    usage: float

class HkClp:
    """Wrapper for API calls"""

    def __init__(
        self,
        username: str,
        password: str,
        login_endpoint: str,
        consumption_endpoint: str,
    ):
        self._username = username
        self._password = password
        self._login_endpoint = login_endpoint
        self._consumption_endpoint = consumption_endpoint
        self._auth_token: Optional[str] = None
        self._login_profile: Optional[Dict[str, Any]] = None
        self._consumption_data: Optional[Dict[str, Any]] = None

    @property
    def auth_token(self) -> Optional[str]:
        """Get the current auth token."""
        return self._auth_token

    @property
    def login_profile(self) -> Optional[Dict[str, Any]]:
        """Get the login profile data."""
        return self._login_profile

    @property
    def consumption_data(self) -> Optional[Dict[str, Any]]:
        """Get the consumption data."""
        return self._consumption_data

    async def login_by_password(
        self,
        session: aiohttp.ClientSession,
    ) -> bool:
        """Call the POST /loginByPassword API to get access token"""
        try:
            _LOGGER.info("Firing call to CLP Login API...")
            login_payload = {
                "username": self._username,
                "password": self._password
            }
            async with session.post(self._login_endpoint, json=login_payload) as login_response:
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

                    self._auth_token = token
                    self._login_profile = res_data
                    _LOGGER.info("Successfully logged in to CLP")
                    return True
                else:
                    _LOGGER.error(f"Login failed with status: {login_response.status}")
                    return False
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Network error during login: {err}")
            return False
        except Exception as err:
            _LOGGER.error(f"Unexpected error during login: {err}")
            return False

    async def fetch_electricity_consumption(
        self,
        session: aiohttp.ClientSession,
        from_date: str,
        to_date: str,
        mode: str,
        data_type: str,
    ) -> bool:
        """Call the POST /consumption/history API to fetch daily electricity usage"""
        try:
            if not self._auth_token:
                _LOGGER.error("No auth token available. Please login first.")
                return False

            _LOGGER.info("Firing call to CLP consumption API...")
            headers = {"authorization": self._auth_token}
            consumption_payload = {
                "ca": self._username,
                "fromDate": from_date,
                "toDate": to_date,
                "mode": mode,
                "type": data_type
            }
            async with session.post(self._consumption_endpoint, headers=headers, json=consumption_payload) as consumption_response:
                if consumption_response.status == 200:
                    consumption_data = await consumption_response.json()
                    res_data = consumption_data.get("data", {})
                    if not res_data:
                        _LOGGER.error("No data return from consumption API")
                        return False

                    self._consumption_data = res_data
                    _LOGGER.info("Successfully fetched electricity consumption")
                    return True
                else:
                    _LOGGER.error(f"Failed to fetch consumption: {consumption_response.status}")
                    return False
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Network error during consumption fetch: {err}")
            return False
        except Exception as err:
            _LOGGER.error(f"Unexpected error during consumption fetch: {err}")
            return False