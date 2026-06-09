import os
import json
import numpy as np

try:
    import tensorflow as tf
    print("TensorFlow version:", tf.__version__)
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MODEL_PATH = os.path.join(BASE_DIR, "data", "Electricity Demand Data", "lstm_demand_model.keras")
    METADATA_PATH = os.path.join(BASE_DIR, "data", "Electricity Demand Data", "lstm_metadata.json")
    
    print("MODEL_PATH exists:", os.path.exists(MODEL_PATH))
    print("METADATA_PATH exists:", os.path.exists(METADATA_PATH))
    
    if os.path.exists(MODEL_PATH):
        model = tf.keras.models.load_model(MODEL_PATH)
        print("Model loaded successfully!")
        print(model.summary())
except Exception as e:
    print("Error:", e)
