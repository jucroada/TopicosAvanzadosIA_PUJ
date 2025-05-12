import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import requests
from data_handler import ExchangeRateDataHandler

# Set page configuration
st.set_page_config(
    page_title="US Dollar Exchange Rate Tracker",
    page_icon="💲",
    layout="wide"
)

# App title and description
st.title("US Dollar Exchange Rate Tracker")
st.markdown("""
This app allows you to check the representative exchange rate of the US dollar against various currencies.
""")

# Initialize data handler
@st.cache_resource
def get_data_handler():
    return ExchangeRateDataHandler(data_source="api")  # Change to "csv" to use CSV data

data_handler = get_data_handler()

# Sidebar for app navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select a page:", ["Current Rates", "Historical Trends", "Currency Converter", "Data Management"])

# Get current exchange rates
rates, last_updated = data_handler.get_current_rates()

if rates:
    # Display different pages based on selection
    if page == "Current Rates":
        st.header("Current Exchange Rates")
        st.write(f"Last Updated: {last_updated}")
        
        # Filter options
        st.subheader("Filter Currencies")
        search_term = st.text_input("Search for a currency code (e.g., EUR, JPY):")
        
        # Convert rates to DataFrame for easier manipulation
        df_rates = pd.DataFrame(list(rates.items()), columns=["Currency", "Rate"])
        
        # Apply search filter if provided
        if search_term:
            df_rates = df_rates[df_rates["Currency"].str.contains(search_term.upper())]
        
        # Display rates in a table
        st.dataframe(df_rates, use_container_width=True)
        
        # Visualize top currencies
        st.subheader("Top 10 Currencies (Relative to USD)")
        
        # Filter for common currencies
        common_currencies = ["EUR", "GBP", "JPY", "CAD", "AUD", "CNY", "MXN", "BRL", "INR", "PEN"]
        common_df = df_rates[df_rates["Currency"].isin(common_currencies)]
        
        # Create bar chart
        fig = px.bar(
            common_df,
            x="Currency",
            y="Rate",
            title="Exchange Rates for Major Currencies",
            labels={"Rate": "Rate (per 1 USD)"},
            color="Rate",
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig, use_container_width=True)
        
    elif page == "Historical Trends":
        st.header("Historical Exchange Rate Trends")
        
        # Get historical data
        historical_data, dates = data_handler.get_historical_rates(30)
        
        if historical_data:
            # Select currencies to display
            available_currencies = list(historical_data.keys())
            selected_currencies = st.multiselect(
                "Select currencies to display:",
                available_currencies,
                default=["EUR", "GBP", "JPY"] if all(c in available_currencies for c in ["EUR", "GBP", "JPY"]) else available_currencies[:3]
            )
            
            if selected_currencies:
                # Create line chart for historical trends
                fig = go.Figure()
                
                for currency in selected_currencies:
                    currency_data = historical_data[currency]
                    dates = [item["date"] for item in currency_data]
                    rates = [item["rate"] for item in currency_data]
                    
                    fig.add_trace(go.Scatter(
                        x=dates,
                        y=rates,
                        mode="lines+markers",
                        name=currency
                    ))
                
                fig.update_layout(
                    title="Historical Exchange Rate Trends",
                    xaxis_title="Date",
                    yaxis_title="Exchange Rate (per 1 USD)",
                    legend_title="Currency",
                    hovermode="x unified"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Show data in tabular format
                st.subheader("Historical Data Table")
                
                # Prepare data for display
                table_data = []
                for currency in selected_currencies:
                    for item in historical_data[currency]:
                        table_data.append({
                            "Date": item["date"],
                            "Currency": currency,
                            "Rate": round(item["rate"], 4)
                        })
                
                table_df = pd.DataFrame(table_data)
                pivot_df = table_df.pivot(index="Date", columns="Currency", values="Rate")
                st.dataframe(pivot_df, use_container_width=True)
            else:
                st.info("Please select at least one currency to display historical trends.")
    
    elif page == "Currency Converter":
        st.header("Currency Converter")
        
        col1, col2 = st.columns(2)
        
        with col1:
            amount = st.number_input("Enter amount:", min_value=0.01, value=100.0, step=10.0)
            from_currency = st.selectbox("From Currency:", list(rates.keys()), index=list(rates.keys()).index("USD") if "USD" in rates else 0)
        
        with col2:
            to_currency = st.selectbox("To Currency:", list(rates.keys()), index=list(rates.keys()).index("EUR") if "EUR" in rates else 0)
            
        # Calculate conversion
        if from_currency == "USD":
            result = amount * rates[to_currency]
        elif to_currency == "USD":
            result = amount / rates[from_currency]
        else:
            # Convert through USD
            usd_amount = amount / rates[from_currency]
            result = usd_amount * rates[to_currency]
        
        # Display result
        st.subheader("Conversion Result")
        st.markdown(f"""
        <div style="padding: 20px; background-color: #f0f2f6; border-radius: 10px; text-align: center;">
            <h2>{amount:.2f} {from_currency} = {result:.2f} {to_currency}</h2>
            <p>Exchange rate: 1 {from_currency} = {result/amount:.4f} {to_currency}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Add a chart showing the exchange rate over time
        st.subheader(f"Recent {from_currency}/{to_currency} Exchange Rate Trend")
        
        # Get historical data for the selected currencies
        historical_data, dates = data_handler.get_historical_rates(30)
        
        if historical_data and from_currency in historical_data and to_currency in historical_data:
            # Calculate cross rates
            from_data = historical_data[from_currency]
            to_data = historical_data[to_currency]
            
            cross_rates = []
            for i in range(len(from_data)):
                if from_currency == "USD":
                    rate = to_data[i]["rate"]
                elif to_currency == "USD":
                    rate = 1 / from_data[i]["rate"]
                else:
                    # Convert through USD
                    rate = to_data[i]["rate"] / from_data[i]["rate"]
                
                cross_rates.append({
                    "date": from_data[i]["date"],
                    "rate": rate
                })
            
            # Create DataFrame for the chart
            df = pd.DataFrame(cross_rates)
            
            # Create line chart
            fig = px.line(
                df,
                x="date",
                y="rate",
                title=f"{from_currency}/{to_currency} Exchange Rate Trend",
                labels={"rate": f"Rate (1 {from_currency} to {to_currency})", "date": "Date"}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    elif page == "Data Management":
        st.header("Data Management")
        
        st.subheader("Data Source")
        data_source = st.radio(
            "Select data source:",
            ["API", "CSV File"],
            index=0 if data_handler.data_source == "api" else 1
        )
        
        if data_source == "CSV File":
            st.info("To use CSV data, you need to have a CSV file with exchange rate data.")
            
            # Check if data directory exists
            data_dir = os.path.join(os.path.dirname(__file__), "data")
            csv_path = os.path.join(data_dir, "exchange_rates.csv")
            
            if not os.path.exists(csv_path):
                st.warning("No exchange rate CSV file found.")
                
                if st.button("Generate Sample CSV Data"):
                    with st.spinner("Generating sample data..."):
                        path = data_handler.create_sample_csv()
                        st.success(f"Sample data created at: {path}")
                        st.info("Please restart the app to use the CSV data source.")
            else:
                st.success(f"CSV data file found: {csv_path}")
                
                # Show preview of the CSV data
                try:
                    df = pd.read_csv(csv_path)
                    st.subheader("CSV Data Preview")
                    st.dataframe(df.head(10), use_container_width=True)
                    
                    st.info("To switch to CSV data source, change the data_source parameter in the get_data_handler function to 'csv' and restart the app.")
                except Exception as e:
                    st.error(f"Error reading CSV file: {e}")
        else:
            st.info("Currently using API data source (open.er-api.com).")
            st.write("""
            For more accurate historical data, consider:
            1. Using a paid API service like Open Exchange Rates, Fixer.io, or Alpha Vantage
            2. Downloading historical exchange rate data from sources like Federal Reserve or European Central Bank
            """)

# Footer
st.markdown("---")
st.markdown("© 2023 US Dollar Exchange Rate Tracker | Data provided by Open Exchange Rates API")