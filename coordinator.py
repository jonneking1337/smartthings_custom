"""DataUpdateCoordinator for smartthings_custom."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, POLL_INTERVAL, ST_API_BASE

_LOGGER = logging.getLogger(__name__)


class SmartThingsCustomCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls SmartThings device status and sends commands.

    Also subscribes to push-events from the official SmartThings integration
    so state changes are reflected in real-time without waiting for the next poll.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        smartthings_entry: ConfigEntry,
        device_id: str,
        device_name: str,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{device_id}",
            update_interval=timedelta(seconds=POLL_INTERVAL),
            always_update=True,
        )
        self.device_id = device_id
        self.device_name = device_name
        self._smartthings_entry = smartthings_entry
        self._session: config_entry_oauth2_flow.OAuth2Session | None = None
        self._unsub_dispatcher: list[Any] = []

    @callback
    def async_subscribe_to_push_updates(self) -> None:
        """Subscribe to real-time device events from the official SmartThings client.

        The official SmartThings integration maintains a WebSocket connection and
        exposes a SmartThings client via entry.runtime_data.client. We register
        a capability event listener on that client for our device so state changes
        are reflected immediately instead of waiting for the next 30s poll.
        """
        st_entry = self._smartthings_entry
        if not hasattr(st_entry, "runtime_data") or not hasattr(st_entry.runtime_data, "client"):
            _LOGGER.warning(
                "Official SmartThings integration has no runtime_data.client — "
                "push updates unavailable, falling back to polling only"
            )
            return

        client = st_entry.runtime_data.client

        @callback
        def _handle_event(event: Any) -> None:
            if getattr(event, "device_id", None) != self.device_id:
                return
            _LOGGER.debug(
                "Push event for %s: %s.%s = %s",
                self.device_name,
                getattr(event, "capability", "?"),
                getattr(event, "attribute", "?"),
                getattr(event, "value", "?"),
            )
            self.hass.async_create_task(self.async_refresh())

        # add_unspecified_device_event_listener catches all device events;
        # we filter by device_id inside the handler.
        unsub = client.add_unspecified_device_event_listener(_handle_event)
        self._unsub_dispatcher.append(unsub)
        _LOGGER.debug(
            "Subscribed to SmartThings push updates for %s via official client",
            self.device_name,
        )

    @callback
    def async_unsubscribe(self) -> None:
        """Unsubscribe from all event listeners."""
        for unsub in self._unsub_dispatcher:
            unsub()
        self._unsub_dispatcher.clear()

    async def _get_session(self) -> config_entry_oauth2_flow.OAuth2Session:
        """Get (or create) a valid OAuth2 session borrowed from SmartThings integration."""
        if self._session is None:
            implementations = await config_entry_oauth2_flow.async_get_implementations(
                self.hass, "smartthings"
            )
            if not implementations:
                raise UpdateFailed("No SmartThings OAuth implementation found")
            implementation = list(implementations.values())[0]
            self._session = config_entry_oauth2_flow.OAuth2Session(
                self.hass, self._smartthings_entry, implementation
            )
        await self._session.async_ensure_token_valid()
        return self._session

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch full device status in one API call."""
        try:
            session = await self._get_session()
            resp = await session.async_request(
                "GET",
                f"{ST_API_BASE}/devices/{self.device_id}/status",
            )
            resp.raise_for_status()
            data = await resp.json()
            # Flatten: {capability_id: {attribute: {value, ...}, ...}}
            return data.get("components", {}).get("main", {})
        except Exception as err:
            raise UpdateFailed(f"Failed to update {self.device_name}: {err}") from err

    async def async_send_command(
        self,
        capability: str,
        command: str,
        arguments: list[Any] | None = None,
    ) -> None:
        """Send a command to the device and optimistically update local state."""
        session = await self._get_session()
        payload = {
            "commands": [
                {
                    "component": "main",
                    "capability": capability,
                    "command": command,
                    "arguments": arguments or [],
                }
            ]
        }
        resp = await session.async_request(
            "POST",
            f"{ST_API_BASE}/devices/{self.device_id}/commands",
            json=payload,
        )
        if not resp.ok:
            body = await resp.text()
            _LOGGER.error(
                "Command failed for %s — %s.%s(%s) → HTTP %s: %s",
                self.device_name,
                capability,
                command,
                arguments,
                resp.status,
                body,
            )
            resp.raise_for_status()
        _LOGGER.debug(
            "Command sent to %s: %s.%s(%s)",
            self.device_name,
            capability,
            command,
            arguments,
        )

    async def async_dump_capabilities(self) -> dict[str, Any]:
        """Fetch and return full raw device status for diagnostics."""
        session = await self._get_session()
        resp = await session.async_request(
            "GET",
            f"{ST_API_BASE}/devices/{self.device_id}/status",
        )
        resp.raise_for_status()
        return await resp.json()

    @staticmethod
    async def async_fetch_devices(
        hass: HomeAssistant,
        smartthings_entry: ConfigEntry,
    ) -> list[dict[str, Any]]:
        """Fetch all SmartThings devices — used during config flow."""
        implementations = await config_entry_oauth2_flow.async_get_implementations(
            hass, "smartthings"
        )
        if not implementations:
            raise Exception("No SmartThings OAuth implementation found")
        implementation = list(implementations.values())[0]
        session = config_entry_oauth2_flow.OAuth2Session(
            hass, smartthings_entry, implementation
        )
        await session.async_ensure_token_valid()
        resp = await session.async_request("GET", f"{ST_API_BASE}/devices")
        resp.raise_for_status()
        data = await resp.json()
        return data.get("items", [])

    @staticmethod
    async def async_fetch_device_capabilities(
        hass: HomeAssistant,
        smartthings_entry: ConfigEntry,
        device_id: str,
    ) -> list[str]:
        """Return list of active capability IDs the device supports.

        Filters out capabilities listed in custom.disabledCapabilities so
        we don't create entities for features the device doesn't actually support.
        """
        implementations = await config_entry_oauth2_flow.async_get_implementations(
            hass, "smartthings"
        )
        implementation = list(implementations.values())[0]
        session = config_entry_oauth2_flow.OAuth2Session(
            hass, smartthings_entry, implementation
        )
        await session.async_ensure_token_valid()

        # Fetch device profile for full capability list
        resp = await session.async_request(
            "GET", f"{ST_API_BASE}/devices/{device_id}"
        )
        resp.raise_for_status()
        data = await resp.json()
        caps = []
        for comp in data.get("components", []):
            if comp.get("id") == "main":
                for cap in comp.get("capabilities", []):
                    caps.append(cap["id"])

        # Fetch current status to check which capabilities are disabled
        resp2 = await session.async_request(
            "GET", f"{ST_API_BASE}/devices/{device_id}/status"
        )
        resp2.raise_for_status()
        status = await resp2.json()
        main = status.get("components", {}).get("main", {})
        disabled = (
            main.get("custom.disabledCapabilities", {})
            .get("disabledCapabilities", {})
            .get("value", [])
        )

        if disabled:
            _LOGGER.debug("Device %s has disabled capabilities: %s", device_id, disabled)

        return [c for c in caps if c not in disabled]
