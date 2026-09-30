"""Auto-generated expansion plugin pack. All handlers are lazy and delegate to core operations."""


def register_tools():
    return [
    {
        "name": "Stopwatch",
        "category": "Time & Productivity",
        "description": "Stopwatch: query and display stopwatch details as structured JSON.",
        "handler": "operations.stopwatch",
        "cli_command": "stopwatch",
        "dependencies": []
    },
    {
        "name": "Countdown",
        "category": "Time & Productivity",
        "description": "Countdown: query and display countdown details as structured JSON.",
        "handler": "operations.countdown",
        "cli_command": "countdown",
        "dependencies": []
    },
    {
        "name": "Date Difference",
        "category": "Time & Productivity",
        "description": "Date Difference: query and display date difference details as structured JSON.",
        "handler": "operations.date_difference",
        "cli_command": "date-difference",
        "dependencies": []
    },
    {
        "name": "Business Day Difference",
        "category": "Time & Productivity",
        "description": "Business Day Difference: query and display business day difference details as structured JSON.",
        "handler": "operations.business_day_difference",
        "cli_command": "business-day-difference",
        "dependencies": []
    },
    {
        "name": "Timestamp Converter",
        "category": "Time & Productivity",
        "description": "Convert timestamp between units or formats.",
        "handler": "operations.timestamp_converter",
        "cli_command": "timestamp-converter",
        "dependencies": []
    },
    {
        "name": "Epoch Converter",
        "category": "Time & Productivity",
        "description": "Convert epoch between units or formats.",
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
        "description": "Calendar Month: query and display calendar month details as structured JSON.",
        "handler": "operations.calendar_month",
        "cli_command": "calendar-month",
        "dependencies": []
    },
    {
        "name": "Calendar Year",
        "category": "Time & Productivity",
        "description": "Calendar Year: query and display calendar year details as structured JSON.",
        "handler": "operations.calendar_year",
        "cli_command": "calendar-year",
        "dependencies": []
    },
    {
        "name": "Week Number",
        "category": "Time & Productivity",
        "description": "Week Number: query and display week number details as structured JSON.",
        "handler": "operations.week_number",
        "cli_command": "week-number",
        "dependencies": []
    },
    {
        "name": "Day Of Year",
        "category": "Time & Productivity",
        "description": "Day Of Year: query and display day of year details as structured JSON.",
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
        "description": "Pomodoro Timer: query and display pomodoro timer details as structured JSON.",
        "handler": "operations.pomodoro_timer",
        "cli_command": "pomodoro-timer",
        "dependencies": []
    },
    {
        "name": "Time Zone Offset",
        "category": "Time & Productivity",
        "description": "Time Zone Offset: query and display time zone offset details as structured JSON.",
        "handler": "operations.time_zone_offset",
        "cli_command": "time-zone-offset",
        "dependencies": []
    },
    {
        "name": "Meeting Time Table",
        "category": "Time & Productivity",
        "description": "Meeting Time Table: query and display meeting time table details as structured JSON.",
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
        "description": "Date Range Expander: query and display date range expander details as structured JSON.",
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
