import logging
import os
import json
import pickle
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Input
from sklearn.preprocessing import StandardScaler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def train_dl_theft_model():
    logger.info("Generating synthetic consumer training data (normal only for autoencoder)...")
    np.random.seed(42)
    tf.random.set_seed(42)
    
    # Generate Normal Consumers (Autoencoders only train on normal data)
    avg_normal = np.random.uniform(500, 2000, 2000)
    current_normal = avg_normal * np.random.uniform(0.85, 1.15, 2000)
    pf_normal = np.random.uniform(0.85, 0.98, 2000)
    dev_normal = ((current_normal - avg_normal) / avg_normal) * 100.0
    
    X_normal = np.column_stack([current_normal, avg_normal, pf_normal, dev_normal])
    
    logger.info("Scaling training features...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_normal)
    
    logger.info("Building Deep Autoencoder...")
    # 4 input features
    model = Sequential([
        Input(shape=(4,)),
        # Encoder
        Dense(8, activation='relu'),
        Dense(4, activation='relu'),
        # Decoder
        Dense(8, activation='relu'),
        Dense(4, activation='linear')
    ])
    
    model.compile(optimizer='adam', loss='mse')
    
    logger.info("Training Autoencoder...")
    model.fit(X_scaled, X_scaled, epochs=50, batch_size=32, validation_split=0.1, verbose=1)
    
    # Calculate reconstruction error for normal data to set the threshold
    predictions = model.predict(X_scaled)
    mse = np.mean(np.power(X_scaled - predictions, 2), axis=1)
    
    # 95th percentile of normal MSE is the threshold
    threshold = float(np.percentile(mse, 95))
    logger.info(f"Anomaly threshold set to: {threshold}")
    
    # Save the model, scaler, and threshold
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    model_dir = os.path.join(base_dir, "app", "models")
    os.makedirs(model_dir, exist_ok=True)
    
    model_path = os.path.join(model_dir, "theft_detection_model.keras")
    scaler_path = os.path.join(model_dir, "theft_scaler.pkl")
    threshold_path = os.path.join(model_dir, "theft_threshold.json")
    
    logger.info(f"Saving Keras Autoencoder model to {model_path}...")
    model.save(model_path)
        
    logger.info(f"Saving scaler to {scaler_path}...")
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
        
    logger.info(f"Saving threshold to {threshold_path}...")
    with open(threshold_path, 'w') as f:
        json.dump({"mse_threshold": threshold}, f)
        
    logger.info("Deep Learning Theft Autoencoder training and serialization complete.")

if __name__ == "__main__":
    train_dl_theft_model()
