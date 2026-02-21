#!/bin/bash
set -e

echo "Building Gaze Cursor for macOS/Linux..."
npm run dist

echo "Build completed successfully. Check the 'dist' directory for the executable."
