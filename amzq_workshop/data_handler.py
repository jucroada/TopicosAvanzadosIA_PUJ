import pandas as pd
import requests
from datetime import datetime, timedelta
import os
import streamlit as st

class ExchangeRateDataHandler:
    """
    Handles fetching and processing exchange rate data from various sources
    """
    
    def __init__(self, data_source="api"):
        """
        Initialize the data handler
        
        Parameters:
        -----------
        data_source : str
            Source of exchange rate data: 'api' or 'csv'
        """
        self.data_source = data_source
        self.csv_path = os.path.join(os.path.dirname(__file__), "data", "exchange_rates.csv")
    
    @st.cache_data(ttl=3600)  # Cache data for 1 hour
    def get_current_rates(self, base="USD"):
        """
        Get current exchange rates
        
        Parameters:
        -----------
        base : str
            Base currency code
            
        Returns:
        --------
        tuple
            (rates_dict, last_updated_timestamp)
        """
        if self.data_source == "api":
            return self._get_rates_from_api(base)
        else:
            return self._get_rates_from_csv(base)
    
    def _get_rates_from_api(self, base="USD"):
        """Fetch exchange rates from API"""
        try:
            url = f"https://open.er-api.com/v6/latest/{base}"
            response = requests.get(url)
            data = response.json()
            
            if data["result"] == "success":
                rates = data["rates"]
                last_updated = data["time_last_update_utc"]
                return rates, last_updated
            else:
                st.error(f"Error fetching data: {data.get('error', 'Unknown error')}")
                return None, None
        except Exception as e:
            st.error(f"Error fetching exchange rates: {e}")
            return None, None
    
    def _get_rates_from_csv(self, base="USD"):
        """Get current rates from CSV file"""
        try:
            if not os.path.exists(self.csv_path):
                st.error(f"CSV file not found: {self.csv_path}")
                return None, None
                
            df = pd.read_csv(self.csv_path)
            
            # Get the most recent date in the CSV
            latest_date = df['date'].max()
            latest_data = df[df['date'] == latest_date]
            
            # Create a dictionary of rates
            rates = {}
            for _, row in latest_data.iterrows():
                currency = row['currency']
                rate = row['rate']
                rates[currency] = rate
                
            return rates, latest_date
        except Exception as e:
            st.error(f"Error reading CSV data: {e}")
            return None, None
    
    @st.cache_data(ttl=3600)  # Cache data for 1 hour
    def get_historical_rates(self, days=30, base="USD"):
        """
        Get historical exchange rates
        
        Parameters:
        -----------
        days : int
            Number of days of historical data to retrieve
        base : str
            Base currency code
            
        Returns:
        --------
        tuple
            (historical_data_dict, dates_list)
        """
        if self.data_source == "api":
            return self._get_historical_from_api(days, base)
        else:
            return self._get_historical_from_csv(days, base)
    
    def _get_historical_from_api(self, days=30, base="USD"):
        """Simulate historical data from API"""
        try:
            # For demo purposes, we'll simulate historical data
            today = datetime.now()
            dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
            
            # Common currencies to track
            currencies = ["EUR", "GBP", "JPY", "CAD", "AUD", "CNY", "MXN", "BRL", "PEN"]
            
            # Simulate historical data with some random variations
            import random
            
            # Get current rates as baseline
            current_rates, _ = self.get_current_rates(base)
            if not current_rates:
                return None, None
                
            historical_data = {}
            for currency in currencies:
                if currency in current_rates:
                    base_rate = current_rates[currency]
                    historical_data[currency] = []
                    
                    for date in dates:
                        # Add some random variation to simulate historical changes
                        variation = random.uniform(-0.05, 0.05)  # ±5% variation
                        rate = base_rate * (1 + variation)
                        historical_data[currency].append({
                            "date": date,
                            "rate": rate
                        })
            
            return historical_data, dates
        except Exception as e:
            st.error(f"Error fetching historical rates: {e}")
            return None, None
    
    def _get_historical_from_csv(self, days=30, base="USD"):
        """Get historical data from CSV file"""
        try:
            if not os.path.exists(self.csv_path):
                st.error(f"CSV file not found: {self.csv_path}")
                return None, None
                
            df = pd.read_csv(self.csv_path)
            
            # Sort by date and get the last 'days' days
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date', ascending=False)
            
            # Get unique dates and limit to requested days
            unique_dates = df['date'].unique()[:days]
            df = df[df['date'].isin(unique_dates)]
            
            # Convert dates back to string format
            df['date'] = df['date'].dt.strftime('%Y-%m-%d')
            
            # Get list of available currencies
            currencies = df['currency'].unique()
            
            # Create historical data dictionary
            historical_data = {}
            dates = sorted(df['date'].unique())
            
            for currency in currencies:
                currency_data = df[df['currency'] == currency]
                historical_data[currency] = []
                
                for date in dates:
                    date_data = currency_data[currency_data['date'] == date]
                    if not date_data.empty:
                        rate = date_data['rate'].values[0]
                        historical_data[currency].append({
                            "date": date,
                            "rate": rate
                        })
            
            return historical_data, dates
        except Exception as e:
            st.error(f"Error reading historical CSV data: {e}")
            return None, None
    
    def create_sample_csv(self, output_path=None):
        """
        Create a sample CSV file with exchange rate data
        
        Parameters:
        -----------
        output_path : str
            Path to save the CSV file. If None, uses the default path.
        """
        if output_path is None:
            output_path = self.csv_path
            
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Generate sample data
        today = datetime.now()
        dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)]
        
        currencies = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CNY", "MXN", "BRL", "PEN"]
        
        # Base rates (approximate as of 2023)
        base_rates = {
            "USD": 1.0,
            "EUR": 0.85,
            "GBP": 0.75,
            "JPY": 110.0,
            "CAD": 1.25,
            "AUD": 1.35,
            "CNY": 6.5,
            "MXN": 20.0,
            "BRL": 5.0,
            "PEN": 3.7
        }
        
        # Generate data with some random variations
        import random
        data = []
        
        for date in dates:
            for currency in currencies:
                # Add some random variation to simulate historical changes
                variation = random.uniform(-0.05, 0.05)  # ±5% variation
                rate = base_rates[currency] * (1 + variation)
                
                data.append({
                    "date": date,
                    "currency": currency,
                    "rate": rate
                })
        
        # Create DataFrame and save to CSV
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
        
        return output_path