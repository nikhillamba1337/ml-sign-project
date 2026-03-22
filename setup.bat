@echo off
REM Quick setup script for Flask app (Windows)

echo 🚀 Setting up Sign Language Detector (Flask Version)...

REM Install dependencies
echo 📦 Installing dependencies...
pip install -r requirements_render.txt

REM Create directories if needed
if not exist "templates" mkdir templates

REM Check for model file
if not exist "model.p" (
    echo ⚠️  model.p not found! Please ensure it's in the project root.
) else (
    echo ✓ model.p found
)

REM Run the app
echo ✓ Setup complete!
echo.
echo To start the app, run:
echo   python app_flask.py
echo.
echo Then visit: http://localhost:5000
pause
