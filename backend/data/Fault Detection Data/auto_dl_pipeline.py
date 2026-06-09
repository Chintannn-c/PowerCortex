"""
Adaptive Deep Learning Pipeline
-------------------------------
Author: Antigravity AI Assistant
Description: A robust, flexible, and fully-portable Python script that auto-adapts
             to the input CSV dataset, parses if it is a Time-Series Forecasting
             or Tabular Classification/Regression task, constructs the optimal
             deep learning model (LSTM/GRU/BiLSTM vs Deep MLP), trains it using
             regularization callbacks, prints key metrics, and exports artifacts.
"""

import os
import sys
import json
import pickle
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, MinMaxScaler, OneHotEncoder, LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, confusion_matrix,
    mean_squared_error, mean_absolute_error, r2_score
)
from sklearn.utils.class_weight import compute_class_weight

# Set random seeds for reproducibility
np.random.seed(42)

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, LSTM, GRU, Bidirectional, Dropout, BatchNormalization, Input
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    tf.random.set_seed(42)
except ImportError:
    print("Error: TensorFlow is not installed in the current environment.", file=sys.stderr)
    sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(description="Adaptive Deep Learning Pipeline")
    parser.add_argument("--data_path", type=str, default="fault detection.csv",
                        help="Path to the CSV dataset")
    parser.add_argument("--target_col", type=str, default=None,
                        help="Name of the target column (optional, will auto-detect if not provided)")
    parser.add_argument("--datetime_col", type=str, default=None,
                        help="Name of the datetime column (optional, will auto-detect if not provided)")
    parser.add_argument("--sequence_model", type=str, default="LSTM", choices=["LSTM", "GRU", "BiLSTM"],
                        help="Type of sequence model for Time-Series forecasting")
    parser.add_argument("--lookback", type=int, default=24,
                        help="Lookback window size (number of time steps) for Time-Series forecasting")
    parser.add_argument("--epochs", type=int, default=30,
                        help="Number of epochs to train the model")
    parser.add_argument("--batch_size", type=int, default=32,
                        help="Batch size for training")
    parser.add_argument("--output_dir", type=str, default="model_outputs",
                        help="Directory to save trained models and preprocessors")
    return parser.parse_args()


def detect_datetime_column(df):
    """
    Auto-detect if there is a 'Date' or 'Datetime' column in the dataframe.
    Looks for column names containing keywords or checks parseability.
    """
    # Check 1: Check column names for keywords
    datetime_keywords = ['date', 'time', 'timestamp', 'datetime']
    for col in df.columns:
        if any(kw in col.lower() for kw in datetime_keywords):
            # Verify if it can be parsed as datetime
            parsed = pd.to_datetime(df[col], errors='coerce')
            if parsed.notna().sum() / len(df) > 0.5:
                print(f"[Diagnosis] Detected datetime column based on name: '{col}'")
                return col

    # Check 2: Fallback to checking object/string columns for datetime parseability
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                parsed = pd.to_datetime(df[col], errors='coerce')
                if parsed.notna().sum() / len(df) > 0.8:
                    print(f"[Diagnosis] Detected datetime column by parseability (>80% valid): '{col}'")
                    return col
            except Exception:
                pass
    return None


def detect_target_column(df, datetime_col=None):
    """
    Identify target column by checking for common naming patterns.
    Defaults to the last column if no target column is found.
    """
    target_keywords = ['fault_label', 'fault', 'label', 'target', 'class', 'theft', 'y', 'status']
    for col in df.columns:
        if col != datetime_col and col.lower() in target_keywords:
            print(f"[Diagnosis] Auto-detected target column matching keyword: '{col}'")
            return col
    for col in df.columns:
        if col != datetime_col and any(kw in col.lower() for kw in target_keywords):
            print(f"[Diagnosis] Auto-detected target column matching partial keyword: '{col}'")
            return col
    # Fallback to the last column that is not the datetime column
    non_dt_cols = [c for c in df.columns if c != datetime_col]
    fallback_col = non_dt_cols[-1]
    print(f"[Diagnosis] Fallback to last column as target column: '{fallback_col}'")
    return fallback_col


def preprocess_time_series(df, datetime_col, target_col, lookback):
    """
    Robust time-series preprocessing:
    1. Sort chronologically.
    2. Handle duplicate timestamps (aggregate using mean).
    3. Fill missing hourly/daily gaps by resampling/reindexing.
    4. Interpolate missing values.
    5. MinMaxScaler target variable.
    6. Chronological split (80% train, 20% test).
    7. Form sliding lookback windows (univariate).
    """
    print("[Preprocess] Executing Time-Series Pipeline...")
    
    # 1. Parse datetime and sort chronologically
    df[datetime_col] = pd.to_datetime(df[datetime_col])
    df = df.sort_values(by=datetime_col).reset_index(drop=True)
    
    # 2. Handle duplicate timestamps by grouping & averaging numeric columns
    orig_len = len(df)
    agg_dict = {
        col: 'mean' if pd.api.types.is_numeric_dtype(df[col]) else 'first'
        for col in df.columns if col != datetime_col
    }
    df = df.groupby(datetime_col).agg(agg_dict).reset_index()
    if len(df) < orig_len:
        print(f"[Preprocess] Aggregated duplicate timestamps. Size reduced from {orig_len} to {len(df)}")
        
    # 3. Fill missing hourly/daily gaps
    df = df.set_index(datetime_col)
    freq = pd.infer_freq(df.index)
    if freq is None:
        deltas = pd.Series(df.index).diff().dropna()
        if not deltas.empty:
            median_delta = deltas.median()
            # Map standard frequencies
            if pd.Timedelta(hours=0.9) <= median_delta <= pd.Timedelta(hours=1.1):
                freq = 'h'
            elif pd.Timedelta(days=0.9) <= median_delta <= pd.Timedelta(days=1.1):
                freq = 'D'
            else:
                freq = median_delta
        else:
            freq = 'h'
    print(f"[Preprocess] Inferred/calculated resampling frequency: {freq}")
    
    # Reindex index with a complete range
    full_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq=freq)
    df = df.reindex(full_range)
    df.index.name = datetime_col
    df = df.reset_index()
    
    # 4. Interpolate missing values (linear for numeric, ffill/bfill for categoricals)
    for col in df.columns:
        if col != datetime_col:
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].interpolate(method='linear')
            df[col] = df[col].ffill().bfill()
            
    print(f"[Preprocess] Cleaned time-series contains {len(df)} records.")
    
    # 5. Chronological Train-Test Split (80% train, 20% test)
    split_idx = int(len(df) * 0.8)
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]
    
    # 6. Scaling target variable (MinMaxScaler on training target)
    scaler = MinMaxScaler()
    train_target = train_df[[target_col]].values
    scaler.fit(train_target)
    
    train_scaled = scaler.transform(train_df[[target_col]].values).flatten()
    test_scaled = scaler.transform(test_df[[target_col]].values).flatten()
    
    # 7. Form sliding window inputs X: (samples, lookback, 1), y: (samples,)
    def create_univariate_windows(data, window_size):
        X_list, y_list = [], []
        for i in range(len(data) - window_size):
            X_list.append(data[i:(i + window_size)])
            y_list.append(data[i + window_size])
        return np.array(X_list)[..., np.newaxis], np.array(y_list)
        
    if len(train_scaled) <= lookback:
        raise ValueError(f"Training data length ({len(train_scaled)}) is smaller than lookback ({lookback}).")
        
    X_train, y_train = create_univariate_windows(train_scaled, lookback)
    X_test, y_test = create_univariate_windows(test_scaled, lookback)
    
    return X_train, y_train, X_test, y_test, scaler, test_scaled


def preprocess_tabular(df, target_col):
    """
    Robust Tabular classification/regression preprocessing:
    1. Identify continuous vs categorical features.
    2. Impute missing values (median for numeric, mode for categorical).
    3. One-hot encode categorical features.
    4. Scale numeric features (StandardScaler).
    5. Encode target variable (LabelEncoder if classification).
    6. Address class imbalance via class weights (if classification).
    7. Perform random stratified or standard split.
    """
    print("[Preprocess] Executing Tabular Pipeline...")
    
    # Separate features and target
    X = df.drop(columns=[target_col])
    y = df[target_col]
    
    # Detect target task type (Classification vs Regression)
    unique_vals = y.dropna().unique()
    num_classes = len(unique_vals)
    is_classification = False
    
    if y.dtype in ['object', 'bool', 'category'] or (np.issubdtype(y.dtype, np.integer) and num_classes <= 20):
        is_classification = True
        print(f"[Diagnosis] Target '{target_col}' detected as CLASSIFICATION with {num_classes} classes.")
    else:
        print(f"[Diagnosis] Target '{target_col}' detected as REGRESSION.")
        
    # Split features into numeric and categorical lists
    num_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = X.select_dtypes(exclude=[np.number]).columns.tolist()
    
    # Remove unique identifiers or useless columns (e.g. ID, Record_ID)
    useless_id_keywords = ['id', 'record_id', 'index']
    for col in list(num_cols):
        if any(kw == col.lower() or col.lower().endswith(f"_{kw}") for kw in useless_id_keywords):
            # Only drop if it has high cardinality (close to 100% unique values)
            if X[col].nunique() / len(X) > 0.95:
                print(f"[Preprocess] Excluding high-cardinality ID column from features: '{col}'")
                num_cols.remove(col)
                X = X.drop(columns=[col])
                
    for col in list(cat_cols):
        if any(kw == col.lower() or col.lower().endswith(f"_{kw}") for kw in useless_id_keywords):
            if X[col].nunique() / len(X) > 0.95:
                print(f"[Preprocess] Excluding high-cardinality ID column from features: '{col}'")
                cat_cols.remove(col)
                X = X.drop(columns=[col])

    # 1. Random train-test split
    # For classification, use stratified split to preserve class distribution
    stratify_y = y if is_classification else None
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=stratify_y
    )
    
    # 2. Impute and process numeric features
    num_imputer = None
    scaler = None
    if num_cols:
        num_imputer = SimpleImputer(strategy='median')
        scaler = StandardScaler()
        
        # Fit on training and transform both
        train_num_imp = num_imputer.fit_transform(X_train[num_cols])
        test_num_imp = num_imputer.transform(X_test[num_cols])
        
        X_train_num_scaled = scaler.fit_transform(train_num_imp)
        X_test_num_scaled = scaler.transform(test_num_imp)
    else:
        X_train_num_scaled = np.empty((len(X_train), 0))
        X_test_num_scaled = np.empty((len(X_test), 0))
        
    # 3. Impute and process categorical features
    cat_imputer = None
    encoder = None
    if cat_cols:
        cat_imputer = SimpleImputer(strategy='most_frequent')
        encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
        
        train_cat_imp = cat_imputer.fit_transform(X_train[cat_cols])
        test_cat_imp = cat_imputer.transform(X_test[cat_cols])
        
        X_train_cat_encoded = encoder.fit_transform(train_cat_imp)
        X_test_cat_encoded = encoder.transform(test_cat_imp)
    else:
        X_train_cat_encoded = np.empty((len(X_train), 0))
        X_test_cat_encoded = np.empty((len(X_test), 0))
        
    # Combine processed arrays
    X_train_processed = np.hstack([X_train_num_scaled, X_train_cat_encoded])
    X_test_processed = np.hstack([X_test_num_scaled, X_test_cat_encoded])
    
    # 4. Target variable encoding
    label_encoder = None
    class_weight_dict = None
    
    if is_classification:
        label_encoder = LabelEncoder()
        y_train_encoded = label_encoder.fit_transform(y_train)
        y_test_encoded = label_encoder.transform(y_test)
        
        # 5. Handle class imbalance using class weights
        class_labels = np.unique(y_train_encoded)
        weights = compute_class_weight('balanced', classes=class_labels, y=y_train_encoded)
        class_weight_dict = {int(k): float(v) for k, v in zip(class_labels, weights)}
        print(f"[Preprocess] Computed Class Weights: {class_weight_dict}")
    else:
        # Regression targets
        y_train_encoded = y_train.values.astype(np.float32)
        y_test_encoded = y_test.values.astype(np.float32)
        
    preprocessors = {
        'num_cols': num_cols,
        'cat_cols': cat_cols,
        'num_imputer': num_imputer,
        'scaler': scaler,
        'cat_imputer': cat_imputer,
        'encoder': encoder,
        'label_encoder': label_encoder
    }
    
    return (X_train_processed, y_train_encoded, X_test_processed, y_test_encoded,
            is_classification, num_classes if is_classification else 1, class_weight_dict, preprocessors)


def build_time_series_model(lookback, sequence_model):
    """
    Build sequence-based model (LSTM, GRU, or Bidirectional LSTM)
    """
    print(f"[Model] Designing sequence model: {sequence_model} (Lookback: {lookback})")
    model = Sequential([
        Input(shape=(lookback, 1))
    ])
    
    if sequence_model == 'LSTM':
        model.add(LSTM(64, return_sequences=False))
    elif sequence_model == 'GRU':
        model.add(GRU(64, return_sequences=False))
    elif sequence_model == 'BiLSTM':
        model.add(Bidirectional(LSTM(64, return_sequences=False)))
    else:
        model.add(LSTM(64, return_sequences=False))
        
    model.add(Dropout(0.2))
    model.add(Dense(32, activation='relu'))
    model.add(Dropout(0.1))
    model.add(Dense(1, activation='linear'))
    
    return model


def build_tabular_model(input_dim, is_classification, num_classes):
    """
    Build Deep Multi-Layer Perceptron (MLP) with Dense, Batch Normalization, and Dropout
    """
    print(f"[Model] Designing Deep MLP model (Input Dimensions: {input_dim})")
    model = Sequential([
        Input(shape=(input_dim,)),
        Dense(128, activation='relu'),
        BatchNormalization(),
        Dropout(0.3),
        Dense(64, activation='relu'),
        BatchNormalization(),
        Dropout(0.2),
        Dense(32, activation='relu'),
        BatchNormalization()
    ])
    
    if is_classification:
        if num_classes == 2:
            model.add(Dense(1, activation='sigmoid'))
        else:
            model.add(Dense(num_classes, activation='softmax'))
    else:
        model.add(Dense(1, activation='linear'))
        
    return model


def main():
    args = parse_args()
    
    # 0. Load Dataset
    print(f"\n=== Step 1: Loading Dataset '{args.data_path}' ===")
    if not os.path.exists(args.data_path):
        print(f"Error: File '{args.data_path}' does not exist.", file=sys.stderr)
        sys.exit(1)
        
    df = pd.read_csv(args.data_path)
    print(f"Dataset Loaded. Shape: {df.shape}")
    
    # 1. Diagnosis and Preprocessing
    datetime_col = args.datetime_col if args.datetime_col else detect_datetime_column(df)
    is_time_series = datetime_col is not None
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    if is_time_series:
        print("[Diagnosis] Pipeline selected: TIME-SERIES FORECASTING")
        target_col = args.target_col if args.target_col else detect_target_column(df, datetime_col)
        
        # Preprocess
        X_train, y_train, X_test, y_test, scaler, test_scaled = preprocess_time_series(
            df, datetime_col, target_col, args.lookback
        )
        
        # Save preprocessor
        preprocessor_dict = {
            'scaler': scaler,
            'lookback': args.lookback,
            'target_col': target_col,
            'datetime_col': datetime_col
        }
        with open(os.path.join(args.output_dir, 'preprocessors.pkl'), 'wb') as f:
            pickle.dump(preprocessor_dict, f)
            
        is_classification = False
        num_classes = 1
        class_weight_dict = None
        
    else:
        print("[Diagnosis] Pipeline selected: TABULAR CLASSIFICATION/REGRESSION")
        target_col = args.target_col if args.target_col else detect_target_column(df)
        
        # Preprocess
        (X_train, y_train, X_test, y_test,
         is_classification, num_classes, class_weight_dict, preprocessors) = preprocess_tabular(df, target_col)
         
        # Save preprocessor
        with open(os.path.join(args.output_dir, 'preprocessors.pkl'), 'wb') as f:
            pickle.dump(preprocessors, f)

    # 2. Adaptive Model Design
    print("\n=== Step 2: Designing Adaptive Model ===")
    if is_time_series:
        model = build_time_series_model(args.lookback, args.sequence_model)
        loss_fn = 'mse'
        model_metrics = ['mae']
    else:
        model = build_tabular_model(X_train.shape[1], is_classification, num_classes)
        if is_classification:
            if num_classes == 2:
                loss_fn = 'binary_crossentropy'
            else:
                loss_fn = 'sparse_categorical_crossentropy'
            model_metrics = ['accuracy']
        else:
            loss_fn = 'mse'
            model_metrics = ['mae']
            
    # Compile Model
    model.compile(optimizer='adam', loss=loss_fn, metrics=model_metrics)
    model.summary()

    # 3. Training & Regularization
    print("\n=== Step 3: Training Model ===")
    
    # Configure callbacks
    monitor_metric = 'val_accuracy' if is_classification else 'val_loss'
    mode_metric = 'max' if is_classification else 'min'
    
    early_stopping = EarlyStopping(
        monitor=monitor_metric,
        patience=10,
        restore_best_weights=True,
        mode=mode_metric,
        verbose=1
    )
    
    lr_scheduler = ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=5,
        min_lr=1e-6,
        verbose=1
    )
    
    callbacks = [early_stopping, lr_scheduler]
    
    # Train
    history = model.fit(
        X_train, y_train,
        validation_split=0.15,
        epochs=args.epochs,
        batch_size=args.batch_size,
        class_weight=class_weight_dict,
        callbacks=callbacks,
        verbose=1
    )

    # 4. Model Performance & Metrics
    print("\n=== Step 4: Model Evaluation ===")
    
    # Plot training logs
    plt.figure(figsize=(10, 4))
    plt.subplot(1, 2, 1)
    plt.plot(history.history['loss'], label='Train Loss')
    plt.plot(history.history['val_loss'], label='Val Loss')
    plt.title('Loss History')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    
    if is_classification:
        plt.subplot(1, 2, 2)
        plt.plot(history.history['accuracy'], label='Train Acc')
        plt.plot(history.history['val_accuracy'], label='Val Acc')
        plt.title('Accuracy History')
        plt.xlabel('Epoch')
        plt.ylabel('Accuracy')
        plt.legend()
    else:
        plt.subplot(1, 2, 2)
        plt.plot(history.history['mae'], label='Train MAE')
        plt.plot(history.history['val_mae'], label='Val MAE')
        plt.title('MAE History')
        plt.xlabel('Epoch')
        plt.ylabel('MAE')
        plt.legend()
        
    plt.tight_layout()
    plt.savefig(os.path.join(args.output_dir, 'training_curves.png'))
    plt.close()
    
    # Generate predictions
    y_pred_raw = model.predict(X_test)
    
    metrics_report = {}
    
    if is_classification:
        if num_classes == 2:
            y_pred = (y_pred_raw > 0.5).astype(int).flatten()
        else:
            y_pred = np.argmax(y_pred_raw, axis=1)
            
        # Metrics
        avg_type = 'binary' if num_classes == 2 else 'weighted'
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, average=avg_type, zero_division=0)
        rec = recall_score(y_test, y_pred, average=avg_type, zero_division=0)
        f1 = f1_score(y_test, y_pred, average=avg_type, zero_division=0)
        
        print(f"Classification Accuracy:  {acc:.4f}")
        print(f"Precision ({avg_type}):      {prec:.4f}")
        print(f"Recall ({avg_type}):         {rec:.4f}")
        print(f"F1-Score ({avg_type}):       {f1:.4f}")
        
        metrics_report = {
            'Accuracy': float(acc),
            'Precision': float(prec),
            'Recall': float(rec),
            'F1-Score': float(f1)
        }
        
        # Plot Confusion Matrix
        cm = confusion_matrix(y_test, y_pred)
        plt.figure(figsize=(8, 6))
        
        label_encoder = preprocessors['label_encoder']
        class_names = [str(c) for c in label_encoder.classes_]
        
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                    xticklabels=class_names, yticklabels=class_names)
        plt.title('Confusion Matrix')
        plt.ylabel('Actual Label')
        plt.xlabel('Predicted Label')
        plt.tight_layout()
        plt.savefig(os.path.join(args.output_dir, 'confusion_matrix.png'))
        plt.close()
        print(f"[Metrics] Saved confusion matrix plot to '{args.output_dir}/confusion_matrix.png'")
        
    else:
        # Regression or Forecasting
        if is_time_series:
            # Scale target variables back to original values
            y_test_orig = scaler.inverse_transform(y_test.reshape(-1, 1)).flatten()
            y_pred_orig = scaler.inverse_transform(y_pred_raw.reshape(-1, 1)).flatten()
        else:
            # Tabular Regression
            y_test_orig = y_test
            y_pred_orig = y_pred_raw.flatten()
            
        rmse = np.sqrt(mean_squared_error(y_test_orig, y_pred_orig))
        mae = mean_absolute_error(y_test_orig, y_pred_orig)
        r2 = r2_score(y_test_orig, y_pred_orig)
        
        # Calculate MAPE handling division by zero
        mape = np.mean(np.abs((y_test_orig - y_pred_orig) / np.clip(np.abs(y_test_orig), 1e-8, None))) * 100
        accuracy = max(0.0, 100.0 - mape)
        
        print(f"Root Mean Squared Error (RMSE): {rmse:.4f}")
        print(f"Mean Absolute Error (MAE):       {mae:.4f}")
        print(f"R2 Coefficient of Determination: {r2:.4f}")
        print(f"Mean Absolute Percentage Error:  {mape:.4f}%")
        print(f"Accuracy (100 - MAPE):           {accuracy:.2f}%")
        
        metrics_report = {
            'RMSE': float(rmse),
            'MAE': float(mae),
            'R2': float(r2),
            'MAPE': float(mape),
            'Accuracy': float(accuracy)
        }
        
        # Plot predictions vs actuals
        plt.figure(figsize=(10, 5))
        plt.plot(y_test_orig[:150], label='Actual', alpha=0.8)
        plt.plot(y_pred_orig[:150], label='Predicted', alpha=0.8, linestyle='--')
        plt.title('Actual vs Predicted Values (First 150 points)')
        plt.ylabel('Target Value')
        plt.xlabel('Sample Index')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(args.output_dir, 'predictions_vs_actuals.png'))
        plt.close()
        print(f"[Metrics] Saved predictions plot to '{args.output_dir}/predictions_vs_actuals.png'")

    # Save metrics report JSON
    with open(os.path.join(args.output_dir, 'metrics.json'), 'w') as f:
        json.dump(metrics_report, f, indent=4)

    # 5. Future Forecasts / Predictions
    print("\n=== Step 5: Generating Future Forecasts / Predictions ===")
    if is_time_series:
        # Time-Series: Recursive forecasting for 168 hours (next week)
        print("[Forecast] Simulating recursive forecasting for next 168 hours...")
        last_window = test_scaled[-args.lookback:]
        current_window = last_window.copy()
        recursive_preds = []
        
        for i in range(168):
            # Shape expected by model: (1, lookback, 1)
            pred = model.predict(current_window.reshape(1, args.lookback, 1), verbose=0)
            pred_val = pred[0, 0]
            recursive_preds.append(pred_val)
            # Roll window
            current_window = np.append(current_window[1:], pred_val)
            
        # Inverse transform forecasts to original scale
        recursive_preds_orig = scaler.inverse_transform(np.array(recursive_preds).reshape(-1, 1)).flatten()
        
        # Plot and save recursive predictions
        plt.figure(figsize=(12, 5))
        plt.plot(range(1, 169), recursive_preds_orig, marker='o', markersize=3, color='orange', label='Forecasted Target')
        plt.title('Recursive Forecasting (Next 168 Time-Steps)')
        plt.ylabel('Forecasted Target')
        plt.xlabel('Future Time Step')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(args.output_dir, 'future_forecast_168h.png'))
        plt.close()
        print(f"[Forecast] Saved 168-step forecast plot to '{args.output_dir}/future_forecast_168h.png'")
        print(f"[Forecast] Sample forecasts (first 10 steps): {recursive_preds_orig[:10].tolist()}")
        
    else:
        # Tabular: Show predictions on first 10 unseen test samples
        print("[Forecast] Simulating prediction on test samples...")
        if is_classification:
            label_encoder = preprocessors['label_encoder']
            # Decode test set targets and predictions
            y_test_decoded = label_encoder.inverse_transform(y_test)
            y_pred_decoded = label_encoder.inverse_transform(y_pred)
            
            print("\nSample Predictions (First 10 Test Records):")
            print(f"{'Index':<8} | {'Actual Class':<20} | {'Predicted Class':<20} | {'Match':<6}")
            print("-" * 62)
            for i in range(min(10, len(y_test))):
                match = "YES" if y_test_decoded[i] == y_pred_decoded[i] else "NO"
                print(f"{i:<8} | {str(y_test_decoded[i]):<20} | {str(y_pred_decoded[i]):<20} | {match:<6}")
        else:
            print("\nSample Predictions (First 10 Test Records):")
            print(f"{'Index':<8} | {'Actual Value':<15} | {'Predicted Value':<15} | {'Error':<12}")
            print("-" * 56)
            for i in range(min(10, len(y_test_orig))):
                error = y_pred_orig[i] - y_test_orig[i]
                print(f"{i:<8} | {y_test_orig[i]:<15.4f} | {y_pred_orig[i]:<15.4f} | {error:<12.4f}")

    # 6. Saving Artifacts
    print("\n=== Step 6: Exporting Saved Artifacts ===")
    model_save_path = os.path.join(args.output_dir, "model.keras")
    model.save(model_save_path)
    print(f"[Export] Saved trained model to '{model_save_path}'")
    print(f"[Export] Preprocessors saved to '{os.path.join(args.output_dir, 'preprocessors.pkl')}'")
    print(f"[Export] Metrics JSON saved to '{os.path.join(args.output_dir, 'metrics.json')}'")
    print("\nDeep Learning Pipeline Completed Successfully!")


if __name__ == "__main__":
    main()
