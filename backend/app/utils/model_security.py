import hashlib
import json
import logging
import os

logger = logging.getLogger("powercortex.utils.model_security")

class SecurityError(Exception):
    """Raised when a security verification fails."""
    pass

def get_file_hash(filepath: str) -> str:
    """Compute the SHA-256 hash of a file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
        
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        # Read in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_file_hash(filepath: str, hashes_dict: dict) -> bool:
    """
    Verify the SHA-256 hash of a file against a dictionary of allowed hashes.
    Raises a SecurityError if the hash does not match, or if the file isn't in the dict.
    """
    filename = os.path.basename(filepath)
    if filename not in hashes_dict:
        logger.error(f"Security violation: No registered hash for {filename}")
        raise SecurityError(f"No hash registered for model file: {filename}")
        
    expected_hash = hashes_dict[filename]
    actual_hash = get_file_hash(filepath)
    
    if actual_hash != expected_hash:
        logger.error(f"Security violation: Hash mismatch for {filename}! Expected {expected_hash}, got {actual_hash}")
        raise SecurityError(f"Hash mismatch for model file: {filename}")
        
    logger.debug(f"Successfully verified cryptographic hash for {filename}")
    return True

def load_model_hashes(hashes_path: str) -> dict:
    """Load the known model hashes from a JSON file."""
    if not os.path.exists(hashes_path):
        logger.warning(f"Model hashes file not found at {hashes_path}")
        return {}
        
    with open(hashes_path, 'r', encoding='utf-8') as f:
        return json.load(f)
