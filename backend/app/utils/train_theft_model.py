import logging
logger = logging.getLogger(__name__)
import os
import pickle
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

def train_theft_model():
    logger.info("Generating synthetic consumer training data...")
    np.random.seed(42)
    
    # Generate Normal Consumers (e.g. 1000 samples)
    avg_normal = np.random.uniform(500, 2000, 1000)
    current_normal = avg_normal * np.random.uniform(0.85, 1.15, 1000)
    pf_normal = np.random.uniform(0.85, 0.98, 1000)
    dev_normal = ((current_normal - avg_normal) / avg_normal) * 100.0
    
    X_normal = np.column_stack([current_normal, avg_normal, pf_normal, dev_normal])
    
    # Generate Theft Consumers (e.g. 200 samples)
    avg_theft = np.random.uniform(500, 2000, 200)
    current_theft = avg_theft * np.random.uniform(0.20, 0.55, 200)
    pf_theft = np.random.uniform(0.50, 0.75, 200)
    dev_theft = ((current_theft - avg_theft) / avg_theft) * 100.0
    
    X_theft = np.column_stack([current_theft, avg_theft, pf_theft, dev_theft])
    
    X = np.vstack([X_normal, X_theft])
    
    logger.info("Scaling training features...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    logger.info("Training Isolation Forest Classifier...")
    model = IsolationForest(n_estimators=100, contamination=0.17, random_state=42)
    model.fit(X_scaled)
    
    # Save the model and scaler
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    model_dir = os.path.join(base_dir, "app", "models")
    os.makedirs(model_dir, exist_ok=True)
    
    model_path = os.path.join(model_dir, "theft_detection_model.pkl")
    scaler_path = os.path.join(model_dir, "theft_scaler.pkl")
    
    logger.info(f"Saving Isolation Forest model to {model_path}...")
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
        
    logger.info(f"Saving scaler to {scaler_path}...")
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
        
    logger.info("Theft model training and serialization complete.")

if __name__ == "__main__":
    train_theft_model()
