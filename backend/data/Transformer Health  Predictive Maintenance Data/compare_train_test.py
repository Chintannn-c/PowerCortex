#!/usr/bin/env python
"""
Train vs Test Performance Comparison Script
Author: Antigravity AI Coding Assistant
"""

import os
import sys
import pickle
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import tensorflow as tf

def main():
    # Paths to artifacts
    model_path = "artifacts_output/multiclass_classification/model.keras"
    preprocessors_path = "artifacts_output/multiclass_classification/preprocessors.pkl"
    data_path = "predictive_maintenance.csv"
    
    print("--- Loading Model, Preprocessors, and Dataset ---")
    if not all(os.path.exists(p) for p in [model_path, preprocessors_path, data_path]):
        print("Error: Missing model, preprocessor, or dataset artifacts. Please ensure you ran multiclass training first.")
        sys.exit(1)
        
    model = tf.keras.models.load_model(model_path)
    with open(preprocessors_path, "rb") as f:
        preprocessors = pickle.load(f)
        
    df = pd.read_csv(data_path)
    
    # Preprocess matching the main training script
    from train_adaptive_model import preprocess_tabular
    X, y, preprocessors_ref = preprocess_tabular(df, "Failure Type")
    
    # Recreate the exact same train/test split using random_state=42 and stratify
    task_type = preprocessors['task_type']
    target_classes = preprocessors['target_classes']
    
    stratify = y
    # Verify min class counts for stratification
    counts = np.sum(y, axis=0).astype(int)
    if np.min(counts) < 2:
        stratify = None
        
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=stratify
    )
    
    print("\n--- Running Inference on Train and Test Sets ---")
    train_preds = model.predict(X_train)
    test_preds = model.predict(X_test)
    
    # Compute losses
    train_loss = model.evaluate(X_train, y_train, verbose=0)[0]
    test_loss = model.evaluate(X_test, y_test, verbose=0)[0]
    
    # Get class predictions
    train_pred_classes = np.argmax(train_preds, axis=1)
    test_pred_classes = np.argmax(test_preds, axis=1)
    
    y_train_labels = np.argmax(y_train, axis=1)
    y_test_labels = np.argmax(y_test, axis=1)
    
    # Calculate performance metrics
    train_acc = accuracy_score(y_train_labels, train_pred_classes)
    test_acc = accuracy_score(y_test_labels, test_pred_classes)
    
    train_prec, train_rec, train_f1, _ = precision_recall_fscore_support(y_train_labels, train_pred_classes, average="weighted")
    test_prec, test_rec, test_f1, _ = precision_recall_fscore_support(y_test_labels, test_pred_classes, average="weighted")
    
    # Print comparison report
    print("\n" + "="*50)
    print("        TRAIN VS TEST METRIC COMPARISON")
    print("="*50)
    print(f"Metric          | Train Set       | Test Set        | Diff (Test - Train)")
    print("-"*50)
    print(f"Loss            | {train_loss:.4f}          | {test_loss:.4f}          | {test_loss - train_loss:+.4f}")
    print(f"Accuracy        | {train_acc*100:.2f}%          | {test_acc*100:.2f}%          | {(test_acc - train_acc)*100:+.2f}%")
    print(f"Precision       | {train_prec*100:.2f}%          | {test_prec*100:.2f}%          | {(test_prec - train_prec)*100:+.2f}%")
    print(f"Recall          | {train_rec*100:.2f}%          | {test_rec*100:.2f}%          | {(test_rec - train_rec)*100:+.2f}%")
    print(f"F1-Score        | {train_f1*100:.2f}%          | {test_f1*100:.2f}%          | {(test_f1 - train_f1)*100:+.2f}%")
    print("="*50)
    
    # Detailed diagnosis of overfitting
    print("\n--- Generalization Diagnosis ---")
    acc_diff = test_acc - train_acc
    if acc_diff < -0.05:
        print("WARNING: Model exhibits signs of overfitting. Test accuracy is significantly lower than training accuracy.")
    elif abs(acc_diff) <= 0.02:
        print("EXCELLENT: The model shows strong generalization. Train and Test performance are highly aligned with zero overfitting.")
    else:
        print("GOOD: The model has generalized successfully to the unseen test dataset.")
        
    # Generate visual comparison plot
    print("\n--- Generating Metric Comparison Chart ---")
    metrics_names = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
    train_metrics = [train_acc * 100, train_prec * 100, train_rec * 100, train_f1 * 100]
    test_metrics = [test_acc * 100, test_prec * 100, test_rec * 100, test_f1 * 100]
    
    x = np.arange(len(metrics_names))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(10, 6))
    rects1 = ax.bar(x - width/2, train_metrics, width, label='Train Set', color='#4A90E2', edgecolor='none', alpha=0.95)
    rects2 = ax.bar(x + width/2, test_metrics, width, label='Test Set (Unseen)', color='#E67E22', edgecolor='none', alpha=0.95)
    
    ax.set_ylabel('Percentage (%)', fontsize=12, fontweight='bold', labelpad=10)
    ax.set_title('Multi-Class Tabular Model: Train vs Test Metrics', fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(metrics_names, fontsize=11, fontweight='bold')
    ax.set_ylim(85, 102)  # Zoom in to focus on differences (>85%)
    ax.legend(fontsize=11, loc='lower right')
    ax.grid(True, linestyle=':', alpha=0.6, axis='y')
    
    # Style styling
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.2f}%',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 4),  # 4 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=10, fontweight='bold')
                        
    autolabel(rects1)
    autolabel(rects2)
    
    plt.tight_layout()
    plot_path = "artifacts_output/multiclass_classification/train_test_comparison.png"
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Comparison plot successfully saved to '{plot_path}'")
    
    # Save comparison report to JSON
    report = {
        "train": {
            "loss": float(train_loss),
            "accuracy": float(train_acc),
            "precision": float(train_prec),
            "recall": float(train_rec),
            "f1_score": float(train_f1)
        },
        "test": {
            "loss": float(test_loss),
            "accuracy": float(test_acc),
            "precision": float(test_prec),
            "recall": float(test_rec),
            "f1_score": float(test_f1)
        },
        "difference": {
            "loss": float(test_loss - train_loss),
            "accuracy": float(test_acc - train_acc),
            "precision": float(test_prec - train_prec),
            "recall": float(test_rec - train_rec),
            "f1_score": float(test_f1 - train_f1)
        }
    }
    
    report_path = "artifacts_output/multiclass_classification/train_test_comparison.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=4)
    print(f"Comparison report successfully saved to '{report_path}'")

if __name__ == "__main__":
    main()
