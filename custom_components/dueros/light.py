"""Light platform for Duer OS."""

from dueros_smarthome.models import (
    Appliance,
    ApplianceType,
    TurnOnState,
    Brightness,
    ColorTemperatureInKelvin,
)

from homeassistant.components.light import (
    LightEntity,
    ColorMode,
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
)
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)

from .const import DOMAIN, BRIGHTNESS_MAX
from .entity import DuerOSEntity


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup the light platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.async_config_entry_first_refresh()
    lights = [
        appliance
        for appliance in coordinator.data.values()
        if ApplianceType.LIGHT in appliance.appliance_types
    ]
    async_add_entities([DuerOSLight(coordinator, light) for light in lights])


class DuerOSLight(LightEntity, DuerOSEntity):
    """Representation of a DuerOS Light."""

    def __init__(
        self, coordinator: DataUpdateCoordinator, appliance: Appliance
    ) -> None:
        super().__init__(coordinator, appliance)
        self._update(appliance)
        self._attr_color_mode = ColorMode.COLOR_TEMP
        self._attr_supported_color_modes = {ColorMode.COLOR_TEMP, ColorMode.BRIGHTNESS}

    @staticmethod
    def brightness_dueros_to_ha(brightness: Brightness) -> int:
        """Convert percentage to HA brightness."""
        return brightness.percentage * BRIGHTNESS_MAX / 100

    @staticmethod
    def brightness_ha_to_dueros(brightness: int) -> Brightness:
        """Convert HA brightness to DuerOS"""
        return Brightness(1 + int((brightness - 1) * 100 / BRIGHTNESS_MAX))

    def _update(self, appliance: Appliance) -> None:
        super()._update(appliance)
        if not self.available:
            return
        self._attr_entity_picture = self._appliance.icon_urls[0]
        if self._appliance.state_settings.brightness.value:
            self._attr_brightness = DuerOSLight.brightness_dueros_to_ha(
                self._appliance.state_settings.brightness.value
            )
        if self._appliance.state_settings.color_temperature_in_kelvin.value:
            self._attr_color_temp_kelvin = (
                self._appliance.state_settings.color_temperature_in_kelvin.value.in_kelvin
            )
        self._attr_min_color_temp_kelvin = (
            self._appliance.state_settings.color_temperature_in_kelvin.value.kelvin_min
        )
        self._attr_max_color_temp_kelvin = (
            self._appliance.state_settings.color_temperature_in_kelvin.value.kelvin_max
        )
        self._attr_is_on = (
            self._appliance.state_settings.turn_on_state.value == TurnOnState.ON
        )

    async def _set_brightness(self, appliance_id: str, brightness: int):
        """Set brightness."""
        rsp = await self.coordinator.client.set_brightness_percentage(
            appliance_id, DuerOSLight.brightness_ha_to_dueros(brightness)
        )
        DuerOSEntity._check_response(rsp)

    async def _set_color_temp(self, appliance_id: str, color_temp_kelvin: int):
        """Set color temp."""
        color_temp = ColorTemperatureInKelvin(
            1
            + int(
                (color_temp_kelvin - self.min_color_temp_kelvin)
                / (self.max_color_temp_kelvin - self.min_color_temp_kelvin)
            ),
            self.min_color_temp_kelvin,
            self.max_color_temp_kelvin,
        )
        rsp = await self.coordinator.client.set_color_temperature(
            appliance_id, color_temp
        )
        DuerOSEntity._check_response(rsp)

    async def async_turn_on(self, **kwargs):
        brightness = kwargs.get(ATTR_BRIGHTNESS, self.brightness)
        if brightness:
            self._attr_brightness = brightness
            await self._set_brightness(self._appliance.appliance_id, brightness)
        color_temp_in_kelvin = kwargs.get(
            ATTR_COLOR_TEMP_KELVIN, self.color_temp_kelvin
        )
        if color_temp_in_kelvin:
            self._attr_color_temp_kelvin = color_temp_in_kelvin
            await self._set_color_temp(
                self._appliance.appliance_id, color_temp_in_kelvin
            )
        self._attr_is_on = True
        rsp = await self.coordinator.client.turn_on(self._appliance.appliance_id)
        DuerOSEntity._check_response(rsp)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        rsp = await self.coordinator.client.turn_off(self._appliance.appliance_id)
        DuerOSEntity._check_response(rsp)
        await self.coordinator.async_request_refresh()
