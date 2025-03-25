from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlowResult, ConfigFlow
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorType,
    TextSelectorConfig,
)

from .const import DOMAIN, CONF_LOGIN_ENDPOINT, CONF_CONSUMPTION_ENDPOINT

_LOGGER = logging.getLogger(__name__)


class HkClpConsumptionConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HK CLP Consumption."""

    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(
            self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                # Validate that all values are strings and not empty
                if not all(isinstance(x, str) and x.strip() for x in user_input.values()):
                    errors["base"] = "All values must be non-empty strings"
                else:
                    # Validate URLs
                    if not user_input[CONF_LOGIN_ENDPOINT].startswith(("http://", "https://")):
                        errors[CONF_LOGIN_ENDPOINT] = "Invalid login endpoint URL"
                    if not user_input[CONF_CONSUMPTION_ENDPOINT].startswith(("http://", "https://")):
                        errors[CONF_CONSUMPTION_ENDPOINT] = "Invalid consumption endpoint URL"

                    if not errors:
                        # Store the user input and create a config entry
                        return self.async_create_entry(
                            title=user_input[CONF_USERNAME],
                            data=user_input,
                        )
            except Exception as err:
                _LOGGER.error("Error validating configuration: %s", err)
                errors["base"] = "Configuration validation failed"

        # Display the form
        return self.async_show_form(
            step_id="user",
            description_placeholders=None,
            data_schema=vol.Schema({
                vol.Required(
                    CONF_USERNAME,
                    description="Your CLP account username"
                ): TextSelector(
                    TextSelectorConfig(
                        type=TextSelectorType.TEXT,
                        autocomplete="username"
                    )
                ),
                vol.Required(
                    CONF_PASSWORD,
                    description="Your CLP account password"
                ): TextSelector(
                    TextSelectorConfig(
                        type=TextSelectorType.PASSWORD,
                        autocomplete="current-password"
                    )
                ),
                vol.Required(
                    CONF_LOGIN_ENDPOINT,
                    description="CLP login API endpoint",
                    default="https://api.clp.com.hk/ts1/ms/profile/accountManagement/loginByPassword"
                ): TextSelector(
                    TextSelectorConfig(
                        type=TextSelectorType.URL,
                        autocomplete="off"
                    )
                ),
                vol.Required(
                    CONF_CONSUMPTION_ENDPOINT,
                    description="CLP consumption API endpoint",
                    default="https://api.clp.com.hk/ts1/ms/consumption/history"
                ): TextSelector(
                    TextSelectorConfig(
                        type=TextSelectorType.TEXT,
                        autocomplete="off"
                    )
                )
            }),
            errors=errors,
        )