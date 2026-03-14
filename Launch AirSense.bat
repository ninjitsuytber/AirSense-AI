@echo off
echo =========================================
echo = AirSense AI Terminal Launcher
echo =========================================
echo.

echo Starting AirSense Python API Backend...
:: Start the Python backend in a separate minimized cmd window
start /min cmd /c "python server.py"

:: Wait a brief moment to ensure the server starts up properly
timeout /t 2 /nobreak >nul

echo.
echo Opening the interactive terminal website in your default browser...
:: Launch the HTML file in the system's default browser
start index.html

echo.
echo Done! 
echo.
echo Note: If you need to fully shut down the Python backend later,
echo       you can close the minimized command prompt window that opened.
pause
