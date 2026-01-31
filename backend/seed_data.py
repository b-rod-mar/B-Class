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

# Bahamas Customs Forms
CUSTOMS_FORMS = [
    # Import Forms
    {"form_number": "C78", "form_name": "Customs Declaration Form", "category": "Import", "description": "Primary import declaration form for all goods entering The Bahamas", "usage": "Required for all commercial and personal imports. Must be completed within 14 days of arrival.", "where_to_obtain": "Customs Department, ASYCUDA World", "related_section": "Section 15-20"},
    {"form_number": "C79", "form_name": "Bill of Entry", "category": "Import", "description": "Detailed entry document for imported goods", "usage": "Used to formally enter goods for consumption, warehousing, or transit", "where_to_obtain": "Customs broker or ASYCUDA", "related_section": "Section 15"},
    {"form_number": "C13", "form_name": "Delivery Order", "category": "Import", "description": "Authorization to release goods from customs control", "usage": "Issued after duty payment to allow goods collection", "where_to_obtain": "Customs Department after duty payment", "related_section": "Section 20"},
    {"form_number": "C63", "form_name": "Single Administrative Document (SAD)", "category": "Import", "description": "Standardized customs declaration for ASYCUDA World", "usage": "Electronic declaration format for commercial imports", "where_to_obtain": "ASYCUDA World system", "related_section": "Section 80"},
    {"form_number": "C88", "form_name": "Inward Report", "category": "Import", "description": "Vessel/aircraft arrival report", "usage": "Filed by carrier upon arrival with cargo manifest", "where_to_obtain": "Customs Department", "related_section": "Section 10"},
    
    # Export Forms
    {"form_number": "C82", "form_name": "Export Declaration", "category": "Export", "description": "Declaration for goods being exported from The Bahamas", "usage": "Required for all commercial exports", "where_to_obtain": "Customs Department, ASYCUDA", "related_section": "Section 25"},
    {"form_number": "C84", "form_name": "Outward Report", "category": "Export", "description": "Vessel/aircraft departure report", "usage": "Filed by carrier before departure", "where_to_obtain": "Customs Department", "related_section": "Section 12"},
    
    # Transit & Warehousing
    {"form_number": "C100", "form_name": "Transit Declaration", "category": "Transit", "description": "For goods transiting through The Bahamas", "usage": "Goods moving through without entering commerce", "where_to_obtain": "Customs Department", "related_section": "Section 35"},
    {"form_number": "C105", "form_name": "Warehouse Entry", "category": "Warehousing", "description": "Entry of goods into bonded warehouse", "usage": "For duty deferral in licensed bonded warehouses", "where_to_obtain": "Customs Department", "related_section": "Regulations Section 50"},
    {"form_number": "C106", "form_name": "Warehouse Withdrawal", "category": "Warehousing", "description": "Removal of goods from bonded warehouse", "usage": "Required when releasing goods for consumption or re-export", "where_to_obtain": "Customs Department", "related_section": "Regulations Section 50"},
    
    # Special Purpose Forms
    {"form_number": "C110", "form_name": "Temporary Import Declaration", "category": "Special", "description": "For goods temporarily imported", "usage": "Exhibition goods, professional equipment requiring re-export", "where_to_obtain": "Customs Department", "related_section": "Regulations Section 40"},
    {"form_number": "C115", "form_name": "ATA Carnet", "category": "Special", "description": "International temporary admission document", "usage": "Professional equipment, samples, exhibition goods", "where_to_obtain": "Chamber of Commerce", "related_section": "International conventions"},
    {"form_number": "C120", "form_name": "Duty Exemption Application", "category": "Exemptions", "description": "Application for duty relief or exemption", "usage": "Hotel developers, manufacturers, approved industries", "where_to_obtain": "Ministry of Finance", "related_section": "Section 60-70"},
    {"form_number": "C125", "form_name": "Returning Resident Declaration", "category": "Exemptions", "description": "Personal effects declaration for returning residents", "usage": "Bahamians returning after extended absence (6+ months)", "where_to_obtain": "Customs Department at port of entry", "related_section": "Section 71-75"},
    
    # Permits & Licenses
    {"form_number": "C200", "form_name": "Import Permit Application", "category": "Permits", "description": "Application for restricted goods import permit", "usage": "Firearms, pharmaceuticals, controlled substances", "where_to_obtain": "Relevant ministry/department", "related_section": "Section 30-35"},
    {"form_number": "C205", "form_name": "Liquor Import License", "category": "Permits", "description": "License to import alcoholic beverages", "usage": "Commercial alcohol importers", "where_to_obtain": "Licensing Authority", "related_section": "Liquor License Act"},
    {"form_number": "C210", "form_name": "Firearms Import Permit", "category": "Permits", "description": "Police permit for firearms import", "usage": "Personal and commercial firearms", "where_to_obtain": "Royal Bahamas Police Force", "related_section": "Firearms Act"},
    
    # Payment & Bonds
    {"form_number": "C300", "form_name": "Duty Payment Voucher", "category": "Payment", "description": "Receipt for customs duties paid", "usage": "Proof of payment for release of goods", "where_to_obtain": "Customs cashier", "related_section": "Section 40"},
    {"form_number": "C305", "form_name": "Bond Application", "category": "Payment", "description": "Application for customs bond", "usage": "Securing duties for temporary import, transit, or warehouse", "where_to_obtain": "Customs Department", "related_section": "Regulations Section 40"},
    {"form_number": "C310", "form_name": "Refund Application", "category": "Payment", "description": "Application for duty refund", "usage": "Overpayment, re-export, or successful appeal", "where_to_obtain": "Customs Department", "related_section": "Section 130"},
    
    # Appeals & Disputes
    {"form_number": "C400", "form_name": "Administrative Review Request", "category": "Appeals", "description": "Request for review of customs decision", "usage": "First level appeal to Comptroller", "where_to_obtain": "Customs Department", "related_section": "Section 130"},
    {"form_number": "C405", "form_name": "Appeal to Revenue Commission", "category": "Appeals", "description": "Formal appeal against customs assessment", "usage": "Second level appeal after Comptroller review", "where_to_obtain": "Revenue Appeals Commission", "related_section": "Section 135"},
    
    # Certificates
    {"form_number": "C500", "form_name": "Certificate of Origin", "category": "Certificates", "description": "Document certifying country of origin", "usage": "Required for preferential duty treatment", "where_to_obtain": "Bahamas Chamber of Commerce", "related_section": "Trade agreements"},
    {"form_number": "C505", "form_name": "CARICOM Certificate of Origin", "category": "Certificates", "description": "Origin certificate for CARICOM trade", "usage": "Duty-free treatment under CARICOM treaty", "where_to_obtain": "Chamber of Commerce", "related_section": "Treaty of Chaguaramas"},
]

# Country Codes (ISO 3166-1)
COUNTRY_CODES = [
    # Caribbean (CARICOM)
    {"code": "BS", "alpha3": "BHS", "name": "Bahamas", "region": "Caribbean", "trade_agreement": "CARICOM", "notes": "Domestic - no import duty"},
    {"code": "BB", "alpha3": "BRB", "name": "Barbados", "region": "Caribbean", "trade_agreement": "CARICOM", "notes": "CARICOM preferential rates apply"},
    {"code": "JM", "alpha3": "JAM", "name": "Jamaica", "region": "Caribbean", "trade_agreement": "CARICOM", "notes": "CARICOM preferential rates apply"},
    {"code": "TT", "alpha3": "TTO", "name": "Trinidad and Tobago", "region": "Caribbean", "trade_agreement": "CARICOM", "notes": "CARICOM preferential rates apply"},
    {"code": "GY", "alpha3": "GUY", "name": "Guyana", "region": "Caribbean", "trade_agreement": "CARICOM", "notes": "CARICOM preferential rates apply"},
    {"code": "SR", "alpha3": "SUR", "name": "Suriname", "region": "Caribbean", "trade_agreement": "CARICOM", "notes": "CARICOM preferential rates apply"},
    {"code": "BZ", "alpha3": "BLZ", "name": "Belize", "region": "Caribbean", "trade_agreement": "CARICOM", "notes": "CARICOM preferential rates apply"},
    {"code": "HT", "alpha3": "HTI", "name": "Haiti", "region": "Caribbean", "trade_agreement": "CARICOM", "notes": "CARICOM preferential rates apply"},
    {"code": "AG", "alpha3": "ATG", "name": "Antigua and Barbuda", "region": "Caribbean", "trade_agreement": "CARICOM", "notes": "CARICOM preferential rates apply"},
    {"code": "DM", "alpha3": "DMA", "name": "Dominica", "region": "Caribbean", "trade_agreement": "CARICOM", "notes": "CARICOM preferential rates apply"},
    {"code": "GD", "alpha3": "GRD", "name": "Grenada", "region": "Caribbean", "trade_agreement": "CARICOM", "notes": "CARICOM preferential rates apply"},
    {"code": "KN", "alpha3": "KNA", "name": "Saint Kitts and Nevis", "region": "Caribbean", "trade_agreement": "CARICOM", "notes": "CARICOM preferential rates apply"},
    {"code": "LC", "alpha3": "LCA", "name": "Saint Lucia", "region": "Caribbean", "trade_agreement": "CARICOM", "notes": "CARICOM preferential rates apply"},
    {"code": "VC", "alpha3": "VCT", "name": "Saint Vincent and the Grenadines", "region": "Caribbean", "trade_agreement": "CARICOM", "notes": "CARICOM preferential rates apply"},
    {"code": "CU", "alpha3": "CUB", "name": "Cuba", "region": "Caribbean", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"code": "DO", "alpha3": "DOM", "name": "Dominican Republic", "region": "Caribbean", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"code": "PR", "alpha3": "PRI", "name": "Puerto Rico", "region": "Caribbean", "trade_agreement": None, "notes": "US Territory - standard rates"},
    {"code": "VI", "alpha3": "VIR", "name": "US Virgin Islands", "region": "Caribbean", "trade_agreement": None, "notes": "US Territory - standard rates"},
    {"code": "TC", "alpha3": "TCA", "name": "Turks and Caicos Islands", "region": "Caribbean", "trade_agreement": None, "notes": "UK Territory - standard rates"},
    {"code": "KY", "alpha3": "CYM", "name": "Cayman Islands", "region": "Caribbean", "trade_agreement": None, "notes": "UK Territory - standard rates"},
    
    # North America
    {"code": "US", "alpha3": "USA", "name": "United States", "region": "North America", "trade_agreement": None, "notes": "Major trading partner - standard rates"},
    {"code": "CA", "alpha3": "CAN", "name": "Canada", "region": "North America", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"code": "MX", "alpha3": "MEX", "name": "Mexico", "region": "North America", "trade_agreement": None, "notes": "Standard duty rates apply"},
    
    # Central America
    {"code": "PA", "alpha3": "PAN", "name": "Panama", "region": "Central America", "trade_agreement": None, "notes": "Free trade zone country"},
    {"code": "CR", "alpha3": "CRI", "name": "Costa Rica", "region": "Central America", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"code": "GT", "alpha3": "GTM", "name": "Guatemala", "region": "Central America", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"code": "HN", "alpha3": "HND", "name": "Honduras", "region": "Central America", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"code": "NI", "alpha3": "NIC", "name": "Nicaragua", "region": "Central America", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"code": "SV", "alpha3": "SLV", "name": "El Salvador", "region": "Central America", "trade_agreement": None, "notes": "Standard duty rates apply"},
    
    # South America
    {"code": "BR", "alpha3": "BRA", "name": "Brazil", "region": "South America", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"code": "AR", "alpha3": "ARG", "name": "Argentina", "region": "South America", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"code": "CO", "alpha3": "COL", "name": "Colombia", "region": "South America", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"code": "CL", "alpha3": "CHL", "name": "Chile", "region": "South America", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"code": "PE", "alpha3": "PER", "name": "Peru", "region": "South America", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"code": "EC", "alpha3": "ECU", "name": "Ecuador", "region": "South America", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"code": "VE", "alpha3": "VEN", "name": "Venezuela", "region": "South America", "trade_agreement": None, "notes": "Standard duty rates apply"},
    
    # Europe
    {"code": "GB", "alpha3": "GBR", "name": "United Kingdom", "region": "Europe", "trade_agreement": None, "notes": "Commonwealth member - standard rates"},
    {"code": "DE", "alpha3": "DEU", "name": "Germany", "region": "Europe", "trade_agreement": None, "notes": "Major EU trading partner"},
    {"code": "FR", "alpha3": "FRA", "name": "France", "region": "Europe", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"code": "IT", "alpha3": "ITA", "name": "Italy", "region": "Europe", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"code": "ES", "alpha3": "ESP", "name": "Spain", "region": "Europe", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"code": "NL", "alpha3": "NLD", "name": "Netherlands", "region": "Europe", "trade_agreement": None, "notes": "Major port - transit goods"},
    {"code": "BE", "alpha3": "BEL", "name": "Belgium", "region": "Europe", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"code": "CH", "alpha3": "CHE", "name": "Switzerland", "region": "Europe", "trade_agreement": None, "notes": "Luxury goods source"},
    {"code": "IE", "alpha3": "IRL", "name": "Ireland", "region": "Europe", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"code": "PT", "alpha3": "PRT", "name": "Portugal", "region": "Europe", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"code": "SE", "alpha3": "SWE", "name": "Sweden", "region": "Europe", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"code": "NO", "alpha3": "NOR", "name": "Norway", "region": "Europe", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"code": "DK", "alpha3": "DNK", "name": "Denmark", "region": "Europe", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"code": "PL", "alpha3": "POL", "name": "Poland", "region": "Europe", "trade_agreement": None, "notes": "Standard duty rates apply"},
    
    # Asia
    {"code": "CN", "alpha3": "CHN", "name": "China", "region": "Asia", "trade_agreement": None, "notes": "Major import source - standard rates"},
    {"code": "JP", "alpha3": "JPN", "name": "Japan", "region": "Asia", "trade_agreement": None, "notes": "Electronics and vehicles source"},
    {"code": "KR", "alpha3": "KOR", "name": "South Korea", "region": "Asia", "trade_agreement": None, "notes": "Electronics and vehicles source"},
    {"code": "TW", "alpha3": "TWN", "name": "Taiwan", "region": "Asia", "trade_agreement": None, "notes": "Electronics manufacturing"},
    {"code": "HK", "alpha3": "HKG", "name": "Hong Kong", "region": "Asia", "trade_agreement": None, "notes": "Major transit hub"},
    {"code": "SG", "alpha3": "SGP", "name": "Singapore", "region": "Asia", "trade_agreement": None, "notes": "Major transit hub"},
    {"code": "TH", "alpha3": "THA", "name": "Thailand", "region": "Asia", "trade_agreement": None, "notes": "Manufacturing source"},
    {"code": "VN", "alpha3": "VNM", "name": "Vietnam", "region": "Asia", "trade_agreement": None, "notes": "Textiles and manufacturing"},
    {"code": "MY", "alpha3": "MYS", "name": "Malaysia", "region": "Asia", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"code": "ID", "alpha3": "IDN", "name": "Indonesia", "region": "Asia", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"code": "PH", "alpha3": "PHL", "name": "Philippines", "region": "Asia", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"code": "IN", "alpha3": "IND", "name": "India", "region": "Asia", "trade_agreement": None, "notes": "Commonwealth member"},
    {"code": "BD", "alpha3": "BGD", "name": "Bangladesh", "region": "Asia", "trade_agreement": None, "notes": "Textiles source"},
    {"code": "PK", "alpha3": "PAK", "name": "Pakistan", "region": "Asia", "trade_agreement": None, "notes": "Textiles source"},
    
    # Middle East
    {"code": "AE", "alpha3": "ARE", "name": "United Arab Emirates", "region": "Middle East", "trade_agreement": None, "notes": "Dubai - major transit hub"},
    {"code": "SA", "alpha3": "SAU", "name": "Saudi Arabia", "region": "Middle East", "trade_agreement": None, "notes": "Petroleum source"},
    {"code": "IL", "alpha3": "ISR", "name": "Israel", "region": "Middle East", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"code": "TR", "alpha3": "TUR", "name": "Turkey", "region": "Middle East", "trade_agreement": None, "notes": "Standard duty rates apply"},
    
    # Africa
    {"code": "ZA", "alpha3": "ZAF", "name": "South Africa", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"code": "NG", "alpha3": "NGA", "name": "Nigeria", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"code": "EG", "alpha3": "EGY", "name": "Egypt", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"code": "KE", "alpha3": "KEN", "name": "Kenya", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"code": "MA", "alpha3": "MAR", "name": "Morocco", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    
    # Oceania
    {"code": "AU", "alpha3": "AUS", "name": "Australia", "region": "Oceania", "trade_agreement": None, "notes": "Commonwealth member"},
    {"code": "NZ", "alpha3": "NZL", "name": "New Zealand", "region": "Oceania", "trade_agreement": None, "notes": "Commonwealth member"},
]

async def seed_customs_forms():
    """Seed the customs forms collection"""
    print("Seeding Customs Forms...")
    
    await db.customs_forms.delete_many({})
    
    for form in CUSTOMS_FORMS:
        form_doc = {
            "id": str(uuid.uuid4()),
            **form
        }
        await db.customs_forms.insert_one(form_doc)
    
    print(f"Seeded {len(CUSTOMS_FORMS)} customs forms")

async def seed_country_codes():
    """Seed the country codes collection"""
    print("Seeding Country Codes...")
    
    await db.country_codes.delete_many({})
    
    for country in COUNTRY_CODES:
        country_doc = {
            "id": str(uuid.uuid4()),
            **country
        }
        await db.country_codes.insert_one(country_doc)
    
    print(f"Seeded {len(COUNTRY_CODES)} country codes")

async def main():
    print("Starting database seeding...")
    await seed_hs_codes()
    await seed_cma_regulations()
    await seed_customs_forms()
    await seed_country_codes()
    print("Database seeding complete!")
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
