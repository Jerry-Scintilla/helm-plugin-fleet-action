@echo off
setlocal

set "ROOT=%~dp0"
set "DIST=%ROOT%dist"

echo ===================================================
echo  helm-plugin-fleet-action build script
echo ===================================================

echo.
echo [1/2] Building Python wheel...
cd /d "%ROOT%"

python -m build --wheel --outdir "%DIST%" 2>nul
if errorlevel 1 (
    echo      Installing build tool...
    pip install build -q
    python -m build --wheel --outdir "%DIST%"
    if errorlevel 1 ( echo [ERROR] wheel build failed & exit /b 1 )
)

echo      OK - wheel saved to dist\

echo.
echo [2/2] Done!
echo.
for %%f in ("%DIST%\*.whl") do echo   %%f
echo.
echo Dev install:   pip install -e "%ROOT%"
echo.
endlocal
