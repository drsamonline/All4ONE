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

# plugins/ must sit BESIDE utility_suite.exe (a plain, user-editable
# folder - see build.spec for why it is not bundled via PyInstaller
# `datas`). Copy it into place as a post-build step.
Write-Host 'Copying plugins/ next to the built executable...' -ForegroundColor Cyan
Copy-Item -Path 'plugins' -Destination 'dist\utility_suite\plugins' -Recurse -Force
New-Item -ItemType Directory -Force -Path 'dist\utility_suite\logs' | Out-Null

# Sanity-check the actual built executable before calling the build done -
# this is the same check that caught the "Total tools: 0" packaging bug.
Write-Host 'Verifying the built executable can see its tools...' -ForegroundColor Cyan
$toolCount = & 'dist\utility_suite\utility_suite.exe' list | Select-String -Pattern 'Total tools:'
Write-Host $toolCount
if ($toolCount -match 'Total tools: 0') {
    Write-Error 'Build verification FAILED: the packaged executable found 0 tools. Plugins were not placed correctly next to the exe.'
    exit 1
}
& 'dist\utility_suite\utility_suite.exe' --version

Write-Host 'Build complete: dist\utility_suite\utility_suite.exe' -ForegroundColor Green
