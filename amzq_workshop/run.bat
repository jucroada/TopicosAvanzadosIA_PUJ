@echo off
echo Starting Colombian Peso (COP) to USD Exchange Rate Tracker...

REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    py -3.11 -m venv venv
    call venv\Scripts\activate
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

REM Run the Streamlit app
streamlit run cop_usd_exchange_app.py

pause