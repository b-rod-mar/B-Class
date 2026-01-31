"""
Script to extract Bahamas-specific HS codes from the 2023 Tariff Schedule
and update the database with duty rates
"""
import asyncio
import re
from pypdf import PdfReader
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import uuid

load_dotenv()

mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'test_database')]

def extract_hs_codes_from_pdf(pdf_path):
    """Extract HS codes, descriptions and rates from the Bahamas Tariff PDF"""
    reader = PdfReader(pdf_path)
    hs_codes = []
    
    # Pattern to match HS codes in format like 0101.2100, 0201.1000, etc.
    code_pattern = re.compile(r'^(\d{4}\.\d{2,4})\s+(.+?)(?:\s+(Free|[\d\.]+%?))?(?:\s+.*)?$', re.MULTILINE)
    
    # Also match codes like 0102.2110, 0102.2120 etc
    detailed_pattern = re.compile(r'(\d{4}\.\d{4})\s+[-]+\s*(.+?)\s+(Free|\d+%)', re.MULTILINE)
    
    current_chapter = ""
    current_heading = ""
    
    for page_num in range(10, min(len(reader.pages), 900)):  # Skip intro pages
        try:
            text = reader.pages[page_num].extract_text()
            if not text:
                continue
            
            # Extract chapter from page header
            chapter_match = re.search(r'Chapter\s+(\d+)', text)
            if chapter_match:
                current_chapter = chapter_match.group(1).zfill(2)
            
            # Parse lines for HS codes
            lines = text.split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Match HS code patterns
                # Pattern 1: 0101.2100 -- Pure-bred breeding animals Free 300% EPA number
                match1 = re.match(r'^(\d{4}\.\d{2,4})\s+[-–]*\s*(.+?)\s+(Free|\d+%)', line)
                if match1:
                    code = match1.group(1)
                    desc = match1.group(2).strip()
                    rate = match1.group(3)
                    
                    # Clean up description
                    desc = re.sub(r'\s+', ' ', desc)
                    desc = desc.strip('-– ')
                    
                    if len(desc) > 5:  # Valid description
                        hs_codes.append({
                            'code': code,
                            'description': desc,
                            'duty_rate': rate,
                            'chapter': code[:2]
                        })
                
                # Pattern 2: Just code and text, look for rate in columns
                match2 = re.match(r'^(\d{4}\.\d{2,4})\s+[-–]+\s*(.+)', line)
                if match2 and not match1:
                    code = match2.group(1)
                    rest = match2.group(2)
                    
                    # Try to find rate
                    rate_match = re.search(r'(Free|\d+%)', rest)
                    rate = rate_match.group(1) if rate_match else None
                    
                    # Extract description (before rate or EPA)
                    desc = re.split(r'\s+(Free|\d+%|EPA|number|pound|kg)', rest)[0]
                    desc = desc.strip('-– ')
                    
                    if rate and len(desc) > 5:
                        hs_codes.append({
                            'code': code,
                            'description': desc,
                            'duty_rate': rate,
                            'chapter': code[:2]
                        })
                        
        except Exception as e:
            print(f"Error on page {page_num}: {e}")
            continue
    
    return hs_codes

async def update_database_with_bahamas_codes():
    """Update the HS codes database with Bahamas-specific rates"""
    print("Extracting HS codes from Bahamas 2023 Tariff Schedule...")
    hs_codes = extract_hs_codes_from_pdf('/tmp/bahamas_tariff_2023.pdf')
    
    print(f"Found {len(hs_codes)} HS codes with rates")
    
    updated = 0
    inserted = 0
    
    for code_data in hs_codes:
        code = code_data['code']
        
        # Try to update existing record
        result = await db.hs_codes.update_one(
            {"code": code},
            {"$set": {
                "duty_rate": code_data['duty_rate'],
                "description": code_data['description'],
                "chapter": code_data['chapter'],
                "source": "Bahamas Tariff Schedule 2023"
            }}
        )
        
        if result.matched_count > 0:
            updated += 1
        else:
            # Insert new record
            await db.hs_codes.insert_one({
                "id": str(uuid.uuid4()),
                "code": code,
                "description": code_data['description'],
                "chapter": code_data['chapter'],
                "duty_rate": code_data['duty_rate'],
                "is_restricted": False,
                "requires_permit": False,
                "notes": "",
                "source": "Bahamas Tariff Schedule 2023"
            })
            inserted += 1
        
        if (updated + inserted) % 100 == 0:
            print(f"Progress: {updated} updated, {inserted} inserted...")
    
    print(f"\nImport complete!")
    print(f"  - Updated: {updated}")
    print(f"  - Inserted: {inserted}")
    print(f"  - Total in database: {await db.hs_codes.count_documents({})}")
    
    # Print sample codes
    print("\nSample codes imported:")
    samples = await db.hs_codes.find({"source": "Bahamas Tariff Schedule 2023"}, {"_id": 0}).limit(10).to_list(10)
    for s in samples:
        print(f"  {s.get('code')}: {s.get('description')[:50]}... - {s.get('duty_rate')}")

if __name__ == "__main__":
    asyncio.run(update_database_with_bahamas_codes())
