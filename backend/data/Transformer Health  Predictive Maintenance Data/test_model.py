#!/usr/bin/env python
"""
Model Inference Script - Test and Predict using Saved Model Artifacts
Author: Antigravity AI Coding Assistant
"""

import os
import sys
import pickle
import argparse
import numpy as np
import pandas as pd
import tensorflow as tf

def parse_args():
    parser = argparse.ArgumentParser(description="Run inference on new data using the saved Keras model")
    parser.add_argument("--model", type=str, default="artifacts_output/model.keras", help="Path to the saved .keras model")
    parser.add_argument("--preprocessors", type=str, default="artifacts_output/preprocessors.pkl", help="Path to preprocessors.pkl")
    parser.add_argument("--input", type=str, default="predictive_maintenance.csv", help="Path to input CSV to test/predict on")
    parser.add_argument("--output", type=str, default="predictions_output.csv", help="Path to save predictions")
    parser.add_argument("--num_samples", type=int, default=10, help="Number of sample predictions to print to screen")
    return parser.parse_args()

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
        
    if rot_speed_col and torque_col:
        df["Power_W"] = df[rot_speed_col[0]] * df[torque_col[0]]
        
    if tool_wear_col and torque_col:
        df["ToolWear_Torque"] = df[tool_wear_col[0]] * df[torque_col[0]]
        
    return df

def preprocess_tabular_inference(df, preprocessors):
    """
    Applies the same preprocessing transformations to new tabular data.
    """
    task_type = preprocessors['task_type']
    feature_cols = preprocessors['feature_cols']
    
    # Copy DataFrame to avoid modifying original
    X = df.copy()
    X = engineer_features(X)
    
    # Create empty dataframe with expected feature columns
    X_aligned = pd.DataFrame(0.0, index=df.index, columns=feature_cols)
    
    num_imputer = preprocessors.get('num_imputer')
    cat_imputer = preprocessors.get('cat_imputer')
    encoder = preprocessors.get('encoder')
    scaler = preprocessors.get('scaler')
    
    # 1. Process numerical features
    if num_imputer and scaler:
        num_cols = num_imputer.feature_names_in_ if hasattr(num_imputer, 'feature_names_in_') else []
        if len(num_cols) > 0:
            # Ensure all numeric columns are present in X
            for col in num_cols:
                if col not in X.columns:
                    X[col] = np.nan
            # Impute
            X_num = num_imputer.transform(X[num_cols])
            X_num_df = pd.DataFrame(X_num, columns=num_cols, index=X.index)
            # Scale
            X_num_scaled = scaler.transform(X_num_df)
            X_num_scaled_df = pd.DataFrame(X_num_scaled, columns=num_cols, index=X.index)
            
            # Copy to X_aligned
            for col in num_cols:
                if col in X_aligned.columns:
                    X_aligned[col] = X_num_scaled_df[col]
                    
    # 2. Process categorical features
    if cat_imputer and encoder:
        cat_cols = cat_imputer.feature_names_in_ if hasattr(cat_imputer, 'feature_names_in_') else []
        if len(cat_cols) > 0:
            # Ensure all categorical columns are present in X
            for col in cat_cols:
                if col not in X.columns:
                    X[col] = "Missing"
            # Impute
            X_cat = cat_imputer.transform(X[cat_cols])
            X_cat_df = pd.DataFrame(X_cat, columns=cat_cols, index=X.index)
            # Encode
            encoded_cats = encoder.transform(X_cat_df)
            cat_feature_names_out = encoder.get_feature_names_out(cat_cols)
            encoded_df = pd.DataFrame(encoded_cats, columns=cat_feature_names_out, index=X.index)
            
            # Copy to X_aligned
            for col in encoded_df.columns:
                if col in X_aligned.columns:
                    X_aligned[col] = encoded_df[col]
                    
    return X_aligned

def preprocess_timeseries_inference(df, preprocessors):
    """
    Applies the same preprocessing transformations to new time-series data and sets up lookback windows.
    """
    target_col = preprocessors['target_col']
    lookback = preprocessors['lookback']
    scaler = preprocessors['scaler']
    
    # Extract only the target column for univariate forecasting
    series_data = df[[target_col]].values
    
    # Scale data
    scaled_data = scaler.transform(series_data)
    
    # Generate sequence windows
    X = []
    for i in range(len(scaled_data) - lookback + 1):
        X.append(scaled_data[i:(i + lookback), 0])
        
    X = np.array(X)
    X = X.reshape((X.shape[0], X.shape[1], 1))
    return X

def main():
    args = parse_args()
    
    # 1. Load trained artifacts
    print(f"--- Loading Model and Preprocessors ---")
    if not os.path.exists(args.model):
        print(f"Error: Model file not found at '{args.model}'")
        sys.exit(1)
    if not os.path.exists(args.preprocessors):
        print(f"Error: Preprocessors file not found at '{args.preprocessors}'")
        sys.exit(1)
        
    model = tf.keras.models.load_model(args.model)
    with open(args.preprocessors, "rb") as f:
        preprocessors = pickle.load(f)
        
    task_type = preprocessors['task_type']
    print(f"Loaded model successfully. Detected Task Type: {task_type}")
    
    # 2. Load input test data
    print(f"\n--- Loading Input Dataset: '{args.input}' ---")
    if not os.path.exists(args.input):
        print(f"Error: Input file not found at '{args.input}'")
        sys.exit(1)
        
    df = pd.read_csv(args.input)
    print(f"Loaded {len(df)} rows to test.")
    
    # Keep copy of original dataframe for final output mapping
    output_df = df.copy()
    
    # 3. Preprocess and predict
    print("\n--- Running Preprocessing and Inference ---")
    if task_type == 'time_series_forecasting':
        # Time Series Pipeline
        # Needs date sorting
        date_cols = [c for c in df.columns if 'date' in c.lower() or 'time' in c.lower()]
        if date_cols:
            df = df.sort_values(by=date_cols[0])
            
        X = preprocess_timeseries_inference(df, preprocessors)
        print(f"Processed into sequence shape: {X.shape}")
        
        predictions_scaled = model.predict(X)
        predictions = preprocessors['scaler'].inverse_transform(predictions_scaled).flatten()
        
        # Save output (the first 'lookback - 1' steps don't have predictions due to lookback window)
        lookback = preprocessors['lookback']
        pred_column = [None] * (lookback - 1) + list(predictions)
        output_df[f"Predicted_{preprocessors['target_col']}"] = pred_column
        
        # Print sample predictions
        print(f"\nSample Predictions (First {args.num_samples}):")
        start_idx = lookback - 1
        for i in range(min(args.num_samples, len(predictions))):
            idx = start_idx + i
            print(f"  Row {idx+1}: Actual = {df.iloc[idx][preprocessors['target_col']]}, Predicted = {predictions[i]:.4f}")
            
    else:
        # Tabular Pipeline
        X = preprocess_tabular_inference(df, preprocessors)
        print(f"Processed feature matrix shape: {X.shape}")
        
        predictions = model.predict(X)
        target_classes = preprocessors.get('target_classes')
        
        if task_type == "regression":
            pred_vals = predictions.flatten()
            output_df["Predicted_Value"] = pred_vals
            
            print(f"\nSample Predictions (First {args.num_samples}):")
            for i in range(min(args.num_samples, len(pred_vals))):
                print(f"  Row {i+1}: Predicted = {pred_vals[i]:.4f}")
                
        elif task_type == "binary_classification":
            prob = predictions.flatten()
            pred_classes = (prob > 0.5).astype(int)
            
            # Map labels if class mapping exists
            if target_classes is not None:
                mapped_classes = [target_classes[c] for c in pred_classes]
            else:
                mapped_classes = pred_classes
                
            output_df["Prediction_Probability"] = prob
            output_df["Predicted_Class"] = mapped_classes
            
            print(f"\nSample Predictions (First {args.num_samples}):")
            for i in range(min(args.num_samples, len(pred_classes))):
                print(f"  Row {i+1}: Class = '{mapped_classes[i]}' (Probability: {prob[i]:.4f})")
                
        else: # multiclass_classification
            pred_classes = np.argmax(predictions, axis=1)
            prob = np.max(predictions, axis=1)
            
            if target_classes is not None:
                mapped_classes = [target_classes[c] for c in pred_classes]
            else:
                mapped_classes = pred_classes
                
            output_df["Prediction_Confidence"] = prob
            output_df["Predicted_Class"] = mapped_classes
            
            print(f"\nSample Predictions (First {args.num_samples}):")
            for i in range(min(args.num_samples, len(pred_classes))):
                print(f"  Row {i+1}: Class = '{mapped_classes[i]}' (Confidence: {prob[i]:.4f})")
                
    # 4. Save results
    output_df.to_csv(args.output, index=False)
    print(f"\nSaved inference output with predictions to '{args.output}'")
    print("Inference completed successfully!")

if __name__ == "__main__":
    main()
