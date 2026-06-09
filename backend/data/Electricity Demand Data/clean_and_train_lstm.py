# Import required libraries
import os
import json
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(SCRIPT_DIR, exist_ok=True) # Create output directory

# Load and clean dataset
df = pd.read_csv(os.path.join(SCRIPT_DIR, "data", "PJME_hourly.csv")) # Read raw CSV data
df['Datetime'] = pd.to_datetime(df['Datetime']) # Convert to datetime objects
df = df.sort_values('Datetime') # Sort by date/time
df = df.groupby('Datetime').mean() # Merge duplicate hours by taking mean

full_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq='h') # Create complete hourly range
df = df.reindex(full_range) # Fill missing hours in timeline
df['PJME_MW'] = df['PJME_MW'].interpolate(method='linear') # Interpolate missing demand values

# Scale data
scaler = MinMaxScaler(feature_range=(0, 1)) # Normalize scale between 0 and 1
scaled_data = scaler.fit_transform(df[['PJME_MW']].values) # Scale load values

# Create sequences
lookback = 24 # Use past 24 hours to predict next hour
def create_sequences(data, lookback=24):
    X, y = [], []
    for i in range(len(data) - lookback):
        X.append(data[i : i + lookback]) # Past 24 hours values (inputs)
        y.append(data[i + lookback])     # Next hour value (target)
    return np.array(X), np.array(y)

X, y = create_sequences(scaled_data, lookback=lookback) # Generate sequences

# Train-test split
split_date = pd.to_datetime('2016-01-01') # Split date threshold
split_idx = df.index.get_loc(split_date) - lookback # Adjust index for lookback
X_train, y_train = X[:split_idx], y[:split_idx] # Train sequences (2002-2015)
X_test, y_test = X[split_idx:], y[split_idx:] # Test sequences (2016-2018)

# Build LSTM model
model = Sequential() # Step-by-step neural net stack
model.add(LSTM(64, input_shape=(lookback, 1), return_sequences=False)) # Memory cell layer
model.add(Dropout(0.2)) # Randomly drop 20% connections to prevent overfitting
model.add(Dense(32, activation='relu')) # Hidden dense layer
model.add(Dense(1)) # Output single node for next hour forecast

model.compile(optimizer='adam', loss='mean_squared_error') # Compile with Adam and MSE loss

# Train model
history = model.fit(X_train, y_train, epochs=5, batch_size=512, validation_data=(X_test, y_test), verbose=1) # Train for 5 epochs

# Predictions
train_pred = scaler.inverse_transform(model.predict(X_train)) # Inverse scale train predictions
test_pred = scaler.inverse_transform(model.predict(X_test)) # Inverse scale test predictions
y_train_actual = scaler.inverse_transform(y_train) # Inverse scale actual train values
y_test_actual = scaler.inverse_transform(y_test) # Inverse scale actual test values

# Metrics
train_rmse = np.sqrt(mean_squared_error(y_train_actual, train_pred))
test_rmse = np.sqrt(mean_squared_error(y_test_actual, test_pred))
train_mae = mean_absolute_error(y_train_actual, train_pred)
test_mae = mean_absolute_error(y_test_actual, test_pred)
train_r2 = r2_score(y_train_actual, train_pred)
test_r2 = r2_score(y_test_actual, test_pred)
train_mape = np.mean(np.abs((y_train_actual - train_pred) / y_train_actual)) * 100
test_mape = np.mean(np.abs((y_test_actual - test_pred) / y_test_actual)) * 100

print(f"\nTrain RMSE: {train_rmse:.2f} | MAE: {train_mae:.2f} | R2: {train_r2:.4f} | MAPE: {train_mape:.2f}%")
print(f"Test RMSE: {test_rmse:.2f} | MAE: {test_mae:.2f} | R2: {test_r2:.4f} | MAPE: {test_mape:.2f}%")

# Plot forecast (Actual vs Predicted) - the only important validation graph
test_timestamps = df.index[split_idx + lookback:] # Test dates
results_df = pd.DataFrame({'Actual': y_test_actual.flatten(), 'Prediction': test_pred.flatten()}, index=test_timestamps)

plt.figure(figsize=(12, 6))
plot_df = results_df.loc['2016-01-01':'2016-01-07'] # Plot first week
plt.plot(plot_df.index, plot_df['Actual'], label='Actual Demand', color='#1B1464', linewidth=2) # Navy Blue for actual
plt.plot(plot_df.index, plot_df['Prediction'], label='Predicted Demand', color='#EA2027', linestyle='--', linewidth=2) # Bright Red for predicted

# Find peak and trough points for annotations
peak_time = plot_df['Actual'].idxmax()
peak_act = plot_df.loc[peak_time, 'Actual']
peak_pr = plot_df.loc[peak_time, 'Prediction']

trough_time = plot_df['Actual'].idxmin()
trough_act = plot_df.loc[trough_time, 'Actual']
trough_pr = plot_df.loc[trough_time, 'Prediction']

# Annotate Peak value
plt.gca().annotate(
    f"Peak Load:\nActual: {peak_act:.0f} MW\nPred: {peak_pr:.0f} MW",
    xy=(peak_time, peak_act),
    xytext=(peak_time + pd.Timedelta(hours=4), peak_act - 1500),
    arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.5),
    fontsize=9,
    bbox=dict(boxstyle='round,pad=0.3', facecolor='#fff5f5', edgecolor='red', alpha=0.9)
)

# Annotate Trough value
plt.gca().annotate(
    f"Trough Load:\nActual: {trough_act:.0f} MW\nPred: {trough_pr:.0f} MW",
    xy=(trough_time, trough_act),
    xytext=(trough_time + pd.Timedelta(hours=4), trough_act + 1500),
    arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.5),
    fontsize=9,
    bbox=dict(boxstyle='round,pad=0.3', facecolor='#f5faff', edgecolor='blue', alpha=0.9)
)

# Add performance metrics text box on the graph to tell what the model says in easy terms
metrics_text = (
    f"Model: LSTM Deep Learning\n"
    f"Test Accuracy: {100 - test_mape:.2f}% (MAPE: {test_mape:.2f}%)\n"
    f"Variance Explained (R2): {test_r2:.4f}\n"
    f"Avg. Prediction Error: {test_mae:.1f} MW"
)
props = dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='gray', alpha=0.8)
plt.gca().text(0.02, 0.95, metrics_text, transform=plt.gca().transAxes, fontsize=10, verticalalignment='top', bbox=props)

plt.title("Electricity Demand: Actual vs. Predicted (LSTM Deep Learning)")
plt.xlabel("Datetime")
plt.ylabel("Megawatts (MW)")
plt.legend(loc='upper right')
plt.tight_layout()
plt.savefig(os.path.join(SCRIPT_DIR, "forecast_graph.png"), dpi=150) # Save forecast graph
plt.close()

# Save model weights
model.save(os.path.join(SCRIPT_DIR, "lstm_demand_model.keras")) # Save keras model weights

# =============================================================
# Step 12: Future Forecasting (Tomorrow & Next Week Predictions)
# =============================================================
# Get the last available 24 hours of actual demand as the seed sequence
last_24_hours = df['PJME_MW'].iloc[-24:].values.reshape(-1, 1) # Extract final day demand values
last_timestamp = df.index[-1] # Find the last timestamp in dataset

# Recursive Forecasting Loop for 168 hours (1 Week)
current_sequence = scaler.transform(last_24_hours) # Scale the seed window
future_predictions = []

for hour in range(168):
    input_seq = current_sequence.reshape(1, lookback, 1) # Reshape sequence for LSTM input: (1, 24, 1)
    pred_scaled = model.predict(input_seq, verbose=0)[0][0] # Predict next hour
    future_predictions.append(pred_scaled) # Save the prediction
    current_sequence = np.append(current_sequence[1:], [[pred_scaled]], axis=0) # Slide the window

# Inverse scale predictions back to original Megawatts (MW)
future_predictions = scaler.inverse_transform(np.array(future_predictions).reshape(-1, 1)).flatten()

# Generate future timestamps
future_timestamps = pd.date_range(start=last_timestamp + pd.Timedelta(hours=1), periods=168, freq='h')
forecast_df = pd.DataFrame({'Forecasted_Demand_MW': future_predictions}, index=future_timestamps) # Create forecast dataframe

# Analyze and aggregate hourly forecast into daily metrics
daily_forecast = forecast_df.resample('D').agg(
    Peak_Demand_MW=('Forecasted_Demand_MW', 'max'),
    Average_Demand_MW=('Forecasted_Demand_MW', 'mean'),
    Minimum_Demand_MW=('Forecasted_Demand_MW', 'min')
).iloc[:7] # Keep exactly the next 7 days

tomorrow_date = daily_forecast.index[0]
tomorrow_peak = daily_forecast.loc[tomorrow_date, 'Peak_Demand_MW']
tomorrow_avg = daily_forecast.loc[tomorrow_date, 'Average_Demand_MW']

week_peak_date = daily_forecast['Peak_Demand_MW'].idxmax()
week_peak_val = daily_forecast['Peak_Demand_MW'].max()
week_avg = daily_forecast['Average_Demand_MW'].mean()

print("\n--- FUTURE DAILY DEMAND FORECAST RESULTS ---")
print(f"Tomorrow's Forecasted Peak: {tomorrow_peak:.2f} MW (Date: {tomorrow_date.strftime('%Y-%m-%d')})")
print(f"Tomorrow's Average Forecasted Demand: {tomorrow_avg:.2f} MW")
print(f"Next Week's Forecasted Peak: {week_peak_val:.2f} MW (Date: {week_peak_date.strftime('%Y-%m-%d')})")
print(f"Next Week's Average Forecasted Demand: {week_avg:.2f} MW")

# Plot Future Forecast Daily Bar Graph - Peak and Average Demand side-by-side with values labeled
plt.figure(figsize=(12, 6), dpi=150)
x = np.arange(len(daily_forecast))
width = 0.35

# Plot Peak and Average Demand bars
plt.bar(x - width/2, daily_forecast['Peak_Demand_MW'], width, label='Daily Peak Demand', color='#1B1464') # Navy Blue
plt.bar(x + width/2, daily_forecast['Average_Demand_MW'], width, label='Daily Average Demand', color='#ff7f0e') # Orange

# Add data labels on top of the bars showing the exact value of both
for idx, val in enumerate(daily_forecast['Peak_Demand_MW']):
    plt.text(idx - width/2, val + 400, f"{val:.0f}", ha='center', va='bottom', fontsize=8, fontweight='bold', color='#1B1464')
for idx, val in enumerate(daily_forecast['Average_Demand_MW']):
    plt.text(idx + width/2, val + 400, f"{val:.0f}", ha='center', va='bottom', fontsize=8, fontweight='bold', color='#ff7f0e')

plt.title("LSTM Deep Learning: 1-Week Future Daily Demand Forecast (Peak vs. Average)", fontsize=13, fontweight='bold', pad=15)
plt.xlabel("Date", fontsize=11, labelpad=10)
plt.ylabel("Electricity Load (Megawatts - MW)", fontsize=11, labelpad=10)
plt.xticks(x, [d.strftime('%a\n%b %d') for d in daily_forecast.index]) # Format dates nicely on X-axis
plt.ylim(0, daily_forecast['Peak_Demand_MW'].max() * 1.15) # Add space for labels
plt.legend(loc='upper right')
plt.grid(True, linestyle=':', alpha=0.6, axis='y')
plt.tight_layout()
plt.savefig(os.path.join(SCRIPT_DIR, "future_forecast_graph.png"), dpi=150) # Save future daily forecast graph
plt.close()

# Save daily forecast values to CSV
daily_forecast.to_csv(os.path.join(SCRIPT_DIR, "future_forecast_1week.csv")) # Save daily metrics to CSV

# Save model metadata configuration
metadata = {
    "model_name": "LSTM_Demand_Forecaster",
    "scaler": {"min": float(scaler.min_[0]), "scale": float(scaler.scale_[0])},
    "metrics": {
        "train": {"rmse": float(train_rmse), "mae": float(train_mae), "r2": float(train_r2), "mape": float(train_mape)},
        "test": {"rmse": float(test_rmse), "mae": float(test_mae), "r2": float(test_r2), "mape": float(test_mape)}
    }
}
with open(os.path.join(SCRIPT_DIR, "lstm_metadata.json"), 'w') as f:
    json.dump(metadata, f, indent=4) # Save metadata configuration

print("Processing complete! Model is trained and daily future predictions are saved.")

