import logging
logger = logging.getLogger(__name__)
import os
import pickle
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Input

def train_model():
    logger.info("Generating synthetic transformer telemetry data...")
    np.random.seed(42)
    n_samples = 5000
    
    # Generate realistic features
    temperature = np.random.uniform(40.0, 110.0, n_samples)
    voltage = np.random.uniform(9.5, 12.5, n_samples)
    current = np.random.uniform(50.0, 600.0, n_samples)
    oil_level = np.random.uniform(30.0, 100.0, n_samples)
    load_percentage = np.random.uniform(10.0, 120.0, n_samples)
    
    # Calculate health score deterministically with some noise
    health = 100.0 - np.zeros(n_samples)
    
    # Penalties
    health -= np.where(temperature > 80.0, (temperature - 80.0) * 1.2, 0.0)
    health -= np.where(temperature > 95.0, (temperature - 95.0) * 1.8, 0.0)
    
    volt_dev = np.abs(voltage - 11.0)
    health -= np.where(volt_dev > 0.5, volt_dev * 15.0, 0.0)
    
    health -= np.where(current > 350.0, (current - 350.0) * 0.1, 0.0)
    health -= np.where(oil_level < 80.0, (80.0 - oil_level) * 1.5, 0.0)
    health -= np.where(load_percentage > 80.0, (load_percentage - 80.0) * 0.8, 0.0)
    
    # Add random noise
    health += np.random.normal(0, 2.0, n_samples)
    health = np.clip(health, 10.0, 100.0)
    
    # Failure probability (correlated with health score)
    failure_probability = 100.0 - health
    failure_probability = np.where(health < 50.0, failure_probability * 1.2, failure_probability * 0.8)
    failure_probability += np.random.normal(0, 3.0, n_samples)
    failure_probability = np.clip(failure_probability, 0.0, 99.0)
    
    # Create DataFrame
    df = pd.DataFrame({
        'temperature': temperature,
        'voltage': voltage,
        'current': current,
        'oil_level': oil_level,
        'load_percentage': load_percentage,
        'health_score': health,
        'failure_probability': failure_probability
    })
    
    X = df[['temperature', 'voltage', 'current', 'oil_level', 'load_percentage']].values
    y = df[['health_score', 'failure_probability']].values
    
    # Scale features
    logger.info("Scaling features...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Build Keras Feed-Forward Neural Network (MLP)
    logger.info("Building Keras MLP model...")
    model = Sequential([
        Input(shape=(5,)),
        Dense(32, activation='relu'),
        Dense(16, activation='relu'),
        Dense(2, activation='linear')
    ])
    
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    
    logger.info("Training Keras MLP model...")
    model.fit(X_scaled, y, epochs=40, batch_size=32, validation_split=0.1, verbose=1)
    
    # Save the Keras model and scaler
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_dir = os.path.join(base_dir, "models")
    os.makedirs(model_dir, exist_ok=True)
    
    model_path = os.path.join(model_dir, "transformer_health_model.keras")
    scaler_path = os.path.join(model_dir, "transformer_scaler.pkl")
    
    logger.info(f"Saving Keras model to {model_path}...")
    model.save(model_path)
    
    logger.info(f"Saving scaler to {scaler_path}...")
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
        
    logger.info("Model training and serialization complete.")

if __name__ == "__main__":
    train_model()
