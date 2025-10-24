@echo off

echo "--- VTS Voice Controller --- "

if not exist .\.venv (
    echo "--- Creating virtual environment... ---"
    python -m venv .venv
)

echo "--- Activating virtual environment... ---"
call .\.venv\Scripts\activate.bat

echo "--- Installing dependencies... ---"
pip install -r requirements.txt

echo "--- Launching application... ---"
python vts_main.py