"""DuerOS entity class."""
from __future__ import annotations

from dueros_smarthome.client import DeviceActionResponse
from dueros_smarthome.const import STATUS_OK, STATUS_NOT_LOGIN
from dueros_smarthome.models import Appliance, Connectivity

from homeassistant.core import callback
from homeassistant.exceptions import ConfigEntryAuthFailed, IntegrationError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME, VERSION, LOGGER
from .coordinator import DuerOSDataUpdateCoordinator, get_unique_id


class DuerOSEntity(CoordinatorEntity):
    """DuerOSEntity class."""

    def _set_unique_id(self) -> None:
        self._attr_unique_id = get_unique_id(self._appliance)

    def __init__(
        self, coordinator: DuerOSDataUpdateCoordinator, appliance: Appliance
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_available = False
        self._attr_has_entity_name = True
        self._update(appliance)
        self._set_unique_id()
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            name=NAME,
            model=VERSION,
            manufacturer=self._appliance.bot_name,
        )

    def _update(self, appliance: Appliance):
        self._appliance = appliance
        self._attr_available = (
            self._appliance.state_settings.connectivity.value == Connectivity.REACHABLE
        )
        self._attr_name = self._appliance.friendly_name

    @callback
    def _handle_coordinator_update(self) -> None:
        self._update(self.coordinator.data[self.unique_id])
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        return self._attr_available

    @staticmethod
    def _check_response(rsp: DeviceActionResponse) -> None:
        if STATUS_NOT_LOGIN == rsp.status:
            LOGGER.error(rsp.msg)
            raise ConfigEntryAuthFailed(rsp.msg)
        if STATUS_OK != rsp.status:
            LOGGER.error(rsp.msg)
            raise IntegrationError(rsp.msg)
