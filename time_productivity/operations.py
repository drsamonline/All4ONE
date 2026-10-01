"""Lazy operation adapters; implementations live in core.extended_ops."""


from core.handler_factory import make_handler

_HANDLERS = {
    "stopwatch": "Stopwatch",
    "countdown": "Countdown",
    "date_difference": "Date Difference",
    "business_day_difference": "Business Day Difference",
    "timestamp_converter": "Timestamp Converter",
    "epoch_converter": "Epoch Converter",
    "iso_time_formatter": "ISO Time Formatter",
    "calendar_month": "Calendar Month",
    "calendar_year": "Calendar Year",
    "week_number": "Week Number",
    "day_of_year": "Day Of Year",
    "working_hours_calculator": "Working Hours Calculator",
    "pomodoro_timer": "Pomodoro Timer",
    "time_zone_offset": "Time Zone Offset",
    "meeting_time_table": "Meeting Time Table",
    "cron_expression_explainer": "cron expression explainer",
    "date_range_expander": "date range expander",
    "relative_time_formatter": "relative time formatter",
    "habit_streak_counter": "habit streak counter",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
