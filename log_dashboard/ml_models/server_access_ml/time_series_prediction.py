import pandas as pd
from prophet import Prophet
import mysql.connector
from mysql.connector import Error
import matplotlib.pyplot as plt

# MySQL credentials
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'rootroot'
MYSQL_DATABASE = 'siem'

def load_data_from_mysql():
    """Load log timestamps from MySQL"""
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        query = "SELECT log_timestamp FROM server_access_logs"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Error as e:
        print("Error:", e)
        return pd.DataFrame()

def prepare_time_series(df):
    """Prepare hourly aggregated time series"""
    # Parse Apache log timestamp format and remove timezone
    df['log_timestamp'] = pd.to_datetime(
        df['log_timestamp'],
        format='%d/%b/%Y:%H:%M:%S %z',
        errors='coerce'
    ).dt.tz_convert(None)

    # Drop rows where parsing failed
    df = df.dropna(subset=['log_timestamp'])

    # Group by hour
    hourly_counts = df.groupby(df['log_timestamp'].dt.floor('h')).size().reset_index(name='y')
    hourly_counts.rename(columns={'log_timestamp': 'ds'}, inplace=True)

    return hourly_counts

def forecast_traffic(df):
    """Forecast next hour's traffic with alert"""
    if df['ds'].nunique() < 2:
        print("❌ Not enough time points for forecasting. Need at least 2 unique hours.")
        return

    # Create model and add hourly seasonality
    model = Prophet(daily_seasonality=True, yearly_seasonality=False)
    model.add_seasonality(name='hourly', period=24, fourier_order=5)
    model.fit(df)

    # Forecast next hour
    future = model.make_future_dataframe(periods=1, freq='h')
    forecast = model.predict(future)

    # Plot forecast
    fig1 = model.plot(forecast)
    plt.title("Next Hour Traffic Forecast")
    plt.show()

    # Next hour prediction
    next_pred = forecast.iloc[-1][['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
    avg_requests = df['y'].mean()

    print("\n📅 Next Hour Prediction:")
    print(f"Hour: {next_pred['ds']}")
    print(f"Expected Requests: {int(next_pred['yhat'])}")
    print(f"Range: {int(next_pred['yhat_lower'])} - {int(next_pred['yhat_upper'])}")

    # Real-time alert for abnormal spike
    if next_pred['yhat'] > 2 * avg_requests:
        print("🚨 ALERT: Predicted traffic spike! Expected requests exceed twice the average.")
    else:
        print("✅ Traffic forecast within normal range.")

if __name__ == "__main__":
    df_logs = load_data_from_mysql()
    if df_logs.empty:
        print("No data found in MySQL.")
    else:
        ts_df = prepare_time_series(df_logs)
        forecast_traffic(ts_df)
