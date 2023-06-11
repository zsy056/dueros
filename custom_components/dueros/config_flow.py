"""Adds config flow for DuerOS."""
from __future__ import annotations

from dueros_smarthome.client import SmartHomeClient
from dueros_smarthome.const import STATUS_OK
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME
from homeassistant.exceptions import IntegrationError
from homeassistant.helpers import selector

from .const import DOMAIN, LOGGER, BDUSS


class BlueprintFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Blueprint."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.FlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                await self._test_credentials(bduss=user_input[BDUSS])
            except RuntimeError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME,
                        default=(user_input or {}).get(CONF_USERNAME),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    vol.Required(BDUSS): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD
                        ),
                    ),
                }
            ),
            errors=_errors,
        )

    async def _test_credentials(self, bduss: str) -> None:
        """Validate credentials."""
        client = SmartHomeClient(bduss=bduss)
        rsp = await client.get_device_list()
        if STATUS_OK != rsp.status:
            LOGGER.error(rsp.msg)
            raise IntegrationError(rsp.msg)
