import re

def mask_sensitive_data(text: str) -> str:
    """
    Scans the provided text and redacts sensitive PII or identifiers.
    Currently masks GUVNL Consumer IDs (e.g., CN-12345 -> CN-****).
    """
    if not text:
        return text
        
    # Mask Consumer IDs (e.g., CN-88029 -> CN-****)
    # The regex looks for 'CN-' followed by one or more digits.
    masked_text = re.sub(r'CN-\d+', 'CN-****', text)
    
    return masked_text
