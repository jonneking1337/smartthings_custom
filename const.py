"""Constants for smartthings_custom integration."""

DOMAIN = "smartthings_custom"
SMARTTHINGS_DOMAIN = "smartthings"
POLL_INTERVAL = 30  # seconds

CONF_DEVICE_ID = "device_id"
CONF_DEVICE_NAME = "device_name"
CONF_ST_ENTRY_ID = "smartthings_entry_id"
CONF_CAPABILITIES = "found_capabilities"

ST_API_BASE = "https://api.smartthings.com/v1"

# Known capabilities → select entities
# Each entry: attribute to read, command to send, where to find options
CAPABILITY_SELECT: dict[str, dict] = {
    "custom.picturemode": {
        "attribute": "pictureMode",
        "command": "setPictureMode",
        "options_attribute": "supportedPictureModes",
        "name": "Picture Mode",
        "icon": "mdi:television-play",
    },
    "custom.soundmode": {
        "attribute": "soundMode",
        "command": "setSoundMode",
        "options_attribute": "supportedSoundModes",
        "name": "Sound Mode",
        "icon": "mdi:speaker",
    },
    "custom.energysavinglevel": {
        "attribute": "energySavingLevel",
        "command": "setEnergySavingLevel",
        "options": ["off", "minimum", "medium", "maximum", "auto"],
        "name": "Energy Saving",
        "icon": "mdi:leaf",
    },
    "custom.picturesize": {
        "attribute": "pictureSize",
        "command": "setPictureSize",
        "options_attribute": "supportedPictureSizes",
        "name": "Picture Size",
        "icon": "mdi:aspect-ratio",
    },
}

# Known capabilities → switch entities
CAPABILITY_SWITCH: dict[str, dict] = {
    "samsungvd.ambientContent": {
        "attribute": "ambientContent",
        "on_value": "true",
        "on_command": "setAmbientContent",
        "on_args": ["true"],
        "off_command": "stopAmbientContent",
        "off_args": [],
        "name": "Art Mode",
        "icon": "mdi:image-frame",
    },
    "custom.allowedocr": {
        "attribute": "ocrStatus",
        "on_value": "on",
        "on_command": "setOcrStatus",
        "on_args": ["on"],
        "off_command": "setOcrStatus",
        "off_args": ["off"],
        "name": "OCR",
        "icon": "mdi:ocr",
    },
}
