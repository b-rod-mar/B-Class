"""
Seed script to populate Bahamas-specific HS codes and CMA regulations
Run with: python seed_data.py
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
import uuid

load_dotenv()

mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'test_database')]

# Bahamas-Specific HS Codes with detailed information
BAHAMAS_HS_CODES = [
    # Chapter 01 - Live Animals
    {"code": "0101.21", "description": "Live horses - Pure-bred breeding animals", "chapter": "01", "section": "I", "duty_rate": "Free", "notes": "Requires import permit from Department of Agriculture", "is_restricted": True, "requires_permit": True},
    {"code": "0102.29", "description": "Live bovine animals - Other than pure-bred", "chapter": "01", "section": "I", "duty_rate": "10%", "notes": "Health certificate required", "is_restricted": True, "requires_permit": True},
    {"code": "0105.11", "description": "Live poultry - Fowls weighing not more than 185g", "chapter": "01", "section": "I", "duty_rate": "10%", "notes": "Subject to veterinary inspection", "is_restricted": False, "requires_permit": True},
    
    # Chapter 02 - Meat and Edible Meat Offal
    {"code": "0201.10", "description": "Meat of bovine animals, fresh or chilled - Carcasses and half-carcasses", "chapter": "02", "section": "I", "duty_rate": "25%", "notes": "Subject to Bahamas Agricultural and Industrial Corporation standards", "is_restricted": False, "requires_permit": False},
    {"code": "0202.30", "description": "Meat of bovine animals, frozen - Boneless", "chapter": "02", "section": "I", "duty_rate": "25%", "notes": "Cold chain documentation required", "is_restricted": False, "requires_permit": False},
    {"code": "0207.14", "description": "Meat of fowls, frozen - Cuts and offal", "chapter": "02", "section": "I", "duty_rate": "35%", "notes": "High duty to protect local poultry industry", "is_restricted": False, "requires_permit": False},
    
    # Chapter 03 - Fish and Crustaceans
    {"code": "0302.11", "description": "Fresh or chilled trout", "chapter": "03", "section": "I", "duty_rate": "20%", "notes": "Requires health certificate from exporting country", "is_restricted": False, "requires_permit": False},
    {"code": "0303.14", "description": "Frozen trout", "chapter": "03", "section": "I", "duty_rate": "20%", "notes": "Temperature monitoring required", "is_restricted": False, "requires_permit": False},
    {"code": "0306.17", "description": "Frozen shrimps and prawns", "chapter": "03", "section": "I", "duty_rate": "25%", "notes": "Subject to size and quality standards", "is_restricted": False, "requires_permit": False},
    {"code": "0307.21", "description": "Live, fresh or chilled scallops", "chapter": "03", "section": "I", "duty_rate": "15%", "notes": "Bahamas marine product", "is_restricted": False, "requires_permit": False},
    
    # Chapter 04 - Dairy Products
    {"code": "0401.10", "description": "Milk and cream, not concentrated - Fat content ≤1%", "chapter": "04", "section": "I", "duty_rate": "5%", "notes": "Refrigeration required", "is_restricted": False, "requires_permit": False},
    {"code": "0402.10", "description": "Milk powder, granules - Fat content ≤1.5%", "chapter": "04", "section": "I", "duty_rate": "10%", "notes": "Must meet Bahamas food standards", "is_restricted": False, "requires_permit": False},
    {"code": "0406.10", "description": "Fresh cheese including whey cheese", "chapter": "04", "section": "I", "duty_rate": "15%", "notes": "Cold storage required", "is_restricted": False, "requires_permit": False},
    
    # Chapter 08 - Edible Fruit and Nuts
    {"code": "0803.10", "description": "Plantains - Fresh or dried", "chapter": "08", "section": "II", "duty_rate": "35%", "notes": "High duty to protect local agriculture", "is_restricted": False, "requires_permit": False},
    {"code": "0804.30", "description": "Pineapples - Fresh or dried", "chapter": "08", "section": "II", "duty_rate": "35%", "notes": "Subject to phytosanitary certificate", "is_restricted": False, "requires_permit": False},
    {"code": "0805.10", "description": "Oranges - Fresh or dried", "chapter": "08", "section": "II", "duty_rate": "25%", "notes": "Citrus inspection required", "is_restricted": False, "requires_permit": False},
    
    # Chapter 17 - Sugars and Sugar Confectionery
    {"code": "1701.13", "description": "Raw cane sugar", "chapter": "17", "section": "IV", "duty_rate": "45%", "notes": "Subject to Bahamas Sugar Corporation regulations", "is_restricted": False, "requires_permit": False},
    {"code": "1704.90", "description": "Sugar confectionery not containing cocoa", "chapter": "17", "section": "IV", "duty_rate": "35%", "notes": "Labeling requirements apply", "is_restricted": False, "requires_permit": False},
    
    # Chapter 22 - Beverages, Spirits and Vinegar
    {"code": "2203.00", "description": "Beer made from malt", "chapter": "22", "section": "IV", "duty_rate": "35%", "bahamas_extension": "10", "notes": "Excise duty $1.50/L applies. Subject to liquor license requirements", "is_restricted": False, "requires_permit": True},
    {"code": "2204.10", "description": "Sparkling wine", "chapter": "22", "section": "IV", "duty_rate": "45%", "bahamas_extension": "00", "notes": "Excise duty $3.50/L applies. Requires liquor import permit", "is_restricted": False, "requires_permit": True},
    {"code": "2204.21", "description": "Wine of fresh grapes in containers ≤2L", "chapter": "22", "section": "IV", "duty_rate": "35%", "bahamas_extension": "10", "notes": "Excise duty $3.50/L. Standard wine import", "is_restricted": False, "requires_permit": True},
    {"code": "2208.20", "description": "Spirits obtained by distilling grape wine or grape marc", "chapter": "22", "section": "IV", "duty_rate": "45%", "bahamas_extension": "00", "notes": "Brandy, Cognac. Excise $20/LPA. Import permit required", "is_restricted": True, "requires_permit": True},
    {"code": "2208.30", "description": "Whiskies", "chapter": "22", "section": "IV", "duty_rate": "45%", "bahamas_extension": "00", "notes": "Scotch, Bourbon, etc. Excise $20/LPA. Import permit required", "is_restricted": True, "requires_permit": True},
    {"code": "2208.40", "description": "Rum and other spirits from fermented sugar cane", "chapter": "22", "section": "IV", "duty_rate": "45%", "bahamas_extension": "00", "notes": "Caribbean rum. Excise $20/LPA. Import permit required", "is_restricted": True, "requires_permit": True},
    {"code": "2208.50", "description": "Gin and Geneva", "chapter": "22", "section": "IV", "duty_rate": "45%", "bahamas_extension": "00", "notes": "Excise $20/LPA. Import permit required", "is_restricted": True, "requires_permit": True},
    {"code": "2208.60", "description": "Vodka", "chapter": "22", "section": "IV", "duty_rate": "45%", "bahamas_extension": "00", "notes": "Excise $20/LPA. Import permit required", "is_restricted": True, "requires_permit": True},
    {"code": "2208.70", "description": "Liqueurs and cordials", "chapter": "22", "section": "IV", "duty_rate": "45%", "bahamas_extension": "00", "notes": "Excise $18/LPA. Import permit required", "is_restricted": True, "requires_permit": True},
    
    # Chapter 27 - Mineral Fuels, Oils
    {"code": "2710.12", "description": "Light petroleum oils and preparations", "chapter": "27", "section": "V", "duty_rate": "10%", "notes": "Gasoline. Subject to Bahamas Petroleum Act", "is_restricted": True, "requires_permit": True},
    {"code": "2710.19", "description": "Other petroleum oils - Diesel, kerosene", "chapter": "27", "section": "V", "duty_rate": "10%", "notes": "Subject to environmental regulations", "is_restricted": True, "requires_permit": True},
    {"code": "2711.21", "description": "Natural gas in gaseous state", "chapter": "27", "section": "V", "duty_rate": "Free", "notes": "Energy sector exemption", "is_restricted": True, "requires_permit": True},
    
    # Chapter 30 - Pharmaceutical Products
    {"code": "3003.90", "description": "Medicaments of mixed products for therapeutic use", "chapter": "30", "section": "VI", "duty_rate": "Free", "notes": "Must be registered with Bahamas National Drug Agency", "is_restricted": True, "requires_permit": True},
    {"code": "3004.90", "description": "Medicaments for retail sale", "chapter": "30", "section": "VI", "duty_rate": "Free", "notes": "Drug registration required. Subject to BNDA approval", "is_restricted": True, "requires_permit": True},
    
    # Chapter 39 - Plastics
    {"code": "3923.10", "description": "Plastic boxes, cases, crates", "chapter": "39", "section": "VII", "duty_rate": "25%", "notes": "Subject to environmental levy on single-use plastics", "is_restricted": False, "requires_permit": False},
    {"code": "3923.21", "description": "Plastic sacks and bags of polymers of ethylene", "chapter": "39", "section": "VII", "duty_rate": "45%", "notes": "Single-use plastic ban may apply. Environmental levy", "is_restricted": True, "requires_permit": False},
    
    # Chapter 61 - Articles of Apparel, Knitted
    {"code": "6109.10", "description": "T-shirts, singlets and other vests, of cotton, knitted", "chapter": "61", "section": "XI", "duty_rate": "35%", "notes": "Textile labeling requirements", "is_restricted": False, "requires_permit": False},
    {"code": "6110.20", "description": "Jerseys, pullovers, cardigans of cotton", "chapter": "61", "section": "XI", "duty_rate": "35%", "notes": "Country of origin labeling required", "is_restricted": False, "requires_permit": False},
    
    # Chapter 62 - Articles of Apparel, Not Knitted
    {"code": "6203.42", "description": "Men's or boys' trousers of cotton", "chapter": "62", "section": "XI", "duty_rate": "35%", "notes": "Textile content labeling required", "is_restricted": False, "requires_permit": False},
    {"code": "6204.62", "description": "Women's or girls' trousers of cotton", "chapter": "62", "section": "XI", "duty_rate": "35%", "notes": "Textile content labeling required", "is_restricted": False, "requires_permit": False},
    
    # Chapter 64 - Footwear
    {"code": "6403.99", "description": "Footwear with outer soles of rubber/plastic, uppers of leather", "chapter": "64", "section": "XII", "duty_rate": "45%", "notes": "High duty on finished footwear", "is_restricted": False, "requires_permit": False},
    {"code": "6404.11", "description": "Sports footwear with rubber/plastic soles and textile uppers", "chapter": "64", "section": "XII", "duty_rate": "45%", "notes": "Athletic shoes, sneakers", "is_restricted": False, "requires_permit": False},
    
    # Chapter 71 - Precious Metals and Stones
    {"code": "7113.19", "description": "Articles of jewelry of precious metal other than silver", "chapter": "71", "section": "XIV", "duty_rate": "35%", "notes": "Gold jewelry. Valuation scrutiny applies", "is_restricted": False, "requires_permit": False},
    {"code": "7117.19", "description": "Imitation jewelry of base metal", "chapter": "71", "section": "XIV", "duty_rate": "35%", "notes": "Costume jewelry", "is_restricted": False, "requires_permit": False},
    
    # Chapter 84 - Machinery and Mechanical Appliances
    {"code": "8415.10", "description": "Air conditioning machines, window or wall types", "chapter": "84", "section": "XVI", "duty_rate": "25%", "notes": "Energy efficiency standards may apply", "is_restricted": False, "requires_permit": False},
    {"code": "8418.10", "description": "Combined refrigerator-freezers", "chapter": "84", "section": "XVI", "duty_rate": "25%", "notes": "Energy rating requirements", "is_restricted": False, "requires_permit": False},
    {"code": "8443.32", "description": "Printers, copying machines, facsimile machines", "chapter": "84", "section": "XVI", "duty_rate": "10%", "notes": "Office equipment - reduced duty", "is_restricted": False, "requires_permit": False},
    {"code": "8471.30", "description": "Portable digital automatic data processing machines ≤10kg", "chapter": "84", "section": "XVI", "duty_rate": "10%", "notes": "Laptops, notebooks. Reduced duty for IT equipment", "is_restricted": False, "requires_permit": False},
    {"code": "8471.41", "description": "Other digital automatic data processing machines", "chapter": "84", "section": "XVI", "duty_rate": "10%", "notes": "Desktop computers", "is_restricted": False, "requires_permit": False},
    
    # Chapter 85 - Electrical Machinery and Equipment
    {"code": "8517.12", "description": "Telephones for cellular networks or wireless networks", "chapter": "85", "section": "XVI", "duty_rate": "10%", "notes": "Mobile phones, smartphones. Subject to URCA regulations", "is_restricted": False, "requires_permit": False},
    {"code": "8517.62", "description": "Machines for reception, conversion and transmission of data", "chapter": "85", "section": "XVI", "duty_rate": "10%", "notes": "Routers, modems, network equipment", "is_restricted": False, "requires_permit": False},
    {"code": "8521.90", "description": "Video recording or reproducing apparatus", "chapter": "85", "section": "XVI", "duty_rate": "35%", "notes": "DVD players, streaming devices", "is_restricted": False, "requires_permit": False},
    {"code": "8528.72", "description": "Reception apparatus for television, color", "chapter": "85", "section": "XVI", "duty_rate": "35%", "notes": "Televisions, monitors", "is_restricted": False, "requires_permit": False},
    
    # Chapter 87 - Vehicles
    {"code": "8703.21", "description": "Motor cars with spark-ignition engine ≤1000cc", "chapter": "87", "section": "XVII", "duty_rate": "65%", "notes": "Small vehicles. High import duty. Age restrictions apply", "is_restricted": False, "requires_permit": False},
    {"code": "8703.22", "description": "Motor cars with spark-ignition engine 1000-1500cc", "chapter": "87", "section": "XVII", "duty_rate": "65%", "notes": "Compact vehicles. Road worthiness certificate required", "is_restricted": False, "requires_permit": False},
    {"code": "8703.23", "description": "Motor cars with spark-ignition engine 1500-3000cc", "chapter": "87", "section": "XVII", "duty_rate": "75%", "notes": "Standard vehicles. Age limit and inspection required", "is_restricted": False, "requires_permit": False},
    {"code": "8703.24", "description": "Motor cars with spark-ignition engine >3000cc", "chapter": "87", "section": "XVII", "duty_rate": "85%", "notes": "Large/luxury vehicles. Highest duty bracket", "is_restricted": False, "requires_permit": False},
    {"code": "8703.80", "description": "Motor vehicles with electric motor for propulsion", "chapter": "87", "section": "XVII", "duty_rate": "25%", "notes": "Electric vehicles - reduced duty incentive", "is_restricted": False, "requires_permit": False},
    {"code": "8711.20", "description": "Motorcycles with reciprocating engine 50-250cc", "chapter": "87", "section": "XVII", "duty_rate": "45%", "notes": "Standard motorcycles", "is_restricted": False, "requires_permit": False},
    
    # Chapter 94 - Furniture
    {"code": "9401.61", "description": "Seats with wooden frames, upholstered", "chapter": "94", "section": "XX", "duty_rate": "35%", "notes": "Furniture import", "is_restricted": False, "requires_permit": False},
    {"code": "9403.10", "description": "Metal furniture for offices", "chapter": "94", "section": "XX", "duty_rate": "25%", "notes": "Office furniture - reduced duty", "is_restricted": False, "requires_permit": False},
    {"code": "9403.50", "description": "Wooden furniture for bedrooms", "chapter": "94", "section": "XX", "duty_rate": "35%", "notes": "Bedroom sets, beds, dressers", "is_restricted": False, "requires_permit": False},
    
    # Chapter 95 - Toys, Games, Sports Equipment
    {"code": "9503.00", "description": "Tricycles, scooters, pedal cars and similar wheeled toys", "chapter": "95", "section": "XX", "duty_rate": "35%", "notes": "Children's toys. Safety standards apply", "is_restricted": False, "requires_permit": False},
    {"code": "9504.50", "description": "Video game consoles and machines", "chapter": "95", "section": "XX", "duty_rate": "35%", "notes": "Gaming systems", "is_restricted": False, "requires_permit": False},
    {"code": "9506.62", "description": "Inflatable balls", "chapter": "95", "section": "XX", "duty_rate": "25%", "notes": "Sports equipment", "is_restricted": False, "requires_permit": False},
]

# Bahamas Customs Management Act & Regulations Reference
CMA_REGULATIONS = [
    # Part I - Preliminary
    {
        "category": "Preliminary Provisions",
        "section": "Part I",
        "title": "Short Title and Commencement",
        "reference": "Section 1",
        "content": "This Act may be cited as the Customs Management Act. The Act applies to all goods imported into or exported from The Bahamas and governs all customs procedures, duties, and enforcement.",
        "keywords": ["customs", "act", "commencement", "application", "scope"]
    },
    {
        "category": "Preliminary Provisions",
        "section": "Part I",
        "title": "Interpretation and Definitions",
        "reference": "Section 2",
        "content": "Key definitions under the CMA include: 'customs duties' means import duty, export duty, excise duty, and any other duties collected by customs; 'goods' includes all kinds of articles, wares, merchandise, and livestock; 'importer' means any person who imports goods or on whose behalf goods are imported; 'proper officer' means the Comptroller or any officer acting under their authority.",
        "keywords": ["definitions", "interpretation", "customs duties", "goods", "importer", "proper officer", "comptroller"]
    },
    
    # Part II - Administration
    {
        "category": "Administration",
        "section": "Part II",
        "title": "Comptroller of Customs",
        "reference": "Section 3",
        "content": "The Comptroller of Customs is responsible for the administration of customs laws in The Bahamas. The Comptroller has authority over all customs officers and is responsible for the collection of duties, prevention of smuggling, and enforcement of trade laws. The Comptroller reports to the Ministry of Finance.",
        "keywords": ["comptroller", "administration", "authority", "customs officers", "ministry of finance"]
    },
    {
        "category": "Administration",
        "section": "Part II",
        "title": "Customs Officers and Powers",
        "reference": "Section 4-7",
        "content": "Customs officers have the power to: examine all goods imported or to be exported; board and search vessels, aircraft, and vehicles; detain goods suspected of being improperly imported; require production of documents; arrest persons suspected of customs offenses. Officers must carry identification and produce it upon request.",
        "keywords": ["officers", "powers", "search", "examination", "arrest", "detention", "documents"]
    },
    
    # Part III - Importation
    {
        "category": "Importation",
        "section": "Part III",
        "title": "Entry of Goods",
        "reference": "Section 15-20",
        "content": "All goods imported into The Bahamas must be entered at a customs port. The importer must submit a customs declaration (Form C78) within 14 days of arrival. The declaration must include: description of goods, quantity, value (CIF), country of origin, and applicable tariff classification (HS code). Failure to enter goods properly is an offense.",
        "keywords": ["entry", "declaration", "C78", "import", "customs port", "14 days", "tariff classification"]
    },
    {
        "category": "Importation",
        "section": "Part III",
        "title": "Customs Valuation",
        "reference": "Section 21-25",
        "content": "The customs value of imported goods is the transaction value - the price actually paid or payable when sold for export to The Bahamas, adjusted for: cost of transport and insurance (CIF), commissions, royalties, and license fees. If transaction value cannot be determined, alternative methods apply: identical goods, similar goods, deductive value, computed value, or fall-back method.",
        "keywords": ["valuation", "CIF", "transaction value", "price", "insurance", "freight", "royalties"]
    },
    {
        "category": "Importation",
        "section": "Part III",
        "title": "Prohibited and Restricted Imports",
        "reference": "Section 30-35",
        "content": "Certain goods are prohibited from import into The Bahamas including: counterfeit currency, obscene materials, dangerous drugs (without license), certain weapons. Restricted goods requiring permits include: firearms and ammunition (Police permit), pharmaceuticals (BNDA approval), live animals (Agriculture permit), plants (Phytosanitary certificate), alcohol (Liquor license).",
        "keywords": ["prohibited", "restricted", "permit", "license", "firearms", "drugs", "alcohol", "animals"]
    },
    
    # Part IV - Duties
    {
        "category": "Duties and Rates",
        "section": "Part IV",
        "title": "Import Duty Rates",
        "reference": "Section 40-45",
        "content": "Import duties are levied on goods based on their tariff classification. The Bahamas uses the Harmonized System (HS) for classification. Duty rates vary from 0% (exempt items) to 85% (luxury vehicles). Most consumer goods attract 35-45% duty. Essential items like medicine and certain foods may be duty-free. The current tariff schedule is available from the Customs Department.",
        "keywords": ["duty rates", "tariff", "HS code", "percentage", "exempt", "schedule"]
    },
    {
        "category": "Duties and Rates",
        "section": "Part IV",
        "title": "Excise Duties",
        "reference": "Section 46-50",
        "content": "Excise duties apply to specific goods in addition to import duty. Alcohol: Beer $1.50/L, Wine $3.50/L, Spirits $20.00 per liter of pure alcohol (LPA). Tobacco: cigarettes $180/1000 sticks, cigars 45% ad valorem. Petroleum products are subject to fuel excise. Excise is calculated separately and added to the duty payable.",
        "keywords": ["excise", "alcohol", "tobacco", "petroleum", "fuel", "spirits", "beer", "wine", "LPA"]
    },
    {
        "category": "Duties and Rates",
        "section": "Part IV",
        "title": "Value Added Tax (VAT)",
        "reference": "Section 51-55",
        "content": "Value Added Tax (VAT) of 10% is charged on imported goods. The VAT is calculated on the total of: CIF value + Import Duty + Excise Duty. VAT registration is required for businesses with turnover exceeding $100,000. Certain essential items are zero-rated or exempt from VAT including basic food items and medical supplies.",
        "keywords": ["VAT", "value added tax", "10%", "registration", "zero-rated", "exempt", "threshold"]
    },
    
    # Part V - Exemptions
    {
        "category": "Exemptions and Reliefs",
        "section": "Part V",
        "title": "Duty Exemptions",
        "reference": "Section 60-70",
        "content": "Duty exemptions may be granted for: diplomatic imports, goods for government use, educational materials, religious articles, goods imported under trade agreements (CARICOM), hotel development supplies (approved projects), manufacturing inputs (approved industries), returning residents' personal effects (within limits).",
        "keywords": ["exemption", "duty-free", "diplomatic", "CARICOM", "hotel", "manufacturing", "returning residents"]
    },
    {
        "category": "Exemptions and Reliefs",
        "section": "Part V",
        "title": "Personal Effects Allowance",
        "reference": "Section 71-75",
        "content": "Returning residents may import personal effects duty-free subject to: minimum 6 months absence, goods for personal use only, maximum value limits apply. Tourists may bring in: $500 worth of goods duty-free, 1L of spirits or 2L of wine, 200 cigarettes or 50 cigars. Commercial quantities are not permitted under personal allowance.",
        "keywords": ["personal effects", "returning resident", "tourist allowance", "duty-free allowance", "6 months"]
    },
    
    # Part VI - ASYCUDA and Procedures
    {
        "category": "Procedures",
        "section": "Part VI",
        "title": "ASYCUDA World System",
        "reference": "Section 80-85",
        "content": "The Bahamas uses ASYCUDA World (Automated System for Customs Data) for processing customs declarations. All commercial importers must register for ASYCUDA access. Electronic declarations are mandatory for commercial shipments. The system calculates duties automatically based on HS code, value, and applicable rates. Payment can be made electronically through approved banks.",
        "keywords": ["ASYCUDA", "electronic", "declaration", "registration", "automated", "payment"]
    },
    {
        "category": "Procedures",
        "section": "Part VI",
        "title": "Customs Brokers",
        "reference": "Section 86-90",
        "content": "Customs brokers must be licensed by the Comptroller. Requirements include: Bahamian citizenship or permanent residency, completion of customs broker examination, payment of annual license fee, posting of bond. Brokers act as agents for importers and are responsible for accurate declarations. Misconduct may result in license revocation.",
        "keywords": ["customs broker", "license", "examination", "agent", "bond", "requirements"]
    },
    
    # Part VII - Penalties and Offenses
    {
        "category": "Enforcement",
        "section": "Part VII",
        "title": "Customs Offenses",
        "reference": "Section 100-110",
        "content": "Customs offenses include: smuggling (importing/exporting without declaration), making false declarations, undervaluation of goods, misclassification to evade duty, removal of goods without duty payment, obstruction of customs officers. Penalties range from fines to imprisonment depending on severity.",
        "keywords": ["offenses", "smuggling", "false declaration", "undervaluation", "penalties", "fines", "imprisonment"]
    },
    {
        "category": "Enforcement",
        "section": "Part VII",
        "title": "Penalties and Forfeitures",
        "reference": "Section 111-120",
        "content": "Penalties for customs offenses: False declaration - fine up to $50,000 or 3x duty evaded. Smuggling - fine up to $100,000 and/or 5 years imprisonment. Goods may be forfeited to the Crown. Vehicles used in smuggling may be seized. Officers may compound offenses for payment in lieu of prosecution for minor infractions.",
        "keywords": ["penalties", "forfeiture", "fine", "imprisonment", "seizure", "compound"]
    },
    
    # Part VIII - Appeals
    {
        "category": "Appeals",
        "section": "Part VIII",
        "title": "Dispute Resolution and Appeals",
        "reference": "Section 130-140",
        "content": "Importers may dispute customs assessments through: Administrative review by the Comptroller (within 30 days), Appeal to the Revenue Appeals Commission (within 60 days of Comptroller's decision), Appeal to the Supreme Court (on points of law). During appeals, disputed duties must be paid or secured by bond. Refunds are available if appeals are successful.",
        "keywords": ["appeal", "dispute", "review", "Revenue Appeals Commission", "Supreme Court", "refund", "30 days"]
    },
    
    # Additional Regulations
    {
        "category": "Special Provisions",
        "section": "Regulations",
        "title": "Temporary Importation",
        "reference": "Customs Regulations Section 40",
        "content": "Temporary importation is permitted for: exhibition goods, professional equipment, containers, goods for repair or processing. A bond equal to duties payable must be posted. Goods must be re-exported within 12 months. Failure to re-export results in forfeiture of bond and duty payment.",
        "keywords": ["temporary import", "bond", "exhibition", "re-export", "12 months", "professional equipment"]
    },
    {
        "category": "Special Provisions",
        "section": "Regulations",
        "title": "Bonded Warehouses",
        "reference": "Customs Regulations Section 50",
        "content": "Bonded warehouses allow storage of imported goods without immediate duty payment. Warehouse operators must be licensed and post bond. Goods may remain in bond for up to 2 years. Duties become payable upon release for consumption. Goods may be re-exported from bond without duty payment. Warehouses are subject to customs inspection.",
        "keywords": ["bonded warehouse", "storage", "license", "2 years", "duty deferral", "inspection"]
    },
    {
        "category": "Special Provisions",
        "section": "Regulations",
        "title": "Free Trade Zone",
        "reference": "Customs Regulations Section 60",
        "content": "The Grand Bahama Free Trade Zone provides duty exemptions for: goods imported for re-export, manufacturing inputs, goods consumed within the zone. Companies must be licensed to operate in the zone. Special provisions apply for services, employment, and goods sold to the domestic market.",
        "keywords": ["free trade zone", "Grand Bahama", "FTZ", "re-export", "manufacturing", "duty exemption"]
    },
    {
        "category": "Trade Agreements",
        "section": "International",
        "title": "CARICOM Trade",
        "reference": "Treaty of Chaguaramas",
        "content": "The Bahamas is a member of CARICOM (Caribbean Community). Goods of CARICOM origin may qualify for duty-free or reduced-duty treatment. Requirements: goods must be 'wholly produced' or meet minimum local content rules, accompanied by CARICOM Certificate of Origin, shipped directly from CARICOM member state. Common External Tariff (CET) applies to non-CARICOM goods.",
        "keywords": ["CARICOM", "Caribbean", "certificate of origin", "duty-free", "trade agreement", "CET"]
    },
]

async def seed_hs_codes():
    """Seed the HS codes collection"""
    print("Seeding Bahamas HS Codes...")
    
    # Clear existing codes
    await db.hs_codes.delete_many({})
    
    # Insert new codes
    for code in BAHAMAS_HS_CODES:
        code_doc = {
            "id": str(uuid.uuid4()),
            **code,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": None,
            "created_by": "system"
        }
        await db.hs_codes.insert_one(code_doc)
    
    print(f"Seeded {len(BAHAMAS_HS_CODES)} HS codes")

async def seed_cma_regulations():
    """Seed the CMA regulations collection"""
    print("Seeding CMA Regulations...")
    
    # Clear existing regulations
    await db.cma_regulations.delete_many({})
    
    # Insert new regulations
    for reg in CMA_REGULATIONS:
        reg_doc = {
            "id": str(uuid.uuid4()),
            **reg,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.cma_regulations.insert_one(reg_doc)
    
    print(f"Seeded {len(CMA_REGULATIONS)} CMA regulations")

async def main():
    print("Starting database seeding...")
    await seed_hs_codes()
    await seed_cma_regulations()
    print("Database seeding complete!")
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
