"""Select entities for SmartThings custom capabilities."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CAPABILITY_SELECT, CONF_DEVICE_ID, CONF_DEVICE_NAME, CONF_CAPABILITIES
from .coordinator import SmartThingsCustomCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SmartThingsCustomCoordinator = hass.data[DOMAIN][entry.entry_id]
    found_capabilities: list[str] = entry.data.get(CONF_CAPABILITIES, [])

    entities = []
    for cap_id, cap_config in CAPABILITY_SELECT.items():
        if cap_id in found_capabilities:
            entities.append(
                SmartThingsSelectEntity(coordinator, entry, cap_id, cap_config)
            )

    if entities:
        async_add_entities(entities)


class SmartThingsSelectEntity(CoordinatorEntity, SelectEntity):
    """A select entity for a single SmartThings capability."""

    _attr_has_entity_name = True

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
        self._attr_unique_id = f"{entry.data[CONF_DEVICE_ID]}_{capability_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data[CONF_DEVICE_ID])},
            name=entry.data[CONF_DEVICE_NAME],
            manufacturer="Samsung",
        )

    @property
    def options(self) -> list[str]:
        """Return available options — from API data if available, else static."""
        data = self.coordinator.data or {}
        cap_data = data.get(self._capability_id, {})

        # Try dynamic options from API
        options_attr = self._cap_config.get("options_attribute")
        if options_attr and options_attr in cap_data:
            raw = cap_data[options_attr].get("value", [])
            if isinstance(raw, list) and raw:
                return raw

        # Fall back to static options
        return self._cap_config.get("options", [])

    @property
    def current_option(self) -> str | None:
        data = self.coordinator.data or {}
        cap_data = data.get(self._capability_id, {})
        attr = self._cap_config["attribute"]
        return cap_data.get(attr, {}).get("value")

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_send_command(
            self._capability_id,
            self._cap_config["command"],
            [option],
        )
        # Optimistically update local state
        if self.coordinator.data and self._capability_id in self.coordinator.data:
            self.coordinator.data[self._capability_id][self._cap_config["attribute"]]["value"] = option
            self.coordinator.async_set_updated_data(self.coordinator.data)
