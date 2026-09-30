"""Auto-generated expansion plugin pack. All handlers are lazy and delegate to core operations."""


def register_tools():
    return [
    {
        "name": "Python Package List",
        "category": "Package & Environment Tools",
        "description": "Python Package List: performs the python package list action with structured, human-readable output.",
        "handler": "operations.python_package_list",
        "cli_command": "python-package-list",
        "dependencies": [
            "python"
        ]
    },
    {
        "name": "Python Package Versions",
        "category": "Package & Environment Tools",
        "description": "Python Package Versions: performs the python package versions action with structured, human-readable output.",
        "handler": "operations.python_package_versions",
        "cli_command": "python-package-versions",
        "dependencies": [
            "python"
        ]
    },
    {
        "name": "Pip Command Guide",
        "category": "Package & Environment Tools",
        "description": "Pip Command Guide: performs the pip command guide action with structured, human-readable output.",
        "handler": "operations.pip_command_guide",
        "cli_command": "pip-command-guide",
        "dependencies": [
            "python"
        ]
    },
    {
        "name": "Executable Package Locator",
        "category": "Package & Environment Tools",
        "description": "Executable Package Locator: performs the executable package locator action with structured, human-readable output.",
        "handler": "operations.executable_package_locator",
        "cli_command": "executable-package-locator",
        "dependencies": [
            "python"
        ]
    },
    {
        "name": "Import Package Test",
        "category": "Package & Environment Tools",
        "description": "Import Package Test: performs the import package test action with structured, human-readable output.",
        "handler": "operations.import_package_test",
        "cli_command": "import-package-test",
        "dependencies": [
            "python"
        ]
    },
    {
        "name": "Requirements Generator",
        "category": "Package & Environment Tools",
        "description": "Requirements Generator: performs the requirements generator action with structured, human-readable output.",
        "handler": "operations.requirements_generator",
        "cli_command": "requirements-generator",
        "dependencies": [
            "python"
        ]
    },
    {
        "name": "Requirements Auditor",
        "category": "Package & Environment Tools",
        "description": "Requirements Auditor: performs the requirements auditor action with structured, human-readable output.",
        "handler": "operations.requirements_auditor",
        "cli_command": "requirements-auditor",
        "dependencies": [
            "python"
        ]
    },
    {
        "name": "Virtual Environment Finder",
        "category": "Package & Environment Tools",
        "description": "Virtual Environment Finder: performs the virtual environment finder action with structured, human-readable output.",
        "handler": "operations.virtual_environment_finder",
        "cli_command": "virtual-environment-finder",
        "dependencies": [
            "python"
        ]
    },
    {
        "name": "Virtual Environment Report",
        "category": "Package & Environment Tools",
        "description": "Virtual Environment Report: performs the virtual environment report action with structured, human-readable output.",
        "handler": "operations.virtual_environment_report",
        "cli_command": "virtual-environment-report",
        "dependencies": [
            "python"
        ]
    },
    {
        "name": "Package Cache Guide",
        "category": "Package & Environment Tools",
        "description": "Package Cache Guide: performs the package cache guide action with structured, human-readable output.",
        "handler": "operations.package_cache_guide",
        "cli_command": "package-cache-guide",
        "dependencies": [
            "python"
        ]
    },
    {
        "name": "Venv Size Reporter",
        "category": "Package Tools",
        "description": "Venv Size Reporter: performs the venv size action with structured, human-readable output.",
        "handler": "operations.venv_size_reporter",
        "cli_command": "venv-size",
        "dependencies": []
    },
    {
        "name": "Wheel Inspector",
        "category": "Package Tools",
        "description": "Wheel Inspector: performs the wheel inspector action with structured, human-readable output.",
        "handler": "operations.wheel_inspector",
        "cli_command": "wheel-inspector",
        "dependencies": []
    }
]
