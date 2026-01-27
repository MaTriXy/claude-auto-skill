@echo off
REM Start Claude Auto-Skill Web UI (Windows)

echo 🦦 Claude Auto-Skill Web UI
echo ================================
echo.

REM Check if uv is installed
where uv >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Error: uv is not installed
    echo Install from: https://docs.astral.sh/uv/getting-started/installation/
    exit /b 1
)

REM Get the port (default 8000)
set PORT=%1
if "%PORT%"=="" set PORT=8000

echo 📦 Installing dependencies...
cd web
uv pip install -r requirements.txt >nul 2>&1

echo ✅ Dependencies ready
echo.
echo 🚀 Starting server on http://localhost:%PORT%
echo    Press Ctrl+C to stop
echo.

REM Run the Flask app
uv run python -c "from pathlib import Path; import sys; sys.path.insert(0, str(Path('.').parent)); from app import app; print('📊 Dashboard: http://localhost:%PORT%'); print('⭐ Graduation: http://localhost:%PORT%#graduation'); print('📤 Publishing: http://localhost:%PORT%#publishing'); print(); app.run(debug=True, host='0.0.0.0', port=%PORT%)"
