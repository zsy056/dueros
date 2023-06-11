"""DuerOS entity class."""
from __future__ import annotations

from dueros_smarthome.models import Appliance, Connectivity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME, VERSION
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
        self._appliance = appliance
        self._set_unique_id()
        self._attr_name = self._appliance.friendly_name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            name=NAME,
            model=VERSION,
            manufacturer=self._appliance.bot_name,
        )
        self._attr_has_entity_name = True

    def _update(self, appliance: Appliance):
        self._appliance = appliance
        self._attr_available = (
            self._appliance.state_settings.connectivity.value == Connectivity.REACHABLE
        )
