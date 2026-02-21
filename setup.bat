@echo off
echo Setting up Gaze Cursor Environment for Windows...

echo Step 1/3: Creating Python Virtual Environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo Failed to create virtual environment. Ensure Python is installed and in your PATH.
    pause
    exit /b %errorlevel%
)

echo Step 2/3: Installing Python Dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install opencv-python numpy mediapipe==0.10.11 pyautogui eyetrax
if %errorlevel% neq 0 (
    echo Failed to install Python dependencies.
    pause
    exit /b %errorlevel%
)

echo Step 3/3: Installing Node.js Dependencies...
call npm install
if %errorlevel% neq 0 (
    echo Failed to install Node dependencies. Ensure Node.js and npm are installed.
    pause
    exit /b %errorlevel%
)

echo.
echo Setup Complete! You can now run 'build.bat' or 'npm start'.
pause
