from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlowResult, ConfigFlow
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.helpers.selector import TextSelector, TextSelectorType, TextSelectorConfig, TimeSelector, \
    TimeSelectorConfig
from .const import DOMAIN, CONF_LOGIN_ENDPOINT, CONF_CONSUMPTION_ENDPOINT

_LOGGER = logging.getLogger(__name__)


class HkClpConsumptionConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(
            self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors = {}

        if user_input is not None:
            # Validate that all values are strings
            if not all(isinstance(x, str) for x in user_input.values()):
                errors["base"] = "All values must be strings"
            else:
                # Store the user input and create a config entry
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME],  # Name displayed in the UI
                    data=user_input,  # Store the user input for future use
                )

        # Display the form
        return self.async_show_form(
            step_id="user",
            description_placeholders=None,
            data_schema=vol.Schema({
                vol.Required(CONF_USERNAME): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT, autocomplete="username")
                ),
                vol.Required(CONF_PASSWORD): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD, autocomplete="current-password")
                ),
                vol.Required(CONF_LOGIN_ENDPOINT, default="https://api.clp.com.hk/ts1/ms/profile/accountManagement/loginByPassword"): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.URL)
                ),
                vol.Required(CONF_CONSUMPTION_ENDPOINT, default="https://api.clp.com.hk/ts1/ms/consumption/history"): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.URL)
                ),
            }),
            errors=errors,
        )