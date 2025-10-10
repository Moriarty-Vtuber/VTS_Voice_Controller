@echo off

echo "--- Activating virtual environment ---"
call .\.venv\Scripts\activate.bat

echo "--- Starting VTS Voice Controller in FAST Mode (Low Latency) ---"
python vts_main.py --mode fast

echo.
echo "--- Program finished. Press any key to exit ---"
pause
