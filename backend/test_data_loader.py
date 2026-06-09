import os
import json
import numpy as np
import pandas as pd
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "data", "Electricity Demand Data", "data", "PJME_hourly.csv")
METADATA_PATH = os.path.join(BASE_DIR, "data", "Electricity Demand Data", "lstm_metadata.json")

print("CSV path:", CSV_PATH)
print("CSV exists:", os.path.exists(CSV_PATH))

df = pd.read_csv(CSV_PATH)
df['Datetime'] = pd.to_datetime(df['Datetime'])
df = df.sort_values('Datetime')
df = df.groupby('Datetime').mean()

full_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq='h')
df = df.reindex(full_range)
df['PJME_MW'] = df['PJME_MW'].interpolate(method='linear')

print("Cleaned DataFrame shape:", df.shape)

# Find split index
split_date = pd.to_datetime('2016-01-01')
split_idx = df.index.get_loc(split_date)
print("Split date index:", split_idx)

# Scaler
with open(METADATA_PATH, 'r') as f:
    meta = json.load(f)
scaler_min = meta["scaler"]["min"]
scaler_scale = meta["scaler"]["scale"]

print("Scaler min:", scaler_min)
print("Scaler scale:", scaler_scale)

# Dynamic index mapping
test_size = len(df) - split_idx
current_seconds = int(time.time())
current_hour_idx = (current_seconds // 3600) % (test_size - 24 - 168)
target_idx = split_idx + current_hour_idx

print("Target index:", target_idx)
print("Target datetime:", df.index[target_idx])
print("Target demand:", df['PJME_MW'].iloc[target_idx])
