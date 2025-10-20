import os
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np

base_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(base_dir, "loginlogoffff.csv")
output_path = os.path.join(base_dir, "sarima_forecast.png")

if not os.path.exists(csv_path):
    print(f"❌ CSV file not found: {csv_path}")
    exit()

df = pd.read_csv(csv_path)
df.columns = [col.strip().replace(" ", "_") for col in df.columns]

if "Login_Timestamp" not in df.columns:
    print("❌ Missing column 'Login_Timestamp'")
    exit()

df["Login_Timestamp"] = pd.to_datetime(df["Login_Timestamp"], errors="coerce")
hourly_counts = df.groupby(df["Login_Timestamp"].dt.floor("h")).size()
ts_hourly = pd.DataFrame(hourly_counts, columns=["logins"])

# Always generate a plot
plt.figure(figsize=(10, 4))
plt.plot(ts_hourly.index, ts_hourly["logins"], label="Observed", color="blue")

if len(ts_hourly) >= 30:
    train_size = int(len(ts_hourly) * 0.8)
    train, test = ts_hourly.iloc[:train_size], ts_hourly.iloc[train_size:]

    model = SARIMAX(train["logins"], order=(1,1,1), seasonal_order=(1,1,1,24))
    results = model.fit(disp=False)

    forecast = results.get_forecast(steps=len(test))
    forecast_mean = forecast.predicted_mean
    forecast_ci = forecast.conf_int()

    mae = mean_absolute_error(test["logins"], forecast_mean)
    rmse = np.sqrt(mean_squared_error(test["logins"], forecast_mean))

    plt.plot(test.index, forecast_mean, label="Forecast", color="green")
    plt.fill_between(test.index, forecast_ci.iloc[:,0], forecast_ci.iloc[:,1],
                     color="gray", alpha=0.2)
    plt.legend()
    plt.title(f"SARIMA Forecast of Hourly Logins\nMAE={mae:.2f}, RMSE={rmse:.2f}")
    print(f"✅ SARIMA Forecast completed — MAE={mae:.2f}, RMSE={rmse:.2f}")
else:
    # fallback simple trend
    plt.title("Observed Login Trends (Insufficient Data for SARIMA)")
    print("ℹ️ Insufficient data for SARIMA — showing trend only.")

plt.xlabel("Time")
plt.ylabel("Number of Logins")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(output_path)
print(f"✅ Plot saved at: {output_path}")
