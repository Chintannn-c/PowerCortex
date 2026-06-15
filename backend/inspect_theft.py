import pymongo
import json
from bson import json_util

def inspect_theft():
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client.powercortex
    collection = db.theft_alerts
    
    count_all = collection.count_documents({})
    count_suspicious = collection.count_documents({"is_suspicious": True})
    count_active_suspicious = collection.count_documents({"is_suspicious": True, "status": "Active"})
    count_resolved = collection.count_documents({"status": "Resolved"})
    
    print(f"Total documents: {count_all}")
    print(f"Suspicious: {count_suspicious}")
    print(f"Active suspicious: {count_active_suspicious}")
    print(f"Resolved: {count_resolved}")
    
    print("\nSample Active Suspicious document:")
    sample = collection.find_one({"is_suspicious": True})
    if sample:
        print(json.dumps(sample, indent=2, default=json_util.default))
    else:
        print("No suspicious document found.")

if __name__ == "__main__":
    inspect_theft()
