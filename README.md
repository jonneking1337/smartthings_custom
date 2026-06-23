# SmartThings Custom — Home Assistant Integration

A custom Home Assistant integration that exposes Samsung-specific SmartThings capabilities that the official SmartThings integration does not support, such as picture mode, sound mode, and energy saving level.

## Why this exists

The official Home Assistant SmartThings integration handles authentication and device discovery well, but does not create entities for many Samsung-specific capabilities (prefixed `custom.*` and `samsungvd.*`). This integration borrows the OAuth token from the official integration — so you never have to manage tokens manually — and maps those capabilities to proper HA entities.

**Background:** Samsung SmartThings Personal Access Tokens (PAT) started expiring after 24 hours in December 2024, making direct PAT-based `rest_command` setups unreliable. This integration solves that by piggybacking on the official integration's OAuth session.

## Supported capabilities

| Capability | Entity type | Description |
|---|---|---|
| `custom.picturemode` | Select | Picture Mode (e.g. Eco, Entertain, Graphic) |
| `custom.soundmode` | Select | Sound Mode |
| `custom.energysavinglevel` | Select | Energy Saving Level |
| `custom.picturesize` | Select | Picture Size / Aspect Ratio |
| `samsungvd.ambientContent` | Switch | Art Mode / Ambient Content |
| `custom.allowedocr` | Switch | OCR |

For each Select entity an **Apply** button is also created (e.g. `button.apply_picture_mode`). Press it to re-send the currently selected value to the device — useful when the device resets its own setting and you want to force re-apply without changing the selection.

Only capabilities the device actually supports are created; disabled capabilities are automatically excluded.

## Requirements

- Home Assistant 2024.1 or newer
- The official **SmartThings** integration must already be installed and configured (Settings → Integrations → SmartThings)

## Installation

### Manual

1. Copy the `smartthings_custom` folder into your HA config directory:
   ```
   /config/custom_components/smartthings_custom/
   ```
2. Restart Home Assistant.

### HACS (custom repository)

1. In HACS, go to **Integrations → ⋮ → Custom repositories**.
2. Add `https://github.com/jonneking1337/smartthings_custom` with category **Integration**.
3. Install **SmartThings Custom** and restart Home Assistant.

## Setup

1. Go to **Settings → Integrations → Add integration**.
2. Search for **SmartThings Custom**.
3. Select the SmartThings device you want to add.
4. A confirmation screen shows which entities will be created based on the device's supported capabilities.
5. Confirm to finish setup.

## Entities created

After setup you will get entities named after the device, for example for a Samsung Odyssey OLED G9:

- `select.49_odyssey_oled_g9_picture_mode`
- `select.49_odyssey_oled_g9_sound_mode`
- `button.49_odyssey_oled_g9_apply_picture_mode`
- `switch.49_odyssey_oled_g9_art_mode`

## How it works

1. The official SmartThings integration maintains an OAuth session and a WebSocket connection to SmartThings.
2. This integration borrows that OAuth session — no separate credentials needed.
3. Device state is polled every 30 seconds and also updated in real-time via push events from the official integration's WebSocket client.
4. Commands are sent directly to the SmartThings API (`POST /v1/devices/{id}/commands`).

## Diagnostics

A `smartthings_custom.dump_capabilities` service is available in Developer Tools. Call it with a `device_id` to log all raw capabilities for a device — useful for discovering new features to add.

```yaml
service: smartthings_custom.dump_capabilities
data:
  device_id: "your-device-id-here"
```
