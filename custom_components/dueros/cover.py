"""Cover platform for Duer OS."""

from dueros_smarthome.models import Appliance, ApplianceType, TurnOnState, Degree

from homeassistant.components.cover import (
    CoverEntity,
    CoverDeviceClass,
    CoverEntityFeature,
    ATTR_POSITION,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, LOGGER
from .entity import DuerOSEntity


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup the cover platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.async_config_entry_first_refresh()
    covers = [
        appliance
        for appliance in coordinator.data.values()
        if ApplianceType.CURTAIN in appliance.appliance_types
    ]
    async_add_entities([DuerOSCover(coordinator, cover) for cover in covers])


class DuerOSCover(CoverEntity, DuerOSEntity):
    """Repersentation of a Duer OS Cover."""

    def __init__(
        self, coordinator: DataUpdateCoordinator, appliance: Appliance
    ) -> None:
        super().__init__(coordinator, appliance)
        self._update(appliance)
        if ApplianceType.CURTAIN in self._appliance.appliance_types:
            self._attr_device_class = CoverDeviceClass.CURTAIN
            self._attr_supported_features = (
                CoverEntityFeature.OPEN
                | CoverEntityFeature.CLOSE
                | CoverEntityFeature.SET_POSITION
                | CoverEntityFeature.STOP
            )

    def _update(self, appliance: Appliance) -> None:
        super()._update(appliance)
        if not self.available:
            return
        if TurnOnState.OFF == self._appliance.state_settings.turn_on_state.value:
            self._attr_is_closed = True
        else:
            self._attr_is_closed = False
            if self._appliance.state_settings.degree.value:
                self._attr_current_cover_position = (
                    self._appliance.state_settings.degree.value.value
                )

    async def async_open_cover(self, **kwargs) -> None:
        """Open the cover."""
        rsp = await self.coordinator.client.turn_on(self._appliance.appliance_id)
        DuerOSEntity._check_response(rsp)
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs) -> None:
        """Close the cover."""
        rsp = await self.coordinator.client.turn_off(self._appliance.appliance_id)
        DuerOSEntity._check_response(rsp)
        await self.coordinator.async_request_refresh()

    async def async_stop_cover(self, **kwargs) -> None:
        """Stop the cover."""
        rsp = await self.coordinator.client.pause(self._appliance.appliance_id)
        DuerOSEntity._check_response(rsp)
        await self.coordinator.async_request_refresh()

    async def async_set_cover_position(self, **kwargs) -> None:
        """Move the cover to a specific position."""
        percent = kwargs.get(ATTR_POSITION, self.current_cover_position)
        rsp = await self.coordinator.client.turn_on_percent(
            self._appliance.appliance_id, Degree(percent)
        )
        DuerOSEntity._check_response(rsp)
        await self.coordinator.async_request_refresh()
