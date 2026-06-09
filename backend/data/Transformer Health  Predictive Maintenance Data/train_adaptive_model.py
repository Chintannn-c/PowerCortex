#!/usr/bin/env python
"""
Adaptive Deep Learning Pipeline for Tabular and Time-Series Datasets
Author: Antigravity AI Coding Assistant
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
from sklearn.preprocessing import StandardScaler, MinMaxScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support, 
    confusion_matrix, mean_squared_error, 
    mean_absolute_error, r2_score
)
from sklearn.utils.class_weight import compute_class_weight

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM, GRU, Bidirectional, Dropout, BatchNormalization, Input
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

# Suppress TensorFlow logging warnings for cleaner output
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

def parse_args():
    parser = argparse.ArgumentParser(description="Auto-Adaptive Keras Deep Learning Pipeline")
    parser.add_argument("--data", type=str, default="predictive_maintenance.csv", help="Path to the CSV dataset")
    parser.add_argument("--target", type=str, default=None, help="Name of the target column (overrides auto-detection)")
    parser.add_argument("--lookback", type=int, default=24, help="Sliding lookback window for time-series forecasting (steps)")
    parser.add_argument("--model_type", type=str, choices=["lstm", "gru", "bilstm"], default="bilstm", 
                        help="Sequence model type for time-series forecasting")
    parser.add_argument("--epochs", type=int, default=50, help="Maximum training epochs")
    parser.add_argument("--batch_size", type=int, default=64, help="Training batch size")
    parser.add_argument("--output_dir", type=str, default="artifacts_output", help="Directory to save output artifacts")
    parser.add_argument("--test_timeseries", action="store_true", help="Generate synthetic time-series data to test the sequence pipeline")
    parser.add_argument("--class_weight_style", type=str, choices=["none", "balanced", "sqrt"], default="sqrt",
                        help="Weight scaling strategy for class imbalances in classification tasks")
    return parser.parse_args()

def generate_synthetic_timeseries():
    """Generates synthetic hourly time-series data for testing the forecasting pipeline."""
    print("\n--- Generating Synthetic Time-Series Data for Testing ---")
    np.random.seed(42)
    date_range = pd.date_range(start="2026-01-01", periods=1000, freq="h")
    
    # Generate a time series with trend, seasonality, and noise
    time = np.arange(len(date_range))
    trend = 0.05 * time
    seasonal = 15 * np.sin(2 * np.pi * time / 24)
    noise = np.random.normal(0, 3, size=len(date_range))
    temperature = 20 + trend + seasonal + noise
    
    df = pd.DataFrame({
        "Timestamp": date_range,
        "Temperature_C": temperature,
        "Humidity_pct": 50 + 10 * np.cos(2 * np.pi * time / 24) + np.random.normal(0, 2, size=len(date_range))
    })
    
    # Introduce some random NaNs to test interpolation
    nan_mask = np.random.rand(len(df)) < 0.02
    df.loc[nan_mask, "Temperature_C"] = np.nan
    
    test_csv = "synthetic_timeseries.csv"
    df.to_csv(test_csv, index=False)
    print(f"Saved synthetic time-series to '{test_csv}'")
    return test_csv

def detect_datetime_column(df):
    """
    Scans column names and types to auto-detect a Date or Datetime column.
    Returns the column name if detected, else None.
    """
    datetime_keywords = ["date", "time", "timestamp", "datetime", "epoch"]
    
    # 1. Check if any column is already parsed as datetime type
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            print(f"[Auto-Detection] Found datetime column by dtype: '{col}'")
            return col
            
    # 2. Check column names for keywords and test parsability
    for col in df.columns:
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in datetime_keywords):
            # Test if it can be parsed as a datetime
            try:
                # Convert a sample first to check if valid datetime format
                sample_non_null = df[col].dropna().head(100)
                if len(sample_non_null) > 0:
                    pd.to_datetime(sample_non_null, errors="raise")
                    print(f"[Auto-Detection] Found datetime column by name and parsability: '{col}'")
                    return col
            except Exception:
                continue
                
    return None

def detect_target_column(df, datetime_col=None):
    """
    Heuristically identifies the target column in the dataset.
    """
    target_keywords = ["target", "label", "class", "failure", "fault", "theft", "diagnose", "output"]
    cols = [col for col in df.columns if col != datetime_col]
    
    # 1. Search for keywords as substrings
    for col in cols:
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in target_keywords):
            print(f"[Auto-Detection] Identified target column by keyword: '{col}'")
            return col
            
    # 2. Search for exact match 'y'
    for col in cols:
        if col.lower() == "y":
            print(f"[Auto-Detection] Identified target column: 'y'")
            return col
            
    # Fallback to the last column
    fallback = cols[-1]
    print(f"[Auto-Detection] Target keyword not found. Defaulting to the last column: '{fallback}'")
    return fallback

def preprocess_timeseries(df, datetime_col, target_col):
    """
    Preprocesses time-series data: sorts chronologically, aggregates duplicates,
    fills missing temporal gaps, interpolates NaNs, and scales features.
    """
    print("\n--- Preprocessing Time-Series Data ---")
    
    # Convert datetime column to pandas DatetimeIndex
    df[datetime_col] = pd.to_datetime(df[datetime_col])
    df = df.sort_values(by=datetime_col)
    
    # Handle duplicates by taking the mean of numeric columns and first of categorical
    if df[datetime_col].duplicated().any():
        print("[Preprocessing] Duplicate timestamps detected. Aggregating by mean...")
        # Separate numeric and non-numeric columns
        num_cols = df.select_dtypes(include=[np.number]).columns
        cat_cols = df.select_dtypes(exclude=[np.number]).columns
        
        df_num = df.groupby(datetime_col)[num_cols].mean()
        if len(cat_cols) > 1: # at least one categorical column other than datetime_col
            df_cat = df.groupby(datetime_col)[cat_cols].first()
            df = pd.concat([df_num, df_cat], axis=1).reset_index()
        else:
            df = df_num.reset_index()
            
    # Set datetime column as index
    df = df.set_index(datetime_col)
    
    # Fill missing temporal gaps
    # Infer frequency (e.g. 'h' for hourly, 'd' for daily)
    inferred_freq = pd.infer_freq(df.index)
    if inferred_freq is None:
        # Fallback heuristic: calculate median time delta between steps
        deltas = pd.Series(df.index).diff().dropna()
        if len(deltas) > 0:
            median_delta = deltas.median()
            print(f"[Preprocessing] Median time delta between steps: {median_delta}")
            # Map common deltas to pandas frequency strings
            if median_delta <= pd.Timedelta(minutes=5):
                inferred_freq = "5min"
            elif median_delta <= pd.Timedelta(minutes=15):
                inferred_freq = "15min"
            elif median_delta <= pd.Timedelta(hours=1):
                inferred_freq = "h"
            elif median_delta <= pd.Timedelta(days=1):
                inferred_freq = "D"
            else:
                inferred_freq = "D"
        else:
            inferred_freq = "h"
            
    print(f"[Preprocessing] Resampling data to inferred frequency: '{inferred_freq}'")
    df = df.resample(inferred_freq).mean()
    
    # Interpolate missing values
    missing_count = df[target_col].isna().sum()
    if missing_count > 0:
        print(f"[Preprocessing] Found {missing_count} missing values in target. Interpolating linearly...")
        df = df.interpolate(method="linear").bfill().ffill()
        
    return df

def engineer_features(df):
    """
    Applies domain-specific feature engineering if columns match AI4I Predictive Maintenance.
    """
    df = df.copy()
    
    # Check for temperature, speed, torque, tool wear columns
    air_temp_col = [c for c in df.columns if "air temperature" in c.lower()]
    proc_temp_col = [c for c in df.columns if "process temperature" in c.lower()]
    rot_speed_col = [c for c in df.columns if "rotational speed" in c.lower()]
    torque_col = [c for c in df.columns if "torque" in c.lower()]
    tool_wear_col = [c for c in df.columns if "tool wear" in c.lower()]
    
    if air_temp_col and proc_temp_col:
        df["Temp_Diff"] = df[proc_temp_col[0]] - df[air_temp_col[0]]
        print("[Feature Engineering] Created 'Temp_Diff' (Process Temp - Air Temp)")
        
    if rot_speed_col and torque_col:
        df["Power_W"] = df[rot_speed_col[0]] * df[torque_col[0]]
        print("[Feature Engineering] Created 'Power_W' (Rotational Speed * Torque)")
        
    if tool_wear_col and torque_col:
        df["ToolWear_Torque"] = df[tool_wear_col[0]] * df[torque_col[0]]
        print("[Feature Engineering] Created 'ToolWear_Torque' (Tool Wear * Torque)")
        
    return df

def preprocess_tabular(df, target_col):
    """
    Preprocesses tabular data: removes high-cardinality ID columns,
    imputes missing values, encodes categoricals, scales numerical features,
    and returns processed datasets.
    """
    print("\n--- Preprocessing Tabular Data ---")
    
    # Apply domain-specific feature engineering
    df = engineer_features(df)
    
    X = df.drop(columns=[target_col])
    y = df[target_col]
    
    # 1. Identify and drop high-cardinality ID-like columns
    id_keywords = ["id", "name", "serial", "udi", "index", "code"]
    cols_to_drop = []
    for col in X.columns:
        col_lower = col.lower()
        unique_pct = X[col].nunique() / len(df)
        is_id_name = any(keyword in col_lower for keyword in id_keywords)
        # Drop if explicitly matching ID name keywords and has high unique count, or if almost completely unique
        if (is_id_name and unique_pct > 0.05) or unique_pct > 0.95:
            cols_to_drop.append(col)
            
    if cols_to_drop:
        print(f"[Preprocessing] Dropping identifier/high-cardinality columns: {cols_to_drop}")
        X = X.drop(columns=cols_to_drop)
        
    # 2. Categorize remaining features
    num_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = X.select_dtypes(exclude=[np.number]).columns.tolist()
    
    print(f"[Preprocessing] Numeric features ({len(num_cols)}): {num_cols}")
    print(f"[Preprocessing] Categorical features ({len(cat_cols)}): {cat_cols}")
    
    # 3. Imputation
    preprocessors = {}
    
    if len(num_cols) > 0:
        num_imputer = SimpleImputer(strategy="median")
        X[num_cols] = num_imputer.fit_transform(X[num_cols])
        preprocessors['num_imputer'] = num_imputer
        
    if len(cat_cols) > 0:
        cat_imputer = SimpleImputer(strategy="most_frequent")
        X[cat_cols] = cat_imputer.fit_transform(X[cat_cols])
        preprocessors['cat_imputer'] = cat_imputer
        
    # 4. Encoding categorical variables
    encoded_cat_dfs = []
    if len(cat_cols) > 0:
        encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        encoded_cats = encoder.fit_transform(X[cat_cols])
        cat_feature_names = encoder.get_feature_names_out(cat_cols)
        encoded_cat_df = pd.DataFrame(encoded_cats, columns=cat_feature_names, index=X.index)
        encoded_cat_dfs.append(encoded_cat_df)
        X = X.drop(columns=cat_cols)
        preprocessors['encoder'] = encoder
        
    # 5. Scaling numeric features
    if len(num_cols) > 0:
        scaler = StandardScaler()
        scaled_nums = scaler.fit_transform(X[num_cols])
        X[num_cols] = scaled_nums
        preprocessors['scaler'] = scaler
        
    # Recombine features
    if encoded_cat_dfs:
        X = pd.concat([X] + encoded_cat_dfs, axis=1)
        
    # 6. Encode Target if categorical classification
    y_encoded = y.copy()
    target_classes = None
    task_type = None
    
    # Determine task type
    unique_vals = y.nunique()
    is_numeric_target = pd.api.types.is_numeric_dtype(y)
    
    if is_numeric_target and unique_vals > 15:
        task_type = "regression"
        print(f"[Auto-Detection] Task type: Regression (Target is numeric with {unique_vals} unique values)")
    elif unique_vals == 2:
        task_type = "binary_classification"
        target_classes = np.sort(y.unique())
        # Encode target to binary (0 and 1)
        y_encoded = pd.Series(np.where(y == target_classes[1], 1, 0), index=y.index)
        print(f"[Auto-Detection] Task type: Binary Classification (Target values: {target_classes} mapped to [0, 1])")
    else:
        task_type = "multiclass_classification"
        target_classes = np.sort(y.unique()).tolist()
        print(f"[Auto-Detection] Task type: Multi-Class Classification ({unique_vals} classes: {target_classes})")
        # One-hot encode the target column
        target_encoder = OneHotEncoder(sparse_output=False)
        y_encoded = target_encoder.fit_transform(y.values.reshape(-1, 1))
        preprocessors['target_encoder'] = target_encoder
        
    preprocessors['feature_cols'] = X.columns.tolist()
    preprocessors['target_classes'] = target_classes
    preprocessors['task_type'] = task_type
    
    return X, y_encoded, preprocessors

def build_mlp_model(input_dim, task_type, num_classes=1):
    """
    Builds a Deep Multi-Layer Perceptron (MLP) for Tabular data.
    """
    model = Sequential()
    model.add(Input(shape=(input_dim,)))
    
    # Layer 1
    model.add(Dense(256, activation="relu"))
    model.add(BatchNormalization())
    model.add(Dropout(0.3))
    
    # Layer 2
    model.add(Dense(128, activation="relu"))
    model.add(BatchNormalization())
    model.add(Dropout(0.3))
    
    # Layer 3
    model.add(Dense(64, activation="relu"))
    model.add(BatchNormalization())
    model.add(Dropout(0.2))
    
    # Output Layer
    if task_type == "regression":
        model.add(Dense(1, activation="linear"))
        loss = "mse"
        metrics = ["mae"]
    elif task_type == "binary_classification":
        model.add(Dense(1, activation="sigmoid"))
        loss = "binary_crossentropy"
        metrics = ["accuracy"]
    else: # multiclass
        model.add(Dense(num_classes, activation="softmax"))
        loss = "categorical_crossentropy"
        metrics = ["accuracy"]
        
    model.compile(optimizer="adam", loss=loss, metrics=metrics)
    return model

def build_sequence_model(lookback, model_type="bilstm"):
    """
    Builds an LSTM, GRU, or Bidirectional LSTM sequence model for Time-Series forecasting.
    """
    model = Sequential()
    model.add(Input(shape=(lookback, 1)))
    
    if model_type == "lstm":
        model.add(LSTM(64, return_sequences=True))
        model.add(Dropout(0.2))
        model.add(LSTM(32))
    elif model_type == "gru":
        model.add(GRU(64, return_sequences=True))
        model.add(Dropout(0.2))
        model.add(GRU(32))
    else: # bilstm
        model.add(Bidirectional(LSTM(64, return_sequences=True)))
        model.add(Dropout(0.2))
        model.add(LSTM(32))
        
    model.add(Dropout(0.2))
    model.add(Dense(1, activation="linear"))
    
    model.compile(optimizer="adam", loss="mse", metrics=["mae"])
    return model

def train_model(model, X_train, y_train, X_val, y_val, task_type, epochs, batch_size, class_weight_style="sqrt"):
    """
    Trains the model with Early Stopping and learning rate reduction on plateau.
    """
    print("\n--- Training Deep Learning Model ---")
    
    # Setup callbacks
    early_stop_monitor = "val_loss"
    early_stop = EarlyStopping(
        monitor=early_stop_monitor, 
        patience=15, 
        restore_best_weights=True,
        verbose=1
    )
    
    lr_scheduler = ReduceLROnPlateau(
        monitor="val_loss", 
        factor=0.5, 
        patience=5, 
        min_lr=1e-6,
        verbose=1
    )
    
    # Compute class weights for imbalanced tabular classification tasks
    class_weights = None
    if task_type in ["binary_classification", "multiclass_classification"] and class_weight_style != "none":
        try:
            # Reconstruct class labels for calculation
            if task_type == "binary_classification":
                y_labels = y_train.values if isinstance(y_train, pd.Series) else y_train
            else: # multiclass
                y_labels = np.argmax(y_train, axis=1)
                
            unique_classes = np.unique(y_labels)
            
            if class_weight_style == "balanced":
                weights = compute_class_weight(
                    class_weight="balanced", 
                    classes=unique_classes, 
                    y=y_labels
                )
                class_weights = dict(zip(unique_classes, weights))
            elif class_weight_style == "sqrt":
                # Sqrt inverse class weights: weight_c = (total / count_c) ** 0.5
                counts = np.bincount(y_labels)
                total = len(y_labels)
                raw_weights = (total / counts) ** 0.5
                # Normalize so that the minimum weight is 1.0 (for majority class)
                normalized_weights = raw_weights / np.min(raw_weights)
                class_weights = {c: normalized_weights[c] for c in unique_classes}
                
            print(f"[Training] Imputed Class Weights ({class_weight_style}): {class_weights}")
        except Exception as e:
            print(f"[Training] Could not compute class weights: {e}. Training without weights.")
            
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        class_weight=class_weights,
        callbacks=[early_stop, lr_scheduler],
        verbose=1
    )
    return history

def evaluate_tabular(model, X_test, y_test, preprocessors, output_dir):
    """
    Evaluates a tabular classification/regression model and prints key metrics.
    """
    print("\n--- Evaluating Tabular Model Performance ---")
    task_type = preprocessors['task_type']
    target_classes = preprocessors['target_classes']
    
    predictions = model.predict(X_test)
    metrics = {}
    
    if task_type == "regression":
        # Regression Metrics
        mse = mean_squared_error(y_test, predictions)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test, predictions)
        r2 = r2_score(y_test, predictions)
        
        # Calculate MAPE (handling zeros gracefully)
        y_test_arr = np.array(y_test)
        non_zero_mask = y_test_arr != 0
        if np.sum(non_zero_mask) > 0:
            mape = np.mean(np.abs((y_test_arr[non_zero_mask] - predictions.flatten()[non_zero_mask]) / y_test_arr[non_zero_mask])) * 100
        else:
            mape = 0.0
            
        accuracy = 100.0 - mape
        
        print(f"Regression Results:")
        print(f"  RMSE: {rmse:.4f}")
        print(f"  MAE:  {mae:.4f}")
        print(f"  R2:   {r2:.4f}")
        print(f"  MAPE: {mape:.2f}% (Accuracy Estimate = {accuracy:.2f}%)")
        
        metrics = {"rmse": float(rmse), "mae": float(mae), "r2": float(r2), "mape": float(mape), "accuracy_est": float(accuracy)}
        
    else:
        # Classification Metrics
        if task_type == "binary_classification":
            pred_classes = (predictions > 0.5).astype(int).flatten()
            y_test_labels = y_test.values if isinstance(y_test, pd.Series) else y_test
        else: # multiclass
            pred_classes = np.argmax(predictions, axis=1)
            y_test_labels = np.argmax(y_test, axis=1)
            
        acc = accuracy_score(y_test_labels, pred_classes)
        precision, recall, f1, _ = precision_recall_fscore_support(y_test_labels, pred_classes, average="weighted")
        
        print(f"Classification Results (Weighted):")
        print(f"  Accuracy:  {acc:.4f}")
        print(f"  Precision: {precision:.4f}")
        print(f"  Recall:    {recall:.4f}")
        print(f"  F1-Score:  {f1:.4f}")
        
        metrics = {"accuracy": float(acc), "precision": float(precision), "recall": float(recall), "f1_score": float(f1)}
        
        # Plot Confusion Matrix
        cm = confusion_matrix(y_test_labels, pred_classes)
        plt.figure(figsize=(8, 6))
        
        # Map label names
        labels = [str(c) for c in target_classes] if target_classes is not None else [str(i) for i in range(len(cm))]
        
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=labels, yticklabels=labels)
        plt.title("Confusion Matrix")
        plt.xlabel("Predicted Class")
        plt.ylabel("True Class")
        plt.tight_layout()
        cm_path = os.path.join(output_dir, "confusion_matrix.png")
        plt.savefig(cm_path, dpi=300)
        plt.close()
        print(f"Confusion Matrix saved to '{cm_path}'")
        
        # Print sample predictions
        print("\nUnseen Test Sample Predictions (First 10):")
        for i in range(min(10, len(y_test_labels))):
            true_lbl = target_classes[y_test_labels[i]] if target_classes is not None else y_test_labels[i]
            pred_lbl = target_classes[pred_classes[i]] if target_classes is not None else pred_classes[i]
            prob = predictions[i][0] if task_type == "binary_classification" else np.max(predictions[i])
            print(f"  Sample {i+1}: True = '{true_lbl}', Predicted = '{pred_lbl}' (Confidence: {prob:.4f})")
            
    return metrics

def plot_history(history, output_dir):
    """
    Plots the training loss and accuracy curves and saves the figure.
    """
    plt.figure(figsize=(12, 5))
    
    # Loss plot
    plt.subplot(1, 2, 1)
    plt.plot(history.history['loss'], label='Train Loss')
    if 'val_loss' in history.history:
        plt.plot(history.history['val_loss'], label='Val Loss')
    plt.title('Model Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid(True)
    
    # Metric plot
    plt.subplot(1, 2, 2)
    metric_name = 'accuracy' if 'accuracy' in history.history else 'mae'
    val_metric_name = f'val_{metric_name}'
    
    if metric_name in history.history:
        plt.plot(history.history[metric_name], label=f'Train {metric_name.capitalize()}')
        if val_metric_name in history.history:
            plt.plot(history.history[val_metric_name], label=f'Val {metric_name.capitalize()}')
        plt.title(f'Model {metric_name.capitalize()}')
        plt.xlabel('Epoch')
        plt.ylabel(metric_name.capitalize())
        plt.legend()
        plt.grid(True)
        
    plt.tight_layout()
    history_path = os.path.join(output_dir, "training_history.png")
    plt.savefig(history_path, dpi=300)
    plt.close()
    print(f"Training History plot saved to '{history_path}'")

def run_timeseries_pipeline(df, datetime_col, target_col, args):
    """
    Runs the full time-series forecasting pipeline.
    """
    df_processed = preprocess_timeseries(df, datetime_col, target_col)
    
    # For robust time-series forecasting, we focus on univariate prediction of the target column
    series_data = df_processed[[target_col]].values
    
    # Scale variables using MinMaxScaler
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(series_data)
    
    # Create sliding lookback window datasets
    lookback = args.lookback
    print(f"[Pipeline] Creating sliding sequences with lookback window of {lookback} steps...")
    X, y = [], []
    for i in range(len(scaled_data) - lookback):
        X.append(scaled_data[i:(i + lookback), 0])
        y.append(scaled_data[i + lookback, 0])
    
    X = np.array(X)
    y = np.array(y)
    
    # Reshape input to 3D for sequence models: (samples, time_steps, features=1)
    X = X.reshape((X.shape[0], X.shape[1], 1))
    
    # Chronological Split (80% train, 20% test)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    # Further split training into train and validation (90/10 chronologically)
    val_split_idx = int(len(X_train) * 0.9)
    X_train_final, X_val = X_train[:val_split_idx], X_train[val_split_idx:]
    y_train_final, y_val = y_train[:val_split_idx], y_train[val_split_idx:]
    
    print(f"Data shapes:")
    print(f"  Train: X={X_train_final.shape}, y={y_train_final.shape}")
    print(f"  Val:   X={X_val.shape}, y={y_val.shape}")
    print(f"  Test:  X={X_test.shape}, y={y_test.shape}")
    
    # Build Model
    model = build_sequence_model(lookback, args.model_type)
    model.summary()
    
    # Train Model
    history = train_model(model, X_train_final, y_train_final, X_val, y_val, "regression", args.epochs, args.batch_size)
    plot_history(history, args.output_dir)
    
    # Predict and evaluate on test set
    predictions_scaled = model.predict(X_test)
    predictions = scaler.inverse_transform(predictions_scaled)
    y_test_actual = scaler.inverse_transform(y_test.reshape(-1, 1))
    
    # Calculate Metrics
    mse = mean_squared_error(y_test_actual, predictions)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_test_actual, predictions)
    r2 = r2_score(y_test_actual, predictions)
    
    # Calculate MAPE
    non_zero_mask = y_test_actual != 0
    if np.sum(non_zero_mask) > 0:
        mape = np.mean(np.abs((y_test_actual[non_zero_mask] - predictions[non_zero_mask]) / y_test_actual[non_zero_mask])) * 100
    else:
        mape = 0.0
    accuracy = 100.0 - mape
    
    print(f"\n--- Forecasting Test Performance ---")
    print(f"  RMSE: {rmse:.4f}")
    print(f"  MAE:  {mae:.4f}")
    print(f"  R2:   {r2:.4f}")
    print(f"  MAPE: {mape:.2f}% (Accuracy = {accuracy:.2f}%)")
    
    # 5. FUTURE FORECASTS: Recursive prediction for the next week (168 steps)
    print(f"\n[Forecasting] Generating recursive predictions for the next 168 hours...")
    recursive_predictions_scaled = []
    
    # Start sequence: last window from the test set
    current_window = scaled_data[-lookback:].copy() # shape: (lookback, 1)
    
    for _ in range(168):
        # Reshape to (1, lookback, 1) for prediction
        input_seq = current_window.reshape((1, lookback, 1))
        pred = model.predict(input_seq, verbose=0) # returns (1, 1)
        pred_val = pred[0, 0]
        recursive_predictions_scaled.append(pred_val)
        
        # Shift lookback window: drop first, append new prediction
        current_window = np.append(current_window[1:], [[pred_val]], axis=0)
        
    recursive_predictions = scaler.inverse_transform(np.array(recursive_predictions_scaled).reshape(-1, 1)).flatten()
    print("Recursive Predictions (First 10 hours):", recursive_predictions[:10])
    
    # Plot forecasts
    plt.figure(figsize=(10, 5))
    plt.plot(df_processed.index[-200:], series_data[-200:], label="Historical Data")
    
    # Create date index for future forecasts
    last_timestamp = df_processed.index[-1]
    inferred_freq = df_processed.index.freq if df_processed.index.freq is not None else "h"
    future_timestamps = pd.date_range(start=last_timestamp, periods=169, freq=inferred_freq)[1:]
    
    plt.plot(future_timestamps, recursive_predictions, label="Recursive Forecast (Next 168h)", color="red", linestyle="--")
    plt.title("Recursive Future Forecasts")
    plt.xlabel("Time")
    plt.ylabel(target_col)
    plt.legend()
    plt.grid(True)
    forecast_plot_path = os.path.join(args.output_dir, "recursive_forecast.png")
    plt.savefig(forecast_plot_path, dpi=300)
    plt.close()
    print(f"Forecast plot saved to '{forecast_plot_path}'")
    
    # Prepare artifacts to save
    preprocessors = {
        'scaler': scaler,
        'lookback': lookback,
        'target_col': target_col,
        'task_type': 'time_series_forecasting'
    }
    
    metrics = {
        "rmse": float(rmse),
        "mae": float(mae),
        "r2": float(r2),
        "mape": float(mape),
        "accuracy": float(accuracy),
        "recursive_predictions_sample": recursive_predictions[:24].tolist()
    }
    
    return model, preprocessors, metrics

def run_tabular_pipeline(df, target_col, args):
    """
    Runs the full tabular regression or classification pipeline.
    """
    X, y, preprocessors = preprocess_tabular(df, target_col)
    
    # Train-test split (80/20 train/test)
    task_type = preprocessors['task_type']
    
    # Determine stratification for classification tasks to address class imbalance
    stratify = y if task_type in ["binary_classification", "multiclass_classification"] else None
    
    # If the minor class size in classification split is too small for stratification
    if stratify is not None:
        # Check counts
        if task_type == "binary_classification":
            counts = np.bincount(y)
        else: # multiclass
            counts = np.sum(y, axis=0).astype(int)
            
        if np.min(counts) < 2:
            print("[Warning] Class count too small for stratified splitting. Splitting without stratification.")
            stratify = None
            
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=stratify
    )
    
    # Train-val split (90/10 validation)
    stratify_val = y_train if task_type in ["binary_classification", "multiclass_classification"] else None
    if stratify_val is not None:
        if task_type == "binary_classification":
            counts_val = np.bincount(y_train)
        else:
            counts_val = np.sum(y_train, axis=0).astype(int)
        if np.min(counts_val) < 2:
            stratify_val = None
            
    X_train_final, X_val, y_train_final, y_val = train_test_split(
        X_train, y_train, test_size=0.1, random_state=42, stratify=stratify_val
    )
    
    print(f"Data Shapes:")
    print(f"  Train features: {X_train_final.shape}, targets: {y_train_final.shape}")
    print(f"  Val features:   {X_val.shape}, targets: {y_val.shape}")
    print(f"  Test features:  {X_test.shape}, targets: {y_test.shape}")
    
    # Build MLP Model
    num_classes = y.shape[1] if task_type == "multiclass_classification" else 1
    model = build_mlp_model(X_train_final.shape[1], task_type, num_classes)
    model.summary()
    
    # Train
    history = train_model(model, X_train_final, y_train_final, X_val, y_val, task_type, args.epochs, args.batch_size, args.class_weight_style)
    plot_history(history, args.output_dir)
    
    # Evaluate
    metrics = evaluate_tabular(model, X_test, y_test, preprocessors, args.output_dir)
    
    return model, preprocessors, metrics

def main():
    args = parse_args()
    
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Trigger synthetic time-series testing if requested
    csv_path = args.data
    if args.test_timeseries:
        csv_path = generate_synthetic_timeseries()
        
    print(f"\n--- Loading Dataset: '{csv_path}' ---")
    if not os.path.exists(csv_path):
        print(f"Error: Dataset file '{csv_path}' does not exist.")
        sys.exit(1)
        
    df = pd.read_csv(csv_path)
    print(f"Loaded {df.shape[0]} rows and {df.shape[1]} columns.")
    
    # 1. Auto-detect datetime column
    datetime_col = detect_datetime_column(df)
    
    if datetime_col is not None:
        print(f"[Pipeline Selection] AUTO-DETECTED TIME-SERIES FORECASTING TASK")
        # Define target for time-series (user specified or default to the first numeric column that isn't date)
        target_col = args.target
        if target_col is None:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                target_col = numeric_cols[0]
                print(f"[Auto-Detection] Defaulting time-series target to first numeric column: '{target_col}'")
            else:
                print("Error: No numeric columns found to forecast.")
                sys.exit(1)
                
        model, preprocessors, metrics = run_timeseries_pipeline(df, datetime_col, target_col, args)
        
    else:
        print(f"[Pipeline Selection] AUTO-DETECTED TABULAR REGRESSION/CLASSIFICATION TASK")
        # Auto-detect target column
        target_col = args.target if args.target else detect_target_column(df)
        print(f"Selected Target Column: '{target_col}'")
        
        model, preprocessors, metrics = run_tabular_pipeline(df, target_col, args)
        
    # 6. SAVING ARTIFACTS
    print(f"\n--- Saving Artifacts to '{args.output_dir}' ---")
    
    # Save Model
    model_path = os.path.join(args.output_dir, "model.keras")
    model.save(model_path)
    print(f"  Saved Keras model to '{model_path}'")
    
    # Save Preprocessors
    preprocessors_path = os.path.join(args.output_dir, "preprocessors.pkl")
    with open(preprocessors_path, "wb") as f:
        pickle.dump(preprocessors, f)
    print(f"  Saved preprocessors/scalers to '{preprocessors_path}'")
    
    # Save Metrics JSON
    metrics_path = os.path.join(args.output_dir, "metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=4)
    print(f"  Saved evaluation metrics to '{metrics_path}'")
    
    print("\nAdaptive deep learning pipeline completed successfully!")

if __name__ == "__main__":
    main()
