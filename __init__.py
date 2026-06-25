"""SmartThings Custom — generic integration for Samsung-specific capabilities."""
from __future__ import annotations

import json
import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, CONF_DEVICE_ID, CONF_DEVICE_NAME, CONF_ST_ENTRY_ID
from .coordinator import SmartThingsCustomCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.BUTTON, Platform.NUMBER, Platform.SELECT, Platform.SWITCH]

DUMP_CAPABILITIES_SCHEMA = vol.Schema(
    {vol.Required(CONF_DEVICE_ID): cv.string}
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a device from a config entry."""
    st_entry = hass.config_entries.async_get_entry(entry.data[CONF_ST_ENTRY_ID])
    if not st_entry:
        _LOGGER.error(
            "SmartThings config entry %s not found — reinstall integration",
            entry.data[CONF_ST_ENTRY_ID],
        )
        return False

    coordinator = SmartThingsCustomCoordinator(
        hass,
        st_entry,
        entry.data[CONF_DEVICE_ID],
        entry.data[CONF_DEVICE_NAME],
    )

    await coordinator.async_config_entry_first_refresh()
    coordinator.async_subscribe_to_push_updates()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register dump_capabilities diagnostic service (once)
    if not hass.services.has_service(DOMAIN, "dump_capabilities"):

        async def handle_dump_capabilities(call: ServiceCall) -> None:
            """Log all raw capabilities for a device — useful for discovering new features."""
            device_id = call.data[CONF_DEVICE_ID]
            # Find the coordinator for this device_id
            target_coordinator: SmartThingsCustomCoordinator | None = None
            for coord in hass.data[DOMAIN].values():
                if isinstance(coord, SmartThingsCustomCoordinator):
                    if coord.device_id == device_id:
                        target_coordinator = coord
                        break

            if target_coordinator is None:
                _LOGGER.error(
                    "dump_capabilities: no coordinator found for device_id=%s. "
                    "Add the device via Settings → Integrations first.",
                    device_id,
                )
                return

            data = await target_coordinator.async_dump_capabilities()
            _LOGGER.warning(
                "=== SmartThings capabilities for %s ===\n%s",
                device_id,
                json.dumps(data, indent=2),
            )

        hass.services.async_register(
            DOMAIN,
            "dump_capabilities",
            handle_dump_capabilities,
            schema=DUMP_CAPABILITIES_SCHEMA,
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator: SmartThingsCustomCoordinator = hass.data[DOMAIN].get(entry.entry_id)
    if coordinator:
        coordinator.async_unsubscribe()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    # Remove service if no more entries
    if not hass.data.get(DOMAIN):
        hass.services.async_remove(DOMAIN, "dump_capabilities")

    return unload_ok
