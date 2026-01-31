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
    
    # Part VI - Electronic Single Window and Procedures
    {
        "category": "Procedures",
        "section": "Part VI",
        "title": "Electronic Single Window System",
        "reference": "Section 80-85",
        "content": "The Bahamas uses the Electronic Single Window (ESW) for processing customs declarations. All commercial importers must register for ESW access. Electronic declarations are mandatory for commercial shipments. The system calculates duties automatically based on HS code, value, and applicable rates. Payment can be made electronically through approved banks.",
        "keywords": ["Electronic Single Window", "ESW", "electronic", "declaration", "registration", "automated", "payment"]
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
    {
        "category": "Special Provisions",
        "section": "Hawksbill Creek Agreement",
        "title": "The Hawksbill Creek Agreement - Overview",
        "reference": "Hawksbill Creek Agreement Act, Chapter 261",
        "content": "The Hawksbill Creek Agreement is a landmark 1955 treaty between the Government of The Bahamas and the Grand Bahama Port Authority Ltd. (GBPA) that established the Freeport area on Grand Bahama Island. Named after Hawksbill Creek, a body of water in the area, this agreement created one of the world's largest free trade zones and transformed Grand Bahama from a sparsely populated island into a major commercial and industrial center.",
        "keywords": ["Hawksbill Creek", "Grand Bahama", "GBPA", "Port Authority", "Freeport", "free trade zone", "1955", "treaty"]
    },
    {
        "category": "Special Provisions",
        "section": "Hawksbill Creek Agreement",
        "title": "Historical Background",
        "reference": "Hawksbill Creek Agreement Act, Chapter 261",
        "content": "In 1955, American financier Wallace Groves negotiated the agreement with the Bahamian colonial government (then under British rule). The original agreement granted the Port Authority the right to develop a 50,000-acre area with significant tax concessions for 99 years (until 2054). The agreement has been amended multiple times, most notably in 1960 (extending the bonded area) and 1993 (redefining certain provisions after Bahamian independence in 1973). The agreement survived independence and remains in effect, though subject to ongoing negotiations between the Government and the Port Authority.",
        "keywords": ["Wallace Groves", "1955", "colonial", "99 years", "2054", "1960", "1993", "independence", "history"]
    },
    {
        "category": "Special Provisions",
        "section": "Hawksbill Creek Agreement",
        "title": "Duty and Tax Exemptions Under Hawksbill Creek",
        "reference": "Hawksbill Creek Agreement Act, Sections 6-10",
        "content": "Licensees operating within the Port Area enjoy significant tax benefits including: (1) No customs duties on goods imported for use within the Port Area or for re-export, (2) No real property taxes until 2054, (3) No business license fees for manufacturing, (4) No personal income tax (applies to all Bahamas), (5) No capital gains tax. To qualify, businesses must obtain a license from the Grand Bahama Port Authority. Goods consumed domestically (outside the Port Area) remain subject to normal customs duties. The C14 Entry Form is used for goods imported under Hawksbill Creek provisions.",
        "keywords": ["duty exemption", "tax exemption", "property tax", "license", "C14", "Port Area", "re-export", "manufacturing"]
    },
    {
        "category": "Special Provisions",
        "section": "Hawksbill Creek Agreement",
        "title": "Implications for Importers and Businesses",
        "reference": "Hawksbill Creek Agreement Act, Sections 11-15",
        "content": "For customs brokers and importers, the Hawksbill Creek Agreement means: (1) Different entry procedures (Form C14) apply for goods destined for Freeport, (2) Goods may enter the Port Area duty-free but become dutiable if transferred to Nassau or other islands, (3) Proof of consumption within the Port Area may be required for audit purposes, (4) Port Authority license verification is required for duty-free treatment, (5) Disputes over Hawksbill Creek provisions are handled through specific channels involving the Port Authority. Brokers should verify their client's licensee status before claiming duty exemptions.",
        "keywords": ["importer", "broker", "C14", "licensee", "transfer", "audit", "verification", "dispute", "entry procedures"]
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

# Bahamas Customs Forms (Complete Official List)
CUSTOMS_FORMS = [
    # Attendance & Reporting Forms
    {"form_number": "C1", "form_name": "Attendance Request", "category": "Reporting", "description": "Request for customs officer attendance", "usage": "To request customs attendance for examination or supervision of goods", "where_to_obtain": "Customs Department", "related_section": "Section 8"},
    {"form_number": "C2", "form_name": "Report Inwards of Vessels", "category": "Reporting", "description": "Arrival report for commercial vessels", "usage": "Filed by ship master upon arrival in Bahamas waters", "where_to_obtain": "Customs Department at port", "related_section": "Section 10"},
    {"form_number": "C2A", "form_name": "Inward Report - Pleasure Vessels", "category": "Reporting", "description": "Arrival report for private pleasure vessels", "usage": "Required for all private boats entering Bahamas", "where_to_obtain": "Customs at any official port of entry", "related_section": "Section 10"},
    {"form_number": "C3", "form_name": "Parcels List", "category": "Reporting", "description": "List of parcels on board vessel", "usage": "Accompanies vessel cargo manifest", "where_to_obtain": "Customs Department", "related_section": "Section 10"},
    {"form_number": "C4", "form_name": "Vessel Passenger List", "category": "Reporting", "description": "List of passengers on vessel", "usage": "Required for all arriving vessels with passengers", "where_to_obtain": "Customs Department", "related_section": "Section 10"},
    {"form_number": "C5", "form_name": "Declaration of Consumable Stores on Board the Vessel", "category": "Reporting", "description": "Declaration of ship stores", "usage": "Required for duty-free stores on board", "where_to_obtain": "Customs Department", "related_section": "Section 10"},
    {"form_number": "C5A", "form_name": "Declaration of Consumable Stores on Board Aircraft", "category": "Reporting", "description": "Declaration of aircraft stores", "usage": "Required for duty-free stores on aircraft", "where_to_obtain": "Customs Department at airport", "related_section": "Section 10"},
    {"form_number": "C6", "form_name": "Declaration of Dutiable Goods in Possession of Crew", "category": "Reporting", "description": "Crew personal effects declaration", "usage": "For dutiable goods held by crew members", "where_to_obtain": "Customs Department", "related_section": "Section 10"},
    
    # Aircraft Forms
    {"form_number": "C7", "form_name": "Aircraft General Declaration", "category": "Aircraft", "description": "General arrival/departure declaration for aircraft", "usage": "Required for all commercial aircraft", "where_to_obtain": "Customs Department at airport", "related_section": "Section 10"},
    {"form_number": "C7A", "form_name": "Inward Declaration for Private Aircraft", "category": "Aircraft", "description": "Inward declaration and cruising permit for private aircraft", "usage": "Private aircraft entering The Bahamas", "where_to_obtain": "Customs at airport of entry", "related_section": "Section 10"},
    {"form_number": "C7B", "form_name": "Outward General Declaration for Private Aircraft", "category": "Aircraft", "description": "Departure declaration for private aircraft", "usage": "Private aircraft departing The Bahamas", "where_to_obtain": "Customs Department", "related_section": "Section 12"},
    {"form_number": "C8", "form_name": "Aircraft Cargo Manifest", "category": "Aircraft", "description": "Cargo manifest for aircraft", "usage": "List of all cargo on board aircraft", "where_to_obtain": "Customs Department", "related_section": "Section 10"},
    {"form_number": "C9", "form_name": "Aircraft Passenger Manifest", "category": "Aircraft", "description": "Passenger list for aircraft", "usage": "Required for all arriving aircraft", "where_to_obtain": "Customs Department", "related_section": "Section 10"},
    
    # Import Entry Forms
    {"form_number": "C10", "form_name": "Application to Amend Inward Report/Outward Manifest", "category": "Import", "description": "Amendment request for vessel reports", "usage": "To correct errors in submitted reports", "where_to_obtain": "Customs Department", "related_section": "Section 15"},
    {"form_number": "C11", "form_name": "Application to Proceed to Sufferance Wharf", "category": "Import", "description": "Permission to unload at unapproved location", "usage": "When goods must be landed at non-designated place", "where_to_obtain": "Customs Department", "related_section": "Section 15"},
    {"form_number": "C12", "form_name": "Landing Certificate", "category": "Import", "description": "Certificate confirming goods landed", "usage": "Proof of landing for customs purposes", "where_to_obtain": "Customs Department", "related_section": "Section 15"},
    {"form_number": "C13", "form_name": "Home Consumption Entry", "category": "Import", "description": "Primary import entry for goods entering Bahamas commerce", "usage": "Required for all goods cleared for domestic consumption", "where_to_obtain": "Customs Department, Electronic Single Window", "related_section": "Section 15-20"},
    {"form_number": "C14", "form_name": "Entry for Goods Under Hawksbill Creek Agreement", "category": "Import", "description": "Entry for Freeport duty-free imports", "usage": "Goods imported conditionally free under Hawksbill Creek", "where_to_obtain": "Grand Bahama Port Authority/Customs", "related_section": "Hawksbill Creek Act"},
    {"form_number": "C14A", "form_name": "Declaration by Purchaser - Over the Counter Sale", "category": "Import", "description": "Purchaser declaration for bonded goods sale", "usage": "When purchasing bonded goods", "where_to_obtain": "Licensed bonded warehouse", "related_section": "Section 50"},
    {"form_number": "C14B", "form_name": "Declaration by Vendor - Over the Counter Sale", "category": "Import", "description": "Vendor declaration for bonded goods sale", "usage": "When selling bonded goods", "where_to_obtain": "Licensed bonded warehouse", "related_section": "Section 50"},
    {"form_number": "C15", "form_name": "Bill of Sight (Provisional Entry)", "category": "Import", "description": "Provisional entry when full details unavailable", "usage": "When importer cannot provide complete information", "where_to_obtain": "Customs Department", "related_section": "Section 15"},
    
    # Warehousing Forms
    {"form_number": "C16", "form_name": "Warehousing Entry", "category": "Warehousing", "description": "Entry of goods into bonded warehouse", "usage": "For duty deferral in licensed bonded warehouses", "where_to_obtain": "Customs Department", "related_section": "Section 50"},
    {"form_number": "C20", "form_name": "Application for Bonded Warehouse Appointment", "category": "Warehousing", "description": "Application to license a building as bonded warehouse", "usage": "For warehouse operators seeking license", "where_to_obtain": "Customs Department", "related_section": "Section 50"},
    {"form_number": "C21", "form_name": "Bonded Warehouse Keeper's Licence", "category": "Warehousing", "description": "License to operate bonded warehouse", "usage": "Issued to approved warehouse operators", "where_to_obtain": "Customs Department", "related_section": "Section 50"},
    {"form_number": "C22", "form_name": "Request to Repack Warehoused Goods", "category": "Warehousing", "description": "Permission to repackage goods in warehouse", "usage": "When goods need repacking in bond", "where_to_obtain": "Customs Department", "related_section": "Section 50"},
    {"form_number": "C23", "form_name": "Notice of Transfer of Ownership of Warehoused Goods", "category": "Warehousing", "description": "Transfer of ownership notification", "usage": "When warehoused goods change ownership", "where_to_obtain": "Customs Department", "related_section": "Section 50"},
    {"form_number": "C24", "form_name": "Ex-Warehousing Home Consumption Entry", "category": "Warehousing", "description": "Removal from warehouse for domestic consumption", "usage": "When releasing goods from bond for local use", "where_to_obtain": "Customs Department", "related_section": "Section 50"},
    {"form_number": "C25", "form_name": "Ex-Warehouse Export Entry", "category": "Warehousing", "description": "Removal from warehouse for export or stores", "usage": "For re-export or ship stores", "where_to_obtain": "Customs Department", "related_section": "Section 50"},
    {"form_number": "C26", "form_name": "Ex-Warehouse Removal Entry", "category": "Warehousing", "description": "Transfer between bonded warehouses", "usage": "Moving goods between licensed warehouses", "where_to_obtain": "Customs Department", "related_section": "Section 50"},
    {"form_number": "C27", "form_name": "Re-Warehousing Entry", "category": "Warehousing", "description": "Return of goods to warehouse", "usage": "When goods are returned to bond", "where_to_obtain": "Customs Department", "related_section": "Section 50"},
    
    # Baggage Forms
    {"form_number": "C17", "form_name": "Accompanied Baggage Declaration", "category": "Baggage", "description": "Declaration for personal baggage arriving with traveler", "usage": "All travelers entering The Bahamas", "where_to_obtain": "Customs at port of entry", "related_section": "Section 71-75"},
    {"form_number": "C18", "form_name": "Unaccompanied Baggage Declaration", "category": "Baggage", "description": "Declaration for baggage arriving separately", "usage": "Personal effects shipped separately", "where_to_obtain": "Customs Department", "related_section": "Section 71-75"},
    {"form_number": "C18A", "form_name": "Courier Unaccompanied Baggage Declaration", "category": "Baggage", "description": "Courier shipment of personal baggage", "usage": "Personal items shipped via courier", "where_to_obtain": "Customs Department", "related_section": "Section 71-75"},
    {"form_number": "C19", "form_name": "Application for Release of Perishable Goods", "category": "Import", "description": "Early release of perishable or urgent goods", "usage": "When goods cannot await normal processing", "where_to_obtain": "Customs Department", "related_section": "Section 20"},
    
    # Export Forms
    {"form_number": "C28", "form_name": "Entry Outwards of Vessels", "category": "Export", "description": "Vessel departure report", "usage": "Required before commercial vessel departure", "where_to_obtain": "Customs Department", "related_section": "Section 12"},
    {"form_number": "C28A", "form_name": "Entry Outwards for Pleasure Vessels", "category": "Export", "description": "Departure report for pleasure vessels", "usage": "Required before private vessel departure", "where_to_obtain": "Customs at port of departure", "related_section": "Section 12"},
    {"form_number": "C29", "form_name": "Export Entry for Domestic Goods", "category": "Export", "description": "Export declaration for Bahamas-origin goods", "usage": "All exports of domestic goods", "where_to_obtain": "Customs Department", "related_section": "Section 25"},
    {"form_number": "C30", "form_name": "Re-Export Entry for Imported Goods", "category": "Export", "description": "Re-export of previously imported goods", "usage": "Goods imported then exported", "where_to_obtain": "Customs Department", "related_section": "Section 25"},
    {"form_number": "C31", "form_name": "Application to Load Goods Prior to Entry", "category": "Export", "description": "Permission to load before entry cleared", "usage": "Urgent export situations", "where_to_obtain": "Customs Department", "related_section": "Section 25"},
    {"form_number": "C32", "form_name": "Application to Reload Goods Unloaded in Error", "category": "Export", "description": "Correction of erroneous unloading", "usage": "When goods unloaded by mistake", "where_to_obtain": "Customs Department", "related_section": "Section 25"},
    {"form_number": "C33", "form_name": "Application to Load Duty Paid or Free Stores", "category": "Export", "description": "Loading of ship stores", "usage": "Provisioning vessels", "where_to_obtain": "Customs Department", "related_section": "Section 25"},
    {"form_number": "C34", "form_name": "Application to Transfer Stores of Aircraft or Vessel", "category": "Export", "description": "Transfer of stores between vessels/aircraft", "usage": "Inter-carrier store transfers", "where_to_obtain": "Customs Department", "related_section": "Section 25"},
    
    # Transit & Transshipment Forms
    {"form_number": "C35", "form_name": "Transhipment Entry", "category": "Transit", "description": "Entry for goods passing through Bahamas", "usage": "Goods transiting without entering commerce", "where_to_obtain": "Customs Department", "related_section": "Section 35"},
    {"form_number": "C36", "form_name": "Certificate of Clearance of Vessels", "category": "Transit", "description": "Clearance certificate for commercial vessels", "usage": "Issued upon completion of customs formalities", "where_to_obtain": "Customs Department", "related_section": "Section 12"},
    {"form_number": "C36A", "form_name": "Certificate of Clearance for Pleasure Vessels", "category": "Transit", "description": "Clearance certificate for pleasure vessels", "usage": "Issued to cleared pleasure vessels", "where_to_obtain": "Customs Department", "related_section": "Section 12"},
    {"form_number": "C37", "form_name": "Outward Manifest of Vessel", "category": "Transit", "description": "Cargo manifest for departing vessel", "usage": "List of all cargo being exported", "where_to_obtain": "Customs Department", "related_section": "Section 12"},
    {"form_number": "C38", "form_name": "Transire", "category": "Transit", "description": "Coastwise goods movement permit", "usage": "Goods moving between Bahamas islands by sea", "where_to_obtain": "Customs Department", "related_section": "Section 38"},
    {"form_number": "C38A", "form_name": "Transire for Movement of Goods Over Land", "category": "Transit", "description": "Land movement of goods under bond", "usage": "Inter-island goods movement by road", "where_to_obtain": "Customs Department", "related_section": "Section 38"},
    {"form_number": "C39", "form_name": "Temporary Cruising Permit", "category": "Transit", "description": "Permit for vessels cruising Bahamas waters", "usage": "Pleasure vessels cruising between islands", "where_to_obtain": "Customs at port of entry", "related_section": "Section 39"},
    
    # Temporary Import Forms
    {"form_number": "C40", "form_name": "Export Certificate for Goods Intended for Re-Importation", "category": "Temporary", "description": "Certificate for goods temporarily exported", "usage": "Equipment or goods for return to Bahamas", "where_to_obtain": "Customs Department", "related_section": "Section 40"},
    {"form_number": "C41", "form_name": "Request to Import Goods for Temporary Use", "category": "Temporary", "description": "Temporary import application", "usage": "Exhibition goods, professional equipment", "where_to_obtain": "Customs Department", "related_section": "Section 40"},
    {"form_number": "C42", "form_name": "Temporary Import Permit for Motor Vehicles/Vessels", "category": "Temporary", "description": "Temporary permit for vehicles and boats", "usage": "Motor cars, motorcycles, pleasure vessels", "where_to_obtain": "Customs Department", "related_section": "Section 40"},
    
    # Valuation Forms
    {"form_number": "C43", "form_name": "Declaration of Value for Customs Purposes", "category": "Valuation", "description": "Customs value declaration", "usage": "To be attached to all import entries", "where_to_obtain": "Customs Department", "related_section": "Section 43"},
    {"form_number": "C44", "form_name": "Standing Authority for Signing Declaration of Value", "category": "Valuation", "description": "Authorization for value declaration signing", "usage": "Authorized persons to sign on behalf of company", "where_to_obtain": "Customs Department", "related_section": "Section 44"},
    {"form_number": "C45", "form_name": "Application to Make a Simplified Declaration of Value", "category": "Valuation", "description": "Simplified valuation for regular importers", "usage": "Authorized importers with established relationships", "where_to_obtain": "Customs Department", "related_section": "Section 45"},
    
    # Drawback & Refund Forms
    {"form_number": "C46", "form_name": "Export Entry for Drawback Goods", "category": "Refunds", "description": "Export entry for duty drawback claim", "usage": "When exporting goods on which duty was paid", "where_to_obtain": "Customs Department", "related_section": "Section 46"},
    {"form_number": "C47", "form_name": "Drawback Claim", "category": "Refunds", "description": "Application for duty drawback", "usage": "Claim refund of duty on re-exported goods", "where_to_obtain": "Customs Department", "related_section": "Section 47"},
    {"form_number": "C48", "form_name": "Miscellaneous Refunds Claim", "category": "Refunds", "description": "General refund application", "usage": "Overpayments and other refund claims", "where_to_obtain": "Customs Department", "related_section": "Section 48"},
    {"form_number": "C49", "form_name": "Claim for Remission/Refund on Lost, Destroyed or Pillaged Goods", "category": "Refunds", "description": "Refund claim for lost goods", "usage": "Regulation 101 claims", "where_to_obtain": "Customs Department", "related_section": "Regulation 101"},
    {"form_number": "C50", "form_name": "Claim for Rebate/Refund on Damaged Goods", "category": "Refunds", "description": "Refund claim for damaged goods", "usage": "Regulation 102 claims", "where_to_obtain": "Customs Department", "related_section": "Regulation 102"},
    
    # Enforcement Forms
    {"form_number": "C51", "form_name": "Notice of Seizure", "category": "Enforcement", "description": "Official seizure notification", "usage": "Issued when goods are seized by Customs", "where_to_obtain": "Customs Department", "related_section": "Section 51"},
    {"form_number": "C52", "form_name": "Request for Compounding of An Offence", "category": "Enforcement", "description": "Settlement request for customs offence", "usage": "Alternative to prosecution for minor offences", "where_to_obtain": "Customs Department", "related_section": "Section 52"},
    
    # Licenses & Permits
    {"form_number": "C53", "form_name": "Customs Broker's Licence", "category": "Licensing", "description": "License to act as customs broker", "usage": "For licensed customs broker operations", "where_to_obtain": "Customs Department", "related_section": "Section 86-90"},
    {"form_number": "C54", "form_name": "Application for Payment of Proceeds of Sale", "category": "Licensing", "description": "Request for sale proceeds", "usage": "After goods sold at customs auction", "where_to_obtain": "Customs Department", "related_section": "Section 54"},
    {"form_number": "C55", "form_name": "Application to Import Chemical Substances", "category": "Permits", "description": "Permit for restricted chemical imports", "usage": "Chemical Precursors and Substances Order 1992", "where_to_obtain": "Customs Department", "related_section": "Chemical Precursors Order"},
    {"form_number": "C56", "form_name": "Application to Export Chemical Substances", "category": "Permits", "description": "Permit for restricted chemical exports", "usage": "Chemical Precursors and Substances Order 1992", "where_to_obtain": "Customs Department", "related_section": "Chemical Precursors Order"},
    {"form_number": "C57", "form_name": "Authorized Economic Operator (AEO) Licence", "category": "Licensing", "description": "AEO program license", "usage": "For trusted trader status", "where_to_obtain": "Customs Department", "related_section": "AEO Program"},
    
    # Advance Ruling & Rules of Origin
    {"form_number": "C58", "form_name": "Application for Advance Ruling", "category": "Ruling", "description": "Request for binding classification ruling", "usage": "Pre-import HS code determination", "where_to_obtain": "Customs Department", "related_section": "Section 58"},
    {"form_number": "C59", "form_name": "Rules of Origin Invoice Declaration", "category": "Origin", "description": "Origin declaration on invoice", "usage": "Annex IV to Fourth Schedule", "where_to_obtain": "Exporter", "related_section": "Fourth Schedule"},
    {"form_number": "C60", "form_name": "Rules of Origin Exporter's Declaration", "category": "Origin", "description": "Exporter's origin declaration", "usage": "Preferential origin certification", "where_to_obtain": "Exporter", "related_section": "Fourth Schedule"},
    {"form_number": "C61", "form_name": "Supplier's Declaration for Preferential Origin Status", "category": "Origin", "description": "Supplier's preferential origin declaration", "usage": "Annex V A to Fourth Schedule", "where_to_obtain": "Supplier", "related_section": "Fourth Schedule"},
    {"form_number": "C62", "form_name": "Supplier's Declaration for Non-Preferential Origin", "category": "Origin", "description": "Non-preferential origin declaration", "usage": "Annex V A to Fourth Schedule", "where_to_obtain": "Supplier", "related_section": "Fourth Schedule"},
    {"form_number": "C63", "form_name": "Rules of Origin Information Certificate", "category": "Origin", "description": "Origin information certificate", "usage": "Supporting documentation for origin", "where_to_obtain": "Customs Department/Chamber of Commerce", "related_section": "Fourth Schedule"},
    {"form_number": "C64", "form_name": "Rules of Origin Request for Verification", "category": "Origin", "description": "Verification request for origin claims", "usage": "Customs verification process", "where_to_obtain": "Customs Department", "related_section": "Fourth Schedule"},
    {"form_number": "C65", "form_name": "Rules of Origin Application for Derogation", "category": "Origin", "description": "Request for origin rule exemption", "usage": "Exceptional circumstances", "where_to_obtain": "Customs Department", "related_section": "Fourth Schedule"},
    
    # Intellectual Property Forms
    {"form_number": "C66", "form_name": "IPR Application for Action by Customs Authority", "category": "IPR", "description": "Application for intellectual property protection", "usage": "Right-holders seeking customs enforcement", "where_to_obtain": "Customs Department", "related_section": "IPR Enforcement"},
    {"form_number": "C66A", "form_name": "IPR Information on Status of Applicant", "category": "IPR", "description": "Applicant status information", "usage": "Supporting C66 application", "where_to_obtain": "Customs Department", "related_section": "IPR Enforcement"},
    {"form_number": "C66B", "form_name": "IPR Applicant Type of Rights", "category": "IPR", "description": "Details of intellectual property rights", "usage": "Trademark, copyright, patent details", "where_to_obtain": "Customs Department", "related_section": "IPR Enforcement"},
    {"form_number": "C66C", "form_name": "IPR Information on Essential Dates of Authentic Goods", "category": "IPR", "description": "Authentic goods information", "usage": "Help identify counterfeit goods", "where_to_obtain": "Customs Department", "related_section": "IPR Enforcement"},
    {"form_number": "C66D", "form_name": "IPR Information on Type or Pattern of Fraud", "category": "IPR", "description": "Fraud pattern information", "usage": "Intelligence on counterfeiting methods", "where_to_obtain": "Customs Department", "related_section": "IPR Enforcement"},
    {"form_number": "C66E", "form_name": "IPR Request for Extension of Validity Period", "category": "IPR", "description": "IPR protection extension request", "usage": "Extend customs enforcement period", "where_to_obtain": "Customs Department", "related_section": "IPR Enforcement"},
    {"form_number": "C66F", "form_name": "IPR Any Other Information from Right-Holder", "category": "IPR", "description": "Additional IPR information", "usage": "Supplementary information", "where_to_obtain": "Right-holder", "related_section": "IPR Enforcement"},
    {"form_number": "C67", "form_name": "IPR Notice of Suspected Infringement", "category": "IPR", "description": "Notification of suspected counterfeit goods", "usage": "Customs notifying right-holder", "where_to_obtain": "Customs Department", "related_section": "IPR Enforcement"},
    {"form_number": "C68", "form_name": "IPR Right-Holder's Declaration", "category": "IPR", "description": "Right-holder confirmation declaration", "usage": "Confirming goods are infringing", "where_to_obtain": "Right-holder", "related_section": "IPR Enforcement"},
    
    # Adjustment & Courier Forms
    {"form_number": "C69", "form_name": "Adjustment Request", "category": "Adjustment", "description": "Request to adjust customs entry", "usage": "Post-clearance amendments", "where_to_obtain": "Customs Department", "related_section": "Section 69"},
    {"form_number": "C70", "form_name": "Detailed Adjustment Statement", "category": "Adjustment", "description": "Detailed statement for adjustments", "usage": "Supporting C69 requests", "where_to_obtain": "Customs Department", "related_section": "Section 70"},
    {"form_number": "C71", "form_name": "Authorized Courier Licence", "category": "Licensing", "description": "License for courier operations", "usage": "Express courier service operators", "where_to_obtain": "Customs Department", "related_section": "Courier Regulations"},
    {"form_number": "C72", "form_name": "Application for Courier Warehouse", "category": "Licensing", "description": "Courier warehouse license application", "usage": "For courier facility approval", "where_to_obtain": "Customs Department", "related_section": "Courier Regulations"},
    
    # Bond Forms
    {"form_number": "CB1", "form_name": "Bond for Delivery of Perishable Goods", "category": "Bonds", "description": "Security bond for early release", "usage": "Securing release of perishables", "where_to_obtain": "Customs Department", "related_section": "Bond Regulations"},
    {"form_number": "CB2", "form_name": "General Bond for a Bonded Warehouse", "category": "Bonds", "description": "Warehouse operator's bond", "usage": "Securing warehouse operations", "where_to_obtain": "Customs Department", "related_section": "Bond Regulations"},
    {"form_number": "CB3", "form_name": "Bond for Movement of Goods", "category": "Bonds", "description": "Transit security bond", "usage": "Goods moving under bond", "where_to_obtain": "Customs Department", "related_section": "Bond Regulations"},
    {"form_number": "CB4", "form_name": "Bond for the Shipment of Stores", "category": "Bonds", "description": "Ship stores security bond", "usage": "Duty-free stores shipment", "where_to_obtain": "Customs Department", "related_section": "Bond Regulations"},
    {"form_number": "CB5", "form_name": "Bond for Exportation", "category": "Bonds", "description": "Export security bond", "usage": "Goods exported under bond", "where_to_obtain": "Customs Department", "related_section": "Bond Regulations"},
    {"form_number": "CB6", "form_name": "Trans-Shipment Bond", "category": "Bonds", "description": "Transshipment security bond", "usage": "Goods in transit through Bahamas", "where_to_obtain": "Customs Department", "related_section": "Bond Regulations"},
    {"form_number": "CB6A", "form_name": "Industrial Encouragement Act Bond", "category": "Bonds", "description": "Bond for industrial incentives", "usage": "Manufacturing enterprises", "where_to_obtain": "Customs Department", "related_section": "Industrial Encouragement Act"},
    {"form_number": "CB7", "form_name": "Bond for Re-Exportation of Temporary Imports", "category": "Bonds", "description": "Temporary import security", "usage": "Ensuring re-export of temp imports", "where_to_obtain": "Customs Department", "related_section": "Bond Regulations"},
    {"form_number": "CB8", "form_name": "Bond for Customs Brokers", "category": "Bonds", "description": "Customs broker's bond", "usage": "Licensed customs broker operations", "where_to_obtain": "Customs Department", "related_section": "Section 86-90"},
    {"form_number": "CB9", "form_name": "Bond for Security of Duty on Imported Goods", "category": "Bonds", "description": "Duty security bond", "usage": "Securing duty payment", "where_to_obtain": "Customs Department", "related_section": "Bond Regulations"},
    {"form_number": "CB10", "form_name": "General Bond for Security of Customs Revenue", "category": "Bonds", "description": "General revenue security bond", "usage": "Comprehensive customs security", "where_to_obtain": "Customs Department", "related_section": "Bond Regulations"},
    {"form_number": "CB10A", "form_name": "Spirits and Beer Manufacturing Act Bond", "category": "Bonds", "description": "Alcohol manufacturing bond", "usage": "Licensed alcohol producers", "where_to_obtain": "Customs Department", "related_section": "Spirits and Beer Act"},
    {"form_number": "CB11", "form_name": "Bond for Authorized Economic Operator", "category": "Bonds", "description": "AEO security bond", "usage": "AEO program participants", "where_to_obtain": "Customs Department", "related_section": "AEO Program"},
    {"form_number": "CB12", "form_name": "Bond for Right-Holders of Intellectual Property", "category": "Bonds", "description": "IPR holder's bond", "usage": "IPR enforcement security", "where_to_obtain": "Customs Department", "related_section": "IPR Enforcement"},
    {"form_number": "CB13", "form_name": "Bond for Authorized Courier", "category": "Bonds", "description": "Courier operator's bond", "usage": "Licensed courier operations", "where_to_obtain": "Customs Department", "related_section": "Courier Regulations"},
    
    # Health Declaration
    {"form_number": "MDH", "form_name": "Maritime Declaration of Health", "category": "Health", "description": "Health declaration for arriving vessels", "usage": "Required for all arriving vessels", "where_to_obtain": "Port Health Authority", "related_section": "International Health Regulations"},
]

# Country Codes - Official Bahamas Customs Numeric Codes (16.02.2021)
COUNTRY_CODES = [
    # A
    {"customs_code": "004", "code": "AF", "name": "Afghanistan", "region": "Asia", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "248", "code": "AX", "name": "Aland Islands", "region": "Europe", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "008", "code": "AL", "name": "Albania", "region": "Europe", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "012", "code": "DZ", "name": "Algeria", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "016", "code": "AS", "name": "American Samoa", "region": "Oceania", "trade_agreement": None, "notes": "US Territory"},
    {"customs_code": "020", "code": "AD", "name": "Andorra", "region": "Europe", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "024", "code": "AO", "name": "Angola", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "660", "code": "AI", "name": "Anguilla", "region": "Caribbean", "trade_agreement": None, "notes": "UK Territory"},
    {"customs_code": "028", "code": "AG", "name": "Antigua and Barbuda", "region": "Caribbean", "trade_agreement": "CARICOM", "notes": "CARICOM preferential rates apply"},
    {"customs_code": "032", "code": "AR", "name": "Argentina", "region": "South America", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "051", "code": "AM", "name": "Armenia", "region": "Asia", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "533", "code": "AW", "name": "Aruba", "region": "Caribbean", "trade_agreement": None, "notes": "Netherlands Territory"},
    {"customs_code": "036", "code": "AU", "name": "Australia", "region": "Oceania", "trade_agreement": None, "notes": "Commonwealth member"},
    {"customs_code": "040", "code": "AT", "name": "Austria", "region": "Europe", "trade_agreement": None, "notes": "EU member"},
    {"customs_code": "031", "code": "AZ", "name": "Azerbaijan", "region": "Asia", "trade_agreement": None, "notes": "Standard duty rates apply"},
    
    # B
    {"customs_code": "044", "code": "BS", "name": "Bahamas", "region": "Caribbean", "trade_agreement": "CARICOM", "notes": "Domestic - no import duty"},
    {"customs_code": "048", "code": "BH", "name": "Bahrain", "region": "Middle East", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "050", "code": "BD", "name": "Bangladesh", "region": "Asia", "trade_agreement": None, "notes": "Textiles source"},
    {"customs_code": "052", "code": "BB", "name": "Barbados", "region": "Caribbean", "trade_agreement": "CARICOM", "notes": "CARICOM preferential rates apply"},
    {"customs_code": "112", "code": "BY", "name": "Belarus", "region": "Europe", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "056", "code": "BE", "name": "Belgium", "region": "Europe", "trade_agreement": None, "notes": "EU member - major port"},
    {"customs_code": "084", "code": "BZ", "name": "Belize", "region": "Caribbean", "trade_agreement": "CARICOM", "notes": "CARICOM preferential rates apply"},
    {"customs_code": "204", "code": "BJ", "name": "Benin", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "060", "code": "BM", "name": "Bermuda", "region": "Caribbean", "trade_agreement": None, "notes": "UK Territory"},
    {"customs_code": "064", "code": "BT", "name": "Bhutan", "region": "Asia", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "068", "code": "BO", "name": "Bolivia", "region": "South America", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "535", "code": "BQ", "name": "Bonaire, Saint Eustatius and Saba", "region": "Caribbean", "trade_agreement": None, "notes": "Netherlands Territory"},
    {"customs_code": "070", "code": "BA", "name": "Bosnia and Herzegovina", "region": "Europe", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "072", "code": "BW", "name": "Botswana", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "076", "code": "BR", "name": "Brazil", "region": "South America", "trade_agreement": None, "notes": "Major trading partner"},
    {"customs_code": "092", "code": "VG", "name": "British Virgin Islands", "region": "Caribbean", "trade_agreement": None, "notes": "UK Territory"},
    {"customs_code": "096", "code": "BN", "name": "Brunei Darussalam", "region": "Asia", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "100", "code": "BG", "name": "Bulgaria", "region": "Europe", "trade_agreement": None, "notes": "EU member"},
    {"customs_code": "854", "code": "BF", "name": "Burkina Faso", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "108", "code": "BI", "name": "Burundi", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    
    # C
    {"customs_code": "116", "code": "KH", "name": "Cambodia", "region": "Asia", "trade_agreement": None, "notes": "Textiles manufacturing"},
    {"customs_code": "120", "code": "CM", "name": "Cameroon", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "124", "code": "CA", "name": "Canada", "region": "North America", "trade_agreement": None, "notes": "Major trading partner"},
    {"customs_code": "132", "code": "CV", "name": "Cape Verde", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "136", "code": "KY", "name": "Cayman Islands", "region": "Caribbean", "trade_agreement": None, "notes": "UK Territory"},
    {"customs_code": "140", "code": "CF", "name": "Central African Republic", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "148", "code": "TD", "name": "Chad", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "830", "code": "GG", "name": "Channel Islands", "region": "Europe", "trade_agreement": None, "notes": "UK Territory"},
    {"customs_code": "152", "code": "CL", "name": "Chile", "region": "South America", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "156", "code": "CN", "name": "China", "region": "Asia", "trade_agreement": None, "notes": "Major import source"},
    {"customs_code": "344", "code": "HK", "name": "China, Hong Kong", "region": "Asia", "trade_agreement": None, "notes": "Major transit hub"},
    {"customs_code": "446", "code": "MO", "name": "China, Macao", "region": "Asia", "trade_agreement": None, "notes": "Special Administrative Region"},
    {"customs_code": "170", "code": "CO", "name": "Colombia", "region": "South America", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "174", "code": "KM", "name": "Comoros", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "178", "code": "CG", "name": "Congo", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "184", "code": "CK", "name": "Cook Islands", "region": "Oceania", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "188", "code": "CR", "name": "Costa Rica", "region": "Central America", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "384", "code": "CI", "name": "Côte d'Ivoire", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "191", "code": "HR", "name": "Croatia", "region": "Europe", "trade_agreement": None, "notes": "EU member"},
    {"customs_code": "192", "code": "CU", "name": "Cuba", "region": "Caribbean", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "531", "code": "CW", "name": "Curaçao", "region": "Caribbean", "trade_agreement": None, "notes": "Netherlands Territory"},
    {"customs_code": "196", "code": "CY", "name": "Cyprus", "region": "Europe", "trade_agreement": None, "notes": "EU member"},
    {"customs_code": "203", "code": "CZ", "name": "Czech Republic", "region": "Europe", "trade_agreement": None, "notes": "EU member"},
    
    # D
    {"customs_code": "408", "code": "KP", "name": "Democratic People's Republic of Korea", "region": "Asia", "trade_agreement": None, "notes": "Restricted - sanctions may apply"},
    {"customs_code": "180", "code": "CD", "name": "Democratic Republic of the Congo", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "208", "code": "DK", "name": "Denmark", "region": "Europe", "trade_agreement": None, "notes": "EU member"},
    {"customs_code": "262", "code": "DJ", "name": "Djibouti", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "212", "code": "DM", "name": "Dominica", "region": "Caribbean", "trade_agreement": "CARICOM", "notes": "CARICOM preferential rates apply"},
    {"customs_code": "214", "code": "DO", "name": "Dominican Republic", "region": "Caribbean", "trade_agreement": None, "notes": "Standard duty rates apply"},
    
    # E
    {"customs_code": "218", "code": "EC", "name": "Ecuador", "region": "South America", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "818", "code": "EG", "name": "Egypt", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "222", "code": "SV", "name": "El Salvador", "region": "Central America", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "226", "code": "GQ", "name": "Equatorial Guinea", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "232", "code": "ER", "name": "Eritrea", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "233", "code": "EE", "name": "Estonia", "region": "Europe", "trade_agreement": None, "notes": "EU member"},
    {"customs_code": "231", "code": "ET", "name": "Ethiopia", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    
    # F
    {"customs_code": "234", "code": "FO", "name": "Faeroe Islands", "region": "Europe", "trade_agreement": None, "notes": "Danish Territory"},
    {"customs_code": "238", "code": "FK", "name": "Falkland Islands (Malvinas)", "region": "South America", "trade_agreement": None, "notes": "UK Territory"},
    {"customs_code": "242", "code": "FJ", "name": "Fiji", "region": "Oceania", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "246", "code": "FI", "name": "Finland", "region": "Europe", "trade_agreement": None, "notes": "EU member"},
    {"customs_code": "250", "code": "FR", "name": "France", "region": "Europe", "trade_agreement": None, "notes": "EU member"},
    {"customs_code": "252", "code": "GF", "name": "French Guiana", "region": "South America", "trade_agreement": None, "notes": "French Territory"},
    {"customs_code": "258", "code": "PF", "name": "French Polynesia", "region": "Oceania", "trade_agreement": None, "notes": "French Territory"},
    
    # G
    {"customs_code": "266", "code": "GA", "name": "Gabon", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "270", "code": "GM", "name": "Gambia", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "268", "code": "GE", "name": "Georgia", "region": "Asia", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "276", "code": "DE", "name": "Germany", "region": "Europe", "trade_agreement": None, "notes": "Major EU trading partner"},
    {"customs_code": "288", "code": "GH", "name": "Ghana", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "292", "code": "GI", "name": "Gibraltar", "region": "Europe", "trade_agreement": None, "notes": "UK Territory"},
    {"customs_code": "300", "code": "GR", "name": "Greece", "region": "Europe", "trade_agreement": None, "notes": "EU member"},
    {"customs_code": "304", "code": "GL", "name": "Greenland", "region": "North America", "trade_agreement": None, "notes": "Danish Territory"},
    {"customs_code": "308", "code": "GD", "name": "Grenada", "region": "Caribbean", "trade_agreement": "CARICOM", "notes": "CARICOM preferential rates apply"},
    {"customs_code": "312", "code": "GP", "name": "Guadeloupe", "region": "Caribbean", "trade_agreement": None, "notes": "French Territory"},
    {"customs_code": "316", "code": "GU", "name": "Guam", "region": "Oceania", "trade_agreement": None, "notes": "US Territory"},
    {"customs_code": "320", "code": "GT", "name": "Guatemala", "region": "Central America", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "831", "code": "GG", "name": "Guernsey", "region": "Europe", "trade_agreement": None, "notes": "UK Crown Dependency"},
    {"customs_code": "324", "code": "GN", "name": "Guinea", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "624", "code": "GW", "name": "Guinea-Bissau", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "328", "code": "GY", "name": "Guyana", "region": "Caribbean", "trade_agreement": "CARICOM", "notes": "CARICOM preferential rates apply"},
    
    # H
    {"customs_code": "332", "code": "HT", "name": "Haiti", "region": "Caribbean", "trade_agreement": "CARICOM", "notes": "CARICOM preferential rates apply"},
    {"customs_code": "336", "code": "VA", "name": "Holy See", "region": "Europe", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "340", "code": "HN", "name": "Honduras", "region": "Central America", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "348", "code": "HU", "name": "Hungary", "region": "Europe", "trade_agreement": None, "notes": "EU member"},
    
    # I
    {"customs_code": "352", "code": "IS", "name": "Iceland", "region": "Europe", "trade_agreement": None, "notes": "EFTA member"},
    {"customs_code": "356", "code": "IN", "name": "India", "region": "Asia", "trade_agreement": None, "notes": "Commonwealth member"},
    {"customs_code": "360", "code": "ID", "name": "Indonesia", "region": "Asia", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "364", "code": "IR", "name": "Iran", "region": "Middle East", "trade_agreement": None, "notes": "Sanctions may apply"},
    {"customs_code": "368", "code": "IQ", "name": "Iraq", "region": "Middle East", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "372", "code": "IE", "name": "Ireland", "region": "Europe", "trade_agreement": None, "notes": "EU member"},
    {"customs_code": "833", "code": "IM", "name": "Isle of Man", "region": "Europe", "trade_agreement": None, "notes": "UK Crown Dependency"},
    {"customs_code": "376", "code": "IL", "name": "Israel", "region": "Middle East", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "380", "code": "IT", "name": "Italy", "region": "Europe", "trade_agreement": None, "notes": "EU member"},
    
    # J
    {"customs_code": "388", "code": "JM", "name": "Jamaica", "region": "Caribbean", "trade_agreement": "CARICOM", "notes": "CARICOM preferential rates apply"},
    {"customs_code": "392", "code": "JP", "name": "Japan", "region": "Asia", "trade_agreement": None, "notes": "Major trading partner"},
    {"customs_code": "832", "code": "JE", "name": "Jersey", "region": "Europe", "trade_agreement": None, "notes": "UK Crown Dependency"},
    {"customs_code": "400", "code": "JO", "name": "Jordan", "region": "Middle East", "trade_agreement": None, "notes": "Standard duty rates apply"},
    
    # K
    {"customs_code": "398", "code": "KZ", "name": "Kazakhstan", "region": "Asia", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "404", "code": "KE", "name": "Kenya", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "296", "code": "KI", "name": "Kiribati", "region": "Oceania", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "414", "code": "KW", "name": "Kuwait", "region": "Middle East", "trade_agreement": None, "notes": "Petroleum source"},
    {"customs_code": "417", "code": "KG", "name": "Kyrgyzstan", "region": "Asia", "trade_agreement": None, "notes": "Standard duty rates apply"},
    
    # L
    {"customs_code": "418", "code": "LA", "name": "Lao People's Democratic Republic", "region": "Asia", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "428", "code": "LV", "name": "Latvia", "region": "Europe", "trade_agreement": None, "notes": "EU member"},
    {"customs_code": "422", "code": "LB", "name": "Lebanon", "region": "Middle East", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "426", "code": "LS", "name": "Lesotho", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "430", "code": "LR", "name": "Liberia", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "434", "code": "LY", "name": "Libya", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "438", "code": "LI", "name": "Liechtenstein", "region": "Europe", "trade_agreement": None, "notes": "EFTA member"},
    {"customs_code": "440", "code": "LT", "name": "Lithuania", "region": "Europe", "trade_agreement": None, "notes": "EU member"},
    {"customs_code": "442", "code": "LU", "name": "Luxembourg", "region": "Europe", "trade_agreement": None, "notes": "EU member"},
    
    # M
    {"customs_code": "450", "code": "MG", "name": "Madagascar", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "454", "code": "MW", "name": "Malawi", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "458", "code": "MY", "name": "Malaysia", "region": "Asia", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "462", "code": "MV", "name": "Maldives", "region": "Asia", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "466", "code": "ML", "name": "Mali", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "470", "code": "MT", "name": "Malta", "region": "Europe", "trade_agreement": None, "notes": "EU member"},
    {"customs_code": "584", "code": "MH", "name": "Marshall Islands", "region": "Oceania", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "474", "code": "MQ", "name": "Martinique", "region": "Caribbean", "trade_agreement": None, "notes": "French Territory"},
    {"customs_code": "478", "code": "MR", "name": "Mauritania", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "480", "code": "MU", "name": "Mauritius", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "175", "code": "YT", "name": "Mayotte", "region": "Africa", "trade_agreement": None, "notes": "French Territory"},
    {"customs_code": "484", "code": "MX", "name": "Mexico", "region": "North America", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "583", "code": "FM", "name": "Micronesia", "region": "Oceania", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "492", "code": "MC", "name": "Monaco", "region": "Europe", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "496", "code": "MN", "name": "Mongolia", "region": "Asia", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "499", "code": "ME", "name": "Montenegro", "region": "Europe", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "500", "code": "MS", "name": "Montserrat", "region": "Caribbean", "trade_agreement": "CARICOM", "notes": "UK Territory - CARICOM associate"},
    {"customs_code": "504", "code": "MA", "name": "Morocco", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "508", "code": "MZ", "name": "Mozambique", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "104", "code": "MM", "name": "Myanmar", "region": "Asia", "trade_agreement": None, "notes": "Standard duty rates apply"},
    
    # N
    {"customs_code": "516", "code": "NA", "name": "Namibia", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "520", "code": "NR", "name": "Nauru", "region": "Oceania", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "524", "code": "NP", "name": "Nepal", "region": "Asia", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "528", "code": "NL", "name": "Netherlands", "region": "Europe", "trade_agreement": None, "notes": "EU member - major port"},
    {"customs_code": "530", "code": "AN", "name": "Netherlands Antilles", "region": "Caribbean", "trade_agreement": None, "notes": "Former Netherlands Territory"},
    {"customs_code": "540", "code": "NC", "name": "New Caledonia", "region": "Oceania", "trade_agreement": None, "notes": "French Territory"},
    {"customs_code": "554", "code": "NZ", "name": "New Zealand", "region": "Oceania", "trade_agreement": None, "notes": "Commonwealth member"},
    {"customs_code": "558", "code": "NI", "name": "Nicaragua", "region": "Central America", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "562", "code": "NE", "name": "Niger", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "566", "code": "NG", "name": "Nigeria", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "570", "code": "NU", "name": "Niue", "region": "Oceania", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "574", "code": "NF", "name": "Norfolk Island", "region": "Oceania", "trade_agreement": None, "notes": "Australian Territory"},
    {"customs_code": "580", "code": "MP", "name": "Northern Mariana Islands", "region": "Oceania", "trade_agreement": None, "notes": "US Territory"},
    {"customs_code": "578", "code": "NO", "name": "Norway", "region": "Europe", "trade_agreement": None, "notes": "EFTA member"},
    
    # O
    {"customs_code": "275", "code": "PS", "name": "Occupied Palestinian Territory", "region": "Middle East", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "512", "code": "OM", "name": "Oman", "region": "Middle East", "trade_agreement": None, "notes": "Standard duty rates apply"},
    
    # P
    {"customs_code": "586", "code": "PK", "name": "Pakistan", "region": "Asia", "trade_agreement": None, "notes": "Textiles source"},
    {"customs_code": "585", "code": "PW", "name": "Palau", "region": "Oceania", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "591", "code": "PA", "name": "Panama", "region": "Central America", "trade_agreement": None, "notes": "Free trade zone"},
    {"customs_code": "598", "code": "PG", "name": "Papua New Guinea", "region": "Oceania", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "600", "code": "PY", "name": "Paraguay", "region": "South America", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "604", "code": "PE", "name": "Peru", "region": "South America", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "608", "code": "PH", "name": "Philippines", "region": "Asia", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "612", "code": "PN", "name": "Pitcairn", "region": "Oceania", "trade_agreement": None, "notes": "UK Territory"},
    {"customs_code": "616", "code": "PL", "name": "Poland", "region": "Europe", "trade_agreement": None, "notes": "EU member"},
    {"customs_code": "620", "code": "PT", "name": "Portugal", "region": "Europe", "trade_agreement": None, "notes": "EU member"},
    {"customs_code": "630", "code": "PR", "name": "Puerto Rico", "region": "Caribbean", "trade_agreement": None, "notes": "US Territory"},
    
    # Q
    {"customs_code": "634", "code": "QA", "name": "Qatar", "region": "Middle East", "trade_agreement": None, "notes": "Standard duty rates apply"},
    
    # R
    {"customs_code": "410", "code": "KR", "name": "Republic of Korea", "region": "Asia", "trade_agreement": None, "notes": "Major trading partner"},
    {"customs_code": "498", "code": "MD", "name": "Republic of Moldova", "region": "Europe", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "638", "code": "RE", "name": "Réunion", "region": "Africa", "trade_agreement": None, "notes": "French Territory"},
    {"customs_code": "642", "code": "RO", "name": "Romania", "region": "Europe", "trade_agreement": None, "notes": "EU member"},
    {"customs_code": "643", "code": "RU", "name": "Russian Federation", "region": "Europe", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "646", "code": "RW", "name": "Rwanda", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    
    # S
    {"customs_code": "654", "code": "SH", "name": "Saint Helena", "region": "Africa", "trade_agreement": None, "notes": "UK Territory"},
    {"customs_code": "659", "code": "KN", "name": "Saint Kitts and Nevis", "region": "Caribbean", "trade_agreement": "CARICOM", "notes": "CARICOM preferential rates apply"},
    {"customs_code": "662", "code": "LC", "name": "Saint Lucia", "region": "Caribbean", "trade_agreement": "CARICOM", "notes": "CARICOM preferential rates apply"},
    {"customs_code": "666", "code": "PM", "name": "Saint Pierre and Miquelon", "region": "North America", "trade_agreement": None, "notes": "French Territory"},
    {"customs_code": "670", "code": "VC", "name": "Saint Vincent and the Grenadines", "region": "Caribbean", "trade_agreement": "CARICOM", "notes": "CARICOM preferential rates apply"},
    {"customs_code": "652", "code": "BL", "name": "Saint-Barthélemy", "region": "Caribbean", "trade_agreement": None, "notes": "French Territory"},
    {"customs_code": "663", "code": "MF", "name": "Saint-Martin (French part)", "region": "Caribbean", "trade_agreement": None, "notes": "French Territory"},
    {"customs_code": "882", "code": "WS", "name": "Samoa", "region": "Oceania", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "674", "code": "SM", "name": "San Marino", "region": "Europe", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "678", "code": "ST", "name": "Sao Tome and Principe", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "682", "code": "SA", "name": "Saudi Arabia", "region": "Middle East", "trade_agreement": None, "notes": "Petroleum source"},
    {"customs_code": "686", "code": "SN", "name": "Senegal", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "688", "code": "RS", "name": "Serbia", "region": "Europe", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "690", "code": "SC", "name": "Seychelles", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "694", "code": "SL", "name": "Sierra Leone", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "702", "code": "SG", "name": "Singapore", "region": "Asia", "trade_agreement": None, "notes": "Major transit hub"},
    {"customs_code": "534", "code": "SX", "name": "Sint Maarten (Dutch part)", "region": "Caribbean", "trade_agreement": None, "notes": "Netherlands Territory"},
    {"customs_code": "703", "code": "SK", "name": "Slovakia", "region": "Europe", "trade_agreement": None, "notes": "EU member"},
    {"customs_code": "705", "code": "SI", "name": "Slovenia", "region": "Europe", "trade_agreement": None, "notes": "EU member"},
    {"customs_code": "090", "code": "SB", "name": "Solomon Islands", "region": "Oceania", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "706", "code": "SO", "name": "Somalia", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "710", "code": "ZA", "name": "South Africa", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "724", "code": "ES", "name": "Spain", "region": "Europe", "trade_agreement": None, "notes": "EU member"},
    {"customs_code": "144", "code": "LK", "name": "Sri Lanka", "region": "Asia", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "736", "code": "SD", "name": "Sudan", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "740", "code": "SR", "name": "Suriname", "region": "Caribbean", "trade_agreement": "CARICOM", "notes": "CARICOM preferential rates apply"},
    {"customs_code": "744", "code": "SJ", "name": "Svalbard and Jan Mayen Islands", "region": "Europe", "trade_agreement": None, "notes": "Norwegian Territory"},
    {"customs_code": "748", "code": "SZ", "name": "Swaziland", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "752", "code": "SE", "name": "Sweden", "region": "Europe", "trade_agreement": None, "notes": "EU member"},
    {"customs_code": "756", "code": "CH", "name": "Switzerland", "region": "Europe", "trade_agreement": None, "notes": "EFTA member - luxury goods"},
    {"customs_code": "760", "code": "SY", "name": "Syrian Arab Republic", "region": "Middle East", "trade_agreement": None, "notes": "Sanctions may apply"},
    
    # T
    {"customs_code": "158", "code": "TW", "name": "Taiwan", "region": "Asia", "trade_agreement": None, "notes": "Electronics manufacturing"},
    {"customs_code": "762", "code": "TJ", "name": "Tajikistan", "region": "Asia", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "764", "code": "TH", "name": "Thailand", "region": "Asia", "trade_agreement": None, "notes": "Manufacturing source"},
    {"customs_code": "626", "code": "TL", "name": "Timor-Leste", "region": "Asia", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "768", "code": "TG", "name": "Togo", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "772", "code": "TK", "name": "Tokelau", "region": "Oceania", "trade_agreement": None, "notes": "New Zealand Territory"},
    {"customs_code": "776", "code": "TO", "name": "Tonga", "region": "Oceania", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "780", "code": "TT", "name": "Trinidad and Tobago", "region": "Caribbean", "trade_agreement": "CARICOM", "notes": "CARICOM preferential rates apply"},
    {"customs_code": "788", "code": "TN", "name": "Tunisia", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "792", "code": "TR", "name": "Turkey", "region": "Europe", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "795", "code": "TM", "name": "Turkmenistan", "region": "Asia", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "796", "code": "TC", "name": "Turks and Caicos Islands", "region": "Caribbean", "trade_agreement": None, "notes": "UK Territory"},
    {"customs_code": "798", "code": "TV", "name": "Tuvalu", "region": "Oceania", "trade_agreement": None, "notes": "Standard duty rates apply"},
    
    # U
    {"customs_code": "800", "code": "UG", "name": "Uganda", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "804", "code": "UA", "name": "Ukraine", "region": "Europe", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "784", "code": "AE", "name": "United Arab Emirates", "region": "Middle East", "trade_agreement": None, "notes": "Dubai - major transit hub"},
    {"customs_code": "826", "code": "GB", "name": "United Kingdom", "region": "Europe", "trade_agreement": None, "notes": "Commonwealth member"},
    {"customs_code": "834", "code": "TZ", "name": "United Republic of Tanzania", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "840", "code": "US", "name": "United States of America", "region": "North America", "trade_agreement": None, "notes": "Major trading partner"},
    {"customs_code": "850", "code": "VI", "name": "United States Virgin Islands", "region": "Caribbean", "trade_agreement": None, "notes": "US Territory"},
    {"customs_code": "858", "code": "UY", "name": "Uruguay", "region": "South America", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "860", "code": "UZ", "name": "Uzbekistan", "region": "Asia", "trade_agreement": None, "notes": "Standard duty rates apply"},
    
    # V
    {"customs_code": "548", "code": "VU", "name": "Vanuatu", "region": "Oceania", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "862", "code": "VE", "name": "Venezuela", "region": "South America", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "704", "code": "VN", "name": "Viet Nam", "region": "Asia", "trade_agreement": None, "notes": "Manufacturing source"},
    
    # W
    {"customs_code": "876", "code": "WF", "name": "Wallis and Futuna Islands", "region": "Oceania", "trade_agreement": None, "notes": "French Territory"},
    {"customs_code": "732", "code": "EH", "name": "Western Sahara", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    
    # Y
    {"customs_code": "887", "code": "YE", "name": "Yemen", "region": "Middle East", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "807", "code": "MK", "name": "North Macedonia", "region": "Europe", "trade_agreement": None, "notes": "Standard duty rates apply"},
    
    # Z
    {"customs_code": "894", "code": "ZM", "name": "Zambia", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
    {"customs_code": "716", "code": "ZW", "name": "Zimbabwe", "region": "Africa", "trade_agreement": None, "notes": "Standard duty rates apply"},
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
