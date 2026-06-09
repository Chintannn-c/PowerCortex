import os
import sys
import time
import numpy as np

# Add app to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import tensorflow as tf

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "data", "Electricity Demand Data", "lstm_demand_model.keras")

model = tf.keras.models.load_model(MODEL_PATH)
x = np.random.rand(1, 24, 1).astype(np.float32)

# Warm up
_ = model(x, training=False)

print("Timing model(x, training=False) (192 runs)...")
start = time.time()
for _ in range(192):
    _ = model(x, training=False).numpy()[0][0]
print("Time taken for model(x, training=False) (192 runs):", time.time() - start)

print("\nTiming model.predict (192 runs)...")
start = time.time()
for _ in range(192):
    _ = model.predict(x, verbose=0)[0][0]
print("Time taken for model.predict (192 runs):", time.time() - start)
