import logging
logger = logging.getLogger(__name__)
import os
import pickle
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score

def train_model():
    logger.info("Loading fault detection dataset...")
    # Find dataset path relative to this file
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csv_path = os.path.join(base_dir, "data", "Fault Detection Data", "fault detection.csv")
    
    if not os.path.exists(csv_path):
        logger.info(f"Dataset not found at {csv_path}!")
        return
        
    df = pd.read_csv(csv_path)
    logger.info(f"Dataset shape: {df.shape}")
    
    X = df[['Voltage', 'Current', 'Frequency']].values
    y = df['Fault_Label'].values
    
    # Check number of classes and check for nulls
    logger.info(f"Unique labels in target: {np.unique(y)}")
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    logger.info("Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    logger.info("Importing TensorFlow and Keras...")
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, Dropout, BatchNormalization, Input
    from tensorflow.keras.callbacks import EarlyStopping
    
    # Set random seeds for reproducibility
    np.random.seed(42)
    tf.random.set_seed(42)
    
    logger.info("Building Keras Multi-Layer Perceptron (MLP) model...")
    model = Sequential([
        Input(shape=(3,)),
        Dense(64, activation='relu'),
        BatchNormalization(),
        Dropout(0.2),
        Dense(32, activation='relu'),
        BatchNormalization(),
        Dropout(0.2),
        Dense(4, activation='softmax')
    ])
    
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    
    model.summary()
    
    # Setup callbacks
    early_stopping = EarlyStopping(
        monitor='val_loss',
        patience=5,
        restore_best_weights=True
    )
    
    logger.info("Training Keras MLP model...")
    model.fit(
        X_train_scaled, y_train,
        epochs=30,
        batch_size=32,
        validation_split=0.15,
        callbacks=[early_stopping],
        verbose=1
    )
    
    # Evaluate
    y_pred_probs = model.predict(X_test_scaled)
    y_pred = np.argmax(y_pred_probs, axis=1)
    
    accuracy = accuracy_score(y_test, y_pred)
    logger.info(f"Test Accuracy: {accuracy:.4f}")
    logger.info("\nClassification Report:")
    logger.info(classification_report(y_test, y_pred))
    
    # Save the model and scaler
    model_dir = os.path.join(base_dir, "app", "models")
    os.makedirs(model_dir, exist_ok=True)
    
    model_path = os.path.join(model_dir, "fault_detection_model.keras")
    scaler_path = os.path.join(model_dir, "fault_scaler.pkl")
    
    logger.info(f"Saving Keras model to {model_path}...")
    model.save(model_path)
    
    # Clean up old pickle model if it exists
    old_model_path = os.path.join(model_dir, "fault_detection_model.pkl")
    if os.path.exists(old_model_path):
        logger.info(f"Removing old Random Forest model file: {old_model_path}")
        try:
            os.remove(old_model_path)
        except Exception as e:
            logger.info(f"Failed to remove old model: {e}")
        
    logger.info(f"Saving scaler to {scaler_path}...")
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
        
    logger.info("Model training and Keras serialization complete.")

if __name__ == "__main__":
    train_model()
