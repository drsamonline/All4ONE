"""Auto-generated expansion plugin pack. All handlers are lazy and delegate to core operations."""


def register_tools():
    return [
        {
            "name": "Virtual Desktop List",
            "category": "Virtual Desktops",
            "description": "Virtual Desktop List: virtual-desktop-list operation.",
            "handler": "operations.virtual_desktop_list",
            "cli_command": "virtual-desktop-list",
            "dependencies": ["powershell"],
        },
        {
            "name": "Virtual Desktop Shortcut",
            "category": "Virtual Desktops",
            "description": "Virtual Desktop Shortcut: virtual-desktop-shortcut operation.",
            "handler": "operations.virtual_desktop_shortcut",
            "cli_command": "virtual-desktop-shortcut",
            "dependencies": ["powershell"],
        },
        {
            "name": "Window Desktop Mapper",
            "category": "Virtual Desktops",
            "description": "Window Desktop Mapper: window-desktop-mapper operation.",
            "handler": "operations.window_desktop_mapper",
            "cli_command": "window-desktop-mapper",
            "dependencies": ["powershell"],
        },
        {
            "name": "Desktop Count Reader",
            "category": "Virtual Desktops",
            "description": "Desktop Count Reader: desktop-count-reader operation.",
            "handler": "operations.desktop_count_reader",
            "cli_command": "desktop-count-reader",
            "dependencies": ["powershell"],
        },
        {
            "name": "Virtual Desktop Settings",
            "category": "Virtual Desktops",
            "description": "Virtual Desktop Settings: virtual-desktop-settings operation.",
            "handler": "operations.virtual_desktop_settings",
            "cli_command": "virtual-desktop-settings",
            "dependencies": ["powershell"],
        },
        {
            "name": "Desktop Hotkey Guide",
            "category": "Virtual Desktops",
            "description": "Desktop Hotkey Guide: desktop-hotkey-guide operation.",
            "handler": "operations.desktop_hotkey_guide",
            "cli_command": "desktop-hotkey-guide",
            "dependencies": ["powershell"],
        },
        {
            "name": "Desktop Process Summary",
            "category": "Virtual Desktops",
            "description": "Desktop Process Summary: desktop-process-summary operation.",
            "handler": "operations.desktop_process_summary",
            "cli_command": "desktop-process-summary",
            "dependencies": ["powershell"],
        },
        {
            "name": "Desktop Launch Helper",
            "category": "Virtual Desktops",
            "description": "Desktop Launch Helper: desktop-launch-helper operation.",
            "handler": "operations.desktop_launch_helper",
            "cli_command": "desktop-launch-helper",
            "dependencies": ["powershell"],
        },
    ]
