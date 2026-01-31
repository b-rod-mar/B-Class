"""
Script to import global 6-digit HS codes from the public dataset
Run with: python import_global_hs_codes.py
"""
import asyncio
import pandas as pd
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import uuid

load_dotenv()

mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'test_database')]

async def import_global_hs_codes():
    """Import global 6-digit HS codes from the public dataset"""
    print("Fetching global HS codes dataset...")
    
    url = "https://raw.githubusercontent.com/datasets/harmonized-system/master/data/harmonized-system.csv"
    df = pd.read_csv(url)
    
    # Filter for 6-digit HS codes only
    df['hs_str'] = df['hscode'].astype(str).str.zfill(6)
    df_6digit = df[df['hs_str'].str.len() == 6].copy()
    
    # Create chapter and heading columns
    df_6digit['chapter'] = df_6digit['hs_str'].str[:2]
    df_6digit['heading'] = df_6digit['hs_str'].str[:4]
    
    print(f"Found {len(df_6digit)} 6-digit HS codes")
    
    # Get existing codes to avoid duplicates
    existing_codes = await db.hs_codes.distinct("code")
    existing_set = set(existing_codes)
    
    imported = 0
    updated = 0
    
    for idx, row in df_6digit.iterrows():
        code = row['hs_str']
        
        # Format code with dot (e.g., "0101.21")
        if len(code) == 6:
            formatted_code = f"{code[:4]}.{code[4:]}"
        else:
            formatted_code = code
        
        # Check if any variation exists
        code_exists = code in existing_set or formatted_code in existing_set
        
        hs_doc = {
            "code": formatted_code,
            "description": row['description'],
            "chapter": row['chapter'],
            "section": row.get('section', ''),
            "duty_rate": None,  # Will need to be set per Bahamas tariff
            "notes": "Global HS nomenclature - verify Bahamas-specific rates",
            "bahamas_extension": None,
            "is_restricted": False,
            "requires_permit": False,
        }
        
        if code_exists:
            # Update existing - but only if description is empty
            result = await db.hs_codes.update_one(
                {"$or": [{"code": code}, {"code": formatted_code}], "description": {"$in": [None, ""]}},
                {"$set": {"description": row['description']}}
            )
            if result.modified_count > 0:
                updated += 1
        else:
            # Insert new code
            hs_doc["id"] = str(uuid.uuid4())
            hs_doc["created_at"] = pd.Timestamp.now().isoformat()
            hs_doc["created_by"] = "system_import"
            await db.hs_codes.insert_one(hs_doc)
            imported += 1
            existing_set.add(formatted_code)
        
        if (imported + updated) % 500 == 0:
            print(f"Progress: {imported} imported, {updated} updated...")
    
    print(f"\nImport complete!")
    print(f"  - New codes imported: {imported}")
    print(f"  - Existing codes updated: {updated}")
    print(f"  - Total codes in database: {await db.hs_codes.count_documents({})}")

if __name__ == "__main__":
    asyncio.run(import_global_hs_codes())
