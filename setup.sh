#!/bin/bash
set -e

echo "Setting up Gaze Cursor Environment for macOS/Linux..."

echo "Step 1/3: Creating Python Virtual Environment..."
if ! command -v python3 &> /dev/null
then
    echo "Python3 could not be found. Please install Python3."
    exit 1
fi
python3 -m venv venv

echo "Step 2/3: Installing Python Dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install opencv-python numpy mediapipe==0.10.11 pyautogui eyetrax

echo "Step 3/3: Installing Node.js Dependencies..."
if ! command -v npm &> /dev/null
then
    echo "npm could not be found. Please install Node.js."
    exit 1
fi
npm install

echo ""
echo "Setup Complete! You can now run './build.sh' or 'npm start'."
