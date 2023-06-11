"""DataUpdateCoordinator for dueros."""
from __future__ import annotations

from datetime import timedelta
from dueros_smarthome.models import Appliance
from dueros_smarthome.client import SmartHomeClient
from dueros_smarthome.const import STATUS_OK, STATUS_NOT_LOGIN

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.exceptions import ConfigEntryAuthFailed


from .const import DOMAIN, LOGGER, BOT_ID_APPLIANCE_ID_SEPARATOR


def get_unique_id(appliance: Appliance) -> str:
    """Get appliance's unique ID."""
    return f"{appliance.bot_id}{BOT_ID_APPLIANCE_ID_SEPARATOR}{appliance.appliance_id}"


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class DuerOSDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: SmartHomeClient,
    ) -> None:
        """Initialize."""
        self.client = client
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=5),
        )

    async def _async_update_data(self):
        """Update data via library."""
        rsp = await self.client.get_device_list()
        if STATUS_NOT_LOGIN == rsp.status:
            LOGGER.error(rsp.msg)
            raise ConfigEntryAuthFailed(rsp.msg)
        if STATUS_OK != rsp.status:
            LOGGER.error(rsp.msg)
            raise UpdateFailed(rsp.msg)
        return {get_unique_id(appliance): appliance for appliance in rsp.appliances}
