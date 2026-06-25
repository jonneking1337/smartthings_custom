"""Button entities for SmartThings — apply-select buttons and media transport."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CAPABILITY_SELECT,
    CAPABILITY_MEDIA_BUTTON,
    CONF_DEVICE_ID,
    CONF_DEVICE_NAME,
    CONF_CAPABILITIES,
)
from .coordinator import SmartThingsCustomCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SmartThingsCustomCoordinator = hass.data[DOMAIN][entry.entry_id]
    found_capabilities: list[str] = entry.data.get(CONF_CAPABILITIES, [])

    entities: list[ButtonEntity] = []

    # "Apply" button for each select capability (re-sends current value)
    for cap_id, cap_config in CAPABILITY_SELECT.items():
        if cap_id in found_capabilities and cap_config.get("apply_button", True):
            entities.append(
                SmartThingsApplySelectButton(coordinator, entry, cap_id, cap_config)
            )

    # Media transport buttons (play, pause, stop, fast-forward, rewind)
    for cap_id, button_list in CAPABILITY_MEDIA_BUTTON.items():
        if cap_id in found_capabilities:
            for btn in button_list:
                entities.append(
                    SmartThingsMediaButton(coordinator, entry, cap_id, btn)
                )

    if entities:
        async_add_entities(entities)


class SmartThingsMediaButton(CoordinatorEntity, ButtonEntity):
    """A button that fires a single media-transport command (play, pause, stop…)."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SmartThingsCustomCoordinator,
        entry: ConfigEntry,
        capability_id: str,
        btn_config: dict[str, Any],
    ) -> None:
        super().__init__(coordinator)
        self._capability_id = capability_id
        self._command = btn_config["command"]
        self._attr_name = btn_config["name"]
        self._attr_icon = btn_config.get("icon")
        self._attr_unique_id = f"{entry.data[CONF_DEVICE_ID]}_{capability_id}_{self._command}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data[CONF_DEVICE_ID])},
            name=entry.data[CONF_DEVICE_NAME],
            manufacturer="Samsung",
        )

    async def async_press(self) -> None:
        await self.coordinator.async_send_command(
            self._capability_id,
            self._command,
            [],
        )


class SmartThingsApplySelectButton(CoordinatorEntity, ButtonEntity):
    """Button that re-sends the current value of a select capability."""

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
        self._attr_name = f"Apply {cap_config['name']}"
        self._attr_icon = cap_config.get("icon")
        self._attr_unique_id = f"{entry.data[CONF_DEVICE_ID]}_{capability_id}_apply"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data[CONF_DEVICE_ID])},
            name=entry.data[CONF_DEVICE_NAME],
            manufacturer="Samsung",
        )

    async def async_press(self) -> None:
        data = self.coordinator.data or {}
        cap_data = data.get(self._capability_id, {})
        current = cap_data.get(self._cap_config["attribute"], {}).get("value")

        if current is None:
            _LOGGER.warning(
                "Apply button pressed but no current value known for %s — skipping",
                self._capability_id,
            )
            return

        _LOGGER.debug("Re-applying %s = %s", self._capability_id, current)
        await self.coordinator.async_send_command(
            self._capability_id,
            self._cap_config["command"],
            [current],
        )
