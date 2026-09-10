"""Lazy operation adapters; implementations live in core.extended_ops."""

from core.handler_factory import make_handler

_HANDLERS = {
    "bytes_converter": "Bytes Converter",
    "size_formatter": "Size Formatter",
    "seconds_converter": "Seconds Converter",
    "temperature_converter": "Temperature Converter",
    "length_converter": "Length Converter",
    "mass_converter": "Mass Converter",
    "area_converter": "Area Converter",
    "volume_converter": "Volume Converter",
    "speed_converter": "Speed Converter",
    "pressure_converter": "Pressure Converter",
    "energy_converter": "Energy Converter",
    "power_converter": "Power Converter",
    "angle_converter": "Angle Converter",
    "frequency_converter": "Frequency Converter",
    "data_rate_converter": "Data Rate Converter",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
