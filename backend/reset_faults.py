import pymongo
from datetime import datetime, timezone, timedelta

def reset_faults_db():
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client.powercortex
    
    print("Dropping faults collection...")
    db.faults.drop()
    
    now = datetime.now(timezone.utc)
    
    initial_faults = [
        # Active Faults (8 items: 6 Critical, 1 High, 1 Medium)
        {
            "fault_id": "FLT-001",
            "fault_type": "Voltage Sag",
            "asset_name": "Transmission Line TL-22A",
            "severity": "Critical",
            "probability": 94.2,
            "status": "Active",
            "voltage": 185.0,
            "current": 450.0,
            "frequency": 49.1,
            "detected_at": now - timedelta(minutes=45)
        },
        {
            "fault_id": "FLT-002",
            "fault_type": "Overload",
            "asset_name": "Transformer T-104",
            "severity": "Critical",
            "probability": 91.8,
            "status": "Active",
            "voltage": 220.0,
            "current": 490.0,
            "frequency": 50.0,
            "detected_at": now - timedelta(hours=2)
        },
        {
            "fault_id": "FLT-003",
            "fault_type": "Short Circuit",
            "asset_name": "Feeder F-22A",
            "severity": "Critical",
            "probability": 96.5,
            "status": "Active",
            "voltage": 85.0,
            "current": 420.0,
            "frequency": 49.8,
            "detected_at": now - timedelta(hours=3)
        },
        {
            "fault_id": "FLT-004",
            "fault_type": "Equipment Failure",
            "asset_name": "Substation SS-04",
            "severity": "Critical",
            "probability": 95.0,
            "status": "Active",
            "voltage": 210.0,
            "current": 520.0,
            "frequency": 50.1,
            "detected_at": now - timedelta(hours=4)
        },
        {
            "fault_id": "FLT-005",
            "fault_type": "Transformer Fault",
            "asset_name": "Transformer T-112",
            "severity": "Critical",
            "probability": 92.5,
            "status": "Active",
            "voltage": 195.0,
            "current": 460.0,
            "frequency": 49.9,
            "detected_at": now - timedelta(hours=5)
        },
        {
            "fault_id": "FLT-006",
            "fault_type": "Frequency Deviation",
            "asset_name": "Transmission Line TL-12",
            "severity": "Critical",
            "probability": 93.8,
            "status": "Active",
            "voltage": 218.0,
            "current": 25.0,
            "frequency": 48.2,
            "detected_at": now - timedelta(hours=5, minutes=30)
        },
        {
            "fault_id": "FLT-007",
            "fault_type": "Line Fault",
            "asset_name": "Feeder F-15B",
            "severity": "High",
            "probability": 87.5,
            "status": "Active",
            "voltage": 175.0,
            "current": 37.4,
            "frequency": 48.8,
            "detected_at": now - timedelta(hours=6)
        },
        {
            "fault_id": "FLT-008",
            "fault_type": "Voltage Swell",
            "asset_name": "Substation SS-02",
            "severity": "Medium",
            "probability": 82.3,
            "status": "Active",
            "voltage": 258.0,
            "current": 13.9,
            "frequency": 50.5,
            "detected_at": now - timedelta(hours=7)
        },
        # Historical Resolved Faults (4 items)
        {
            "fault_id": "FLT-009",
            "fault_type": "Voltage Sag",
            "asset_name": "Feeder F-22A",
            "severity": "High",
            "probability": 76.5,
            "status": "Resolved",
            "voltage": 192.0,
            "current": 18.0,
            "frequency": 49.6,
            "detected_at": now - timedelta(days=2, hours=1)
        },
        {
            "fault_id": "FLT-010",
            "fault_type": "Overload",
            "asset_name": "Transformer T-112",
            "severity": "Medium",
            "probability": 65.2,
            "status": "Resolved",
            "voltage": 215.0,
            "current": 320.0,
            "frequency": 49.9,
            "detected_at": now - timedelta(days=2, hours=3)
        },
        {
            "fault_id": "FLT-011",
            "fault_type": "Line Fault",
            "asset_name": "Line TL-22",
            "severity": "Critical",
            "probability": 93.1,
            "status": "Resolved",
            "voltage": 172.0,
            "current": 380.0,
            "frequency": 48.9,
            "detected_at": now - timedelta(days=1, hours=2)
        },
        {
            "fault_id": "FLT-012",
            "fault_type": "Voltage Swell",
            "asset_name": "Feeder F-15B",
            "severity": "Low",
            "probability": 48.0,
            "status": "Resolved",
            "voltage": 252.0,
            "current": 12.0,
            "frequency": 50.3,
            "detected_at": now - timedelta(days=1, hours=5)
        }
    ]
    
    print(f"Inserting {len(initial_faults)} faults...")
    db.faults.insert_many(initial_faults)
    
    # Recreate index in case
    db.faults.create_index([("fault_id", pymongo.ASCENDING)], unique=True)
    db.faults.create_index([("status", pymongo.ASCENDING)])
    db.faults.create_index([("detected_at", pymongo.DESCENDING)])
    
    print("Database faults reset and seeded successfully.")

if __name__ == "__main__":
    reset_faults_db()
