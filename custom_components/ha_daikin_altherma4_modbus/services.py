"""Services for Daikin Altherma 4 Modbus integration."""

import logging

try:
    import voluptuous as vol
    from homeassistant.config_entries import ConfigEntryState
    from homeassistant.exceptions import ServiceValidationError
    from homeassistant.helpers import config_validation as cv
    from homeassistant.helpers.service import async_register_admin_service

    HAS_HA = True
except ImportError:
    # Fallback for testing when homeassistant is not available
    HAS_HA = False

from .const import (
    DOMAIN,
    HVAC_COOL,
    HVAC_HEAT,
    HVAC_OFF,
    REGISTER_DHW_HVAC_MODE,
    REGISTER_OPERATION_MODE,
    SERVICE_SET_ADDITIONAL_ZONE_STATE,
    SERVICE_SET_DHW_STATE,
    SERVICE_SET_MAIN_ZONE_STATE,
    SERVICE_SET_OPERATION_MODE,
    SERVICE_SET_SMART_GRID_MODE,
)
from .register_constants import COIL_REGISTERS, HOLDING_REGISTERS

_LOGGER = logging.getLogger(__name__)

ATTR_CONFIG_ENTRY_ID = "config_entry_id"
ATTR_OPERATION_MODE = "operation_mode"
ATTR_STATE = "state"
ATTR_SMART_GRID_MODE = "smart_grid_mode"

# Operation mode mapping for service calls (lowercase keys for service API)
OPERATION_MODE_MAP = {
    "off": HVAC_OFF,
    "heat": HVAC_HEAT,
    "cool": HVAC_COOL,
}


# Smart Grid mode mapping for service calls (lowercase keys for service API)
def get_smart_grid_mode_map():
    """Get Smart Grid mode mapping from register constants."""
    # Find the Smart Grid register in HOLDING_REGISTERS
    for register in HOLDING_REGISTERS:
        if register.register_name == "holding_56":
            return {v.lower(): k for k, v in register.enum_map.items()}
    return {}


# Service schemas (only defined when HA is available)
if HAS_HA:
    SERVICE_SET_OPERATION_MODE_SCHEMA = vol.Schema(
        {
            vol.Required(ATTR_CONFIG_ENTRY_ID): cv.string,
            vol.Required(ATTR_OPERATION_MODE): vol.In(["off", "heat", "cool"]),
        }
    )

    SERVICE_SET_DHW_STATE_SCHEMA = vol.Schema(
        {
            vol.Required(ATTR_CONFIG_ENTRY_ID): cv.string,
            vol.Required(ATTR_STATE): cv.boolean,
        }
    )

    SERVICE_SET_MAIN_ZONE_STATE_SCHEMA = vol.Schema(
        {
            vol.Required(ATTR_CONFIG_ENTRY_ID): cv.string,
            vol.Required(ATTR_STATE): cv.boolean,
        }
    )

    SERVICE_SET_ADDITIONAL_ZONE_STATE_SCHEMA = vol.Schema(
        {
            vol.Required(ATTR_CONFIG_ENTRY_ID): cv.string,
            vol.Required(ATTR_STATE): cv.boolean,
        }
    )

    # Get Smart Grid mode options from register constants
    smart_grid_options = list(get_smart_grid_mode_map().keys())
    SERVICE_SET_SMART_GRID_MODE_SCHEMA = vol.Schema(
        {
            vol.Required(ATTR_CONFIG_ENTRY_ID): cv.string,
            vol.Required(ATTR_SMART_GRID_MODE): vol.In(smart_grid_options),
        }
    )
else:
    # Placeholders for testing - create dummy schemas that accept anything
    def _make_dummy_schema(fields):
        class DummySchema:
            def __call__(self, data):
                return data

        return DummySchema()

    SERVICE_SET_OPERATION_MODE_SCHEMA = _make_dummy_schema(None)
    SERVICE_SET_DHW_STATE_SCHEMA = _make_dummy_schema(None)
    SERVICE_SET_MAIN_ZONE_STATE_SCHEMA = _make_dummy_schema(None)
    SERVICE_SET_ADDITIONAL_ZONE_STATE_SCHEMA = _make_dummy_schema(None)
    SERVICE_SET_SMART_GRID_MODE_SCHEMA = _make_dummy_schema(None)


def get_operation_mode_map():
    """Return the operation mode mapping."""
    return OPERATION_MODE_MAP.copy()


def _get_coil_address(register_name: str) -> int:
    """Get the coil address from register name."""
    for coil in COIL_REGISTERS:
        if coil.register_name == register_name:
            return coil.address
    raise ValueError(f"Coil register {register_name} not found")


if HAS_HA:

    def _get_entry_and_validate(hass, config_entry_id):
        """Get config entry and validate it's loaded."""
        entry = hass.config_entries.async_get_entry(config_entry_id)
        if entry is None:
            raise ServiceValidationError(
                f"Configuration entry {config_entry_id} not found"
            )
        if entry.state != ConfigEntryState.LOADED:
            raise ServiceValidationError(
                f"Configuration entry {config_entry_id} is not loaded"
            )
        return entry

    async def async_set_operation_mode(hass, call) -> None:
        """Set the heat pump operation mode."""
        config_entry_id = call.data[ATTR_CONFIG_ENTRY_ID]
        operation_mode = call.data[ATTR_OPERATION_MODE]

        entry = _get_entry_and_validate(hass, config_entry_id)
        runtime_data = entry.runtime_data
        manager = runtime_data.manager

        mode_value = OPERATION_MODE_MAP.get(operation_mode)
        if mode_value is None:
            raise ServiceValidationError(f"Invalid operation mode: {operation_mode}")

        await manager.write_holding_register(REGISTER_OPERATION_MODE, mode_value)
        _LOGGER.debug(
            "Set operation mode to %s (value: %s) for entry %s",
            operation_mode,
            mode_value,
            config_entry_id,
        )

    async def async_set_dhw_state(hass, call) -> None:
        """Enable or disable Domestic Hot Water."""
        config_entry_id = call.data[ATTR_CONFIG_ENTRY_ID]
        state = call.data[ATTR_STATE]

        entry = _get_entry_and_validate(hass, config_entry_id)
        runtime_data = entry.runtime_data
        manager = runtime_data.manager

        coil_address = _get_coil_address(REGISTER_DHW_HVAC_MODE)
        await manager.write_coil_register(coil_address, state)
        _LOGGER.debug(
            "Set DHW state to %s for entry %s",
            state,
            config_entry_id,
        )

    async def async_set_main_zone_state(hass, call) -> None:
        """Enable or disable the main zone."""
        config_entry_id = call.data[ATTR_CONFIG_ENTRY_ID]
        state = call.data[ATTR_STATE]

        entry = _get_entry_and_validate(hass, config_entry_id)
        runtime_data = entry.runtime_data
        manager = runtime_data.manager

        # Main zone is coil_2
        coil_address = _get_coil_address("coil_2")
        await manager.write_coil_register(coil_address, state)
        _LOGGER.debug(
            "Set main zone state to %s for entry %s",
            state,
            config_entry_id,
        )

    async def async_set_additional_zone_state(hass, call) -> None:
        """Enable or disable the additional zone."""
        config_entry_id = call.data[ATTR_CONFIG_ENTRY_ID]
        state = call.data[ATTR_STATE]

        entry = _get_entry_and_validate(hass, config_entry_id)
        runtime_data = entry.runtime_data
        manager = runtime_data.manager

        # Additional zone is coil_3
        coil_address = _get_coil_address("coil_3")
        await manager.write_coil_register(coil_address, state)
        _LOGGER.debug(
            "Set additional zone state to %s for entry %s",
            state,
            config_entry_id,
        )

    async def async_set_smart_grid_mode(hass, call) -> None:
        """Set the Smart Grid operation mode."""
        config_entry_id = call.data[ATTR_CONFIG_ENTRY_ID]
        smart_grid_mode = call.data[ATTR_SMART_GRID_MODE]

        entry = _get_entry_and_validate(hass, config_entry_id)
        runtime_data = entry.runtime_data
        manager = runtime_data.manager

        smart_grid_mode_map = get_smart_grid_mode_map()
        mode_value = smart_grid_mode_map.get(smart_grid_mode)
        if mode_value is None:
            raise ServiceValidationError(f"Invalid Smart Grid mode: {smart_grid_mode}")

        await manager.write_holding_register("holding_56", mode_value)
        _LOGGER.debug(
            "Set Smart Grid mode to %s (value: %s) for entry %s",
            smart_grid_mode,
            mode_value,
            config_entry_id,
        )

else:
    # Dummy functions for testing imports
    async def async_set_operation_mode(hass, call):
        pass

    async def async_set_dhw_state(hass, call):
        pass

    async def async_set_main_zone_state(hass, call):
        pass

    async def async_set_additional_zone_state(hass, call):
        pass

    async def async_set_smart_grid_mode(hass, call):
        pass


def register_services(hass) -> None:
    """Register integration services."""
    if not HAS_HA:
        return
    async_register_admin_service(
        hass,
        DOMAIN,
        SERVICE_SET_OPERATION_MODE,
        async_set_operation_mode,
        schema=SERVICE_SET_OPERATION_MODE_SCHEMA,
    )
    async_register_admin_service(
        hass,
        DOMAIN,
        SERVICE_SET_DHW_STATE,
        async_set_dhw_state,
        schema=SERVICE_SET_DHW_STATE_SCHEMA,
    )
    async_register_admin_service(
        hass,
        DOMAIN,
        SERVICE_SET_MAIN_ZONE_STATE,
        async_set_main_zone_state,
        schema=SERVICE_SET_MAIN_ZONE_STATE_SCHEMA,
    )
    async_register_admin_service(
        hass,
        DOMAIN,
        SERVICE_SET_ADDITIONAL_ZONE_STATE,
        async_set_additional_zone_state,
        schema=SERVICE_SET_ADDITIONAL_ZONE_STATE_SCHEMA,
    )
    async_register_admin_service(
        hass,
        DOMAIN,
        SERVICE_SET_SMART_GRID_MODE,
        async_set_smart_grid_mode,
        schema=SERVICE_SET_SMART_GRID_MODE_SCHEMA,
    )
    _LOGGER.debug("Registered Daikin Altherma 4 Modbus services")
