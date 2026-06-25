"""Number entities for SmartThings capabilities (e.g. volume slider)."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CAPABILITY_NUMBER, CONF_DEVICE_ID, CONF_DEVICE_NAME, CONF_CAPABILITIES
from .coordinator import SmartThingsCustomCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SmartThingsCustomCoordinator = hass.data[DOMAIN][entry.entry_id]
    found_capabilities: list[str] = entry.data.get(CONF_CAPABILITIES, [])

    entities = [
        SmartThingsNumberEntity(coordinator, entry, cap_id, cap_config)
        for cap_id, cap_config in CAPABILITY_NUMBER.items()
        if cap_id in found_capabilities
    ]

    if entities:
        async_add_entities(entities)


class SmartThingsNumberEntity(CoordinatorEntity, NumberEntity):
    """A number/slider entity for a single SmartThings capability."""

    _attr_has_entity_name = True
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator: SmartThingsCustomCoordinator,
        entry: ConfigEntry,
        capability_id: str,
        cap_config: dict[str, Any],
    ) -> None:
        super().__init__(coordinator)
        self._capability_id = capability_id
        self._cap_config = cap_config
        self._attr_name = cap_config["name"]
        self._attr_icon = cap_config.get("icon")
        self._attr_native_min_value = cap_config["min"]
        self._attr_native_max_value = cap_config["max"]
        self._attr_native_step = cap_config["step"]
        self._attr_native_unit_of_measurement = cap_config.get("unit")
        self._attr_unique_id = f"{entry.data[CONF_DEVICE_ID]}_{capability_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data[CONF_DEVICE_ID])},
            name=entry.data[CONF_DEVICE_NAME],
            manufacturer="Samsung",
        )

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data or {}
        cap_data = data.get(self._capability_id, {})
        raw = cap_data.get(self._cap_config["attribute"], {}).get("value")
        if raw is None:
            return None
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        int_value = int(value)
        await self.coordinator.async_send_command(
            self._capability_id,
            self._cap_config["command"],
            [int_value],
        )
        # Optimistic update
        data = self.coordinator.data
        if data and self._capability_id in data:
            attr = self._cap_config["attribute"]
            if attr in data[self._capability_id]:
                data[self._capability_id][attr]["value"] = int_value
                self.coordinator.async_set_updated_data(data)
