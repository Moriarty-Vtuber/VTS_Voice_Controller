@echo off

echo "--- Activating virtual environment ---"
call .\.venv\Scripts\activate.bat

echo "--- Launching VTS Voice Controller UI ---"
python vts_main.py

echo.
echo "--- Program finished. Press any key to exit ---"
pause
