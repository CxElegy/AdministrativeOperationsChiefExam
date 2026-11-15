@echo off
rem One-click installer for the three Live2D MCP servers. Double-click it, or run: install.cmd [-Dir E:\somewhere]
setlocal
cd /d "%~dp0"

echo [1/4] Looking for Live2D Cubism Editor - 5.3.03 or 5.3.04 is needed for cubism53-native-mcp
dir /b /ad "C:\Program Files\Live2D Cubism*" 2>nul
if not errorlevel 1 goto editor_ok
echo Cubism Editor was not found in C:\Program Files.
echo Install it from the official Live2D site first: https://www.live2d.com/en/download/cubism/
choice /m "Is it installed somewhere else, and do you want to continue anyway"
if errorlevel 2 goto fail
:editor_ok

echo.
echo [2/4] Checking git and Claude Code
where git >nul 2>nul || (echo git is missing - install it from https://git-scm.com/ & goto fail)
where claude >nul 2>nul || (echo claude is missing - install Claude Code first & goto fail)
echo OK

echo.
echo [3/4] Running setup.ps1 - Setup.cmd will ask for the editor folder and your models folder
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1" %*
if errorlevel 1 (echo setup.ps1 failed - copy the messages above and send them to Claude & goto fail)

echo.
echo [4/4] Done. Check that the list above shows cubism-mcp, cubism53-native-mcp and live2d-automation.
echo.
echo Next, in Cubism Editor:
echo   File - External application integration - turn it ON, port 22033
echo   Approve cubism-mcp and Cubism53 Native MCP - needed again after every editor restart
echo Then restart Claude Code.
pause
exit /b 0

:fail
pause
exit /b 1
