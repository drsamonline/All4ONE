$ErrorActionPreference = 'Stop'
Write-Host 'Utility Suite Windows Release Build' -ForegroundColor Cyan
python --version
python -m pip install --upgrade pyinstaller
python create_plugin_zips.py
if (Test-Path dist) { Remove-Item dist -Recurse -Force }
if (Test-Path build) { Remove-Item build -Recurse -Force }
python -B audit.py
python -B -m tests.test_suite
python -m PyInstaller build.spec --clean --noconfirm
Write-Host 'Build complete: dist\utility_suite\utility_suite.exe' -ForegroundColor Green
