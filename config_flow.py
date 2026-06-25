"""Config flow for smartthings_custom integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    SMARTTHINGS_DOMAIN,
    CONF_DEVICE_ID,
    CONF_DEVICE_NAME,
    CONF_ST_ENTRY_ID,
    CONF_CAPABILITIES,
    CAPABILITY_SELECT,
    CAPABILITY_SWITCH,
    CAPABILITY_NUMBER,
    CAPABILITY_MEDIA_BUTTON,
)
from .coordinator import SmartThingsCustomCoordinator

_LOGGER = logging.getLogger(__name__)

KNOWN_CAPABILITIES = (
    set(CAPABILITY_SELECT.keys())
    | set(CAPABILITY_SWITCH.keys())
    | set(CAPABILITY_NUMBER.keys())
    | set(CAPABILITY_MEDIA_BUTTON.keys())
)


async def _get_smartthings_entry(hass: HomeAssistant):
    """Get the first available SmartThings config entry."""
    entries = hass.config_entries.async_entries(SMARTTHINGS_DOMAIN)
    if not entries:
        return None
    return entries[0]


class SmartThingsCustomConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle setup via UI: pick device → confirm."""

    VERSION = 1

    def __init__(self) -> None:
        self._devices: list[dict[str, Any]] = []
        self._st_entry_id: str = ""
        self._selected_device: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Step 1: Pick a SmartThings device."""
        errors: dict[str, str] = {}

        st_entry = await _get_smartthings_entry(self.hass)
        if not st_entry:
            return self.async_abort(reason="no_smartthings_integration")

        self._st_entry_id = st_entry.entry_id

        if not self._devices:
            try:
                self._devices = await SmartThingsCustomCoordinator.async_fetch_devices(
                    self.hass, st_entry
                )
            except Exception as err:
                _LOGGER.error("Failed to fetch SmartThings devices: %s", err)
                return self.async_abort(reason="cannot_connect")

        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID]
            self._selected_device = next(
                (d for d in self._devices if d["deviceId"] == device_id), {}
            )
            if self._selected_device:
                return await self.async_step_confirm()
            errors[CONF_DEVICE_ID] = "device_not_found"

        # Build device dropdown options
        device_options = {
            d["deviceId"]: d.get("label", d.get("name", d["deviceId"]))
            for d in self._devices
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_DEVICE_ID): vol.In(device_options)}
            ),
            errors=errors,
        )

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Step 2: Show which entities will be created, ask for confirmation."""
        device_id = self._selected_device["deviceId"]
        device_name = self._selected_device.get(
            "label", self._selected_device.get("name", device_id)
        )

        # Check for duplicate
        await self.async_set_unique_id(device_id)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            # Discover capabilities
            st_entry = self.hass.config_entries.async_get_entry(self._st_entry_id)
            try:
                all_caps = await SmartThingsCustomCoordinator.async_fetch_device_capabilities(
                    self.hass, st_entry, device_id
                )
            except Exception as err:
                _LOGGER.error("Failed to fetch capabilities for %s: %s", device_id, err)
                return self.async_abort(reason="cannot_connect")

            found = [c for c in all_caps if c in KNOWN_CAPABILITIES]
            _LOGGER.info(
                "Device %s supports these known capabilities: %s", device_name, found
            )

            return self.async_create_entry(
                title=device_name,
                data={
                    CONF_DEVICE_ID: device_id,
                    CONF_DEVICE_NAME: device_name,
                    CONF_ST_ENTRY_ID: self._st_entry_id,
                    CONF_CAPABILITIES: found,
                },
            )

        # Show summary of what will be created
        st_entry = self.hass.config_entries.async_get_entry(self._st_entry_id)
        try:
            all_caps = await SmartThingsCustomCoordinator.async_fetch_device_capabilities(
                self.hass, st_entry, device_id
            )
        except Exception:
            all_caps = []

        found = [c for c in all_caps if c in KNOWN_CAPABILITIES]
        found_names = []
        for cap in found:
            if cap in CAPABILITY_SELECT:
                found_names.append(f"Select: {CAPABILITY_SELECT[cap]['name']}")
            elif cap in CAPABILITY_SWITCH:
                found_names.append(f"Switch: {CAPABILITY_SWITCH[cap]['name']}")
            elif cap in CAPABILITY_NUMBER:
                found_names.append(f"Number: {CAPABILITY_NUMBER[cap]['name']}")
            elif cap in CAPABILITY_MEDIA_BUTTON:
                btns = ", ".join(b["name"] for b in CAPABILITY_MEDIA_BUTTON[cap])
                found_names.append(f"Buttons: {btns}")

        description = (
            f"Device: {device_name}\n"
            f"Entities to create: {', '.join(found_names) if found_names else 'None found'}"
        )

        return self.async_show_form(
            step_id="confirm",
            description_placeholders={"summary": description},
            data_schema=vol.Schema({}),
        )
