import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import io
import os
import json

# Set page configuration
st.set_page_config(
    page_title="Colombian Peso (COP) to USD Exchange Rate",
    page_icon="🇨🇴",
    layout="wide"
)

# App title and description
st.title("Colombian Peso (COP) to USD Exchange Rate")
st.markdown("""
This application tracks the Representative Market Rate (TRM) of the Colombian Peso against the US Dollar.
Data is sourced from the Colombian Central Bank (Banco de la República) via the Datos Abiertos API.
""")

# Function to fetch TRM data from Datos Abiertos Colombia API
@st.cache_data(ttl=3600)  # Cache data for 1 hour
def get_trm_data(start_date=None, end_date=None):
    """
    Fetch TRM data from Datos Abiertos Colombia API
    
    Parameters:
    -----------
    start_date : str
        Start date in YYYY-MM-DD format
    end_date : str
        End date in YYYY-MM-DD format
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with date and TRM value
    """
    try:
        # If no dates provided, get last 30 days
        if not start_date:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            start_date = start_date.strftime("%Y-%m-%d")
            end_date = end_date.strftime("%Y-%m-%d")
        
        # Convert string dates to datetime for filtering
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # URL for the TRM data from Datos Abiertos Colombia
        # This API provides TRM data from the Colombian Central Bank
        url = "https://www.datos.gov.co/resource/32sa-8pi3.json"
        
        # Add query parameters to get data for the last year (maximum allowed)
        # We'll filter further in Python
        params = {
            "$limit": 5000,  # Get maximum records
            "$order": "vigenciadesde DESC"  # Order by date descending
        }
        
        st.info("Fetching TRM data from Datos Abiertos Colombia... This may take a moment.")
        
        # Make the API request
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            # Parse JSON response
            data = response.json()
            
            # Create DataFrame
            df = pd.DataFrame(data)
            
            # Rename columns for clarity
            df = df.rename(columns={
                'vigenciadesde': 'date',
                'valor': 'trm'
            })
            
            # Convert date column to datetime
            df['date'] = pd.to_datetime(df['date'])
            
            # Convert TRM to float
            df['trm'] = df['trm'].astype(float)
            
            # Filter by date range
            df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]
            
            # Sort by date
            df = df.sort_values('date')
            
            # Select only needed columns
            df = df[['date', 'trm']]
            
            return df
        else:
            st.error(f"Failed to download data: HTTP {response.status_code}")
            # Try alternative source
            return get_alternative_trm_data(start_date, end_date)
    except Exception as e:
        st.error(f"Error fetching TRM data: {e}")
        # Try alternative source
        return get_alternative_trm_data(start_date, end_date)

# Function to get TRM data from alternative source
def get_alternative_trm_data(start_date=None, end_date=None):
    """
    Get TRM data from alternative source (Banco de la República API)
    
    Parameters:
    -----------
    start_date : str
        Start date in YYYY-MM-DD format
    end_date : str
        End date in YYYY-MM-DD format
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with date and TRM value
    """
    try:
        # If no dates provided, get last 30 days
        if not start_date:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            start_date = start_date.strftime("%Y-%m-%d")
            end_date = end_date.strftime("%Y-%m-%d")
            
        # Convert to datetime for API format
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Format dates for API
        start_api = start_dt.strftime("%Y-%m-%d")
        end_api = end_dt.strftime("%Y-%m-%d")
        
        st.info("Trying alternative data source (Banco de la República API)...")
        
        # Banco de la República API URL
        url = f"https://www.banrep.gov.co/estadisticas/trm?from={start_api}&to={end_api}"
        
        # Make the request
        response = requests.get(url)
        
        if response.status_code == 200:
            # Parse JSON response
            data = response.json()
            
            # Create DataFrame
            records = []
            for item in data:
                records.append({
                    'date': datetime.strptime(item['date'], "%Y-%m-%d"),
                    'trm': float(item['value'])
                })
            
            df = pd.DataFrame(records)
            
            # Sort by date
            df = df.sort_values('date')
            
            return df
        else:
            st.error(f"Failed to download data from alternative source: HTTP {response.status_code}")
            # Try web scraping as last resort
            return get_scraped_trm_data(start_date, end_date)
    except Exception as e:
        st.error(f"Error fetching alternative TRM data: {e}")
        # Try web scraping as last resort
        return get_scraped_trm_data(start_date, end_date)

# Function to get TRM data by scraping
def get_scraped_trm_data(start_date=None, end_date=None):
    """
    Get TRM data by scraping websites
    
    Parameters:
    -----------
    start_date : str
        Start date in YYYY-MM-DD format
    end_date : str
        End date in YYYY-MM-DD format
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with date and TRM value
    """
    try:
        st.info("Trying to scrape TRM data from web sources...")
        
        # Try to scrape data from dolar-colombia.com
        url = "https://dolar-colombia.com/historico-trm"
        response = requests.get(url)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Find the table with TRM data
            table = soup.find('table', {'class': 'table'})
            
            if table:
                # Extract data from table
                rows = table.find_all('tr')
                data = []
                
                for row in rows[1:]:  # Skip header row
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        date_str = cols[0].text.strip()
                        trm_str = cols[1].text.strip().replace('$', '').replace('.', '').replace(',', '.')
                        
                        try:
                            date = datetime.strptime(date_str, '%d/%m/%Y')
                            trm = float(trm_str)
                            data.append({'date': date, 'trm': trm})
                        except:
                            pass
                
                df = pd.DataFrame(data)
                
                # Convert string dates to datetime for filtering
                if start_date and end_date:
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                    
                    # Filter by date range
                    df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]
                
                # Sort by date
                df = df.sort_values('date')
                
                if not df.empty:
                    return df
        
        # If scraping fails, use sample data
        st.warning("Could not fetch data from online sources. Using sample data instead.")
        return get_sample_trm_data(start_date, end_date)
    except Exception as e:
        st.error(f"Error scraping TRM data: {e}")
        return get_sample_trm_data(start_date, end_date)

# Function to generate sample TRM data if all sources fail
def get_sample_trm_data(start_date=None, end_date=None):
    """Generate sample TRM data for demonstration"""
    import random
    
    # If no dates provided, get last 30 days
    if not start_date:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
    
    # Generate dates
    dates = []
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() < 5:  # Only weekdays (0-4 are Monday to Friday)
            dates.append(current_date)
        current_date += timedelta(days=1)
    
    # Generate sample TRM values (around 4000 COP per USD with some variation)
    base_trm = 4000
    data = []
    
    for date in dates:
        # Add some random variation
        variation = random.uniform(-100, 100)  # ±100 COP variation
        trm = base_trm + variation
        data.append({'date': date, 'trm': trm})
    
    return pd.DataFrame(data)

# Function to save data to CSV
def save_to_csv(df, filename="trm_data.csv"):
    """Save DataFrame to CSV file"""
    try:
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)
        
        # Save to CSV
        filepath = os.path.join("data", filename)
        df.to_csv(filepath, index=False)
        return filepath
    except Exception as e:
        st.error(f"Error saving data to CSV: {e}")
        return None

# Sidebar for date range selection
st.sidebar.title("Options")

# Date range selection
st.sidebar.subheader("Date Range")

# Get min and max dates for the date picker
today = datetime.now()
min_date = today - timedelta(days=365*5)  # 5 years ago
max_date = today

# Default to last 30 days
default_start_date = today - timedelta(days=30)
default_end_date = today

start_date = st.sidebar.date_input(
    "Start Date",
    value=default_start_date,
    min_value=min_date,
    max_value=max_date
)

end_date = st.sidebar.date_input(
    "End Date",
    value=default_end_date,
    min_value=min_date,
    max_value=max_date
)

# Convert to string format
start_date_str = start_date.strftime("%Y-%m-%d")
end_date_str = end_date.strftime("%Y-%m-%d")

# Fetch TRM data
trm_data = get_trm_data(start_date_str, end_date_str)

# Main content
if trm_data is not None and not trm_data.empty:
    # Display summary statistics
    st.header("TRM Summary Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Current TRM",
            f"${trm_data['trm'].iloc[-1]:,.2f}",
            f"{trm_data['trm'].iloc[-1] - trm_data['trm'].iloc[-2]:,.2f}"
        )
    
    with col2:
        st.metric(
            "Average",
            f"${trm_data['trm'].mean():,.2f}"
        )
    
    with col3:
        st.metric(
            "Minimum",
            f"${trm_data['trm'].min():,.2f}"
        )
    
    with col4:
        st.metric(
            "Maximum",
            f"${trm_data['trm'].max():,.2f}"
        )
    
    # Display TRM trend chart
    st.header("TRM Trend")
    
    fig = px.line(
        trm_data,
        x="date",
        y="trm",
        title="Colombian Peso to USD Exchange Rate (TRM)",
        labels={"trm": "TRM (COP per USD)", "date": "Date"}
    )
    
    # Add range slider
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=7, label="1w", step="day", stepmode="backward"),
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=3, label="3m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(visible=True),
            type="date"
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display candlestick chart for weekly aggregation
    st.header("Weekly TRM Analysis")
    
    # Resample data to weekly frequency
    weekly_data = trm_data.copy()
    weekly_data.set_index('date', inplace=True)
    weekly_ohlc = weekly_data['trm'].resample('W').ohlc()
    weekly_ohlc.reset_index(inplace=True)
    
    fig_candle = go.Figure(data=[go.Candlestick(
        x=weekly_ohlc['date'],
        open=weekly_ohlc['open'],
        high=weekly_ohlc['high'],
        low=weekly_ohlc['low'],
        close=weekly_ohlc['close'],
        name="TRM"
    )])
    
    fig_candle.update_layout(
        title="Weekly TRM Candlestick Chart",
        xaxis_title="Date",
        yaxis_title="TRM (COP per USD)",
        xaxis_rangeslider_visible=False
    )
    
    st.plotly_chart(fig_candle, use_container_width=True)
    
    # Display data table
    st.header("TRM Data Table")
    
    # Format date and TRM columns
    trm_table = trm_data.copy()
    trm_table['date'] = trm_table['date'].dt.strftime('%Y-%m-%d')
    trm_table['trm'] = trm_table['trm'].map('${:,.2f}'.format)
    
    # Rename columns for display
    trm_table = trm_table.rename(columns={
        'date': 'Date',
        'trm': 'TRM (COP per USD)'
    })
    
    st.dataframe(trm_table, use_container_width=True)
    
    # Download data option
    st.subheader("Download Data")
    
    if st.button("Save TRM Data to CSV"):
        filepath = save_to_csv(trm_data)
        if filepath:
            st.success(f"Data saved to {filepath}")
else:
    st.error("No data available for the selected date range. Please try a different date range.")

# Footer
st.markdown("---")
st.markdown("© 2023 Colombian Peso (COP) to USD Exchange Rate Tracker | Data sourced from Datos Abiertos Colombia and Banco de la República")