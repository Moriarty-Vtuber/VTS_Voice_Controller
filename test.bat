@echo off

echo "--- Activating virtual environment ---"
call .\.venv\Scripts\activate.bat

echo "--- Starting VTS Voice Controller in Test Mode ---"
python vts_main.py --test

echo.
echo "--- Program finished. Press any key to exit ---"
pause
