"""Constants for CCT Virtual Lights."""

DOMAIN = "cct_virtual_lights"

CONF_NAME = "name"
CONF_WARM_ENTITY = "warm_entity"
CONF_COLD_ENTITY = "cold_entity"
CONF_WARM_KELVIN = "warm_kelvin"
CONF_COLD_KELVIN = "cold_kelvin"
CONF_GAMMA = "gamma"
CONF_WARM_SCALE = "warm_scale"
CONF_COLD_SCALE = "cold_scale"
CONF_MIX_MODE = "mix_mode"
CONF_TRANSITION_SECONDS = "transition_seconds"
CONF_SCALE_UNIT = "scale_unit"

SCALE_UNIT_PERCENT = "percent"
SCALE_UNIT_FACTOR = "factor"

DEFAULT_WARM_KELVIN = 2400
DEFAULT_COLD_KELVIN = 5500
DEFAULT_GAMMA = 1.0
DEFAULT_WARM_SCALE_PERCENT = 100.0
DEFAULT_COLD_SCALE_PERCENT = 100.0
DEFAULT_TRANSITION_SECONDS = 0.5
DEFAULT_MIX_MODE = "constant_brightness"

MIX_MODE_CONSTANT_BRIGHTNESS = "constant_brightness"
MIX_MODE_MAX_BRIGHTNESS = "max_brightness"

ATTR_EFFECTIVE_BRIGHTNESS = "effective_brightness"
ATTR_WARM_LEVEL = "warm_level"
ATTR_COLD_LEVEL = "cold_level"
ATTR_MIX_MODE = "mix_mode"
ATTR_WARM_MIREDS = "warm_mired"
ATTR_COLD_MIREDS = "cold_mired"
ATTR_TARGET_MIREDS = "target_mired"
