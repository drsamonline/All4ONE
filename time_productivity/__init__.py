"""Auto-generated expansion plugin pack. All handlers are lazy and delegate to core operations."""


def register_tools():
    return [
    {
        "name": "Stopwatch",
        "category": "Time & Productivity",
        "description": "Run a simple stopwatch.",
        "handler": "operations.stopwatch",
        "cli_command": "stopwatch",
        "dependencies": []
    },
    {
        "name": "Countdown",
        "category": "Time & Productivity",
        "description": "Run a countdown timer.",
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
        "description": "Print a calendar for a month.",
        "handler": "operations.calendar_month",
        "cli_command": "calendar-month",
        "dependencies": []
    },
    {
        "name": "Calendar Year",
        "category": "Time & Productivity",
        "description": "Print a calendar for a year.",
        "handler": "operations.calendar_year",
        "cli_command": "calendar-year",
        "dependencies": []
    },
    {
        "name": "Week Number",
        "category": "Time & Productivity",
        "description": "Report the ISO week number for a date.",
        "handler": "operations.week_number",
        "cli_command": "week-number",
        "dependencies": []
    },
    {
        "name": "Day Of Year",
        "category": "Time & Productivity",
        "description": "Report the day-of-year number for a date.",
        "handler": "operations.day_of_year",
        "cli_command": "day-of-year",
        "dependencies": []
    },
    {
        "name": "Working Hours Calculator",
        "category": "Time & Productivity",
        "description": "Compute the hours between two times, excluding breaks.",
        "handler": "operations.working_hours_calculator",
        "cli_command": "working-hours-calculator",
        "dependencies": []
    },
    {
        "name": "Pomodoro Timer",
        "category": "Time & Productivity",
        "description": "Run a Pomodoro work/break timer.",
        "handler": "operations.pomodoro_timer",
        "cli_command": "pomodoro-timer",
        "dependencies": []
    },
    {
        "name": "Time Zone Offset",
        "category": "Time & Productivity",
        "description": "Report the UTC offset for a time zone.",
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
        "description": "Translate a cron expression into plain English.",
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
        "description": "Track a habit and report the current and best streak.",
        "handler": "operations.habit_streak_counter",
        "cli_command": "habit-streak",
        "dependencies": []
    }
]
