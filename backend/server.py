from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import pandas as pd
import io
import json
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'hs_classifier')]

# JWT Config
JWT_SECRET = os.environ.get('JWT_SECRET', 'hs-classifier-secret-key-2024')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Create the main app
app = FastAPI(title="Bahamas HS Code Classification API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Upload directory
UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# ============= ENUMS =============
class ReviewStatus(str, Enum):
    AUTO_APPROVED = "auto_approved"
    NEEDS_REVIEW = "needs_review"
    REVIEWED = "reviewed"
    REJECTED = "rejected"

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

# ============= MODELS =============
class UserBase(BaseModel):
    email: EmailStr
    name: str
    company: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: str
    role: UserRole = UserRole.USER
    created_at: datetime

class HSCodeBase(BaseModel):
    code: str
    description: str
    chapter: str
    section: Optional[str] = None
    notes: Optional[str] = None
    duty_rate: Optional[str] = None
    bahamas_extension: Optional[str] = None
    is_restricted: bool = False
    requires_permit: bool = False

class HSCodeCreate(HSCodeBase):
    pass

class HSCodeResponse(HSCodeBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

class ClassificationItemBase(BaseModel):
    original_description: str
    clean_description: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    unit_value: Optional[float] = None
    total_value: Optional[float] = None
    weight: Optional[float] = None
    country_of_origin: Optional[str] = None
    hs_code: Optional[str] = None
    hs_description: Optional[str] = None
    gri_rules_applied: List[str] = []
    confidence_score: float = 0.0
    reasoning: Optional[str] = None
    cma_notes: Optional[str] = None
    review_status: ReviewStatus = ReviewStatus.NEEDS_REVIEW
    is_restricted: bool = False
    requires_permit: bool = False

class ClassificationCreate(BaseModel):
    document_id: str
    items: List[ClassificationItemBase]

class ClassificationResponse(BaseModel):
    id: str
    user_id: str
    document_id: str
    document_name: str
    items: List[ClassificationItemBase]
    total_items: int
    auto_approved_count: int
    needs_review_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

class DocumentResponse(BaseModel):
    id: str
    user_id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    created_at: datetime
    classification_id: Optional[str] = None

class DashboardStats(BaseModel):
    total_classifications: int
    total_items: int
    pending_review: int
    auto_approved: int
    avg_confidence: float

# ============= AUTH HELPERS =============
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["user_id"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def require_admin(user: dict = Depends(get_current_user)):
    if user.get("role") != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# ============= AI CLASSIFICATION SERVICE =============
async def classify_items_with_ai(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Use GPT-5.2 to classify items with HS codes"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        logger.warning("No EMERGENT_LLM_KEY found, using mock classification")
        return mock_classify_items(items)
    
    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=f"hs-classification-{uuid.uuid4()}",
            system_message="""You are an expert Customs Classification AI Agent for The Bahamas. 
Your task is to analyze product descriptions and assign accurate Harmonized System (HS) codes following:
- Bahamas Customs Management Act (CMA)
- World Customs Organization (WCO) HS Nomenclature
- General Rules of Interpretation (GRI 1-6)

For each item, provide:
1. HS Code (6-digit minimum, 8-10 digit Bahamas extension if applicable)
2. Official HS Description
3. GRI Rules Applied (explain which rules you used)
4. Confidence Score (0-100%)
5. Reasoning (brief explanation of classification logic)
6. CMA Notes (any regulatory flags, restrictions, permits required)
7. is_restricted (boolean)
8. requires_permit (boolean)

Respond ONLY with valid JSON array, no markdown formatting."""
        ).with_model("openai", "gpt-5.2")
        
        items_text = json.dumps([{
            "description": item.get("original_description", item.get("description", "")),
            "quantity": item.get("quantity"),
            "unit_value": item.get("unit_value"),
            "country_of_origin": item.get("country_of_origin")
        } for item in items], indent=2)
        
        prompt = f"""Classify the following items for Bahamas Customs import:

{items_text}

Return a JSON array with each item containing:
- clean_description: normalized product description
- hs_code: 6-10 digit code
- hs_description: official nomenclature text
- gri_rules_applied: array of rules like ["GRI 1", "GRI 3(a)"]
- confidence_score: number 0-100
- reasoning: string explaining classification
- cma_notes: any compliance notes or flags
- is_restricted: boolean
- requires_permit: boolean
- review_status: "auto_approved" if confidence >= 85, else "needs_review"
"""
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        # Parse JSON response
        response_text = response.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        
        classified_items = json.loads(response_text)
        
        # Merge with original items
        result = []
        for i, item in enumerate(items):
            classified = classified_items[i] if i < len(classified_items) else {}
            result.append({
                **item,
                "clean_description": classified.get("clean_description", item.get("original_description", "")),
                "hs_code": classified.get("hs_code", ""),
                "hs_description": classified.get("hs_description", ""),
                "gri_rules_applied": classified.get("gri_rules_applied", []),
                "confidence_score": classified.get("confidence_score", 0),
                "reasoning": classified.get("reasoning", ""),
                "cma_notes": classified.get("cma_notes", ""),
                "is_restricted": classified.get("is_restricted", False),
                "requires_permit": classified.get("requires_permit", False),
                "review_status": classified.get("review_status", "needs_review")
            })
        
        return result
        
    except Exception as e:
        logger.error(f"AI classification error: {e}")
        return mock_classify_items(items)

def mock_classify_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Mock classification for testing when AI is unavailable"""
    result = []
    for item in items:
        desc = item.get("original_description", item.get("description", "")).lower()
        
        # Simple mock classification based on keywords
        hs_code = "8471.30"
        hs_desc = "Portable digital automatic data processing machines"
        confidence = 75
        
        if "phone" in desc or "mobile" in desc:
            hs_code = "8517.12"
            hs_desc = "Telephones for cellular networks or other wireless networks"
            confidence = 88
        elif "laptop" in desc or "computer" in desc:
            hs_code = "8471.30"
            hs_desc = "Portable digital automatic data processing machines"
            confidence = 92
        elif "shirt" in desc or "cloth" in desc:
            hs_code = "6205.20"
            hs_desc = "Men's or boys' shirts of cotton"
            confidence = 85
        elif "food" in desc or "fruit" in desc:
            hs_code = "0804.50"
            hs_desc = "Guavas, mangoes and mangosteens, fresh or dried"
            confidence = 70
        elif "medicine" in desc or "drug" in desc:
            hs_code = "3004.90"
            hs_desc = "Medicaments for therapeutic or prophylactic uses"
            confidence = 65
        
        result.append({
            **item,
            "clean_description": item.get("original_description", item.get("description", "")),
            "hs_code": hs_code,
            "hs_description": hs_desc,
            "gri_rules_applied": ["GRI 1", "GRI 6"],
            "confidence_score": confidence,
            "reasoning": f"Classified based on product description matching HS nomenclature heading {hs_code[:4]}",
            "cma_notes": "Standard import, no special requirements" if confidence >= 80 else "Manual review recommended",
            "is_restricted": "medicine" in desc.lower() or "drug" in desc.lower(),
            "requires_permit": "medicine" in desc.lower(),
            "review_status": "auto_approved" if confidence >= 85 else "needs_review"
        })
    
    return result

# ============= FILE PROCESSING =============
async def process_uploaded_file(file_path: Path, file_type: str) -> List[Dict[str, Any]]:
    """Extract items from uploaded file"""
    items = []
    
    try:
        if file_type in ["xlsx", "xls"]:
            df = pd.read_excel(file_path)
        elif file_type == "csv":
            df = pd.read_csv(file_path)
        else:
            # For PDF, we'd use AI extraction
            return await extract_pdf_with_ai(file_path)
        
        # Normalize column names
        df.columns = df.columns.str.lower().str.strip()
        
        # Map common column names
        column_mapping = {
            "description": ["description", "item description", "product", "goods", "item", "commodity"],
            "quantity": ["quantity", "qty", "units", "pcs", "pieces"],
            "unit": ["unit", "uom", "unit of measure"],
            "unit_value": ["unit value", "unit price", "price", "value", "unit_value"],
            "total_value": ["total", "total value", "amount", "line total", "total_value"],
            "weight": ["weight", "gross weight", "net weight", "kg", "lbs"],
            "country": ["country", "origin", "country of origin", "coo", "made in"]
        }
        
        def find_column(possible_names):
            for name in possible_names:
                if name in df.columns:
                    return name
            return None
        
        desc_col = find_column(column_mapping["description"])
        qty_col = find_column(column_mapping["quantity"])
        unit_col = find_column(column_mapping["unit"])
        unit_val_col = find_column(column_mapping["unit_value"])
        total_col = find_column(column_mapping["total_value"])
        weight_col = find_column(column_mapping["weight"])
        country_col = find_column(column_mapping["country"])
        
        for _, row in df.iterrows():
            if desc_col and pd.notna(row.get(desc_col)):
                item = {
                    "original_description": str(row.get(desc_col, "")),
                    "quantity": float(row.get(qty_col, 0)) if qty_col and pd.notna(row.get(qty_col)) else None,
                    "unit": str(row.get(unit_col, "")) if unit_col and pd.notna(row.get(unit_col)) else None,
                    "unit_value": float(row.get(unit_val_col, 0)) if unit_val_col and pd.notna(row.get(unit_val_col)) else None,
                    "total_value": float(row.get(total_col, 0)) if total_col and pd.notna(row.get(total_col)) else None,
                    "weight": float(row.get(weight_col, 0)) if weight_col and pd.notna(row.get(weight_col)) else None,
                    "country_of_origin": str(row.get(country_col, "")) if country_col and pd.notna(row.get(country_col)) else None
                }
                items.append(item)
                
    except Exception as e:
        logger.error(f"File processing error: {e}")
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")
    
    return items

async def extract_pdf_with_ai(file_path: Path) -> List[Dict[str, Any]]:
    """Extract items from PDF using AI with file attachment"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContentWithMimeType
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service unavailable for PDF processing")
    
    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=f"pdf-extraction-{uuid.uuid4()}",
            system_message="""You are a document extraction specialist for customs invoices.
Extract all line items from commercial invoices, packing lists, or similar documents.
Return ONLY valid JSON array, no markdown formatting."""
        ).with_model("gemini", "gemini-2.5-flash")
        
        pdf_file = FileContentWithMimeType(
            file_path=str(file_path),
            mime_type="application/pdf"
        )
        
        prompt = """Extract all line items from this commercial document. For each item, extract:
- description: product description
- quantity: number of units
- unit: unit of measure (pcs, kg, etc.)
- unit_value: price per unit
- total_value: line total
- weight: if available
- country_of_origin: if mentioned

Return as JSON array with these fields:
[{"original_description": "...", "quantity": ..., "unit": "...", "unit_value": ..., "total_value": ..., "weight": ..., "country_of_origin": "..."}]"""
        
        response = await chat.send_message(UserMessage(text=prompt, file_contents=[pdf_file]))
        
        response_text = response.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        
        items = json.loads(response_text)
        return items
        
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        raise HTTPException(status_code=400, detail=f"Error extracting PDF: {str(e)}")

# ============= AUTH ROUTES =============
@api_router.post("/auth/register", response_model=dict)
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "company": user_data.company,
        "password": hash_password(user_data.password),
        "role": UserRole.USER,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_doc)
    token = create_token(user_id, user_data.email, UserRole.USER)
    
    return {"token": token, "user": {"id": user_id, "email": user_data.email, "name": user_data.name, "role": UserRole.USER}}

@api_router.post("/auth/login", response_model=dict)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"], user["email"], user.get("role", UserRole.USER))
    return {
        "token": token, 
        "user": {
            "id": user["id"], 
            "email": user["email"], 
            "name": user["name"],
            "role": user.get("role", UserRole.USER)
        }
    }

@api_router.get("/auth/me", response_model=dict)
async def get_me(user: dict = Depends(get_current_user)):
    return {"id": user["id"], "email": user["email"], "name": user["name"], "role": user.get("role", UserRole.USER)}

# ============= DOCUMENT ROUTES =============
@api_router.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    # Validate file type
    allowed_types = ["xlsx", "xls", "csv", "pdf"]
    file_ext = file.filename.split(".")[-1].lower()
    
    if file_ext not in allowed_types:
        raise HTTPException(status_code=400, detail=f"File type not supported. Allowed: {', '.join(allowed_types)}")
    
    # Save file
    doc_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{doc_id}.{file_ext}"
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Create document record
    doc = {
        "id": doc_id,
        "user_id": user["id"],
        "filename": file.filename,
        "file_type": file_ext,
        "file_size": len(content),
        "file_path": str(file_path),
        "status": "uploaded",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "classification_id": None
    }
    
    await db.documents.insert_one(doc)
    
    return DocumentResponse(**{k: v for k, v in doc.items() if k != "file_path"})

@api_router.get("/documents", response_model=List[DocumentResponse])
async def get_documents(user: dict = Depends(get_current_user)):
    docs = await db.documents.find({"user_id": user["id"]}, {"_id": 0, "file_path": 0}).sort("created_at", -1).to_list(100)
    for doc in docs:
        if isinstance(doc.get("created_at"), str):
            doc["created_at"] = datetime.fromisoformat(doc["created_at"])
    return docs

@api_router.get("/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str, user: dict = Depends(get_current_user)):
    doc = await db.documents.find_one({"id": doc_id, "user_id": user["id"]}, {"_id": 0, "file_path": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if isinstance(doc.get("created_at"), str):
        doc["created_at"] = datetime.fromisoformat(doc["created_at"])
    return doc

# ============= CLASSIFICATION ROUTES =============
@api_router.post("/classifications/process/{doc_id}", response_model=ClassificationResponse)
async def process_and_classify(doc_id: str, user: dict = Depends(get_current_user)):
    # Get document
    doc = await db.documents.find_one({"id": doc_id, "user_id": user["id"]}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Process file
    file_path = Path(doc["file_path"])
    items = await process_uploaded_file(file_path, doc["file_type"])
    
    if not items:
        raise HTTPException(status_code=400, detail="No items found in document")
    
    # Classify with AI
    classified_items = await classify_items_with_ai(items)
    
    # Calculate stats
    auto_approved = sum(1 for item in classified_items if item.get("review_status") == "auto_approved")
    needs_review = len(classified_items) - auto_approved
    
    # Create classification record
    classification_id = str(uuid.uuid4())
    classification = {
        "id": classification_id,
        "user_id": user["id"],
        "document_id": doc_id,
        "document_name": doc["filename"],
        "items": classified_items,
        "total_items": len(classified_items),
        "auto_approved_count": auto_approved,
        "needs_review_count": needs_review,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": None
    }
    
    await db.classifications.insert_one(classification)
    
    # Update document
    await db.documents.update_one(
        {"id": doc_id},
        {"$set": {"status": "classified", "classification_id": classification_id}}
    )
    
    classification["created_at"] = datetime.fromisoformat(classification["created_at"])
    return classification

@api_router.get("/classifications", response_model=List[ClassificationResponse])
async def get_classifications(user: dict = Depends(get_current_user)):
    classifications = await db.classifications.find(
        {"user_id": user["id"]}, 
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    for c in classifications:
        if isinstance(c.get("created_at"), str):
            c["created_at"] = datetime.fromisoformat(c["created_at"])
        if isinstance(c.get("updated_at"), str):
            c["updated_at"] = datetime.fromisoformat(c["updated_at"])
    
    return classifications

@api_router.get("/classifications/{classification_id}", response_model=ClassificationResponse)
async def get_classification(classification_id: str, user: dict = Depends(get_current_user)):
    classification = await db.classifications.find_one(
        {"id": classification_id, "user_id": user["id"]}, 
        {"_id": 0}
    )
    if not classification:
        raise HTTPException(status_code=404, detail="Classification not found")
    
    if isinstance(classification.get("created_at"), str):
        classification["created_at"] = datetime.fromisoformat(classification["created_at"])
    
    return classification

@api_router.put("/classifications/{classification_id}/items/{item_index}", response_model=dict)
async def update_classification_item(
    classification_id: str,
    item_index: int,
    item_update: ClassificationItemBase,
    user: dict = Depends(get_current_user)
):
    classification = await db.classifications.find_one(
        {"id": classification_id, "user_id": user["id"]},
        {"_id": 0}
    )
    if not classification:
        raise HTTPException(status_code=404, detail="Classification not found")
    
    if item_index < 0 or item_index >= len(classification["items"]):
        raise HTTPException(status_code=400, detail="Invalid item index")
    
    # Update item
    classification["items"][item_index] = item_update.model_dump()
    
    # Recalculate stats
    auto_approved = sum(1 for item in classification["items"] if item.get("review_status") == "auto_approved")
    
    await db.classifications.update_one(
        {"id": classification_id},
        {"$set": {
            "items": classification["items"],
            "auto_approved_count": auto_approved,
            "needs_review_count": len(classification["items"]) - auto_approved,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Item updated successfully"}

@api_router.get("/classifications/{classification_id}/export")
async def export_classification(
    classification_id: str,
    format: str = "csv",
    user: dict = Depends(get_current_user)
):
    from fastapi.responses import StreamingResponse
    
    classification = await db.classifications.find_one(
        {"id": classification_id, "user_id": user["id"]},
        {"_id": 0}
    )
    if not classification:
        raise HTTPException(status_code=404, detail="Classification not found")
    
    # Prepare data
    export_data = []
    for item in classification["items"]:
        export_data.append({
            "Description": item.get("clean_description", ""),
            "HS Code": item.get("hs_code", ""),
            "HS Description": item.get("hs_description", ""),
            "Quantity": item.get("quantity", ""),
            "Unit": item.get("unit", ""),
            "Unit Value": item.get("unit_value", ""),
            "Total Value": item.get("total_value", ""),
            "Weight": item.get("weight", ""),
            "Country of Origin": item.get("country_of_origin", ""),
            "GRI Rules": ", ".join(item.get("gri_rules_applied", [])),
            "Confidence (%)": item.get("confidence_score", 0),
            "Review Status": item.get("review_status", ""),
            "CMA Notes": item.get("cma_notes", ""),
            "Restricted": "Yes" if item.get("is_restricted") else "No",
            "Requires Permit": "Yes" if item.get("requires_permit") else "No"
        })
    
    df = pd.DataFrame(export_data)
    
    if format == "xlsx":
        output = io.BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=classification_{classification_id}.xlsx"}
        )
    else:  # csv
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=classification_{classification_id}.csv"}
        )

# ============= HS CODE LIBRARY ROUTES =============

# Bulk HS Code Classification Template and Upload
@api_router.get("/hs-codes/template")
async def get_hs_classification_template(user: dict = Depends(get_current_user)):
    """Download CSV template for bulk HS code classification"""
    from fastapi.responses import StreamingResponse
    
    template_data = """description,quantity,unit,unit_value,total_value,country_of_origin
Apple iPhone 15 Pro Max 256GB,10,pcs,999.00,9990.00,China
Nike Air Jordan Basketball Shoes Size 10,24,pairs,180.00,4320.00,Vietnam
Samsung 65 inch 4K Smart TV,5,units,1200.00,6000.00,South Korea
Organic Colombian Coffee Beans 1kg bags,100,kg,15.00,1500.00,Colombia
Cotton T-Shirts Assorted Colors,500,pcs,8.50,4250.00,Bangladesh
Lithium Ion Batteries 5000mAh,200,pcs,12.00,2400.00,China
Wooden Dining Table Oak 6-seater,3,units,850.00,2550.00,Malaysia
Stainless Steel Kitchen Knives Set,50,sets,45.00,2250.00,Germany"""
    
    output = io.StringIO()
    output.write(template_data)
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=hs_classification_template.csv"}
    )

@api_router.post("/hs-codes/bulk-classify")
async def bulk_classify_items(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """Upload CSV/Excel file for bulk HS code classification using AI"""
    
    # Validate file type
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ["csv", "xlsx", "xls"]:
        raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")
    
    content = await file.read()
    
    try:
        if file_ext == "csv":
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
    
    # Normalize column names
    df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')
    
    # Check for description column
    if 'description' not in df.columns:
        raise HTTPException(status_code=400, detail="Missing required 'description' column")
    
    # Prepare items for classification
    items = []
    for idx, row in df.iterrows():
        if pd.notna(row.get('description')):
            item = {
                "original_description": str(row['description']),
                "quantity": float(row['quantity']) if 'quantity' in df.columns and pd.notna(row.get('quantity')) else None,
                "unit": str(row['unit']) if 'unit' in df.columns and pd.notna(row.get('unit')) else None,
                "unit_value": float(row['unit_value']) if 'unit_value' in df.columns and pd.notna(row.get('unit_value')) else None,
                "total_value": float(row['total_value']) if 'total_value' in df.columns and pd.notna(row.get('total_value')) else None,
                "country_of_origin": str(row['country_of_origin']) if 'country_of_origin' in df.columns and pd.notna(row.get('country_of_origin')) else None
            }
            items.append(item)
    
    if not items:
        raise HTTPException(status_code=400, detail="No valid items found in file")
    
    # Classify with AI
    classified_items = await classify_items_with_ai(items)
    
    # Calculate stats
    auto_approved = sum(1 for item in classified_items if item.get("review_status") == "auto_approved")
    needs_review = len(classified_items) - auto_approved
    avg_confidence = sum(item.get("confidence_score", 0) for item in classified_items) / len(classified_items) if classified_items else 0
    
    # Create batch record
    batch_id = str(uuid.uuid4())
    batch_record = {
        "id": batch_id,
        "user_id": user["id"],
        "filename": file.filename,
        "total_items": len(classified_items),
        "auto_approved_count": auto_approved,
        "needs_review_count": needs_review,
        "avg_confidence": round(avg_confidence, 1),
        "items": classified_items,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.hs_classification_batches.insert_one(batch_record)
    
    return {
        "batch_id": batch_id,
        "filename": file.filename,
        "total_items": len(classified_items),
        "auto_approved": auto_approved,
        "needs_review": needs_review,
        "avg_confidence": round(avg_confidence, 1),
        "items": classified_items
    }

@api_router.get("/hs-codes/batches")
async def get_hs_classification_batches(user: dict = Depends(get_current_user)):
    """Get user's bulk classification history"""
    batches = await db.hs_classification_batches.find(
        {"user_id": user["id"]},
        {"_id": 0, "items": 0}
    ).sort("created_at", -1).to_list(50)
    
    for batch in batches:
        if isinstance(batch.get("created_at"), str):
            batch["created_at"] = datetime.fromisoformat(batch["created_at"])
    
    return batches

@api_router.get("/hs-codes/batches/{batch_id}")
async def get_hs_classification_batch(batch_id: str, user: dict = Depends(get_current_user)):
    """Get specific batch details"""
    batch = await db.hs_classification_batches.find_one(
        {"id": batch_id, "user_id": user["id"]},
        {"_id": 0}
    )
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    if isinstance(batch.get("created_at"), str):
        batch["created_at"] = datetime.fromisoformat(batch["created_at"])
    
    return batch

@api_router.get("/hs-codes/batches/{batch_id}/export")
async def export_hs_classification_batch(batch_id: str, format: str = "csv", user: dict = Depends(get_current_user)):
    """Export bulk classification as CSV or Excel"""
    from fastapi.responses import StreamingResponse
    
    batch = await db.hs_classification_batches.find_one(
        {"id": batch_id, "user_id": user["id"]},
        {"_id": 0}
    )
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    # Prepare export data
    export_data = []
    for item in batch["items"]:
        export_data.append({
            "Description": item.get("clean_description", item.get("original_description", "")),
            "HS Code": item.get("hs_code", ""),
            "HS Description": item.get("hs_description", ""),
            "Quantity": item.get("quantity", ""),
            "Unit": item.get("unit", ""),
            "Unit Value": item.get("unit_value", ""),
            "Total Value": item.get("total_value", ""),
            "Country of Origin": item.get("country_of_origin", ""),
            "GRI Rules": ", ".join(item.get("gri_rules_applied", [])),
            "Confidence %": item.get("confidence_score", 0),
            "Review Status": item.get("review_status", ""),
            "Reasoning": item.get("reasoning", ""),
            "CMA Notes": item.get("cma_notes", ""),
            "Restricted": "Yes" if item.get("is_restricted") else "No",
            "Requires Permit": "Yes" if item.get("requires_permit") else "No"
        })
    
    df = pd.DataFrame(export_data)
    
    if format == "xlsx":
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='HS Classifications')
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=hs_classification_{batch_id[:8]}.xlsx"}
        )
    else:
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=hs_classification_{batch_id[:8]}.csv"}
        )

# ============= HS CODE IMPORT =============
@api_router.get("/hs-codes/import-template")
async def get_hs_import_template(user: dict = Depends(get_current_user)):
    """Download CSV template for importing HS codes to library"""
    from fastapi.responses import StreamingResponse
    
    template_data = """code,description,chapter,section,duty_rate,notes,bahamas_extension,is_restricted,requires_permit
8471.30,Portable digital automatic data processing machines,84,XVI,10%,Laptops and notebooks,,false,false
8517.12,Telephones for cellular networks,85,XVI,10%,Mobile phones and smartphones,,false,false
2208.40,Rum and other spirits from sugar cane,22,IV,45%,Excise $20/LPA applies,00,true,true
6403.99,Footwear with leather uppers,64,XII,45%,High duty on finished footwear,,false,false"""
    
    output = io.StringIO()
    output.write(template_data)
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=hs_codes_import_template.csv"}
    )

@api_router.post("/hs-codes/import")
async def import_hs_codes(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """Import HS codes from CSV/Excel file"""
    
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ["csv", "xlsx", "xls"]:
        raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")
    
    content = await file.read()
    
    try:
        if file_ext == "csv":
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
    
    # Normalize column names
    df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')
    
    required_cols = ['code', 'description', 'chapter']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise HTTPException(status_code=400, detail=f"Missing required columns: {', '.join(missing_cols)}")
    
    imported = 0
    updated = 0
    errors = []
    
    for idx, row in df.iterrows():
        try:
            code = str(row['code']).strip()
            if not code:
                continue
            
            # Check if code exists
            existing = await db.hs_codes.find_one({"code": code})
            
            code_doc = {
                "code": code,
                "description": str(row['description']),
                "chapter": str(row['chapter']),
                "section": str(row.get('section', '')) if pd.notna(row.get('section')) else None,
                "duty_rate": str(row.get('duty_rate', '')) if pd.notna(row.get('duty_rate')) else None,
                "notes": str(row.get('notes', '')) if pd.notna(row.get('notes')) else None,
                "bahamas_extension": str(row.get('bahamas_extension', '')) if pd.notna(row.get('bahamas_extension')) else None,
                "is_restricted": str(row.get('is_restricted', 'false')).lower() in ['true', '1', 'yes'],
                "requires_permit": str(row.get('requires_permit', 'false')).lower() in ['true', '1', 'yes'],
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            if existing:
                await db.hs_codes.update_one({"code": code}, {"$set": code_doc})
                updated += 1
            else:
                code_doc["id"] = str(uuid.uuid4())
                code_doc["created_at"] = datetime.now(timezone.utc).isoformat()
                code_doc["created_by"] = user["id"]
                await db.hs_codes.insert_one(code_doc)
                imported += 1
                
        except Exception as e:
            errors.append({"row": idx + 1, "error": str(e)})
    
    return {
        "imported": imported,
        "updated": updated,
        "errors": errors,
        "total_processed": imported + updated
    }

@api_router.get("/hs-codes", response_model=List[HSCodeResponse])
async def get_hs_codes(
    search: Optional[str] = None,
    chapter: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    query = {}
    if search:
        query["$or"] = [
            {"code": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    if chapter:
        query["chapter"] = chapter
    
    codes = await db.hs_codes.find(query, {"_id": 0}).sort("code", 1).to_list(500)
    
    for code in codes:
        if isinstance(code.get("created_at"), str):
            code["created_at"] = datetime.fromisoformat(code["created_at"])
        if isinstance(code.get("updated_at"), str):
            code["updated_at"] = datetime.fromisoformat(code["updated_at"])
    
    return codes

@api_router.post("/hs-codes", response_model=HSCodeResponse)
async def create_hs_code(hs_code: HSCodeCreate, user: dict = Depends(get_current_user)):
    # Check if code exists
    existing = await db.hs_codes.find_one({"code": hs_code.code})
    if existing:
        raise HTTPException(status_code=400, detail="HS code already exists")
    
    code_id = str(uuid.uuid4())
    code_doc = {
        "id": code_id,
        **hs_code.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": None,
        "created_by": user["id"]
    }
    
    await db.hs_codes.insert_one(code_doc)
    code_doc["created_at"] = datetime.fromisoformat(code_doc["created_at"])
    
    return code_doc

@api_router.put("/hs-codes/{code_id}", response_model=HSCodeResponse)
async def update_hs_code(code_id: str, hs_code: HSCodeCreate, user: dict = Depends(get_current_user)):
    existing = await db.hs_codes.find_one({"id": code_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="HS code not found")
    
    await db.hs_codes.update_one(
        {"id": code_id},
        {"$set": {
            **hs_code.model_dump(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    updated = await db.hs_codes.find_one({"id": code_id}, {"_id": 0})
    if isinstance(updated.get("created_at"), str):
        updated["created_at"] = datetime.fromisoformat(updated["created_at"])
    if isinstance(updated.get("updated_at"), str):
        updated["updated_at"] = datetime.fromisoformat(updated["updated_at"])
    
    return updated

@api_router.delete("/hs-codes/{code_id}")
async def delete_hs_code(code_id: str, user: dict = Depends(require_admin)):
    result = await db.hs_codes.delete_one({"id": code_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="HS code not found")
    return {"message": "HS code deleted"}

# ============= DASHBOARD ROUTES =============
@api_router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(user: dict = Depends(get_current_user)):
    classifications = await db.classifications.find({"user_id": user["id"]}, {"_id": 0}).to_list(1000)
    
    total_classifications = len(classifications)
    total_items = 0
    pending_review = 0
    auto_approved = 0
    total_confidence = 0
    confidence_count = 0
    
    for c in classifications:
        items = c.get("items", [])
        total_items += len(items)
        for item in items:
            if item.get("review_status") == "needs_review":
                pending_review += 1
            elif item.get("review_status") == "auto_approved":
                auto_approved += 1
            if item.get("confidence_score"):
                total_confidence += item["confidence_score"]
                confidence_count += 1
    
    avg_confidence = total_confidence / confidence_count if confidence_count > 0 else 0
    
    return DashboardStats(
        total_classifications=total_classifications,
        total_items=total_items,
        pending_review=pending_review,
        auto_approved=auto_approved,
        avg_confidence=round(avg_confidence, 1)
    )

# ============= ADMIN ROUTES =============
@api_router.get("/admin/users", response_model=List[dict])
async def get_all_users(user: dict = Depends(require_admin)):
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    return users

@api_router.put("/admin/users/{user_id}/role")
async def update_user_role(user_id: str, role: UserRole, admin: dict = Depends(require_admin)):
    result = await db.users.update_one({"id": user_id}, {"$set": {"role": role}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User role updated"}

# ============= ALCOHOL CALCULATION MODULE =============

class AlcoholType(str, Enum):
    WINE = "wine"
    BEER = "beer"
    SPIRITS = "spirits"
    LIQUEUR = "liqueur"
    OTHER = "other"

class AlcoholCalculationRequest(BaseModel):
    product_name: str
    alcohol_type: AlcoholType
    volume_ml: float  # Volume per container in milliliters
    alcohol_percentage: float  # ABV %
    quantity: int  # Number of bottles/containers
    cif_value: float  # Cost, Insurance, Freight value in USD
    country_of_origin: str
    brand_label: Optional[str] = None
    has_liquor_license: bool = False

class AlcoholCalculationResult(BaseModel):
    id: str
    product_name: str
    alcohol_type: AlcoholType
    hs_code: str
    hs_description: str
    quantity: int
    total_volume_liters: float
    alcohol_percentage: float
    pure_alcohol_liters: float
    cif_value: float
    import_duty: float
    import_duty_rate: str
    excise_duty: float
    excise_calculation: str
    vat: float
    vat_rate: str
    license_fee: float
    total_landed_cost: float
    breakdown: Dict[str, Any]
    warnings: List[str]
    requires_permit: bool
    created_at: datetime

# Bahamas Alcohol Duty Rates (CMA Compliant)
ALCOHOL_RATES = {
    "wine": {
        "hs_code": "2204.21",
        "hs_description": "Wine of fresh grapes, in containers holding 2L or less",
        "import_duty_rate": 0.35,  # 35%
        "excise_per_liter": 3.50,  # $3.50 per liter
        "requires_permit": False
    },
    "beer": {
        "hs_code": "2203.00",
        "hs_description": "Beer made from malt",
        "import_duty_rate": 0.35,  # 35%
        "excise_per_liter": 1.50,  # $1.50 per liter
        "requires_permit": False
    },
    "spirits": {
        "hs_code": "2208.40",
        "hs_description": "Rum and other spirits obtained by distilling fermented cane products",
        "import_duty_rate": 0.45,  # 45%
        "excise_per_lpa": 20.00,  # $20.00 per liter of pure alcohol (LPA)
        "requires_permit": True
    },
    "liqueur": {
        "hs_code": "2208.70",
        "hs_description": "Liqueurs and cordials",
        "import_duty_rate": 0.45,  # 45%
        "excise_per_lpa": 18.00,  # $18.00 per liter of pure alcohol
        "requires_permit": True
    },
    "other": {
        "hs_code": "2208.90",
        "hs_description": "Other spirituous beverages",
        "import_duty_rate": 0.40,  # 40%
        "excise_per_lpa": 15.00,  # $15.00 per liter of pure alcohol
        "requires_permit": True
    }
}

VAT_RATE = 0.10  # 10% VAT (Bahamas current rate)
LICENSE_FEE_BASE = 50.00  # Base license processing fee

@api_router.post("/alcohol/calculate", response_model=AlcoholCalculationResult)
async def calculate_alcohol_duties(
    request: AlcoholCalculationRequest,
    user: dict = Depends(get_current_user)
):
    """Calculate duties, excise, VAT, and fees for alcohol imports"""
    
    rates = ALCOHOL_RATES.get(request.alcohol_type, ALCOHOL_RATES["other"])
    warnings = []
    
    # Calculate volumes
    volume_per_unit_liters = request.volume_ml / 1000
    total_volume_liters = volume_per_unit_liters * request.quantity
    pure_alcohol_liters = total_volume_liters * (request.alcohol_percentage / 100)
    
    # Calculate Import Duty
    import_duty = request.cif_value * rates["import_duty_rate"]
    
    # Calculate Excise Duty
    if request.alcohol_type in ["spirits", "liqueur", "other"]:
        # Spirits: charged per liter of pure alcohol (LPA)
        excise_rate = rates.get("excise_per_lpa", 15.00)
        excise_duty = pure_alcohol_liters * excise_rate
        excise_calculation = f"{pure_alcohol_liters:.2f} LPA × ${excise_rate:.2f}/LPA"
    else:
        # Beer/Wine: charged per liter of beverage
        excise_rate = rates.get("excise_per_liter", 2.00)
        excise_duty = total_volume_liters * excise_rate
        excise_calculation = f"{total_volume_liters:.2f}L × ${excise_rate:.2f}/L"
    
    # Calculate VAT (on CIF + Duty + Excise)
    vat_base = request.cif_value + import_duty + excise_duty
    vat = vat_base * VAT_RATE
    
    # Calculate License Fee
    license_fee = 0.0
    if request.has_liquor_license:
        license_fee = LICENSE_FEE_BASE
        if request.quantity > 24:
            license_fee += (request.quantity - 24) * 0.50  # Additional fee for bulk
    
    # Total Landed Cost
    total_landed_cost = request.cif_value + import_duty + excise_duty + vat + license_fee
    
    # Warnings and flags
    if request.alcohol_percentage > 40:
        warnings.append("High ABV product (>40%) - may require additional inspection")
    if total_volume_liters > 10 and not request.has_liquor_license:
        warnings.append("Volume exceeds personal use allowance - liquor license recommended")
    if rates["requires_permit"]:
        warnings.append(f"Import permit required for {request.alcohol_type.value}")
    if request.cif_value > 5000:
        warnings.append("High value shipment - may be subject to additional documentation")
    
    # Create calculation record
    calc_id = str(uuid.uuid4())
    calculation = {
        "id": calc_id,
        "user_id": user["id"],
        "product_name": request.product_name,
        "alcohol_type": request.alcohol_type,
        "hs_code": rates["hs_code"],
        "hs_description": rates["hs_description"],
        "quantity": request.quantity,
        "total_volume_liters": round(total_volume_liters, 2),
        "alcohol_percentage": request.alcohol_percentage,
        "pure_alcohol_liters": round(pure_alcohol_liters, 2),
        "cif_value": round(request.cif_value, 2),
        "import_duty": round(import_duty, 2),
        "import_duty_rate": f"{rates['import_duty_rate'] * 100:.0f}%",
        "excise_duty": round(excise_duty, 2),
        "excise_calculation": excise_calculation,
        "vat": round(vat, 2),
        "vat_rate": f"{VAT_RATE * 100:.0f}%",
        "license_fee": round(license_fee, 2),
        "total_landed_cost": round(total_landed_cost, 2),
        "breakdown": {
            "cif_value": round(request.cif_value, 2),
            "import_duty": round(import_duty, 2),
            "excise_duty": round(excise_duty, 2),
            "vat": round(vat, 2),
            "license_fee": round(license_fee, 2),
            "total": round(total_landed_cost, 2)
        },
        "warnings": warnings,
        "requires_permit": rates["requires_permit"],
        "country_of_origin": request.country_of_origin,
        "brand_label": request.brand_label,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Save to database
    await db.alcohol_calculations.insert_one(calculation)
    
    calculation["created_at"] = datetime.fromisoformat(calculation["created_at"])
    return calculation

@api_router.get("/alcohol/calculations", response_model=List[AlcoholCalculationResult])
async def get_alcohol_calculations(user: dict = Depends(get_current_user)):
    """Get user's alcohol calculation history"""
    calculations = await db.alcohol_calculations.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    for calc in calculations:
        if isinstance(calc.get("created_at"), str):
            calc["created_at"] = datetime.fromisoformat(calc["created_at"])
    
    return calculations

@api_router.get("/alcohol/calculations/{calc_id}", response_model=AlcoholCalculationResult)
async def get_alcohol_calculation(calc_id: str, user: dict = Depends(get_current_user)):
    """Get a specific alcohol calculation"""
    calculation = await db.alcohol_calculations.find_one(
        {"id": calc_id, "user_id": user["id"]},
        {"_id": 0}
    )
    if not calculation:
        raise HTTPException(status_code=404, detail="Calculation not found")
    
    if isinstance(calculation.get("created_at"), str):
        calculation["created_at"] = datetime.fromisoformat(calculation["created_at"])
    
    return calculation

@api_router.get("/alcohol/calculations/{calc_id}/export")
async def export_alcohol_calculation(calc_id: str, user: dict = Depends(get_current_user)):
    """Export alcohol calculation as PDF-ready data"""
    from fastapi.responses import JSONResponse
    
    calculation = await db.alcohol_calculations.find_one(
        {"id": calc_id, "user_id": user["id"]},
        {"_id": 0}
    )
    if not calculation:
        raise HTTPException(status_code=404, detail="Calculation not found")
    
    # Format for PDF export
    export_data = {
        "title": "Bahamas Customs Alcohol Import Duty Calculation",
        "reference_number": calc_id[:8].upper(),
        "date": datetime.now(timezone.utc).strftime("%B %d, %Y"),
        "product_details": {
            "Product Name": calculation["product_name"],
            "Brand/Label": calculation.get("brand_label", "N/A"),
            "Type": calculation["alcohol_type"].title(),
            "HS Code": calculation["hs_code"],
            "HS Description": calculation["hs_description"],
            "Country of Origin": calculation.get("country_of_origin", "N/A"),
            "Quantity": f"{calculation['quantity']} units",
            "Total Volume": f"{calculation['total_volume_liters']} liters",
            "Alcohol Content": f"{calculation['alcohol_percentage']}% ABV",
            "Pure Alcohol": f"{calculation['pure_alcohol_liters']} liters"
        },
        "duty_breakdown": {
            "CIF Value (USD)": f"${calculation['cif_value']:,.2f}",
            f"Import Duty ({calculation['import_duty_rate']})": f"${calculation['import_duty']:,.2f}",
            f"Excise Duty ({calculation['excise_calculation']})": f"${calculation['excise_duty']:,.2f}",
            f"VAT ({calculation['vat_rate']})": f"${calculation['vat']:,.2f}",
            "License/Processing Fee": f"${calculation['license_fee']:,.2f}",
            "TOTAL LANDED COST": f"${calculation['total_landed_cost']:,.2f}"
        },
        "warnings": calculation.get("warnings", []),
        "requires_permit": calculation.get("requires_permit", False),
        "disclaimer": "This calculation is for estimation purposes. Final duties may vary based on Bahamas Customs assessment."
    }
    
    return JSONResponse(content=export_data)

@api_router.get("/alcohol/rates")
async def get_alcohol_rates(user: dict = Depends(get_current_user)):
    """Get current alcohol duty rates"""
    return {
        "rates": ALCOHOL_RATES,
        "vat_rate": VAT_RATE,
        "license_fee_base": LICENSE_FEE_BASE,
        "last_updated": "January 2026",
        "note": "Rates based on Bahamas Customs Management Act"
    }

@api_router.get("/alcohol/template")
async def get_alcohol_template(user: dict = Depends(get_current_user)):
    """Download CSV template for bulk alcohol calculations"""
    from fastapi.responses import StreamingResponse
    
    template_data = """product_name,alcohol_type,volume_ml,alcohol_percentage,quantity,cif_value,country_of_origin,brand_label,has_liquor_license
Bacardi Superior Rum,spirits,750,40,12,540,Puerto Rico,Bacardi,false
Heineken Beer,beer,330,5,24,48,Netherlands,Heineken,false
Chardonnay White Wine,wine,750,13,6,120,France,Robert Mondavi,false
Baileys Irish Cream,liqueur,750,17,4,160,Ireland,Baileys,true
Jack Daniels Whiskey,spirits,1000,40,6,300,USA,Jack Daniels,false"""
    
    output = io.StringIO()
    output.write(template_data)
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=alcohol_import_template.csv"}
    )

@api_router.post("/alcohol/upload")
async def upload_alcohol_batch(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """Process bulk alcohol calculations from CSV/Excel upload"""
    
    # Validate file type
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ["csv", "xlsx", "xls"]:
        raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")
    
    content = await file.read()
    
    try:
        if file_ext == "csv":
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
    
    # Normalize column names
    df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')
    
    # Required columns
    required_cols = ['product_name', 'alcohol_type', 'volume_ml', 'alcohol_percentage', 'quantity', 'cif_value']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise HTTPException(status_code=400, detail=f"Missing required columns: {', '.join(missing_cols)}")
    
    # Process each row
    results = []
    errors = []
    batch_id = str(uuid.uuid4())
    total_landed_cost = 0
    
    for idx, row in df.iterrows():
        try:
            # Validate alcohol type
            alcohol_type = str(row['alcohol_type']).lower().strip()
            if alcohol_type not in ALCOHOL_RATES:
                alcohol_type = 'other'
            
            rates = ALCOHOL_RATES[alcohol_type]
            warnings = []
            
            # Parse values
            volume_ml = float(row['volume_ml'])
            alcohol_percentage = float(row['alcohol_percentage'])
            quantity = int(row['quantity'])
            cif_value = float(row['cif_value'])
            has_license = str(row.get('has_liquor_license', 'false')).lower() in ['true', '1', 'yes']
            
            # Calculate volumes
            volume_per_unit_liters = volume_ml / 1000
            total_volume_liters = volume_per_unit_liters * quantity
            pure_alcohol_liters = total_volume_liters * (alcohol_percentage / 100)
            
            # Calculate duties
            import_duty = cif_value * rates["import_duty_rate"]
            
            if alcohol_type in ["spirits", "liqueur", "other"]:
                excise_rate = rates.get("excise_per_lpa", 15.00)
                excise_duty = pure_alcohol_liters * excise_rate
                excise_calculation = f"{pure_alcohol_liters:.2f} LPA × ${excise_rate:.2f}/LPA"
            else:
                excise_rate = rates.get("excise_per_liter", 2.00)
                excise_duty = total_volume_liters * excise_rate
                excise_calculation = f"{total_volume_liters:.2f}L × ${excise_rate:.2f}/L"
            
            vat_base = cif_value + import_duty + excise_duty
            vat = vat_base * VAT_RATE
            
            license_fee = 0.0
            if has_license:
                license_fee = LICENSE_FEE_BASE
                if quantity > 24:
                    license_fee += (quantity - 24) * 0.50
            
            item_total = cif_value + import_duty + excise_duty + vat + license_fee
            total_landed_cost += item_total
            
            # Warnings
            if alcohol_percentage > 40:
                warnings.append("High ABV (>40%)")
            if rates["requires_permit"]:
                warnings.append("Permit required")
            
            result = {
                "row": idx + 1,
                "product_name": str(row['product_name']),
                "alcohol_type": alcohol_type,
                "hs_code": rates["hs_code"],
                "quantity": quantity,
                "total_volume_liters": round(total_volume_liters, 2),
                "alcohol_percentage": alcohol_percentage,
                "cif_value": round(cif_value, 2),
                "import_duty": round(import_duty, 2),
                "import_duty_rate": f"{rates['import_duty_rate'] * 100:.0f}%",
                "excise_duty": round(excise_duty, 2),
                "excise_calculation": excise_calculation,
                "vat": round(vat, 2),
                "license_fee": round(license_fee, 2),
                "total_landed_cost": round(item_total, 2),
                "warnings": warnings,
                "requires_permit": rates["requires_permit"]
            }
            results.append(result)
            
        except Exception as e:
            errors.append({"row": idx + 1, "error": str(e)})
    
    # Save batch to database
    batch_record = {
        "id": batch_id,
        "user_id": user["id"],
        "filename": file.filename,
        "total_items": len(results),
        "total_landed_cost": round(total_landed_cost, 2),
        "results": results,
        "errors": errors,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.alcohol_batches.insert_one(batch_record)
    
    return {
        "batch_id": batch_id,
        "filename": file.filename,
        "total_items": len(results),
        "successful": len(results),
        "failed": len(errors),
        "total_landed_cost": round(total_landed_cost, 2),
        "results": results,
        "errors": errors
    }

@api_router.get("/alcohol/batches")
async def get_alcohol_batches(user: dict = Depends(get_current_user)):
    """Get user's batch calculation history"""
    batches = await db.alcohol_batches.find(
        {"user_id": user["id"]},
        {"_id": 0, "results": 0}
    ).sort("created_at", -1).to_list(50)
    
    for batch in batches:
        if isinstance(batch.get("created_at"), str):
            batch["created_at"] = datetime.fromisoformat(batch["created_at"])
    
    return batches

@api_router.get("/alcohol/batches/{batch_id}")
async def get_alcohol_batch(batch_id: str, user: dict = Depends(get_current_user)):
    """Get specific batch calculation details"""
    batch = await db.alcohol_batches.find_one(
        {"id": batch_id, "user_id": user["id"]},
        {"_id": 0}
    )
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    if isinstance(batch.get("created_at"), str):
        batch["created_at"] = datetime.fromisoformat(batch["created_at"])
    
    return batch

@api_router.get("/alcohol/batches/{batch_id}/export")
async def export_alcohol_batch(batch_id: str, format: str = "csv", user: dict = Depends(get_current_user)):
    """Export batch calculation as CSV or Excel"""
    from fastapi.responses import StreamingResponse
    
    batch = await db.alcohol_batches.find_one(
        {"id": batch_id, "user_id": user["id"]},
        {"_id": 0}
    )
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    # Prepare export data
    export_data = []
    for item in batch["results"]:
        export_data.append({
            "Product Name": item["product_name"],
            "Alcohol Type": item["alcohol_type"],
            "HS Code": item["hs_code"],
            "Quantity": item["quantity"],
            "Total Volume (L)": item["total_volume_liters"],
            "ABV %": item["alcohol_percentage"],
            "CIF Value": item["cif_value"],
            "Import Duty": item["import_duty"],
            "Duty Rate": item["import_duty_rate"],
            "Excise Duty": item["excise_duty"],
            "VAT": item["vat"],
            "License Fee": item["license_fee"],
            "Total Landed Cost": item["total_landed_cost"],
            "Permit Required": "Yes" if item["requires_permit"] else "No",
            "Warnings": "; ".join(item.get("warnings", []))
        })
    
    df = pd.DataFrame(export_data)
    
    # Add summary row
    summary_row = {col: "" for col in df.columns}
    summary_row["Product Name"] = "TOTAL"
    summary_row["Total Landed Cost"] = batch["total_landed_cost"]
    df = pd.concat([df, pd.DataFrame([summary_row])], ignore_index=True)
    
    if format == "xlsx":
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Alcohol Duties')
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=alcohol_batch_{batch_id[:8]}.xlsx"}
        )
    else:
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=alcohol_batch_{batch_id[:8]}.csv"}
        )

# ============= CMA REGULATIONS MODULE =============

class CMARegulationResponse(BaseModel):
    id: str
    category: str
    section: str
    title: str
    reference: str
    content: str
    keywords: List[str]
    created_at: datetime

# ============= CUSTOMS FORMS MODULE =============
class CustomsFormResponse(BaseModel):
    id: str
    form_number: str
    form_name: str
    category: str
    description: str
    usage: str
    where_to_obtain: str
    related_section: Optional[str] = None

@api_router.get("/customs-forms", response_model=List[CustomsFormResponse])
async def get_customs_forms(
    search: Optional[str] = None,
    category: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get Bahamas Customs forms list"""
    query = {}
    if search:
        query["$or"] = [
            {"form_number": {"$regex": search, "$options": "i"}},
            {"form_name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    if category:
        query["category"] = category
    
    forms = await db.customs_forms.find(query, {"_id": 0}).sort("form_number", 1).to_list(200)
    return forms

@api_router.get("/customs-forms/categories")
async def get_forms_categories(user: dict = Depends(get_current_user)):
    """Get customs form categories"""
    categories = await db.customs_forms.distinct("category")
    return {"categories": categories}

# ============= COUNTRY CODES MODULE =============
class CountryCodeResponse(BaseModel):
    id: str
    code: str
    alpha3: str
    name: str
    region: str
    trade_agreement: Optional[str] = None
    notes: Optional[str] = None

@api_router.get("/country-codes", response_model=List[CountryCodeResponse])
async def get_country_codes(
    search: Optional[str] = None,
    region: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get country codes for customs declarations"""
    query = {}
    if search:
        query["$or"] = [
            {"code": {"$regex": search, "$options": "i"}},
            {"alpha3": {"$regex": search, "$options": "i"}},
            {"name": {"$regex": search, "$options": "i"}}
        ]
    if region:
        query["region"] = region
    
    countries = await db.country_codes.find(query, {"_id": 0}).sort("name", 1).to_list(300)
    return countries

@api_router.get("/country-codes/regions")
async def get_country_regions(user: dict = Depends(get_current_user)):
    """Get country regions"""
    regions = await db.country_codes.distinct("region")
    return {"regions": regions}

# ============= USER NOTATIONS MODULE =============
class NotationCreate(BaseModel):
    label: str
    content: str  # Max 100 words enforced in validation
    reference_type: str  # entry, tariff_code, general
    reference_id: Optional[str] = None

class NotationResponse(BaseModel):
    id: str
    user_id: str
    label: str
    content: str
    reference_type: str
    reference_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

@api_router.get("/notations", response_model=List[NotationResponse])
async def get_notations(
    reference_type: Optional[str] = None,
    search: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get user's notations"""
    query = {"user_id": user["id"]}
    if reference_type:
        query["reference_type"] = reference_type
    if search:
        query["$or"] = [
            {"label": {"$regex": search, "$options": "i"}},
            {"content": {"$regex": search, "$options": "i"}}
        ]
    
    notations = await db.notations.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    for note in notations:
        if isinstance(note.get("created_at"), str):
            note["created_at"] = datetime.fromisoformat(note["created_at"])
        if isinstance(note.get("updated_at"), str):
            note["updated_at"] = datetime.fromisoformat(note["updated_at"])
    
    return notations

@api_router.post("/notations", response_model=NotationResponse)
async def create_notation(notation: NotationCreate, user: dict = Depends(get_current_user)):
    """Create a new notation"""
    # Validate word count (max 100 words)
    word_count = len(notation.content.split())
    if word_count > 100:
        raise HTTPException(status_code=400, detail=f"Content exceeds 100 word limit ({word_count} words)")
    
    if not notation.label.strip():
        raise HTTPException(status_code=400, detail="Label is required")
    
    note_id = str(uuid.uuid4())
    note_doc = {
        "id": note_id,
        "user_id": user["id"],
        "label": notation.label.strip(),
        "content": notation.content.strip(),
        "reference_type": notation.reference_type,
        "reference_id": notation.reference_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": None
    }
    
    await db.notations.insert_one(note_doc)
    note_doc["created_at"] = datetime.fromisoformat(note_doc["created_at"])
    
    return note_doc

@api_router.put("/notations/{note_id}", response_model=NotationResponse)
async def update_notation(note_id: str, notation: NotationCreate, user: dict = Depends(get_current_user)):
    """Update a notation"""
    existing = await db.notations.find_one({"id": note_id, "user_id": user["id"]}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Notation not found")
    
    word_count = len(notation.content.split())
    if word_count > 100:
        raise HTTPException(status_code=400, detail=f"Content exceeds 100 word limit ({word_count} words)")
    
    await db.notations.update_one(
        {"id": note_id},
        {"$set": {
            "label": notation.label.strip(),
            "content": notation.content.strip(),
            "reference_type": notation.reference_type,
            "reference_id": notation.reference_id,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    updated = await db.notations.find_one({"id": note_id}, {"_id": 0})
    if isinstance(updated.get("created_at"), str):
        updated["created_at"] = datetime.fromisoformat(updated["created_at"])
    if isinstance(updated.get("updated_at"), str):
        updated["updated_at"] = datetime.fromisoformat(updated["updated_at"])
    
    return updated

@api_router.delete("/notations/{note_id}")
async def delete_notation(note_id: str, user: dict = Depends(get_current_user)):
    """Delete a notation"""
    result = await db.notations.delete_one({"id": note_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Notation not found")
    return {"message": "Notation deleted"}

@api_router.get("/cma/search", response_model=List[CMARegulationResponse])
async def search_cma_regulations(
    q: Optional[str] = None,
    category: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Search CMA regulations by keyword or category"""
    query = {}
    
    if q:
        search_terms = q.lower().split()
        query["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"content": {"$regex": q, "$options": "i"}},
            {"reference": {"$regex": q, "$options": "i"}},
            {"keywords": {"$in": search_terms}}
        ]
    
    if category:
        query["category"] = {"$regex": category, "$options": "i"}
    
    regulations = await db.cma_regulations.find(query, {"_id": 0}).to_list(100)
    
    for reg in regulations:
        if isinstance(reg.get("created_at"), str):
            reg["created_at"] = datetime.fromisoformat(reg["created_at"])
    
    return regulations

@api_router.get("/cma/categories")
async def get_cma_categories(user: dict = Depends(get_current_user)):
    """Get all CMA regulation categories"""
    categories = await db.cma_regulations.distinct("category")
    return {"categories": categories}

@api_router.get("/cma/regulations/{reg_id}", response_model=CMARegulationResponse)
async def get_cma_regulation(reg_id: str, user: dict = Depends(get_current_user)):
    """Get specific CMA regulation by ID"""
    regulation = await db.cma_regulations.find_one({"id": reg_id}, {"_id": 0})
    if not regulation:
        raise HTTPException(status_code=404, detail="Regulation not found")
    
    if isinstance(regulation.get("created_at"), str):
        regulation["created_at"] = datetime.fromisoformat(regulation["created_at"])
    
    return regulation

# ============= CLASSI HELPDESK CHATBOT =============
class ClassiChatRequest(BaseModel):
    message: str

# Bahamas Customs Knowledge Base
BAHAMAS_CUSTOMS_KNOWLEDGE = """
## BAHAMAS CUSTOMS INFORMATION

### Contact Information
- **Bahamas Customs Department Main Office**
  - Address: Thompson Boulevard, Nassau, The Bahamas
  - Phone: +1 (242) 325-6550 / 325-6551
  - Fax: +1 (242) 322-6505
  - Email: customsinfo@bahamas.gov.bs
  - Website: www.bahamas.gov.bs/customs
  - Hours: Monday-Friday, 9:00 AM - 5:00 PM

### Ports of Entry in The Bahamas
1. **Nassau (New Providence)**
   - Nassau Container Port - Main commercial port
   - Prince George Wharf - Cruise and cargo
   - Lynden Pindling International Airport (NAS)
   
2. **Freeport (Grand Bahama)**
   - Freeport Container Port - Major transshipment hub
   - Grand Bahama International Airport (FPO)
   - Freeport Harbour Company
   
3. **Family Islands Ports**
   - Marsh Harbour, Abaco (MHH)
   - Governor's Harbour, Eleuthera (GHB)
   - George Town, Exuma (GGT)
   - Rock Sound, Eleuthera (RSD)
   - North Eleuthera (ELH)
   - San Salvador (ZSA)
   - Cat Island (TBI)
   - Long Island (LGI)

### Common Customs Forms
- **C-13**: Customs Entry Form (main import declaration)
- **C-14**: Customs Declaration for Unaccompanied Baggage
- **C-15**: Export Entry Form
- **C-17**: Transshipment Entry
- **C-18**: Warehouse Entry
- **C-63**: Application for Duty Exemption
- **C-78**: Application for Temporary Import Permit
- **SAD (Single Administrative Document)**: ASYCUDA World format

### Duty Rates Overview
- **0% (Free)**: Essential medicines, some raw materials, educational materials
- **5-10%**: Basic foodstuffs, agricultural inputs, IT equipment
- **25-35%**: General manufactured goods, clothing, footwear
- **35-45%**: Alcoholic beverages (plus excise duty)
- **45%**: Luxury items, certain protected goods

### Import Process Steps
1. Obtain business license (if commercial)
2. Register with Customs (get TIN - Taxpayer ID Number)
3. Prepare commercial invoice, packing list, bill of lading
4. Classify goods using correct HS codes
5. Submit entry via ASYCUDA World or customs broker
6. Pay duties, VAT (10%), and processing fees
7. Arrange for inspection if required
8. Clear goods and collect from port

### Special Requirements
- **Restricted Items**: Firearms, ammunition, drugs, endangered species
- **Permit Required**: Alcohol, pharmaceuticals, live animals, plants
- **Prohibited**: Counterfeit goods, obscene materials, certain weapons
- **VAT**: 10% on CIF value plus duties

### Best Practices for Customs Entries
1. Ensure accurate HS code classification (use GRI rules 1-6)
2. Declare correct value (transaction value method)
3. Include country of origin for preferential rates
4. Keep all documentation for 5 years
5. Use licensed customs broker for complex shipments
6. Apply for exemptions before importing (C-63 form)
7. Check restricted/prohibited lists before shipping
"""

@api_router.post("/classi/chat")
async def classi_chat(request: ClassiChatRequest, user: dict = Depends(get_current_user)):
    """Classi AI Helpdesk - Bahamas Customs Assistant"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        # Fallback response without AI
        return {"response": "I'm currently in limited mode. For immediate assistance, please contact Bahamas Customs at +1 (242) 325-6550."}
    
    try:
        # Fetch HS codes from database for context
        hs_codes = await db.hs_codes.find({}, {"_id": 0, "code": 1, "description": 1, "duty_rate": 1}).to_list(100)
        hs_context = "\n".join([f"- {c['code']}: {c['description']} (Duty: {c.get('duty_rate', 'N/A')})" for c in hs_codes[:50]])
        
        # Fetch country codes if available
        country_codes = await db.country_codes.find({}, {"_id": 0}).to_list(50)
        country_context = "\n".join([f"- {c.get('code', '')}: {c.get('name', '')}" for c in country_codes[:30]]) if country_codes else ""
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"classi-{user['id']}-{uuid.uuid4()}",
            system_message=f"""You are Classi, a friendly and knowledgeable AI assistant for the Class-B HS Code Agent application - a Bahamas Customs classification system.

Your role is to help users with:
1. Understanding how to use the app features (HS classification, alcohol calculator, CMA reference)
2. Bahamas Customs procedures, forms, and regulations
3. HS code guidance and classification tips
4. Duty rates and calculations
5. Port of entry information
6. When and how to contact Bahamas Customs directly

{BAHAMAS_CUSTOMS_KNOWLEDGE}

### Available HS Codes in Library:
{hs_context}

### Country Codes:
{country_context}

Guidelines:
- Be helpful, friendly, and professional
- Use the Bahamian context (e.g., BSD currency, local regulations)
- Always recommend contacting Bahamas Customs directly for official rulings
- Provide specific form numbers when relevant (C-13, C-14, etc.)
- If unsure, say so and recommend official sources
- Keep responses concise but informative
- Include relevant phone numbers and emails when appropriate"""
        ).with_model("openai", "gpt-5.2")
        
        response = await chat.send_message(UserMessage(text=request.message))
        return {"response": response}
        
    except Exception as e:
        logger.error(f"Classi chat error: {e}")
        return {"response": f"I'm having trouble processing your request. For immediate assistance, please contact Bahamas Customs at +1 (242) 325-6550 or email customsinfo@bahamas.gov.bs."}

# ============= HS CODE AUTO-SUGGEST =============
@api_router.get("/hs-codes/suggest")
async def suggest_hs_codes(
    q: str,
    limit: int = 10,
    user: dict = Depends(get_current_user)
):
    """Auto-suggest HS codes based on description query"""
    if not q or len(q) < 2:
        return {"suggestions": []}
    
    # Search by code prefix or description
    query = {
        "$or": [
            {"code": {"$regex": f"^{q}", "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}}
        ]
    }
    
    codes = await db.hs_codes.find(
        query, 
        {"_id": 0, "code": 1, "description": 1, "chapter": 1, "duty_rate": 1, "is_restricted": 1, "requires_permit": 1}
    ).limit(limit).to_list(limit)
    
    return {"suggestions": codes}

# ============= ROOT ROUTE =============
@api_router.get("/")
async def root():
    return {"message": "Bahamas HS Code Classification API", "version": "1.0.0"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
