import os
import json
import hashlib
from glob import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "backend", "models")
DATA_DIR = os.path.join(BASE_DIR, "data", "Electricity Demand Data")
OUTPUT_JSON = os.path.join(MODELS_DIR, "model_hashes.json")

def get_file_hash(filepath: str) -> str:
    """Compute the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    print("Generating model signatures for PowerCortex...")
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    hashes = {}
    
    # 1. Models dir
    model_files = glob(os.path.join(MODELS_DIR, "*.keras")) + glob(os.path.join(MODELS_DIR, "*.pkl"))
    for file in model_files:
        filename = os.path.basename(file)
        hashes[filename] = get_file_hash(file)
        print(f"Signed: {filename} -> {hashes[filename]}")
        
    # 2. Data dir (LSTM demand model)
    if os.path.exists(DATA_DIR):
        lstm_model = os.path.join(DATA_DIR, "lstm_demand_model.keras")
        if os.path.exists(lstm_model):
            filename = os.path.basename(lstm_model)
            hashes[filename] = get_file_hash(lstm_model)
            print(f"Signed: {filename} -> {hashes[filename]}")
            
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(hashes, f, indent=4)
        
    print(f"\nSuccessfully generated {len(hashes)} cryptographic signatures.")
    print(f"Hashes written to: {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
