@echo off
setlocal

set "ROOT=%~dp0"
set "FRONTEND=%ROOT%fleet_action\frontend"
set "DIST=%ROOT%dist"

echo ===================================================
echo  helm-plugin-fleet-action build script
echo ===================================================

echo.
echo [1/3] Cleaning old build artifacts...
cd /d "%ROOT%"
if exist build rmdir /s /q build
if exist dist  rmdir /s /q dist

echo.
echo [2/3] Building Vue frontend...
cd /d "%FRONTEND%"

if not exist "node_modules" (
    echo      node_modules not found, running npm install...
    call npm install
    if errorlevel 1 ( echo [ERROR] npm install failed & exit /b 1 )
)

call npm run build
if errorlevel 1 ( echo [ERROR] Vue build failed & exit /b 1 )
echo      OK - frontend dist ready

echo.
echo [3/3] Building Python wheel...
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
echo [Done]
for %%f in ("%DIST%\*.whl") do echo   %%f
echo.
echo Dev install:   pip install -e "%ROOT%"
echo.
endlocal
