"""Auto-generated expansion plugin pack. All handlers are lazy and delegate to core operations."""


def register_tools():
    return [
    {
        "name": "Python Package List",
        "category": "Package & Environment Tools",
        "description": "List python package entries.",
        "handler": "operations.python_package_list",
        "cli_command": "python-package-list",
        "dependencies": [
            "python"
        ]
    },
    {
        "name": "Python Package Versions",
        "category": "Package & Environment Tools",
        "description": "List python package entries.",
        "handler": "operations.python_package_versions",
        "cli_command": "python-package-versions",
        "dependencies": [
            "python"
        ]
    },
    {
        "name": "Pip Command Guide",
        "category": "Package & Environment Tools",
        "description": "Show guidance for pip command.",
        "handler": "operations.pip_command_guide",
        "cli_command": "pip-command-guide",
        "dependencies": [
            "python"
        ]
    },
    {
        "name": "Executable Package Locator",
        "category": "Package & Environment Tools",
        "description": "Show guidance for pip command.",
        "handler": "operations.executable_package_locator",
        "cli_command": "executable-package-locator",
        "dependencies": [
            "python"
        ]
    },
    {
        "name": "Import Package Test",
        "category": "Package & Environment Tools",
        "description": "Locate executable package paths on disk.",
        "handler": "operations.import_package_test",
        "cli_command": "import-package-test",
        "dependencies": [
            "python"
        ]
    },
    {
        "name": "Requirements Generator",
        "category": "Package & Environment Tools",
        "description": "Generate requirements output.",
        "handler": "operations.requirements_generator",
        "cli_command": "requirements-generator",
        "dependencies": [
            "python"
        ]
    },
    {
        "name": "Requirements Auditor",
        "category": "Package & Environment Tools",
        "description": "Audit requirements for issues.",
        "handler": "operations.requirements_auditor",
        "cli_command": "requirements-auditor",
        "dependencies": [
            "python"
        ]
    },
    {
        "name": "Virtual Environment Finder",
        "category": "Package & Environment Tools",
        "description": "Locate virtual environment on disk or in scope.",
        "handler": "operations.virtual_environment_finder",
        "cli_command": "virtual-environment-finder",
        "dependencies": [
            "python"
        ]
    },
    {
        "name": "Virtual Environment Report",
        "category": "Package & Environment Tools",
        "description": "Locate virtual environment on disk or in scope.",
        "handler": "operations.virtual_environment_report",
        "cli_command": "virtual-environment-report",
        "dependencies": [
            "python"
        ]
    },
    {
        "name": "Package Cache Guide",
        "category": "Package & Environment Tools",
        "description": "Show guidance for package cache.",
        "handler": "operations.package_cache_guide",
        "cli_command": "package-cache-guide",
        "dependencies": [
            "python"
        ]
    },
    {
        "name": "Venv Size Reporter",
        "category": "Package Tools",
        "description": "Produce a detailed report of venv size.",
        "handler": "operations.venv_size_reporter",
        "cli_command": "venv-size",
        "dependencies": []
    },
    {
        "name": "Wheel Inspector",
        "category": "Package Tools",
        "description": "Inspect wheel and report internals.",
        "handler": "operations.wheel_inspector",
        "cli_command": "wheel-inspector",
        "dependencies": []
    }
]
