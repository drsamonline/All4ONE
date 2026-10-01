"""Auto-generated expansion plugin pack. All handlers are lazy and delegate to core operations."""


def register_tools():
    return [
    {
        "name": "Stopwatch",
        "category": "Time & Productivity",
        "description": "Stopwatch: stopwatch as structured JSON output.",
        "handler": "operations.stopwatch",
        "cli_command": "stopwatch",
        "dependencies": []
    },
    {
        "name": "Countdown",
        "category": "Time & Productivity",
        "description": "Countdown: countdown as structured JSON output.",
        "handler": "operations.countdown",
        "cli_command": "countdown",
        "dependencies": []
    },
    {
        "name": "Date Difference",
        "category": "Time & Productivity",
        "description": "Compute the difference between date inputs.",
        "handler": "operations.date_difference",
        "cli_command": "date-difference",
        "dependencies": []
    },
    {
        "name": "Business Day Difference",
        "category": "Time & Productivity",
        "description": "Compute the difference between business day inputs.",
        "handler": "operations.business_day_difference",
        "cli_command": "business-day-difference",
        "dependencies": []
    },
    {
        "name": "Timestamp Converter",
        "category": "Time & Productivity",
        "description": "Convert between ISO-8601 timestamps and Unix epochs.",
        "handler": "operations.timestamp_converter",
        "cli_command": "timestamp-converter",
        "dependencies": []
    },
    {
        "name": "Epoch Converter",
        "category": "Time & Productivity",
        "description": "Convert a Unix epoch timestamp to a human-readable date and back.",
        "handler": "operations.epoch_converter",
        "cli_command": "epoch-converter",
        "dependencies": []
    },
    {
        "name": "ISO Time Formatter",
        "category": "Time & Productivity",
        "description": "Reformat iso time to a clean layout.",
        "handler": "operations.iso_time_formatter",
        "cli_command": "iso-time-formatter",
        "dependencies": []
    },
    {
        "name": "Calendar Month",
        "category": "Time & Productivity",
        "description": "Calendar Month: calendar month as structured JSON output.",
        "handler": "operations.calendar_month",
        "cli_command": "calendar-month",
        "dependencies": []
    },
    {
        "name": "Calendar Year",
        "category": "Time & Productivity",
        "description": "Calendar Year: calendar year as structured JSON output.",
        "handler": "operations.calendar_year",
        "cli_command": "calendar-year",
        "dependencies": []
    },
    {
        "name": "Week Number",
        "category": "Time & Productivity",
        "description": "Week Number: week number as structured JSON output.",
        "handler": "operations.week_number",
        "cli_command": "week-number",
        "dependencies": []
    },
    {
        "name": "Day Of Year",
        "category": "Time & Productivity",
        "description": "Day Of Year: day of year as structured JSON output.",
        "handler": "operations.day_of_year",
        "cli_command": "day-of-year",
        "dependencies": []
    },
    {
        "name": "Working Hours Calculator",
        "category": "Time & Productivity",
        "description": "Compute working hours values.",
        "handler": "operations.working_hours_calculator",
        "cli_command": "working-hours-calculator",
        "dependencies": []
    },
    {
        "name": "Pomodoro Timer",
        "category": "Time & Productivity",
        "description": "Pomodoro Timer: pomodoro timer as structured JSON output.",
        "handler": "operations.pomodoro_timer",
        "cli_command": "pomodoro-timer",
        "dependencies": []
    },
    {
        "name": "Time Zone Offset",
        "category": "Time & Productivity",
        "description": "Time Zone Offset: time zone offset as structured JSON output.",
        "handler": "operations.time_zone_offset",
        "cli_command": "time-zone-offset",
        "dependencies": []
    },
    {
        "name": "Meeting Time Table",
        "category": "Time & Productivity",
        "description": "Lay out data as a meeting time table table.",
        "handler": "operations.meeting_time_table",
        "cli_command": "meeting-time-table",
        "dependencies": []
    },
    {
        "name": "Cron Expression Explainer",
        "category": "Time & Productivity",
        "description": "Explain cron expression in human terms.",
        "handler": "operations.cron_expression_explainer",
        "cli_command": "cron-explainer",
        "dependencies": []
    },
    {
        "name": "Date Range Expander",
        "category": "Time & Productivity",
        "description": "Expand date range into enumerated items.",
        "handler": "operations.date_range_expander",
        "cli_command": "date-range-expander",
        "dependencies": []
    },
    {
        "name": "Relative Time Formatter",
        "category": "Time & Productivity",
        "description": "Reformat relative time to a clean layout.",
        "handler": "operations.relative_time_formatter",
        "cli_command": "relative-time",
        "dependencies": []
    },
    {
        "name": "Habit Streak Counter",
        "category": "Time & Productivity",
        "description": "Count occurrences within habit streak.",
        "handler": "operations.habit_streak_counter",
        "cli_command": "habit-streak",
        "dependencies": []
    }
]
