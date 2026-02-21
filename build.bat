@echo off
echo Building Gaze Cursor for Windows...
call npm run dist
if %errorlevel% neq 0 (
    echo Build failed. Check the output above for errors.
    pause
    exit /b %errorlevel%
)
echo Build completed successfully. Check the 'dist' directory for the executable.
pause
