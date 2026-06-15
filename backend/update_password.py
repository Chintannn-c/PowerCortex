import asyncio
import os
import sys

# Add backend directory to system path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.security import hash_password

async def main():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client.powercortex
    
    email = "sharmachintan585@gmail.com"
    new_hash = hash_password("Password123!")
    
    result = await db.users.update_one(
        {"email": email},
        {"$set": {"password_hash": new_hash}}
    )
    
    if result.matched_count > 0:
        print(f"Successfully updated password for {email} to 'Password123!'")
    else:
        print(f"No user found with email {email}")
        
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
