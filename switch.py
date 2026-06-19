"""Switch entities for SmartThings custom capabilities."""
from __future__ import annotations
import logging
from typing import Any
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, CAPABILITY_SWITCH, CONF_DEVICE_ID, CONF_DEVICE_NAME, CONF_CAPABILITIES
from .coordinator import SmartThingsCustomCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    found_capabilities = entry.data.get(CONF_CAPABILITIES, [])
    entities = []
    for cap_id, cap_config in CAPABILITY_SWITCH.items():
        if cap_id in found_capabilities:
            entities.append(SmartThingsSwitchEntity(coordinator, entry, cap_id, cap_config))
    if entities:
        async_add_entities(entities)

class SmartThingsSwitchEntity(CoordinatorEntity, SwitchEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, capability_id, cap_config):
        super().__init__(coordinator)
        self._capability_id = capability_id
        self._cap_config = cap_config
        self._attr_name = cap_config["name"]
        self._attr_icon = cap_config.get("icon")
        self._attr_unique_id = f"{entry.data[CONF_DEVICE_ID]}_{capability_id}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.data[CONF_DEVICE_ID])}, name=entry.data[CONF_DEVICE_NAME], manufacturer="Samsung")

    @property
    def is_on(self):
        data = self.coordinator.data or {}
        cap_data = data.get(self._capability_id, {})
        attr = self._cap_config["attribute"]
        entry = cap_data.get(attr)
        if entry is None:
            return None
        value = entry.get("value")
        if value is None:
            return None
        return str(value).lower() == str(self._cap_config["on_value"]).lower()

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_send_command(self._capability_id, self._cap_config["on_command"], self._cap_config.get("on_args", []))
        self._optimistic_update(True)

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_send_command(self._capability_id, self._cap_config["off_command"], self._cap_config.get("off_args", []))
        self._optimistic_update(False)

    def _optimistic_update(self, is_on):
        if not self.coordinator.data:
            return
        cap_data = self.coordinator.data.get(self._capability_id)
        if cap_data is None:
            return
        attr = self._cap_config["attribute"]
        if attr not in cap_data:
            _LOGGER.debug("Skipping optimistic update for %s.%s — attribute not in status data", self._capability_id, attr)
            return
        value = self._cap_config["on_value"] if is_on else "false"
        cap_data[attr]["value"] = value
        self.coordinator.async_set_updated_data(self.coordinator.data)
