@echo off

echo "--- Activating virtual environment ---"
call .\.venv\Scripts\activate.bat

echo "--- Starting VTS Voice Controller in ACCURATE Mode (Higher Accuracy) ---"
python vts_main.py --mode accurate

echo.
echo "--- Program finished. Press any key to exit ---"
pause
