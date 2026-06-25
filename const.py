"""Constants for smartthings_custom integration."""

DOMAIN = "smartthings_custom"
SMARTTHINGS_DOMAIN = "smartthings"
POLL_INTERVAL = 60  # seconds

CONF_DEVICE_ID = "device_id"
CONF_DEVICE_NAME = "device_name"
CONF_ST_ENTRY_ID = "smartthings_entry_id"
CONF_CAPABILITIES = "found_capabilities"

ST_API_BASE = "https://api.smartthings.com/v1"

# Known capabilities → select entities
# Each entry: attribute to read, command to send, where to find options
# apply_button=False suppresses the "Apply" button for capabilities where it makes no sense
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
    "mediaInputSource": {
        "attribute": "inputSource",
        "command": "setInputSource",
        "options_attribute": "supportedInputSources",
        "name": "Input Source",
        "icon": "mdi:hdmi-port",
        "apply_button": False,
    },
}

# Known capabilities → switch entities
CAPABILITY_SWITCH: dict[str, dict] = {
    "switch": {
        "attribute": "switch",
        "on_value": "on",
        "on_command": "on",
        "on_args": [],
        "off_command": "off",
        "off_args": [],
        "name": "Power",
        "icon": "mdi:power",
    },
    "audioMute": {
        "attribute": "mute",
        "on_value": "muted",
        "on_command": "mute",
        "on_args": ["muted"],
        "off_command": "mute",
        "off_args": ["unmuted"],
        "name": "Mute",
        "icon": "mdi:volume-off",
    },
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

# Known capabilities → number entities (sliders)
CAPABILITY_NUMBER: dict[str, dict] = {
    "audioVolume": {
        "attribute": "volume",
        "command": "setVolume",
        "min": 0,
        "max": 100,
        "step": 1,
        "unit": None,
        "name": "Volume",
        "icon": "mdi:volume-high",
    },
}

# Known capabilities → standalone action buttons (e.g. media transport)
# Each capability maps to a list of button definitions.
CAPABILITY_MEDIA_BUTTON: dict[str, list[dict]] = {
    "mediaPlayback": [
        {"command": "play",        "name": "Play",         "icon": "mdi:play"},
        {"command": "pause",       "name": "Pause",        "icon": "mdi:pause"},
        {"command": "stop",        "name": "Stop",         "icon": "mdi:stop"},
        {"command": "fastForward", "name": "Fast Forward", "icon": "mdi:fast-forward"},
        {"command": "rewind",      "name": "Rewind",       "icon": "mdi:rewind"},
    ],
}
