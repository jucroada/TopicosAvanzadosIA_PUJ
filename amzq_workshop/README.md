# Colombian Peso (COP) to USD Exchange Rate Tracker

A Streamlit application that allows users to track the Representative Market Rate (TRM) of the Colombian Peso against the US Dollar.

## Features

- **Historical TRM Data**: View historical exchange rate data from official Colombian sources
- **Interactive Charts**: Analyze TRM trends with interactive line and candlestick charts
- **Date Range Selection**: Select custom date ranges for analysis
- **Summary Statistics**: View key statistics like current rate, average, minimum, and maximum
- **Data Export**: Download TRM data as CSV for further analysis

## Installation

1. Clone this repository or download the files
2. Create a virtual environment:
   ```bash
   py -3.11 -m venv venv
   venv\Scripts\activate
   python.exe -m pip install --upgrade pip
   ```
3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Activate the virtual environment:
   ```bash
   venv\Scripts\activate
   ```
2. Run the Streamlit app:
   ```bash
   streamlit run cop_usd_exchange_app.py
   ```
3. Open your web browser and navigate to the URL displayed in the terminal (typically http://localhost:8501)

## Data Sources

The application uses multiple data sources to ensure reliability:

1. **Primary Source**: Datos Abiertos Colombia API (official Colombian government open data)
2. **Secondary Source**: Banco de la República API
3. **Tertiary Source**: Web scraping from financial websites
4. **Fallback**: Sample data generation if all online sources fail

## Project Structure

- `cop_usd_exchange_app.py`: Main Streamlit application
- `requirements.txt`: List of required Python packages
- `data/`: Directory where exported CSV files are saved

## Notes

- The application requires an internet connection to fetch the latest TRM data
- The app includes multiple fallback mechanisms if the primary data sources are unavailable
- You can export the data to CSV for offline analysis