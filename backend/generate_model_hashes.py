import os
import json
import hashlib
from glob import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "app", "models")
DATA_DIR = os.path.join(BASE_DIR, "data", "Electricity Demand Data")
OUTPUT_JSON = os.path.join(BASE_DIR, "models", "model_hashes.json")

def get_file_hash(filepath: str) -> str:
    """Compute the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    print("Generating model signatures for PowerCortex...")
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    
    hashes = {}
    
    # 1. Models dir
    model_files = glob(os.path.join(MODELS_DIR, "*.keras")) + glob(os.path.join(MODELS_DIR, "*.pkl"))
    for file in sorted(model_files):
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
            
    # Load existing to see if anything changed or to keep order
    existing_hashes = {}
    if os.path.exists(OUTPUT_JSON):
        try:
            with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
                existing_hashes = json.load(f)
        except Exception:
            pass
            
    # Sort hashes dictionary keys to match existing format
    sorted_hashes = {}
    # First, preserve order of existing hashes if they are present in new hashes
    for key in existing_hashes:
        if key in hashes:
            sorted_hashes[key] = hashes[key]
    # Then append any new hashes not in existing
    for key in hashes:
        if key not in sorted_hashes:
            sorted_hashes[key] = hashes[key]
            
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(sorted_hashes, f, indent=4)
        
    print(f"\nSuccessfully generated {len(sorted_hashes)} cryptographic signatures.")
    print(f"Hashes written to: {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
