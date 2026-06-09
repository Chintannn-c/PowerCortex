import zipfile
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "data", "Electricity Demand Data", "lstm_demand_model.keras")

if os.path.exists(MODEL_PATH):
    with zipfile.ZipFile(MODEL_PATH, 'r') as zip_ref:
        zip_ref.printdir()
else:
    print("Model file not found")
