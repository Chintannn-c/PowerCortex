import logging
logger = logging.getLogger(__name__)
import os
import pickle
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Input
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

def generate_system_health_data(n_samples: int = 5000):
    np.random.seed(42)
    
    # 1. Generate features
    # CPU usage: 0% to 100% (skewed slightly lower to represent standard workloads)
    cpu_usage = np.random.beta(2, 5, n_samples) * 100.0
    
    # Memory usage: 10% to 95%
    memory_usage = np.random.beta(3, 4, n_samples) * 85.0 + 10.0
    
    # Network latency: 5ms to 500ms
    network_latency = np.random.exponential(50.0, n_samples) + 5.0
    network_latency = np.clip(network_latency, 5.0, 500.0)
    
    # DB connected: 1.0 (connected) or 0.0 (disconnected, ~3% chance)
    db_connected = np.random.choice([1.0, 0.0], size=n_samples, p=[0.97, 0.03])
    
    # API latency: 10ms to 300ms
    api_latency = np.random.exponential(40.0, n_samples) + 10.0
    api_latency = np.clip(api_latency, 10.0, 300.0)
    
    # 2. Compute targets (health_score and failure_probability)
    health = 100.0 - np.zeros(n_samples)
    
    # Database impact
    health -= np.where(db_connected == 0.0, 45.0, 0.0)
    
    # CPU impact (warning > 70%)
    health -= np.where(cpu_usage > 70.0, (cpu_usage - 70.0) * 1.5, 0.0)
    
    # Memory impact (warning > 80%)
    health -= np.where(memory_usage > 80.0, (memory_usage - 80.0) * 2.0, 0.0)
    
    # Network latency impact (warning > 150ms)
    health -= np.where(network_latency > 150.0, (network_latency - 150.0) * 0.1, 0.0)
    
    # API latency impact (warning > 100ms)
    health -= np.where(api_latency > 100.0, (api_latency - 100.0) * 0.2, 0.0)
    
    # Add small normal noise
    health += np.random.normal(0, 1.5, n_samples)
    health = np.clip(health, 10.0, 100.0)
    
    # Failure probability (correlated with health)
    failure_probability = 100.0 - health
    failure_probability = np.where(health < 50.0, failure_probability * 1.2, failure_probability * 0.8)
    failure_probability = np.clip(failure_probability, 0.0, 99.0)
    
    df = pd.DataFrame({
        'cpu_usage': cpu_usage,
        'memory_usage': memory_usage,
        'network_latency': network_latency,
        'db_connected': db_connected,
        'api_latency': api_latency,
        'health_score': health,
        'failure_probability': failure_probability
    })
    return df

def train_model():
    logger.info("Generating synthetic system health data...")
    df = generate_system_health_data()
    
    X = df[['cpu_usage', 'memory_usage', 'network_latency', 'db_connected', 'api_latency']].values
    y = df[['health_score', 'failure_probability']].values
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Build Keras MLP
    model = Sequential([
        Input(shape=(5,)),
        Dense(32, activation='relu'),
        Dense(16, activation='relu'),
        Dense(2, activation='linear')
    ])
    
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    
    logger.info("Training Keras MLP Model...")
    model.fit(X_train_scaled, y_train, epochs=40, batch_size=32, validation_split=0.1, verbose=1)
    
    test_loss, test_mae = model.evaluate(X_test_scaled, y_test, verbose=0)
    logger.info(f"Test MSE Loss: {test_loss:.4f}, Test MAE: {test_mae:.4f}")
    
    # Save directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    models_dir = os.path.join(base_dir, "models")
    os.makedirs(models_dir, exist_ok=True)
    
    model_path = os.path.join(models_dir, "system_health_model.keras")
    scaler_path = os.path.join(models_dir, "system_health_scaler.pkl")
    
    logger.info(f"Saving Keras model to {model_path}...")
    model.save(model_path)
    
    logger.info(f"Saving scaler to {scaler_path}...")
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
        
    logger.info("System Health model training complete!")

if __name__ == '__main__':
    train_model()
