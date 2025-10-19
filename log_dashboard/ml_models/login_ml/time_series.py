import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np

# 1. Load data
df = pd.read_csv("loginlogoffff.csv")

# 2. Convert timestamp to datetime
df['Login Timestamp'] = pd.to_datetime(df['Login Timestamp'])

# 3. Aggregate hourly login counts
hourly_counts = df.groupby(df['Login Timestamp'].dt.floor('H')).size()
ts_hourly = pd.DataFrame(hourly_counts, columns=['logins'])

# 4. Plot hourly data
plt.figure(figsize=(10,4))
plt.plot(ts_hourly['logins'])
plt.title("Hourly Login Counts")
plt.xlabel("Date")
plt.ylabel("Number of Logins")
plt.show()

# 5. Train-test split
train_size = int(len(ts_hourly) * 0.8)
train, test = ts_hourly.iloc[:train_size], ts_hourly.iloc[train_size:]

# 6. Fit SARIMA model (hourly seasonality: 24)
model = SARIMAX(train['logins'],
                order=(1,1,1),
                seasonal_order=(1,1,1,24),
                enforce_stationarity=False,
                enforce_invertibility=False)
results = model.fit(disp=False)

# 7. Forecast
forecast = results.get_forecast(steps=len(test))
forecast_mean = forecast.predicted_mean
forecast_ci = forecast.conf_int()

# 8. Plot forecasts
plt.figure(figsize=(10,4))
plt.plot(train.index, train['logins'], label='Train')
plt.plot(test.index, test['logins'], label='Test', color='orange')
plt.plot(test.index, forecast_mean, label='Forecast', color='green')
plt.fill_between(test.index, forecast_ci.iloc[:,0], forecast_ci.iloc[:,1],
                 color='k', alpha=0.1)
plt.legend()
plt.title("SARIMA Forecast of Hourly Logins")
plt.show()

# 9. Metrics
mae = mean_absolute_error(test['logins'], forecast_mean)
rmse = np.sqrt(mean_squared_error(test['logins'], forecast_mean))
print("MAE:", mae)
print("RMSE:", rmse)
