from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks, Body
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
    USER_UPDATED = "user_updated"

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class AdminAccessLevel(str, Enum):
    FULL = "full"  # Full access to all admin features
    BROADCAST_ONLY = "broadcast_only"  # View + broadcast notifications only
    VIEW_ONLY = "view_only"  # View only, can export data

class AccountStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"

# ============= MODELS =============
class UserBase(BaseModel):
    email: EmailStr
    name: str
    company: Optional[str] = None

class UserCreate(UserBase):
    password: str
    secret_code: str  # 4-6 digit numeric code for account recovery

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
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    source: Optional[str] = None

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
    if user.get("role") not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def require_super_admin(user: dict = Depends(get_current_user)):
    if user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Super Admin access required")
    return user

async def require_admin_with_access(required_level: str):
    """Factory function to check admin access level"""
    async def checker(user: dict = Depends(get_current_user)):
        if user.get("role") not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Super admins always have full access
        if user.get("role") == UserRole.SUPER_ADMIN:
            return user
        
        access_level = user.get("admin_access_level", AdminAccessLevel.VIEW_ONLY)
        
        if required_level == "full" and access_level != AdminAccessLevel.FULL:
            raise HTTPException(status_code=403, detail="Full admin access required")
        elif required_level == "broadcast" and access_level not in [AdminAccessLevel.FULL, AdminAccessLevel.BROADCAST_ONLY]:
            raise HTTPException(status_code=403, detail="Broadcast access required")
        
        return user
    return checker

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
    # Validate secret_code (4-6 digits)
    if not user_data.secret_code or not user_data.secret_code.isdigit() or len(user_data.secret_code) < 4 or len(user_data.secret_code) > 6:
        raise HTTPException(status_code=400, detail="Account Secret Code must be 4-6 digits")
    
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
        "secret_code": hash_password(user_data.secret_code),  # Store hashed
        "role": UserRole.USER,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_doc)
    token = create_token(user_id, user_data.email, UserRole.USER)
    
    return {"token": token, "user": {"id": user_id, "email": user_data.email, "name": user_data.name, "role": UserRole.USER}}

@api_router.post("/auth/login", response_model=dict)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check account status
    account_status = user.get("account_status", AccountStatus.ACTIVE)
    if account_status == AccountStatus.DEACTIVATED:
        raise HTTPException(status_code=401, detail="Account has been deactivated")
    if account_status == AccountStatus.SUSPENDED:
        raise HTTPException(status_code=401, detail="Account is suspended. Please contact administrator.")
    
    token = create_token(user["id"], user["email"], user.get("role", UserRole.USER))
    return {
        "token": token, 
        "user": {
            "id": user["id"], 
            "email": user["email"], 
            "name": user["name"],
            "role": user.get("role", UserRole.USER),
            "admin_access_level": user.get("admin_access_level"),
            "must_change_password": user.get("must_change_password", False),
            "must_set_secret_code": user.get("must_set_secret_code", False)
        }
    }

@api_router.get("/auth/me", response_model=dict)
async def get_me(user: dict = Depends(get_current_user)):
    full_user = await db.users.find_one({"id": user["id"]}, {"_id": 0, "password": 0, "secret_code": 0})
    return {
        "id": full_user["id"], 
        "email": full_user["email"], 
        "name": full_user["name"], 
        "role": full_user.get("role", UserRole.USER),
        "admin_access_level": full_user.get("admin_access_level"),
        "must_change_password": full_user.get("must_change_password", False),
        "must_set_secret_code": full_user.get("must_set_secret_code", False)
    }

# ============= USER PROFILE MANAGEMENT =============
class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    secret_code: str  # Required for verification

class EmailUpdate(BaseModel):
    new_email: EmailStr
    secret_code: str  # Required for verification

class PasswordUpdate(BaseModel):
    current_password: Optional[str] = None  # Optional if using secret_code
    new_password: str
    secret_code: str  # Required for verification

class SecretCodeReset(BaseModel):
    email: EmailStr
    secret_code: str
    new_password: str

@api_router.get("/auth/profile")
async def get_profile(user: dict = Depends(get_current_user)):
    """Get full user profile"""
    full_user = await db.users.find_one({"id": user["id"]}, {"_id": 0, "password": 0, "secret_code": 0})
    if not full_user:
        raise HTTPException(status_code=404, detail="User not found")
    return full_user

@api_router.put("/auth/profile")
async def update_profile(update_data: ProfileUpdate, user: dict = Depends(get_current_user)):
    """Update user profile (requires secret_code verification)"""
    # Verify secret code
    full_user = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    if not full_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not verify_password(update_data.secret_code, full_user.get("secret_code", "")):
        raise HTTPException(status_code=403, detail="Invalid Account Secret Code")
    
    # Build update document
    update_doc = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if update_data.name is not None:
        update_doc["name"] = update_data.name
    if update_data.company is not None:
        update_doc["company"] = update_data.company
    
    await db.users.update_one({"id": user["id"]}, {"$set": update_doc})
    
    # Return updated user
    updated_user = await db.users.find_one({"id": user["id"]}, {"_id": 0, "password": 0, "secret_code": 0})
    return {"message": "Profile updated successfully", "user": updated_user}

@api_router.put("/auth/email")
async def update_email(update_data: EmailUpdate, user: dict = Depends(get_current_user)):
    """Update user email address (requires secret_code verification)"""
    # Verify secret code
    full_user = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    if not full_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not verify_password(update_data.secret_code, full_user.get("secret_code", "")):
        raise HTTPException(status_code=403, detail="Invalid Account Secret Code")
    
    # Check if new email is already in use
    existing = await db.users.find_one({"email": update_data.new_email, "id": {"$ne": user["id"]}})
    if existing:
        raise HTTPException(status_code=400, detail="Email already in use by another account")
    
    # Update email
    await db.users.update_one(
        {"id": user["id"]}, 
        {"$set": {
            "email": update_data.new_email,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Generate new token with updated email
    new_token = create_token(user["id"], update_data.new_email, user.get("role", UserRole.USER))
    
    return {"message": "Email updated successfully", "token": new_token, "email": update_data.new_email}

@api_router.put("/auth/password")
async def update_password(update_data: PasswordUpdate, user: dict = Depends(get_current_user)):
    """Update user password (requires secret_code verification)"""
    # Verify secret code
    full_user = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    if not full_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not verify_password(update_data.secret_code, full_user.get("secret_code", "")):
        raise HTTPException(status_code=403, detail="Invalid Account Secret Code")
    
    # Optionally verify current password if provided
    if update_data.current_password:
        if not verify_password(update_data.current_password, full_user["password"]):
            raise HTTPException(status_code=403, detail="Current password is incorrect")
    
    # Update password
    await db.users.update_one(
        {"id": user["id"]}, 
        {"$set": {
            "password": hash_password(update_data.new_password),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Password updated successfully"}

@api_router.put("/auth/secret-code")
async def update_secret_code(
    current_secret: str = Body(...),
    new_secret: str = Body(...),
    user: dict = Depends(get_current_user)
):
    """Update Account Secret Code (requires current secret_code)"""
    # Validate new secret code
    if not new_secret.isdigit() or len(new_secret) < 4 or len(new_secret) > 6:
        raise HTTPException(status_code=400, detail="New secret code must be 4-6 digits")
    
    # Verify current secret code
    full_user = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    if not full_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not verify_password(current_secret, full_user.get("secret_code", "")):
        raise HTTPException(status_code=403, detail="Invalid current Account Secret Code")
    
    # Update secret code
    await db.users.update_one(
        {"id": user["id"]}, 
        {"$set": {
            "secret_code": hash_password(new_secret),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Account Secret Code updated successfully"}

@api_router.post("/auth/recover-with-code")
async def recover_with_secret_code(recovery_data: SecretCodeReset):
    """Reset password using email + secret code (alternative to email link)"""
    user = await db.users.find_one({"email": recovery_data.email}, {"_id": 0})
    
    if not user:
        # Don't reveal if email exists
        raise HTTPException(status_code=400, detail="Invalid email or secret code")
    
    if not verify_password(recovery_data.secret_code, user.get("secret_code", "")):
        raise HTTPException(status_code=400, detail="Invalid email or secret code")
    
    # Update password
    await db.users.update_one(
        {"email": recovery_data.email}, 
        {"$set": {
            "password": hash_password(recovery_data.new_password),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Password reset successfully. You can now log in with your new password."}

# ============= PASSWORD RESET =============
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

@api_router.post("/auth/forgot-password")
async def forgot_password(request: PasswordResetRequest):
    """Request password reset - generates token and sends email"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import secrets
    
    user = await db.users.find_one({"email": request.email}, {"_id": 0})
    
    # Always return success to prevent email enumeration attacks
    if not user:
        return {"message": "If an account exists with this email, you will receive a password reset link."}
    
    # Generate reset token (valid for 1 hour)
    reset_token = secrets.token_urlsafe(32)
    reset_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
    
    # Store reset token in database
    await db.password_resets.update_one(
        {"email": request.email},
        {
            "$set": {
                "email": request.email,
                "token": reset_token,
                "expires_at": reset_expiry.isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        },
        upsert=True
    )
    
    # Send email with reset link
    NOTIFICATION_EMAIL = "gfp6ixhc@yourfeedback.anonaddy.me"
    frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    reset_link = f"{frontend_url}/reset-password?token={reset_token}"
    
    email_body = f"""
Password Reset Request - Class-B HS Code Agent

Hello {user.get('name', 'User')},

We received a request to reset your password. Click the link below to set a new password:

{reset_link}

This link will expire in 1 hour.

If you didn't request this password reset, please ignore this email.

---
Request timestamp: {datetime.now(timezone.utc).isoformat()}
"""
    
    try:
        print(f"Password reset requested for {request.email}")
        
        smtp_host = os.environ.get('SMTP_HOST', 'localhost')
        smtp_port = int(os.environ.get('SMTP_PORT', 25))
        
        msg = MIMEMultipart()
        msg['From'] = f"Class-B Agent <noreply@classb-agent.com>"
        msg['To'] = request.email
        msg['Subject'] = "[Class-B Agent] Password Reset Request"
        msg.attach(MIMEText(email_body, 'plain'))
        
        if os.environ.get('SMTP_HOST'):
            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                server.sendmail(msg['From'], [request.email], msg.as_string())
    except Exception as e:
        print(f"Password reset email failed (token still saved): {str(e)}")
    
    return {"message": "If an account exists with this email, you will receive a password reset link."}

@api_router.post("/auth/reset-password")
async def reset_password(request: PasswordResetConfirm):
    """Reset password using token"""
    # Find valid reset token
    reset_record = await db.password_resets.find_one({"token": request.token}, {"_id": 0})
    
    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    # Check if token is expired
    expires_at = datetime.fromisoformat(reset_record["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        # Delete expired token
        await db.password_resets.delete_one({"token": request.token})
        raise HTTPException(status_code=400, detail="Reset token has expired. Please request a new one.")
    
    # Update user password
    new_password_hash = hash_password(request.new_password)
    result = await db.users.update_one(
        {"email": reset_record["email"]},
        {"$set": {"password": new_password_hash}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to update password")
    
    # Delete used token
    await db.password_resets.delete_one({"token": request.token})
    
    return {"message": "Password has been reset successfully. You can now log in with your new password."}

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

@api_router.delete("/classifications/{classification_id}/items/{item_index}")
async def delete_classification_item(
    classification_id: str,
    item_index: int,
    user: dict = Depends(get_current_user)
):
    """Delete a specific item from a classification"""
    classification = await db.classifications.find_one(
        {"id": classification_id, "user_id": user["id"]},
        {"_id": 0}
    )
    if not classification:
        raise HTTPException(status_code=404, detail="Classification not found")
    
    if item_index < 0 or item_index >= len(classification["items"]):
        raise HTTPException(status_code=400, detail="Invalid item index")
    
    # Remove item
    classification["items"].pop(item_index)
    
    # Recalculate stats
    auto_approved = sum(1 for item in classification["items"] if item.get("review_status") == "auto_approved")
    
    await db.classifications.update_one(
        {"id": classification_id},
        {"$set": {
            "items": classification["items"],
            "total_items": len(classification["items"]),
            "auto_approved_count": auto_approved,
            "needs_review_count": len(classification["items"]) - auto_approved,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Item deleted successfully"}

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

@api_router.delete("/classifications/{classification_id}")
async def delete_classification(classification_id: str, user: dict = Depends(get_current_user)):
    """Delete a classification record"""
    result = await db.classifications.delete_one({"id": classification_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Classification not found")
    # Also delete the associated document
    await db.documents.delete_one({"id": classification_id, "user_id": user["id"]})
    return {"message": "Classification deleted"}

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
    users = await db.users.find({}, {"_id": 0, "password": 0, "secret_code": 0}).to_list(1000)
    return users

@api_router.put("/admin/users/{user_id}/role")
async def update_user_role(user_id: str, role: UserRole, admin: dict = Depends(require_super_admin)):
    # Log the action
    await log_admin_action(admin["id"], "update_role", f"Changed user {user_id} role to {role}")
    result = await db.users.update_one({"id": user_id}, {"$set": {"role": role, "updated_at": datetime.now(timezone.utc).isoformat()}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User role updated"}

# ============= SUPER ADMIN SYSTEM =============

async def log_admin_action(admin_id: str, action_type: str, description: str, metadata: dict = None):
    """Log all admin actions for audit trail"""
    log_entry = {
        "id": str(uuid.uuid4()),
        "admin_id": admin_id,
        "action_type": action_type,
        "description": description,
        "metadata": metadata or {},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.admin_audit_logs.insert_one(log_entry)
    return log_entry

async def seed_super_admin():
    """Create initial super admin if not exists"""
    existing = await db.users.find_one({"email": "admin1@classbagent.com"})
    if not existing:
        admin_doc = {
            "id": str(uuid.uuid4()),
            "email": "admin1@classbagent.com",
            "name": "System Administrator",
            "company": "System",
            "password": hash_password("bcl@ss_1"),
            "secret_code": "",  # Must be set on first login
            "role": UserRole.SUPER_ADMIN,
            "admin_access_level": AdminAccessLevel.FULL,
            "account_status": AccountStatus.ACTIVE,
            "must_change_password": True,
            "must_set_secret_code": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(admin_doc)
        logger.info("Super admin account created: admin1@classbagent.com")
        return True
    return False

# Admin Models
class AdminUserCreate(BaseModel):
    email: EmailStr
    name: str
    company: Optional[str] = ""
    password: str
    role: UserRole = UserRole.USER
    admin_access_level: Optional[AdminAccessLevel] = None

class AdminUserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    company: Optional[str] = None
    role: Optional[UserRole] = None
    admin_access_level: Optional[AdminAccessLevel] = None
    account_status: Optional[AccountStatus] = None

class BroadcastNotification(BaseModel):
    title: str
    message: str
    notification_type: str = "info"  # info, warning, urgent, update
    expires_at: Optional[str] = None

class SystemSettings(BaseModel):
    terms_of_use: Optional[str] = None
    disclaimer_text: Optional[str] = None
    weekly_email_enabled: Optional[bool] = None
    classi_knowledge: Optional[str] = None  # Additional knowledge for Classi AI chatbot

# Super Admin User Management
@api_router.post("/admin/users/create")
async def admin_create_user(user_data: AdminUserCreate, admin: dict = Depends(require_super_admin)):
    """Create a new user account (admin only)"""
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
        "secret_code": "",
        "role": user_data.role,
        "admin_access_level": user_data.admin_access_level if user_data.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN] else None,
        "account_status": AccountStatus.ACTIVE,
        "must_change_password": True,
        "must_set_secret_code": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "created_by": admin["id"]
    }
    
    await db.users.insert_one(user_doc)
    await log_admin_action(admin["id"], "create_user", f"Created user {user_data.email} with role {user_data.role}")
    
    return {"message": "User created successfully", "user_id": user_id}

@api_router.post("/admin/users/bulk-create")
async def admin_bulk_create_users(file: UploadFile = File(...), admin: dict = Depends(require_super_admin)):
    """Bulk create users from CSV/Excel file"""
    content = await file.read()
    
    if file.filename.endswith('.csv'):
        df = pd.read_csv(io.BytesIO(content))
    else:
        df = pd.read_excel(io.BytesIO(content))
    
    required_cols = ['email', 'name', 'password']
    if not all(col in df.columns for col in required_cols):
        raise HTTPException(status_code=400, detail=f"Missing required columns: {required_cols}")
    
    created = 0
    errors = []
    
    for idx, row in df.iterrows():
        try:
            existing = await db.users.find_one({"email": row['email']})
            if existing:
                errors.append(f"Row {idx+1}: Email {row['email']} already exists")
                continue
            
            user_id = str(uuid.uuid4())
            user_doc = {
                "id": user_id,
                "email": row['email'],
                "name": row['name'],
                "company": row.get('company', ''),
                "password": hash_password(str(row['password'])),
                "secret_code": "",
                "role": UserRole.USER,
                "account_status": AccountStatus.ACTIVE,
                "must_change_password": True,
                "must_set_secret_code": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "created_by": admin["id"]
            }
            await db.users.insert_one(user_doc)
            created += 1
        except Exception as e:
            errors.append(f"Row {idx+1}: {str(e)}")
    
    await log_admin_action(admin["id"], "bulk_create_users", f"Bulk created {created} users from {file.filename}")
    
    return {"created": created, "errors": errors}

@api_router.put("/admin/users/{user_id}")
async def admin_update_user(user_id: str, update_data: AdminUserUpdate, admin: dict = Depends(require_super_admin)):
    """Update user account details"""
    update_doc = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if update_data.name is not None:
        update_doc["name"] = update_data.name
    if update_data.email is not None:
        # Check email not in use
        existing = await db.users.find_one({"email": update_data.email, "id": {"$ne": user_id}})
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        update_doc["email"] = update_data.email
    if update_data.company is not None:
        update_doc["company"] = update_data.company
    if update_data.role is not None:
        update_doc["role"] = update_data.role
    if update_data.admin_access_level is not None:
        update_doc["admin_access_level"] = update_data.admin_access_level
    if update_data.account_status is not None:
        update_doc["account_status"] = update_data.account_status
    
    result = await db.users.update_one({"id": user_id}, {"$set": update_doc})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    await log_admin_action(admin["id"], "update_user", f"Updated user {user_id}", update_doc)
    
    return {"message": "User updated successfully"}

@api_router.post("/admin/users/{user_id}/reset-password")
async def admin_reset_user_password(user_id: str, new_password: str = Body(..., embed=True), admin: dict = Depends(require_super_admin)):
    """Reset a user's password"""
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "password": hash_password(new_password),
            "must_change_password": True,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    await log_admin_action(admin["id"], "reset_password", f"Reset password for user {user_id}")
    
    return {"message": "Password reset successfully"}

@api_router.post("/admin/users/{user_id}/suspend")
async def admin_suspend_user(user_id: str, admin: dict = Depends(require_super_admin)):
    """Suspend a user account"""
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"account_status": AccountStatus.SUSPENDED, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    await log_admin_action(admin["id"], "suspend_user", f"Suspended user {user_id}")
    
    return {"message": "User suspended"}

@api_router.post("/admin/users/{user_id}/reactivate")
async def admin_reactivate_user(user_id: str, admin: dict = Depends(require_super_admin)):
    """Reactivate a suspended/deactivated user account"""
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"account_status": AccountStatus.ACTIVE, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    await log_admin_action(admin["id"], "reactivate_user", f"Reactivated user {user_id}")
    
    return {"message": "User reactivated"}

@api_router.delete("/admin/users/{user_id}")
async def admin_deactivate_user(user_id: str, admin: dict = Depends(require_super_admin)):
    """Deactivate a user account (soft delete)"""
    # Don't allow deactivating yourself
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"account_status": AccountStatus.DEACTIVATED, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    await log_admin_action(admin["id"], "deactivate_user", f"Deactivated user {user_id}")
    
    return {"message": "User deactivated"}

@api_router.get("/admin/users/export")
async def admin_export_users(admin: dict = Depends(require_admin)):
    """Export all user data as Excel"""
    from fastapi.responses import StreamingResponse
    
    users = await db.users.find({}, {"_id": 0, "password": 0, "secret_code": 0}).to_list(5000)
    
    rows = []
    for user in users:
        rows.append({
            "ID": user.get("id", ""),
            "Name": user.get("name", ""),
            "Email": user.get("email", ""),
            "Company": user.get("company", ""),
            "Role": user.get("role", ""),
            "Admin Access Level": user.get("admin_access_level", ""),
            "Account Status": user.get("account_status", "active"),
            "Created At": user.get("created_at", ""),
            "Updated At": user.get("updated_at", ""),
        })
    
    df = pd.DataFrame(rows)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Users', index=False)
    output.seek(0)
    
    await log_admin_action(admin["id"], "export_users", f"Exported {len(users)} users")
    
    filename = f"users_export_{datetime.now(timezone.utc).strftime('%Y%m%d')}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# Broadcast Notifications
@api_router.post("/admin/notifications/broadcast")
async def admin_broadcast_notification(notification: BroadcastNotification, admin: dict = Depends(require_admin)):
    """Send a broadcast notification to all users"""
    # Check access level for non-super admins
    if admin.get("role") != UserRole.SUPER_ADMIN:
        access_level = admin.get("admin_access_level", AdminAccessLevel.VIEW_ONLY)
        if access_level not in [AdminAccessLevel.FULL, AdminAccessLevel.BROADCAST_ONLY]:
            raise HTTPException(status_code=403, detail="Broadcast access required")
    
    notification_doc = {
        "id": str(uuid.uuid4()),
        "title": notification.title,
        "message": notification.message,
        "notification_type": notification.notification_type,
        "created_by": admin["id"],
        "created_by_name": admin.get("name", "Admin"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": notification.expires_at,
        "is_active": True
    }
    
    await db.broadcast_notifications.insert_one(notification_doc)
    await log_admin_action(admin["id"], "broadcast_notification", f"Sent notification: {notification.title}")
    
    return {"message": "Notification broadcast successfully", "id": notification_doc["id"]}

@api_router.get("/admin/notifications")
async def admin_get_notifications(admin: dict = Depends(require_admin)):
    """Get all broadcast notifications"""
    notifications = await db.broadcast_notifications.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return notifications

@api_router.delete("/admin/notifications/{notification_id}")
async def admin_delete_notification(notification_id: str, admin: dict = Depends(require_admin)):
    """Delete/deactivate a broadcast notification"""
    result = await db.broadcast_notifications.update_one(
        {"id": notification_id},
        {"$set": {"is_active": False}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    await log_admin_action(admin["id"], "delete_notification", f"Deleted notification {notification_id}")
    
    return {"message": "Notification deleted"}

# User-facing notification endpoint
@api_router.get("/notifications/active")
async def get_active_notifications(user: dict = Depends(get_current_user)):
    """Get active broadcast notifications for dashboard"""
    now = datetime.now(timezone.utc).isoformat()
    notifications = await db.broadcast_notifications.find({
        "is_active": True,
        "$or": [
            {"expires_at": None},
            {"expires_at": {"$gt": now}}
        ]
    }, {"_id": 0}).sort("created_at", -1).to_list(10)
    return notifications

# System Settings
@api_router.get("/admin/settings")
async def admin_get_settings(admin: dict = Depends(require_admin)):
    """Get system settings"""
    settings = await db.system_settings.find_one({"type": "global"}, {"_id": 0})
    if not settings:
        settings = {
            "type": "global",
            "terms_of_use": "",
            "disclaimer_text": "",
            "weekly_email_enabled": True
        }
    return settings

@api_router.put("/admin/settings")
async def admin_update_settings(settings: SystemSettings, admin: dict = Depends(require_super_admin)):
    """Update system settings"""
    update_doc = {"updated_at": datetime.now(timezone.utc).isoformat(), "updated_by": admin["id"]}
    
    if settings.terms_of_use is not None:
        update_doc["terms_of_use"] = settings.terms_of_use
    if settings.disclaimer_text is not None:
        update_doc["disclaimer_text"] = settings.disclaimer_text
    if settings.weekly_email_enabled is not None:
        update_doc["weekly_email_enabled"] = settings.weekly_email_enabled
    
    await db.system_settings.update_one(
        {"type": "global"},
        {"$set": update_doc},
        upsert=True
    )
    
    await log_admin_action(admin["id"], "update_settings", "Updated system settings", update_doc)
    
    return {"message": "Settings updated successfully"}

# Public endpoint for terms and disclaimer
@api_router.get("/settings/public")
async def get_public_settings():
    """Get public system settings (terms, disclaimer)"""
    settings = await db.system_settings.find_one({"type": "global"}, {"_id": 0})
    if not settings:
        return {"terms_of_use": "", "disclaimer_text": ""}
    return {
        "terms_of_use": settings.get("terms_of_use", ""),
        "disclaimer_text": settings.get("disclaimer_text", "")
    }

# Audit Logs
@api_router.get("/admin/audit-logs")
async def admin_get_audit_logs(
    limit: int = 100,
    action_type: Optional[str] = None,
    admin: dict = Depends(require_admin)
):
    """Get admin audit logs"""
    query = {}
    if action_type:
        query["action_type"] = action_type
    
    logs = await db.admin_audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).to_list(limit)
    
    # Enrich with admin names
    admin_ids = list(set(log.get("admin_id") for log in logs))
    admins = await db.users.find({"id": {"$in": admin_ids}}, {"_id": 0, "id": 1, "name": 1, "email": 1}).to_list(100)
    admin_map = {a["id"]: a for a in admins}
    
    for log in logs:
        admin_info = admin_map.get(log.get("admin_id"), {})
        log["admin_name"] = admin_info.get("name", "Unknown")
        log["admin_email"] = admin_info.get("email", "")
    
    return logs

# Dashboard stats for admin
@api_router.get("/admin/stats")
async def admin_get_stats(admin: dict = Depends(require_admin)):
    """Get admin dashboard statistics"""
    total_users = await db.users.count_documents({})
    active_users = await db.users.count_documents({"account_status": {"$ne": AccountStatus.DEACTIVATED}})
    admin_users = await db.users.count_documents({"role": {"$in": [UserRole.ADMIN, UserRole.SUPER_ADMIN]}})
    
    # Recent activity
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=7)
    
    new_users_today = await db.users.count_documents({"created_at": {"$gte": today.isoformat()}})
    new_users_week = await db.users.count_documents({"created_at": {"$gte": week_ago.isoformat()}})
    
    total_classifications = await db.classifications.count_documents({})
    total_alcohol_calcs = await db.alcohol_calculations.count_documents({})
    total_vehicle_calcs = await db.vehicle_calculations.count_documents({})
    
    active_notifications = await db.broadcast_notifications.count_documents({"is_active": True})
    
    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "admins": admin_users,
            "new_today": new_users_today,
            "new_this_week": new_users_week
        },
        "activity": {
            "total_classifications": total_classifications,
            "total_alcohol_calculations": total_alcohol_calcs,
            "total_vehicle_calculations": total_vehicle_calcs
        },
        "notifications": {
            "active": active_notifications
        }
    }

# First login password/secret code change
@api_router.post("/auth/complete-setup")
async def complete_account_setup(
    new_password: str = Body(...),
    secret_code: str = Body(...),
    user: dict = Depends(get_current_user)
):
    """Complete account setup (change password and set secret code on first login)"""
    # Validate secret code
    if not secret_code.isdigit() or len(secret_code) < 4 or len(secret_code) > 6:
        raise HTTPException(status_code=400, detail="Secret code must be 4-6 digits")
    
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "password": hash_password(new_password),
            "secret_code": hash_password(secret_code),
            "must_change_password": False,
            "must_set_secret_code": False,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Account setup completed successfully"}

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

# Bahamas Alcohol Duty Rates (Official Rates per Customs Broker Training)
ALCOHOL_RATES = {
    "wine": {
        "hs_code": "2204.2190",
        "hs_description": "Wine of fresh grapes (Claret, Shiraz, Port, Sherry)",
        "import_duty_rate": 0.50,  # 50%
        "duty_per_imperial_gallon": None,  # Ad valorem only
        "duty_type": "ad_valorem",
        "requires_permit": False
    },
    "beer": {
        "hs_code": "2203.0090",
        "hs_description": "Beer made from malt",
        "import_duty_rate": 0.10,  # 10% ad valorem
        "duty_per_imperial_gallon": 10.00,  # $10 per Imperial Gallon
        "duty_type": "specific_plus_ad_valorem",
        "requires_permit": False
    },
    "ale": {
        "hs_code": "2203.0010",
        "hs_description": "Ale",
        "import_duty_rate": 0.10,  # 10% ad valorem
        "duty_per_imperial_gallon": 10.00,  # $10 per Imperial Gallon
        "duty_type": "specific_plus_ad_valorem",
        "requires_permit": False
    },
    "stout": {
        "hs_code": "2203.0030",
        "hs_description": "Stout",
        "import_duty_rate": 0.10,  # 10% ad valorem
        "duty_per_imperial_gallon": 10.00,  # $10 per Imperial Gallon
        "duty_type": "specific_plus_ad_valorem",
        "requires_permit": False
    },
    "spirits": {
        "hs_code": "2208.4010",
        "hs_description": "Rum and spirits by distillation (Whisky, Vodka, Gin, Brandy)",
        "import_duty_rate": 0.0,  # Spirits use proof gallon rate only
        "duty_per_proof_gallon": 15.00,  # $15 per Proof Gallon
        "duty_type": "proof_gallon",
        "requires_permit": True
    },
    "whisky": {
        "hs_code": "2208.3010",
        "hs_description": "Whisky (Bourbon/Scotch)",
        "import_duty_rate": 0.0,
        "duty_per_proof_gallon": 15.00,  # $15 per Proof Gallon
        "duty_type": "proof_gallon",
        "requires_permit": True
    },
    "vodka": {
        "hs_code": "2208.6000",
        "hs_description": "Vodka",
        "import_duty_rate": 0.0,
        "duty_per_proof_gallon": 15.00,  # $15 per Proof Gallon
        "duty_type": "proof_gallon",
        "requires_permit": True
    },
    "rum": {
        "hs_code": "2208.4010",
        "hs_description": "Rum",
        "import_duty_rate": 0.0,
        "duty_per_proof_gallon": 15.00,  # $15 per Proof Gallon
        "duty_type": "proof_gallon",
        "requires_permit": True
    },
    "brandy": {
        "hs_code": "2208.2010",
        "hs_description": "Brandy/Cognac",
        "import_duty_rate": 0.0,
        "duty_per_proof_gallon": 15.00,  # $15 per Proof Gallon
        "duty_type": "proof_gallon",
        "requires_permit": True
    },
    "liqueur": {
        "hs_code": "2208.7000",
        "hs_description": "Liqueurs and cordials",
        "import_duty_rate": 0.0,
        "duty_per_imperial_gallon": 15.00,  # $15 per Imperial Gallon
        "duty_type": "imperial_gallon",
        "requires_permit": True
    },
    "tequila": {
        "hs_code": "2208.9090",
        "hs_description": "Tequila",
        "import_duty_rate": 0.0,
        "duty_per_imperial_gallon": 15.00,  # $15 per Imperial Gallon
        "duty_type": "imperial_gallon",
        "requires_permit": True
    },
    "bitters": {
        "hs_code": "2208.7000",
        "hs_description": "Bitters",
        "import_duty_rate": 0.0,
        "duty_per_imperial_gallon": 15.00,  # $15 per Imperial Gallon
        "duty_type": "imperial_gallon",
        "requires_permit": True
    },
    "other": {
        "hs_code": "2208.9090",
        "hs_description": "Other spirituous beverages",
        "import_duty_rate": 0.0,
        "duty_per_imperial_gallon": 15.00,  # $15 per Imperial Gallon
        "duty_type": "imperial_gallon",
        "requires_permit": True
    }
}

# Conversion constants (from Bahamas Customs Broker Training)
LITERS_TO_IMPERIAL_GALLON = 0.22  # 1 liter = 0.22 imperial gallons
US_OZ_TO_IMPERIAL_GALLON = 153.6  # Divide US oz by this to get imperial gallons
UK_OZ_TO_IMPERIAL_GALLON = 160    # Divide UK oz by this to get imperial gallons
US_GALLON_TO_IMPERIAL_GALLON = 0.833  # Multiply US gal by this
ABV_TO_BRITISH_PROOF = 1.75  # Multiply % ABV by this for British Proof
US_PROOF_TO_BRITISH_PROOF = 0.875  # Multiply US Proof by this

VAT_RATE = 0.10  # 10% VAT (Bahamas current rate)
LICENSE_FEE_BASE = 50.00  # Base license processing fee

@api_router.post("/alcohol/calculate", response_model=AlcoholCalculationResult)
async def calculate_alcohol_duties(
    request: AlcoholCalculationRequest,
    user: dict = Depends(get_current_user)
):
    """Calculate duties using official Bahamas Customs methodology"""
    
    rates = ALCOHOL_RATES.get(request.alcohol_type, ALCOHOL_RATES["other"])
    warnings = []
    calculation_steps = []
    
    # Step 1: Convert volume to Liters
    volume_per_unit_liters = request.volume_ml / 1000
    total_volume_liters = volume_per_unit_liters * request.quantity
    calculation_steps.append(f"Volume: {request.volume_ml}ml × {request.quantity} units = {total_volume_liters:.2f} liters")
    
    # Step 2: Convert to Imperial Gallons
    imperial_gallons = total_volume_liters * LITERS_TO_IMPERIAL_GALLON
    calculation_steps.append(f"Imperial Gallons: {total_volume_liters:.2f}L × 0.22 = {imperial_gallons:.4f} IG")
    
    # Step 3: Calculate duty based on type
    duty_type = rates.get("duty_type", "ad_valorem")
    import_duty = 0.0
    excise_duty = 0.0
    excise_calculation = ""
    proof_gallons = 0.0
    british_proof_strength = 0.0
    
    if duty_type == "proof_gallon":
        # Spirits: Convert ABV to British Proof and calculate Proof Gallons
        british_proof_strength = request.alcohol_percentage * ABV_TO_BRITISH_PROOF
        proof_gallons = imperial_gallons * british_proof_strength
        excise_duty = proof_gallons * rates["duty_per_proof_gallon"]
        
        calculation_steps.append(f"British Proof: {request.alcohol_percentage}% × 1.75 = {british_proof_strength:.2f} BP")
        calculation_steps.append(f"Proof Gallons: {imperial_gallons:.4f} IG × {british_proof_strength:.2f} = {proof_gallons:.4f} PG")
        calculation_steps.append(f"Duty: {proof_gallons:.4f} PG × ${rates['duty_per_proof_gallon']:.2f}/PG = ${excise_duty:.2f}")
        excise_calculation = f"{proof_gallons:.4f} PG × ${rates['duty_per_proof_gallon']:.2f}/PG"
        
    elif duty_type == "imperial_gallon":
        # Liqueurs, Tequila, Bitters: $15 per Imperial Gallon
        excise_duty = imperial_gallons * rates["duty_per_imperial_gallon"]
        
        calculation_steps.append(f"Duty: {imperial_gallons:.4f} IG × ${rates['duty_per_imperial_gallon']:.2f}/IG = ${excise_duty:.2f}")
        excise_calculation = f"{imperial_gallons:.4f} IG × ${rates['duty_per_imperial_gallon']:.2f}/IG"
        
    elif duty_type == "specific_plus_ad_valorem":
        # Beer/Ale/Stout: $10 per Imperial Gallon + 10% ad valorem
        specific_duty = imperial_gallons * rates["duty_per_imperial_gallon"]
        ad_valorem_duty = request.cif_value * rates["import_duty_rate"]
        excise_duty = specific_duty
        import_duty = ad_valorem_duty
        
        calculation_steps.append(f"Specific Duty: {imperial_gallons:.4f} IG × ${rates['duty_per_imperial_gallon']:.2f}/IG = ${specific_duty:.2f}")
        calculation_steps.append(f"Ad Valorem: ${request.cif_value:.2f} × {rates['import_duty_rate']*100:.0f}% = ${ad_valorem_duty:.2f}")
        excise_calculation = f"{imperial_gallons:.4f} IG × ${rates['duty_per_imperial_gallon']:.2f}/IG + {rates['import_duty_rate']*100:.0f}% CIF"
        
    else:  # ad_valorem (wine)
        import_duty = request.cif_value * rates["import_duty_rate"]
        calculation_steps.append(f"Import Duty: ${request.cif_value:.2f} × {rates['import_duty_rate']*100:.0f}% = ${import_duty:.2f}")
        excise_calculation = f"Ad valorem: {rates['import_duty_rate']*100:.0f}% of CIF value"
    
    # Calculate VAT (on CIF + all duties)
    vat_base = request.cif_value + import_duty + excise_duty
    vat = vat_base * VAT_RATE
    calculation_steps.append(f"VAT Base: ${request.cif_value:.2f} + ${import_duty:.2f} + ${excise_duty:.2f} = ${vat_base:.2f}")
    calculation_steps.append(f"VAT: ${vat_base:.2f} × 10% = ${vat:.2f}")
    
    # Calculate License Fee
    license_fee = 0.0
    if request.has_liquor_license:
        license_fee = LICENSE_FEE_BASE
        if request.quantity > 24:
            license_fee += (request.quantity - 24) * 0.50
    
    # Total Landed Cost
    total_landed_cost = request.cif_value + import_duty + excise_duty + vat + license_fee
    
    # Pure alcohol calculation (for reference)
    pure_alcohol_liters = total_volume_liters * (request.alcohol_percentage / 100)
    
    # Warnings and flags
    if request.alcohol_percentage > 40:
        warnings.append("High ABV product (>40%) - verify proof gallon calculation")
    if total_volume_liters > 10 and not request.has_liquor_license:
        warnings.append("Volume exceeds personal use allowance - liquor license required")
    if rates.get("requires_permit"):
        warnings.append(f"Import permit required for {request.alcohol_type}")
    if request.cif_value > 5000:
        warnings.append("High value shipment - may require additional documentation")
    
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
        "volume_ml": request.volume_ml,
        "total_volume_liters": round(total_volume_liters, 2),
        "imperial_gallons": round(imperial_gallons, 4),
        "alcohol_percentage": request.alcohol_percentage,
        "british_proof_strength": round(british_proof_strength, 2) if british_proof_strength else None,
        "proof_gallons": round(proof_gallons, 4) if proof_gallons else None,
        "pure_alcohol_liters": round(pure_alcohol_liters, 4),
        "cif_value": round(request.cif_value, 2),
        "import_duty": round(import_duty, 2),
        "import_duty_rate": f"{rates['import_duty_rate'] * 100:.0f}%",
        "excise_duty": round(excise_duty, 2),
        "excise_calculation": excise_calculation,
        "duty_type": duty_type,
        "calculation_steps": calculation_steps,
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

@api_router.get("/alcohol/history/export")
async def export_alcohol_history(user: dict = Depends(get_current_user)):
    """Export all alcohol calculation history as Excel"""
    from fastapi.responses import StreamingResponse
    
    calculations = await db.alcohol_calculations.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(500)
    
    if not calculations:
        raise HTTPException(status_code=404, detail="No calculations to export")
    
    # Prepare data for Excel
    rows = []
    for calc in calculations:
        rows.append({
            "Date": calc.get("created_at", "")[:10] if isinstance(calc.get("created_at"), str) else calc.get("created_at").strftime("%Y-%m-%d") if calc.get("created_at") else "",
            "Product Name": calc.get("product_name", ""),
            "Alcohol Type": calc.get("alcohol_type", ""),
            "ABV %": calc.get("abv_percentage", 0),
            "Volume (ml)": calc.get("volume_ml", 0),
            "Quantity": calc.get("quantity", 0),
            "CIF Value": calc.get("cif_value", 0),
            "Import Duty": calc.get("import_duty", 0),
            "Excise Duty": calc.get("excise_duty", 0),
            "VAT": calc.get("vat", 0),
            "License Fee": calc.get("license_fee", 0),
            "Total Landed Cost": calc.get("total_landed_cost", 0),
            "HS Code": calc.get("hs_code", ""),
            "Liquor License": "Yes" if calc.get("has_liquor_license") else "No",
        })
    
    df = pd.DataFrame(rows)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Alcohol History', index=False)
        
        worksheet = writer.sheets['Alcohol History']
        for column in worksheet.columns:
            max_length = max(len(str(cell.value or "")) for cell in column)
            worksheet.column_dimensions[column[0].column_letter].width = min(max_length + 2, 30)
    
    output.seek(0)
    
    filename = f"alcohol_history_{datetime.now(timezone.utc).strftime('%Y%m%d')}.xlsx"
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

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

@api_router.delete("/alcohol/calculations/{calc_id}")
async def delete_alcohol_calculation(calc_id: str, user: dict = Depends(get_current_user)):
    """Delete a specific alcohol calculation"""
    result = await db.alcohol_calculations.delete_one({"id": calc_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Calculation not found")
    return {"message": "Alcohol calculation deleted"}

@api_router.get("/alcohol/calculations/{calc_id}/invoice")
async def export_alcohol_invoice(calc_id: str, user: dict = Depends(get_current_user)):
    """Generate and export alcohol duty invoice as Excel"""
    from fastapi.responses import StreamingResponse
    
    calculation = await db.alcohol_calculations.find_one(
        {"id": calc_id, "user_id": user["id"]},
        {"_id": 0}
    )
    if not calculation:
        raise HTTPException(status_code=404, detail="Calculation not found")
    
    # Create invoice data
    invoice_data = [
        {"Item": "ALCOHOL IMPORT DUTY INVOICE", "Description": "", "Amount": ""},
        {"Item": "", "Description": "", "Amount": ""},
        {"Item": "Product Information", "Description": "", "Amount": ""},
        {"Item": "Product Name", "Description": calculation.get('product_name', ''), "Amount": ""},
        {"Item": "Brand/Label", "Description": calculation.get('brand_label', 'N/A'), "Amount": ""},
        {"Item": "Type", "Description": calculation.get('alcohol_type', '').title(), "Amount": ""},
        {"Item": "HS Code", "Description": calculation.get('hs_code', ''), "Amount": ""},
        {"Item": "HS Description", "Description": calculation.get('hs_description', ''), "Amount": ""},
        {"Item": "Country of Origin", "Description": calculation.get('country_of_origin', 'N/A'), "Amount": ""},
        {"Item": "", "Description": "", "Amount": ""},
        {"Item": "Volume Details", "Description": "", "Amount": ""},
        {"Item": "Quantity", "Description": f"{calculation.get('quantity', 0)} units", "Amount": ""},
        {"Item": "Total Volume", "Description": f"{calculation.get('total_volume_liters', 0)} liters", "Amount": ""},
        {"Item": "Alcohol Content", "Description": f"{calculation.get('alcohol_percentage', 0)}% ABV", "Amount": ""},
        {"Item": "Pure Alcohol", "Description": f"{calculation.get('pure_alcohol_liters', 0)} liters", "Amount": ""},
        {"Item": "", "Description": "", "Amount": ""},
        {"Item": "Duty Breakdown", "Description": "", "Amount": ""},
        {"Item": "CIF Value", "Description": "", "Amount": f"${calculation.get('cif_value', 0):,.2f}"},
        {"Item": f"Import Duty ({calculation.get('import_duty_rate', '')})", "Description": "", "Amount": f"${calculation.get('import_duty', 0):,.2f}"},
        {"Item": f"Excise Duty", "Description": calculation.get('excise_calculation', ''), "Amount": f"${calculation.get('excise_duty', 0):,.2f}"},
        {"Item": f"VAT ({calculation.get('vat_rate', '10%')})", "Description": "", "Amount": f"${calculation.get('vat', 0):,.2f}"},
        {"Item": "License/Processing Fee", "Description": "", "Amount": f"${calculation.get('license_fee', 0):,.2f}"},
        {"Item": "", "Description": "", "Amount": ""},
        {"Item": "TOTAL LANDED COST", "Description": "", "Amount": f"${calculation.get('total_landed_cost', 0):,.2f}"},
        {"Item": "", "Description": "", "Amount": ""},
        {"Item": "License Status", "Description": "Liquor License Holder" if calculation.get('has_liquor_license') else "No Liquor License", "Amount": ""},
    ]
    
    if calculation.get('requires_permit'):
        invoice_data.append({"Item": "⚠️ IMPORT PERMIT REQUIRED", "Description": "", "Amount": ""})
    
    invoice_data.extend([
        {"Item": "", "Description": "", "Amount": ""},
        {"Item": "DISCLAIMER", "Description": "This is an estimate only. Final duties determined by Customs Officers.", "Amount": ""},
        {"Item": "Generated by", "Description": "Class-B HS Code Agent", "Amount": f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"},
    ])
    
    df = pd.DataFrame(invoice_data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Invoice')
    output.seek(0)
    
    filename = f"alcohol_invoice_{calculation.get('product_name', 'alcohol').replace(' ', '_')}_{calc_id[:8]}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

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

@api_router.get("/alcohol/guide")
async def get_alcohol_calculation_guide():
    """Download PDF guide for alcohol duty calculations"""
    from fastapi.responses import StreamingResponse
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem
    from reportlab.lib.units import inch
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, spaceAfter=12, textColor=colors.HexColor('#2DD4BF'))
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, spaceAfter=8, spaceBefore=16, textColor=colors.HexColor('#2DD4BF'))
    subheading_style = ParagraphStyle('SubHeading', parent=styles['Heading3'], fontSize=12, spaceAfter=6, spaceBefore=12)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, spaceAfter=6, leading=14)
    note_style = ParagraphStyle('Note', parent=styles['Normal'], fontSize=9, textColor=colors.grey, spaceAfter=6)
    
    story = []
    
    # Title
    story.append(Paragraph("Bahamas Alcohol Import Duty Calculation Guide", title_style))
    story.append(Paragraph("Class-B HS Code Agent - B-CLASS Alcohol Calculator", note_style))
    story.append(Spacer(1, 0.25*inch))
    
    # Overview
    story.append(Paragraph("Overview", heading_style))
    story.append(Paragraph(
        "This guide explains how alcohol import duties are calculated for imports into The Bahamas. "
        "The calculation includes Import Duty, Excise Duty, VAT, and License Fees based on the "
        "Customs Management Act (CMA) and current tariff schedules.",
        body_style
    ))
    
    # Duty Rates Table
    story.append(Paragraph("1. Import Duty Rates by Alcohol Type", heading_style))
    
    duty_data = [
        ['Alcohol Type', 'Import Duty Rate', 'HS Code Range'],
        ['Wine', '45%', '2204.xx'],
        ['Beer', '35%', '2203.xx'],
        ['Spirits (Rum, Vodka, Whiskey)', '45%', '2208.xx'],
        ['Liqueur & Cordials', '45%', '2208.70'],
        ['Other Alcohol', '45%', '22xx.xx'],
    ]
    
    duty_table = Table(duty_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
    duty_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a3a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0f0f0')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f8f8')]),
    ]))
    story.append(duty_table)
    story.append(Spacer(1, 0.15*inch))
    
    # Excise Duty
    story.append(Paragraph("2. Excise Duty Calculation", heading_style))
    story.append(Paragraph(
        "Excise duty is calculated differently based on alcohol type:",
        body_style
    ))
    
    excise_data = [
        ['Alcohol Type', 'Excise Method', 'Rate'],
        ['Beer (< 6% ABV)', 'Per Liter', '$0.75 per liter'],
        ['Beer (≥ 6% ABV)', 'Per LPA', '$15.00 per LPA'],
        ['Wine', 'Per LPA', '$15.00 per LPA'],
        ['Spirits', 'Per LPA', '$25.00 per LPA'],
        ['Liqueur', 'Per LPA', '$20.00 per LPA'],
    ]
    
    excise_table = Table(excise_data, colWidths=[2*inch, 1.5*inch, 2*inch])
    excise_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a3a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f8f8')]),
    ]))
    story.append(excise_table)
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("LPA = Liters of Pure Alcohol = (Volume in Liters) × (ABV% / 100)", note_style))
    story.append(Paragraph("Example: 750ml bottle at 40% ABV = 0.75L × 0.40 = 0.30 LPA", note_style))
    
    # VAT
    story.append(Paragraph("3. Value Added Tax (VAT)", heading_style))
    story.append(Paragraph(
        "VAT is calculated at 10% on the total of CIF Value + Import Duty + Excise Duty.",
        body_style
    ))
    story.append(Paragraph("VAT = (CIF + Import Duty + Excise Duty) × 10%", body_style))
    
    # License Fee
    story.append(Paragraph("4. License Fee", heading_style))
    story.append(Paragraph(
        "A liquor license fee applies to commercial importers. The base fee is $50.00 per shipment, "
        "with additional fees based on total value. Licensed importers may receive reduced rates.",
        body_style
    ))
    
    # Calculation Formula
    story.append(Paragraph("5. Complete Calculation Formula", heading_style))
    
    formula_data = [
        ['Step', 'Calculation'],
        ['1. Import Duty', 'CIF Value × Duty Rate (35-45%)'],
        ['2. Excise Duty', '(For Spirits/Wine) LPA × Rate per LPA × Quantity'],
        ['', '(For Beer < 6%) Volume (L) × $0.75 × Quantity'],
        ['3. Subtotal', 'CIF + Import Duty + Excise Duty'],
        ['4. VAT (10%)', 'Subtotal × 10%'],
        ['5. License Fee', '$50.00 base (if applicable)'],
        ['6. TOTAL', 'Subtotal + VAT + License Fee'],
    ]
    
    formula_table = Table(formula_data, colWidths=[1.5*inch, 4*inch])
    formula_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a3a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f8f8')]),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#2DD4BF')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    story.append(formula_table)
    
    # Example Calculation
    story.append(Paragraph("6. Example Calculation", heading_style))
    story.append(Paragraph("Product: 12 bottles of Rum (750ml, 40% ABV) with CIF value of $540", subheading_style))
    
    example_data = [
        ['Component', 'Calculation', 'Amount'],
        ['CIF Value', '12 bottles × $45 each', '$540.00'],
        ['Import Duty (45%)', '$540 × 45%', '$243.00'],
        ['LPA Calculation', '0.75L × 40% × 12 bottles', '3.60 LPA'],
        ['Excise Duty', '3.60 LPA × $25.00', '$90.00'],
        ['Subtotal', '$540 + $243 + $90', '$873.00'],
        ['VAT (10%)', '$873 × 10%', '$87.30'],
        ['License Fee', 'Base fee', '$50.00'],
        ['TOTAL DUE', '', '$1,010.30'],
    ]
    
    example_table = Table(example_data, colWidths=[1.8*inch, 2.2*inch, 1.5*inch])
    example_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a3a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f8f8')]),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#2DD4BF')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    story.append(example_table)
    
    # Disclaimer
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("Important Notice", heading_style))
    story.append(Paragraph(
        "This guide is for informational purposes only. Actual duties and fees are determined by "
        "Bahamas Customs at the time of import. Rates may change without notice. Always consult "
        "with Bahamas Customs for official rates and requirements.",
        note_style
    ))
    story.append(Paragraph(
        "Contact: Bahamas Customs Department | Tel: +1 (242) 325-6550 | customs.bahamas.gov.bs",
        note_style
    ))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(f"Generated by Class-B HS Code Agent | {datetime.now(timezone.utc).strftime('%Y-%m-%d')}", note_style))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=Bahamas_Alcohol_Duty_Guide.pdf"}
    )

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
    customs_code: str
    code: str
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
            {"customs_code": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}},
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

### Bahamas Tariff Structure (2023)
- **8-digit HS codes** based on international Harmonized System
- **Tariff schedule columns:**
  - Column 3: General Rate (ad valorem percentage)
  - Column 4: Specific Rate (per unit - kg, liter, etc.)
  - Column 5: Maximum Variable Rate (Minister may impose by Order)
  - Column 6: EPA Preferential Rate (CARIFORUM/EU)
  - Column 7: Statistical Unit of Measure
- **"**" symbol** indicates excise duty also applies

### Common Duty Rates by Category
- **0% (Free)**: Beef, educational materials, medical equipment for public facilities
- **5%**: Refrigerators, energy-efficient appliances
- **10%**: Live poultry, live swine, basic agricultural items
- **25%**: Most manufactured goods, motor vehicles (base)
- **35%**: Wine, beer, general textiles
- **40%**: Pets (dogs/cats less), exotic animals, luxury items
- **45%**: Spirits, high-value items
- **100%**: All types of bottled water (protect local industry)
- **220%**: Manufactured tobacco products (cigarettes, cigars)

### Excise Duties (in addition to import duty)
- **Alcoholic Beverages:**
  - Beer: $5.00 per liter of pure alcohol (LPA)
  - Wine (still): $2.50 per liter
  - Wine (sparkling): $4.00 per liter
  - Spirits: $8.00 per LPA
  - Liqueurs: $6.00 per LPA

- **Tobacco Products:**
  - Cigarettes: $0.25 per stick
  - Cigars: $1.50 each
  - Smoking tobacco: $15.00/kg

- **Petroleum:**
  - Motor gasoline: $0.75/gallon
  - Diesel: $0.60/gallon

### Additional Charges
- **VAT**: 10% on (CIF value + all duties)
- **Warehousing Duty**: 1% ad valorem
- **Environmental Levy**: Applies to certain items

### Common Customs Forms
- **C-13**: Home Consumption Entry (main import declaration)
- **C-14**: Entry for Goods Under Hawksbill Creek Agreement
- **C-15**: Bill of Sight (provisional entry)
- **C-16**: Warehousing Entry
- **C-17**: Accompanied Baggage Declaration
- **C-18**: Unaccompanied Baggage Declaration
- **C-24**: Ex-Warehousing Home Consumption Entry
- **C-29**: Export Entry for Domestic Goods
- **C-35**: Transhipment Entry
- **C-43**: Declaration of Value for Customs Purposes
- **C-46**: Export Entry for Drawback Goods
- **C-63**: Application for Duty Exemption (use BEFORE importing)
- **CB1-CB13**: Various bond forms

### Chapter 98 - Duty Exemptions
- Agricultural equipment
- Educational materials for accredited institutions
- Medical equipment for public health facilities
- Religious artifacts for recognized organizations
- Sporting equipment for registered organizations
- Relief goods and disaster supplies
- Goods under Hawksbill Creek Agreement (Freeport)

### General Rules of Interpretation (GRI)
1. **GRI 1**: Start with heading descriptions and section/chapter notes
2. **GRI 2(a)**: Incomplete/unassembled goods classified as complete if essential character present
3. **GRI 2(b)**: Mixtures - heading for material includes mixtures with others
4. **GRI 3(a)**: Most specific description wins
5. **GRI 3(b)**: Essential character determines classification
6. **GRI 3(c)**: Last heading numerically wins as tiebreaker
7. **GRI 4**: Classify by most similar goods
8. **GRI 5(a)**: Cases/containers classified with their contents
9. **GRI 5(b)**: Normal packing classified with goods
10. **GRI 6**: Same rules apply at subheading level
- **5-10%**: Basic foodstuffs, agricultural inputs, IT equipment
- **25-35%**: General manufactured goods, clothing, footwear
- **35-45%**: Alcoholic beverages (plus excise duty)
- **45%**: Luxury items, certain protected goods

### Import Process Steps
1. Obtain business license (if commercial)
2. Register with Customs (get TIN - Taxpayer ID Number)
3. Prepare commercial invoice, packing list, bill of lading
4. Classify goods using correct HS codes
5. Submit entry via Electronic Single Window or customs broker
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

# ============= VEHICLE BROKERING MODULE =============

class VehicleType(str, Enum):
    ELECTRIC = "electric"
    HYBRID = "hybrid"
    GASOLINE = "gasoline"
    DIESEL = "diesel"
    COMMERCIAL = "commercial"

class VehicleCalculationRequest(BaseModel):
    vin: Optional[str] = None
    make: str
    model: str
    year: int
    vehicle_type: VehicleType
    body_style: Optional[str] = None  # sedan, suv, pickup, etc.
    engine_size_cc: Optional[int] = None  # Engine displacement in cc (not applicable for electric)
    cif_value: float  # Cost, Insurance, Freight value in USD
    country_of_origin: str
    is_new: bool = True
    fuel_type: Optional[str] = None
    color: Optional[str] = None
    mileage: Optional[int] = None
    # Concessionary rate fields
    is_first_time_owner: bool = False
    qualifies_for_concession: bool = False
    concession_type: Optional[str] = None  # "first_vehicle", "returning_resident", "disabled", etc.
    # Environmental levy options
    is_antique: bool = False  # For antique/vintage vehicles
    num_tires: int = 4  # Number of used tires (for tire levy)

class VehicleCalculationResult(BaseModel):
    id: str
    vin: Optional[str]
    make: str
    model: str
    year: int
    vehicle_type: VehicleType
    engine_size_cc: Optional[int]
    engine_category: str
    cif_value: float
    duty_rate: float
    duty_rate_display: str
    import_duty: float
    environmental_levy: float
    environmental_levy_rate: str
    vat: float
    vat_rate: str
    stamp_duty: float
    stamp_duty_rate: str
    processing_fee: float
    total_landed_cost: float
    hs_code: str
    hs_description: str
    breakdown: Dict[str, Any]
    warnings: List[str]
    concessionary_applied: bool
    original_duty_rate: Optional[float]
    savings: Optional[float]
    country_of_origin: str
    is_new: bool
    created_at: datetime

# Vehicle Duty Rates (Bahamas 2024)
VEHICLE_DUTY_RATES = {
    "electric": {
        "hs_code": "8703.80",
        "hs_description": "Motor vehicles with only electric motor for propulsion",
        "tiers": [
            {"max_value": 50000, "rate": 0.10, "description": "Value up to $50,000"},
            {"max_value": float('inf'), "rate": 0.25, "description": "Value over $50,000"}
        ]
    },
    "hybrid": {
        "hs_code": "8703.40",
        "hs_description": "Vehicles with both spark-ignition engine and electric motor",
        "tiers": [
            {"max_value": 50000, "rate": 0.10, "description": "Value up to $50,000"},
            {"max_value": float('inf'), "rate": 0.25, "description": "Value over $50,000"}
        ]
    },
    "gasoline": {
        "hs_code": "8703.23",
        "hs_description": "Motor cars with spark-ignition engine",
        "tiers": [
            {"max_cc": 1500, "max_value": float('inf'), "rate": 0.45, "description": "Engine under 1.5L (1500cc)"},
            {"min_cc": 1500, "max_cc": 2000, "max_value": 50000, "rate": 0.45, "description": "1.5L to 2.0L (valued ≤ $50k)"},
            {"min_cc": 1500, "max_cc": 2000, "min_value": 50000, "rate": 0.65, "description": "1.5L to 2.0L (valued > $50k)"},
            {"min_cc": 2000, "max_value": float('inf'), "rate": 0.65, "description": "Engine over 2.0L (2000cc)"}
        ]
    },
    "diesel": {
        "hs_code": "8703.32",
        "hs_description": "Motor cars with compression-ignition engine (diesel)",
        "tiers": [
            {"max_cc": 1500, "max_value": float('inf'), "rate": 0.45, "description": "Engine under 1.5L"},
            {"min_cc": 1500, "max_cc": 2000, "max_value": 50000, "rate": 0.45, "description": "1.5L to 2.0L (valued ≤ $50k)"},
            {"min_cc": 1500, "max_cc": 2000, "min_value": 50000, "rate": 0.65, "description": "1.5L to 2.0L (valued > $50k)"},
            {"min_cc": 2000, "max_value": float('inf'), "rate": 0.65, "description": "Engine over 2.0L"}
        ]
    },
    "commercial": {
        "hs_code": "8704.21",
        "hs_description": "Motor vehicles for transport of goods (trucks, heavy equipment)",
        "tiers": [
            {"max_weight": 5000, "rate": 0.65, "description": "GVW up to 5 tons"},
            {"min_weight": 5000, "rate": 0.85, "description": "GVW over 5 tons (heavy equipment)"}
        ]
    }
}

# Additional fees (Bahamas Vehicle Import 2024)
VEHICLE_VAT_RATE = 0.10  # 10% VAT
# Environmental Levy - varies by vehicle age/type
ENVIRONMENTAL_LEVY_NEW = 250.00  # Flat $250 for new/standard vehicles
ENVIRONMENTAL_LEVY_OVER_10_YEARS = 0.20  # 20% of landed cost for vehicles >10 years old
ENVIRONMENTAL_LEVY_ANTIQUE = 200.00  # $200 for antique/vintage vehicles
TIRE_LEVY_PER_TIRE = 5.00  # $5 per used tire
# Processing Fee: 1% of CIF, min $10, max $750
PROCESSING_FEE_RATE = 0.01
PROCESSING_FEE_MIN = 10.00
PROCESSING_FEE_MAX = 750.00

def calculate_processing_fee(cif_value: float) -> float:
    """Calculate processing fee: 1% of CIF, min $10, max $750"""
    fee = cif_value * PROCESSING_FEE_RATE
    return max(PROCESSING_FEE_MIN, min(fee, PROCESSING_FEE_MAX))

def calculate_environmental_levy(year: int, is_new: bool, is_antique: bool, cif_value: float, import_duty: float, num_tires: int = 4) -> tuple:
    """Calculate environmental levy based on vehicle age and type"""
    current_year = datetime.now().year
    vehicle_age = current_year - year
    
    levy = 0.0
    levy_description = ""
    requires_approval = False
    tire_levy = 0.0
    
    if is_antique:
        levy = ENVIRONMENTAL_LEVY_ANTIQUE
        levy_description = "Antique/Vintage Vehicle ($200 flat)"
        requires_approval = True
    elif vehicle_age > 10:
        # 20% of landed cost (CIF + Duty) for vehicles over 10 years
        landed_for_levy = cif_value + import_duty
        levy = landed_for_levy * ENVIRONMENTAL_LEVY_OVER_10_YEARS
        levy_description = f"Over 10 years old (20% of ${landed_for_levy:,.2f})"
        requires_approval = True
    else:
        levy = ENVIRONMENTAL_LEVY_NEW
        levy_description = "Standard Vehicle ($250 flat)"
    
    # Add tire levy for used vehicles
    if not is_new and num_tires > 0:
        tire_levy = num_tires * TIRE_LEVY_PER_TIRE
    
    return levy, levy_description, requires_approval, tire_levy

def determine_vehicle_duty_rate(vehicle_type: str, engine_cc: Optional[int], cif_value: float) -> tuple:
    """Determine the applicable duty rate based on vehicle type, engine size, and value"""
    rates = VEHICLE_DUTY_RATES.get(vehicle_type, VEHICLE_DUTY_RATES["gasoline"])
    
    for tier in rates["tiers"]:
        # Check engine size constraints
        min_cc = tier.get("min_cc", 0)
        max_cc = tier.get("max_cc", float('inf'))
        
        # Check value constraints
        min_value = tier.get("min_value", 0)
        max_value = tier.get("max_value", float('inf'))
        
        # For electric/hybrid, only check value
        if vehicle_type in ["electric", "hybrid"]:
            if cif_value <= max_value and cif_value > min_value:
                return tier["rate"], tier["description"]
            elif min_value == 0 and cif_value <= max_value:
                return tier["rate"], tier["description"]
        else:
            # Check engine size first
            engine_matches = (engine_cc is None) or (min_cc <= engine_cc < max_cc) or (min_cc <= engine_cc and max_cc == float('inf'))
            # Check value
            value_matches = (min_value < cif_value <= max_value) or (min_value == 0 and cif_value <= max_value)
            
            if engine_matches and value_matches:
                return tier["rate"], tier["description"]
    
    # Default to highest rate if no match
    return 0.65, "Default rate"

def get_engine_category(engine_cc: Optional[int], vehicle_type: str) -> str:
    """Get human-readable engine category"""
    if vehicle_type == "electric":
        return "Electric Motor"
    elif vehicle_type == "hybrid":
        return "Hybrid (Electric + ICE)"
    elif engine_cc is None:
        return "Unknown"
    elif engine_cc < 1500:
        return f"Small ({engine_cc}cc / {engine_cc/1000:.1f}L)"
    elif engine_cc < 2000:
        return f"Medium ({engine_cc}cc / {engine_cc/1000:.1f}L)"
    else:
        return f"Large ({engine_cc}cc / {engine_cc/1000:.1f}L)"

@api_router.post("/vehicle/calculate")
async def calculate_vehicle_duties(
    request: VehicleCalculationRequest,
    user: dict = Depends(get_current_user)
):
    """Calculate duties for vehicle import into The Bahamas"""
    
    warnings = []
    rates_info = VEHICLE_DUTY_RATES.get(request.vehicle_type, VEHICLE_DUTY_RATES["gasoline"])
    
    # Determine duty rate
    duty_rate, duty_description = determine_vehicle_duty_rate(
        request.vehicle_type,
        request.engine_size_cc,
        request.cif_value
    )
    
    original_duty_rate = None
    savings = None
    concessionary_applied = False
    
    # Apply concessionary rates if applicable
    if request.qualifies_for_concession:
        original_duty_rate = duty_rate
        if request.concession_type == "first_vehicle":
            duty_rate = max(duty_rate - 0.20, 0.10)  # 20% reduction, min 10%
            concessionary_applied = True
            warnings.append(f"Concessionary rate applied: First-time vehicle owner (reduced from {original_duty_rate*100:.0f}% to {duty_rate*100:.0f}%)")
        elif request.concession_type == "returning_resident":
            duty_rate = max(duty_rate - 0.15, 0.10)
            concessionary_applied = True
            warnings.append(f"Concessionary rate applied: Returning resident (reduced from {original_duty_rate*100:.0f}% to {duty_rate*100:.0f}%)")
        elif request.concession_type == "disabled":
            duty_rate = 0.10  # Flat 10% for disabled persons
            concessionary_applied = True
            warnings.append("Concessionary rate applied: Disabled person exemption (10%)")
    
    # Calculate duties
    import_duty = request.cif_value * duty_rate
    
    # Calculate processing fee: 1% of CIF, min $10, max $750
    processing_fee = calculate_processing_fee(request.cif_value)
    
    # Calculate environmental levy based on vehicle age/type
    environmental_levy, levy_description, requires_approval, tire_levy = calculate_environmental_levy(
        request.year,
        request.is_new,
        request.is_antique,
        request.cif_value,
        import_duty,
        request.num_tires
    )
    
    # Landed Cost = CIF + Duty + Environmental Levy + Processing Fee + Tire Levy
    landed_cost = request.cif_value + import_duty + environmental_levy + processing_fee + tire_levy
    
    # VAT = 10% of Landed Cost
    vat = landed_cost * VEHICLE_VAT_RATE
    
    # Total Due = All fees + VAT
    total_landed_cost = landed_cost + vat
    
    # Calculate savings if concessionary
    if concessionary_applied and original_duty_rate:
        original_duty = request.cif_value * original_duty_rate
        savings = original_duty - import_duty
    
    # Add relevant warnings
    if requires_approval:
        warnings.append("⚠️ Ministry of Finance approval required for this vehicle category")
    
    if request.year < datetime.now().year - 10:
        warnings.append(f"Vehicle is {datetime.now().year - request.year} years old - 20% Environmental Levy applies, Ministry approval required")
    
    if not request.is_new and request.mileage and request.mileage > 100000:
        warnings.append("High mileage vehicle - may require pre-import inspection")
    
    if request.vehicle_type == "commercial":
        warnings.append("Commercial vehicles may require additional permits and weight certification")
    
    if request.cif_value > 100000:
        warnings.append("High-value import - may require additional documentation and insurance verification")
    
    if request.vehicle_type in ["gasoline", "diesel"] and request.engine_size_cc and request.engine_size_cc > 3000:
        warnings.append("Large engine vehicles face higher duties and environmental levies")
    
    # Get HS code info
    engine_category = get_engine_category(request.engine_size_cc, request.vehicle_type)
    
    # Create calculation record
    calc_id = str(uuid.uuid4())
    calculation = {
        "id": calc_id,
        "user_id": user["id"],
        "vin": request.vin,
        "make": request.make,
        "model": request.model,
        "year": request.year,
        "vehicle_type": request.vehicle_type,
        "body_style": request.body_style,
        "engine_size_cc": request.engine_size_cc,
        "engine_category": engine_category,
        "cif_value": round(request.cif_value, 2),
        "duty_rate": duty_rate,
        "duty_rate_display": f"{duty_rate * 100:.0f}% ({duty_description})",
        "import_duty": round(import_duty, 2),
        "environmental_levy": round(environmental_levy, 2),
        "environmental_levy_description": levy_description,
        "tire_levy": round(tire_levy, 2),
        "processing_fee": round(processing_fee, 2),
        "processing_fee_description": f"1% of CIF (min $10, max $750)",
        "landed_cost": round(landed_cost, 2),
        "vat": round(vat, 2),
        "vat_rate": f"{VEHICLE_VAT_RATE * 100:.0f}%",
        "total_landed_cost": round(total_landed_cost, 2),
        "hs_code": rates_info["hs_code"],
        "hs_description": rates_info["hs_description"],
        "breakdown": {
            "cif_value": round(request.cif_value, 2),
            "import_duty": round(import_duty, 2),
            "environmental_levy": round(environmental_levy, 2),
            "tire_levy": round(tire_levy, 2),
            "processing_fee": round(processing_fee, 2),
            "landed_cost": round(landed_cost, 2),
            "vat": round(vat, 2),
            "total": round(total_landed_cost, 2)
        },
        "warnings": warnings,
        "concessionary_applied": concessionary_applied,
        "original_duty_rate": original_duty_rate,
        "savings": round(savings, 2) if savings else None,
        "country_of_origin": request.country_of_origin,
        "is_new": request.is_new,
        "is_antique": request.is_antique,
        "num_tires": request.num_tires,
        "requires_approval": requires_approval,
        "fuel_type": request.fuel_type,
        "color": request.color,
        "mileage": request.mileage,
        "concession_type": request.concession_type,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Save to database
    await db.vehicle_calculations.insert_one(calculation)
    
    # Remove MongoDB _id before returning (not JSON serializable)
    calculation.pop("_id", None)
    calculation["created_at"] = datetime.fromisoformat(calculation["created_at"])
    return calculation

@api_router.get("/vehicle/calculations")
async def get_vehicle_calculations(user: dict = Depends(get_current_user)):
    """Get user's vehicle calculation history"""
    calculations = await db.vehicle_calculations.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    for calc in calculations:
        if isinstance(calc.get("created_at"), str):
            calc["created_at"] = datetime.fromisoformat(calc["created_at"])
    
    return calculations

@api_router.get("/vehicle/history/export")
async def export_vehicle_history(user: dict = Depends(get_current_user)):
    """Export all vehicle calculation history as Excel"""
    from fastapi.responses import StreamingResponse
    
    calculations = await db.vehicle_calculations.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(500)
    
    if not calculations:
        raise HTTPException(status_code=404, detail="No calculations to export")
    
    # Prepare data for Excel
    rows = []
    for calc in calculations:
        rows.append({
            "Date": calc.get("created_at", "")[:10] if isinstance(calc.get("created_at"), str) else calc.get("created_at").strftime("%Y-%m-%d") if calc.get("created_at") else "",
            "VIN": calc.get("vin", ""),
            "Year": calc.get("year", ""),
            "Make": calc.get("make", ""),
            "Model": calc.get("model", ""),
            "Body Style": calc.get("body_style", ""),
            "Vehicle Type": calc.get("vehicle_type", ""),
            "Engine Size (cc)": calc.get("engine_size_cc", ""),
            "Country of Origin": calc.get("country_of_origin", ""),
            "CIF Value": calc.get("cif_value", 0),
            "Duty Rate": f"{calc.get('duty_rate', 0) * 100:.0f}%" if calc.get('duty_rate') else "",
            "Import Duty": calc.get("import_duty", 0),
            "Environmental Levy": calc.get("environmental_levy", 0),
            "Processing Fee": calc.get("processing_fee", 0),
            "Stamp Duty": calc.get("stamp_duty", 0),
            "VAT": calc.get("vat", 0),
            "Total Landed Cost": calc.get("total_landed_cost", 0),
            "HS Code": calc.get("hs_code", ""),
            "New/Used": "New" if calc.get("is_new") else "Used",
            "Antique": "Yes" if calc.get("is_antique") else "No",
        })
    
    df = pd.DataFrame(rows)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Vehicle History', index=False)
        
        worksheet = writer.sheets['Vehicle History']
        for column in worksheet.columns:
            max_length = max(len(str(cell.value or "")) for cell in column)
            worksheet.column_dimensions[column[0].column_letter].width = min(max_length + 2, 30)
    
    output.seek(0)
    
    filename = f"vehicle_history_{datetime.now(timezone.utc).strftime('%Y%m%d')}.xlsx"
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@api_router.get("/vehicle/calculations/{calc_id}")
async def get_vehicle_calculation(calc_id: str, user: dict = Depends(get_current_user)):
    """Get a specific vehicle calculation"""
    calculation = await db.vehicle_calculations.find_one(
        {"id": calc_id, "user_id": user["id"]},
        {"_id": 0}
    )
    if not calculation:
        raise HTTPException(status_code=404, detail="Calculation not found")
    
    if isinstance(calculation.get("created_at"), str):
        calculation["created_at"] = datetime.fromisoformat(calculation["created_at"])
    
    return calculation

@api_router.delete("/vehicle/calculations/{calc_id}")
async def delete_vehicle_calculation(calc_id: str, user: dict = Depends(get_current_user)):
    """Delete a specific vehicle calculation"""
    result = await db.vehicle_calculations.delete_one({"id": calc_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Calculation not found")
    return {"message": "Vehicle calculation deleted"}

@api_router.get("/vehicle/calculations/{calc_id}/invoice")
async def export_vehicle_invoice(calc_id: str, user: dict = Depends(get_current_user)):
    """Generate and export vehicle duty invoice as Excel"""
    from fastapi.responses import StreamingResponse
    
    calculation = await db.vehicle_calculations.find_one(
        {"id": calc_id, "user_id": user["id"]},
        {"_id": 0}
    )
    if not calculation:
        raise HTTPException(status_code=404, detail="Calculation not found")
    
    # Create invoice data
    invoice_data = [
        {"Item": "VEHICLE IMPORT DUTY INVOICE", "Description": "", "Amount": ""},
        {"Item": "", "Description": "", "Amount": ""},
        {"Item": "Vehicle Information", "Description": "", "Amount": ""},
        {"Item": "Make/Model", "Description": f"{calculation.get('year', '')} {calculation.get('make', '')} {calculation.get('model', '')}", "Amount": ""},
        {"Item": "VIN", "Description": calculation.get('vin', 'N/A'), "Amount": ""},
        {"Item": "Body Style", "Description": calculation.get('body_style', 'N/A').replace('_', ' ').title() if calculation.get('body_style') else 'N/A', "Amount": ""},
        {"Item": "HS Code", "Description": calculation.get('hs_code', ''), "Amount": ""},
        {"Item": "Fuel/Duty Type", "Description": calculation.get('vehicle_type', '').title(), "Amount": ""},
        {"Item": "Engine Size", "Description": calculation.get('engine_category', 'N/A'), "Amount": ""},
        {"Item": "Country of Origin", "Description": calculation.get('country_of_origin', ''), "Amount": ""},
        {"Item": "Condition", "Description": "New" if calculation.get('is_new') else "Used", "Amount": ""},
        {"Item": "", "Description": "", "Amount": ""},
        {"Item": "Cost Breakdown", "Description": "", "Amount": ""},
        {"Item": "CIF Value (Cost + Insurance + Freight)", "Description": "", "Amount": f"${calculation.get('cif_value', 0):,.2f}"},
        {"Item": f"Import Duty ({calculation.get('duty_rate_display', '')})", "Description": "", "Amount": f"${calculation.get('import_duty', 0):,.2f}"},
        {"Item": f"Environmental Levy", "Description": calculation.get('environmental_levy_description', ''), "Amount": f"${calculation.get('environmental_levy', 0):,.2f}"},
    ]
    
    if calculation.get('tire_levy', 0) > 0:
        invoice_data.append({"Item": f"Used Tire Levy ({calculation.get('num_tires', 4)} tires × $5)", "Description": "", "Amount": f"${calculation.get('tire_levy', 0):,.2f}"})
    
    invoice_data.extend([
        {"Item": f"Processing Fee", "Description": calculation.get('processing_fee_description', '1% of CIF'), "Amount": f"${calculation.get('processing_fee', 0):,.2f}"},
        {"Item": "Landed Cost (Subtotal)", "Description": "", "Amount": f"${calculation.get('landed_cost', 0):,.2f}"},
        {"Item": f"VAT ({calculation.get('vat_rate', '10%')})", "Description": "10% of Landed Cost", "Amount": f"${calculation.get('vat', 0):,.2f}"},
        {"Item": "", "Description": "", "Amount": ""},
        {"Item": "TOTAL LANDED COST", "Description": "", "Amount": f"${calculation.get('total_landed_cost', 0):,.2f}"},
        {"Item": "", "Description": "", "Amount": ""},
    ])
    
    if calculation.get('concessionary_applied'):
        invoice_data.append({"Item": "Concessionary Rate Applied", "Description": calculation.get('concession_type', '').replace('_', ' ').title(), "Amount": f"Savings: ${calculation.get('savings', 0):,.2f}"})
    
    if calculation.get('requires_approval'):
        invoice_data.append({"Item": "⚠️ REQUIRES MINISTRY APPROVAL", "Description": "", "Amount": ""})
    
    invoice_data.extend([
        {"Item": "", "Description": "", "Amount": ""},
        {"Item": "DISCLAIMER", "Description": "This is an estimate only. Final duties determined by Customs Officers.", "Amount": ""},
        {"Item": "Generated by", "Description": "Class-B HS Code Agent", "Amount": f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"},
    ])
    
    df = pd.DataFrame(invoice_data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Invoice')
    output.seek(0)
    
    filename = f"vehicle_invoice_{calculation.get('make', 'vehicle')}_{calculation.get('model', '')}_{calc_id[:8]}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@api_router.get("/vehicle/rates")
async def get_vehicle_rates(user: dict = Depends(get_current_user)):
    """Get current vehicle duty rates"""
    # Create a JSON-serializable copy of rates (replace infinity with None/large number)
    serializable_rates = {}
    for vehicle_type, info in VEHICLE_DUTY_RATES.items():
        serializable_rates[vehicle_type] = {
            "hs_code": info["hs_code"],
            "hs_description": info["hs_description"],
            "tiers": []
        }
        for tier in info["tiers"]:
            safe_tier = {}
            for key, value in tier.items():
                if value == float('inf'):
                    safe_tier[key] = None  # Replace infinity with None
                else:
                    safe_tier[key] = value
            serializable_rates[vehicle_type]["tiers"].append(safe_tier)
    
    return {
        "rates": serializable_rates,
        "vat_rate": VEHICLE_VAT_RATE,
        "environmental_levy": {
            "new_vehicle": ENVIRONMENTAL_LEVY_NEW,
            "over_10_years_rate": ENVIRONMENTAL_LEVY_OVER_10_YEARS,
            "antique": ENVIRONMENTAL_LEVY_ANTIQUE,
            "tire_levy": TIRE_LEVY_PER_TIRE
        },
        "processing_fee": {
            "rate": PROCESSING_FEE_RATE,
            "min": PROCESSING_FEE_MIN,
            "max": PROCESSING_FEE_MAX
        },
        "last_updated": "January 2026",
        "note": "Rates based on Bahamas Customs Management Act and 2024 Budget"
    }

@api_router.get("/vehicle/guide")
async def get_vehicle_calculation_guide():
    """Download PDF guide for vehicle duty calculations"""
    from fastapi.responses import StreamingResponse
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.units import inch
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, spaceAfter=12, textColor=colors.HexColor('#2DD4BF'))
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, spaceAfter=8, spaceBefore=16, textColor=colors.HexColor('#2DD4BF'))
    subheading_style = ParagraphStyle('SubHeading', parent=styles['Heading3'], fontSize=12, spaceAfter=6, spaceBefore=12)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, spaceAfter=6, leading=14)
    note_style = ParagraphStyle('Note', parent=styles['Normal'], fontSize=9, textColor=colors.grey, spaceAfter=6)
    
    story = []
    
    # Title
    story.append(Paragraph("Bahamas Vehicle Import Duty Calculation Guide", title_style))
    story.append(Paragraph("Class-B HS Code Agent - Vehicle Brokering Calculator", note_style))
    story.append(Spacer(1, 0.25*inch))
    
    # Overview
    story.append(Paragraph("Overview", heading_style))
    story.append(Paragraph(
        "This guide explains how vehicle import duties are calculated for imports into The Bahamas. "
        "The calculation includes Import Duty (based on vehicle type and engine size), Environmental Levy, "
        "Processing Fee, Stamp Duty, and VAT based on the Customs Management Act (CMA) and current tariff schedules.",
        body_style
    ))
    story.append(Paragraph("Note: USD and BSD are pegged at 1:1 exchange rate.", note_style))
    
    # Gasoline/Diesel Vehicles
    story.append(Paragraph("1. Gasoline & Diesel Vehicle Duty Rates", heading_style))
    
    gas_data = [
        ['Engine Size (cc)', 'CIF Range', 'Duty Rate', 'HS Code'],
        ['Under 1,000cc', 'All values', '45%', '8703.21'],
        ['1,000 - 1,999cc', 'All values', '65%', '8703.22'],
        ['2,000 - 2,999cc', 'Under $40,000', '65%', '8703.23'],
        ['2,000 - 2,999cc', '$40,000+', '75%', '8703.23'],
        ['3,000cc and above', 'Under $40,000', '75%', '8703.24'],
        ['3,000cc and above', '$40,000+', '85%', '8703.24'],
    ]
    
    gas_table = Table(gas_data, colWidths=[1.5*inch, 1.3*inch, 1*inch, 1*inch])
    gas_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a3a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f8f8')]),
    ]))
    story.append(gas_table)
    story.append(Spacer(1, 0.15*inch))
    
    # Electric/Hybrid Vehicles
    story.append(Paragraph("2. Electric & Hybrid Vehicle Duty Rates", heading_style))
    story.append(Paragraph("Electric and hybrid vehicles receive preferential duty rates to encourage green vehicle adoption.", body_style))
    
    ev_data = [
        ['Vehicle Type', 'CIF Range', 'Duty Rate', 'HS Code'],
        ['Electric', 'Under $50,000', '25%', '8703.80'],
        ['Electric', '$50,000 - $100,000', '35%', '8703.80'],
        ['Electric', 'Over $100,000', '45%', '8703.80'],
        ['Hybrid', 'Under $40,000', '45%', '8703.40/60/70'],
        ['Hybrid', '$40,000 - $80,000', '55%', '8703.40/60/70'],
        ['Hybrid', 'Over $80,000', '65%', '8703.40/60/70'],
    ]
    
    ev_table = Table(ev_data, colWidths=[1.3*inch, 1.5*inch, 1*inch, 1.3*inch])
    ev_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a3a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f8f8')]),
    ]))
    story.append(ev_table)
    story.append(Spacer(1, 0.15*inch))
    
    # Commercial Vehicles
    story.append(Paragraph("3. Commercial Vehicle Duty Rates", heading_style))
    
    comm_data = [
        ['Vehicle Type', 'Duty Rate', 'HS Code'],
        ['Trucks (under 5 tonnes)', '45%', '8704.21'],
        ['Trucks (5-20 tonnes)', '35%', '8704.22'],
        ['Trucks (over 20 tonnes)', '25%', '8704.23'],
        ['Buses (10+ passengers)', '35%', '8702.10/20'],
    ]
    
    comm_table = Table(comm_data, colWidths=[2*inch, 1.2*inch, 1.3*inch])
    comm_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a3a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f8f8')]),
    ]))
    story.append(comm_table)
    story.append(Spacer(1, 0.15*inch))
    
    # Environmental Levy
    story.append(Paragraph("4. Environmental Levy", heading_style))
    story.append(Paragraph(
        "An environmental levy applies to all vehicle imports. The amount depends on the vehicle's age:",
        body_style
    ))
    
    env_data = [
        ['Vehicle Age', 'Environmental Levy'],
        ['New vehicles (0-3 years)', '$300 flat fee'],
        ['Used vehicles (4-10 years)', '$300 flat fee'],
        ['Vehicles 11+ years old', '20% of landed cost (MOF approval required)'],
        ['Antique vehicles (25+ years)', '$200 flat fee'],
        ['Used tires (per tire)', '$15 per tire'],
    ]
    
    env_table = Table(env_data, colWidths=[2.2*inch, 3*inch])
    env_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a3a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f8f8')]),
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#fff3cd')),
    ]))
    story.append(env_table)
    story.append(Paragraph("* Ministry of Finance approval required for vehicles over 10 years old.", note_style))
    
    # Other Fees
    story.append(Paragraph("5. Additional Fees & VAT", heading_style))
    
    fees_data = [
        ['Fee Type', 'Rate/Amount', 'Notes'],
        ['Processing Fee', '1% of CIF', 'Min $10, Max $750'],
        ['Stamp Duty', '8% of CIF', 'Standard rate'],
        ['VAT', '10%', 'On (CIF + Duty + Levy + Fees)'],
    ]
    
    fees_table = Table(fees_data, colWidths=[1.5*inch, 1.3*inch, 2.2*inch])
    fees_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a3a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f8f8')]),
    ]))
    story.append(fees_table)
    
    # Calculation Formula
    story.append(Paragraph("6. Complete Calculation Formula", heading_style))
    
    formula_data = [
        ['Step', 'Calculation'],
        ['1. Import Duty', 'CIF Value × Duty Rate (based on vehicle type/engine)'],
        ['2. Environmental Levy', '$300 (new/used) OR 20% (11+ years) OR $200 (antique)'],
        ['3. Processing Fee', 'CIF × 1% (min $10, max $750)'],
        ['4. Stamp Duty', 'CIF × 8%'],
        ['5. Landed Cost', 'CIF + Import Duty + Env Levy + Processing Fee'],
        ['6. VAT (10%)', '(Landed Cost + Stamp Duty) × 10%'],
        ['7. TOTAL', 'Landed Cost + Stamp Duty + VAT'],
    ]
    
    formula_table = Table(formula_data, colWidths=[1.8*inch, 4*inch])
    formula_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a3a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f8f8')]),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#2DD4BF')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    story.append(formula_table)
    
    # Example Calculation
    story.append(Paragraph("7. Example Calculation", heading_style))
    story.append(Paragraph("Vehicle: 2023 Toyota Camry, 2.5L Gasoline (2,500cc), CIF $35,000 USD", subheading_style))
    
    example_data = [
        ['Component', 'Calculation', 'Amount'],
        ['CIF Value', 'Purchase + Shipping + Insurance', '$35,000.00'],
        ['Duty Rate', '2,000-2,999cc, under $40k = 65%', '65%'],
        ['Import Duty', '$35,000 × 65%', '$22,750.00'],
        ['Environmental Levy', 'New vehicle flat fee', '$300.00'],
        ['Processing Fee', '$35,000 × 1%', '$350.00'],
        ['Stamp Duty', '$35,000 × 8%', '$2,800.00'],
        ['Landed Cost', '$35,000 + $22,750 + $300 + $350', '$58,400.00'],
        ['VAT (10%)', '($58,400 + $2,800) × 10%', '$6,120.00'],
        ['TOTAL LANDED COST', '', '$67,320.00'],
    ]
    
    example_table = Table(example_data, colWidths=[1.8*inch, 2.5*inch, 1.3*inch])
    example_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a3a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f8f8')]),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#2DD4BF')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    story.append(example_table)
    
    # Concessions
    story.append(Paragraph("8. Special Concessions", heading_style))
    story.append(Paragraph(
        "Certain buyers may qualify for reduced duty rates under special concession programs:",
        body_style
    ))
    story.append(Paragraph("• First-time vehicle owner concession", body_style))
    story.append(Paragraph("• Returning resident concession", body_style))
    story.append(Paragraph("• Investment Act concessions (for qualifying businesses)", body_style))
    story.append(Paragraph("• Public service vehicle concessions", body_style))
    story.append(Paragraph("Contact Bahamas Customs for eligibility requirements.", note_style))
    
    # Disclaimer
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("Important Notice", heading_style))
    story.append(Paragraph(
        "This guide is for informational purposes only. Actual duties and fees are determined by "
        "Bahamas Customs at the time of import. Rates may change without notice. Always consult "
        "with Bahamas Customs for official rates and requirements. Ministry of Finance approval is "
        "required for importing vehicles over 10 years old.",
        note_style
    ))
    story.append(Paragraph(
        "Contact: Bahamas Customs Department | Tel: +1 (242) 325-6550 | customs.bahamas.gov.bs",
        note_style
    ))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(f"Generated by Class-B HS Code Agent | {datetime.now(timezone.utc).strftime('%Y-%m-%d')}", note_style))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=Bahamas_Vehicle_Duty_Guide.pdf"}
    )

@api_router.get("/vehicle/template")
async def get_vehicle_template(user: dict = Depends(get_current_user)):
    """Download CSV template for bulk vehicle calculations"""
    from fastapi.responses import StreamingResponse
    
    template_data = """vin,make,model,year,vehicle_type,body_style,engine_size_cc,cif_value,country_of_origin,is_new,mileage,color
1HGBH41JXMN109186,Toyota,Camry,2023,gasoline,sedan,2500,35000,Japan,true,0,White
5YJSA1DG9DFP14705,Tesla,Model S,2024,electric,sedan,,85000,USA,true,0,Black
WVWZZZ3CZWE123456,Volkswagen,Golf,2023,hybrid,hatchback,1400,42000,Germany,true,0,Silver
1C4RJFAG5FC123456,Jeep,Grand Cherokee,2022,gasoline,suv,3600,55000,USA,false,25000,Blue
3FADP4BJ9DM123456,Ford,Focus,2021,gasoline,hatchback,1000,18000,USA,false,45000,Red
JN1TANT31U0000001,Nissan,Leaf,2024,electric,hatchback,,32000,Japan,true,0,White"""
    
    output = io.StringIO()
    output.write(template_data)
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=vehicle_import_template.csv"}
    )

@api_router.post("/vehicle/upload")
async def upload_vehicle_batch(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """Process bulk vehicle calculations from CSV/Excel upload"""
    
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
    required_cols = ['make', 'model', 'year', 'vehicle_type', 'cif_value', 'country_of_origin']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise HTTPException(status_code=400, detail=f"Missing required columns: {', '.join(missing_cols)}")
    
    # Process each row
    results = []
    errors = []
    batch_id = str(uuid.uuid4())
    total_landed_cost = 0
    total_duties = 0
    
    for idx, row in df.iterrows():
        try:
            # Parse values
            vehicle_type = str(row['vehicle_type']).lower().strip()
            if vehicle_type not in VEHICLE_DUTY_RATES:
                vehicle_type = 'gasoline'
            
            engine_cc = int(row['engine_size_cc']) if 'engine_size_cc' in df.columns and pd.notna(row.get('engine_size_cc')) else None
            cif_value = float(row['cif_value'])
            year = int(row['year'])
            is_new = str(row.get('is_new', 'true')).lower() in ['true', '1', 'yes']
            
            # Determine duty rate
            duty_rate, duty_description = determine_vehicle_duty_rate(vehicle_type, engine_cc, cif_value)
            rates_info = VEHICLE_DUTY_RATES.get(vehicle_type, VEHICLE_DUTY_RATES["gasoline"])
            
            # Calculate duties
            import_duty = cif_value * duty_rate
            environmental_levy = cif_value * ENVIRONMENTAL_LEVY_RATE
            stamp_duty = cif_value * STAMP_DUTY_RATE
            vat_base = cif_value + import_duty + environmental_levy + stamp_duty
            vat = vat_base * VEHICLE_VAT_RATE
            item_total = cif_value + import_duty + environmental_levy + stamp_duty + vat + PROCESSING_FEE
            
            result = {
                "row": idx + 1,
                "vin": str(row.get('vin', '')) if 'vin' in df.columns and pd.notna(row.get('vin')) else None,
                "make": str(row['make']),
                "model": str(row['model']),
                "year": year,
                "vehicle_type": vehicle_type,
                "body_style": str(row.get('body_style', '')) if 'body_style' in df.columns and pd.notna(row.get('body_style')) else None,
                "engine_size_cc": engine_cc,
                "engine_category": get_engine_category(engine_cc, vehicle_type),
                "cif_value": round(cif_value, 2),
                "duty_rate": duty_rate,
                "duty_rate_display": f"{duty_rate * 100:.0f}%",
                "import_duty": round(import_duty, 2),
                "environmental_levy": round(environmental_levy, 2),
                "stamp_duty": round(stamp_duty, 2),
                "vat": round(vat, 2),
                "processing_fee": PROCESSING_FEE,
                "total_landed_cost": round(item_total, 2),
                "hs_code": rates_info["hs_code"],
                "country_of_origin": str(row['country_of_origin']),
                "is_new": is_new,
                "color": str(row.get('color', '')) if 'color' in df.columns and pd.notna(row.get('color')) else None,
                "mileage": int(row.get('mileage', 0)) if 'mileage' in df.columns and pd.notna(row.get('mileage')) else None
            }
            
            results.append(result)
            total_landed_cost += item_total
            total_duties += import_duty
            
        except Exception as e:
            errors.append({"row": idx + 1, "error": str(e)})
    
    # Save batch record
    batch_record = {
        "id": batch_id,
        "user_id": user["id"],
        "filename": file.filename,
        "total_vehicles": len(results),
        "successful": len(results),
        "failed": len(errors),
        "total_cif": round(sum(r["cif_value"] for r in results), 2),
        "total_duties": round(total_duties, 2),
        "total_landed_cost": round(total_landed_cost, 2),
        "results": results,
        "errors": errors,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.vehicle_batches.insert_one(batch_record)
    
    return {
        "batch_id": batch_id,
        "filename": file.filename,
        "total_vehicles": len(results),
        "successful": len(results),
        "failed": len(errors),
        "total_cif": round(sum(r["cif_value"] for r in results), 2),
        "total_duties": round(total_duties, 2),
        "total_landed_cost": round(total_landed_cost, 2),
        "results": results,
        "errors": errors
    }

@api_router.get("/vehicle/batches")
async def get_vehicle_batches(user: dict = Depends(get_current_user)):
    """Get user's vehicle batch history"""
    batches = await db.vehicle_batches.find(
        {"user_id": user["id"]},
        {"_id": 0, "results": 0}
    ).sort("created_at", -1).to_list(50)
    
    for batch in batches:
        if isinstance(batch.get("created_at"), str):
            batch["created_at"] = datetime.fromisoformat(batch["created_at"])
    
    return batches

@api_router.get("/vehicle/batches/{batch_id}")
async def get_vehicle_batch(batch_id: str, user: dict = Depends(get_current_user)):
    """Get specific vehicle batch details"""
    batch = await db.vehicle_batches.find_one(
        {"id": batch_id, "user_id": user["id"]},
        {"_id": 0}
    )
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    if isinstance(batch.get("created_at"), str):
        batch["created_at"] = datetime.fromisoformat(batch["created_at"])
    
    return batch

@api_router.get("/vehicle/batches/{batch_id}/export")
async def export_vehicle_batch(batch_id: str, format: str = "csv", user: dict = Depends(get_current_user)):
    """Export vehicle batch as CSV or Excel"""
    from fastapi.responses import StreamingResponse
    
    batch = await db.vehicle_batches.find_one(
        {"id": batch_id, "user_id": user["id"]},
        {"_id": 0}
    )
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    # Prepare export data
    export_data = []
    for item in batch["results"]:
        export_data.append({
            "VIN": item.get("vin", ""),
            "Make": item.get("make", ""),
            "Model": item.get("model", ""),
            "Year": item.get("year", ""),
            "Type": item.get("vehicle_type", ""),
            "Engine (cc)": item.get("engine_size_cc", ""),
            "Engine Category": item.get("engine_category", ""),
            "HS Code": item.get("hs_code", ""),
            "Country": item.get("country_of_origin", ""),
            "New/Used": "New" if item.get("is_new") else "Used",
            "CIF Value ($)": item.get("cif_value", 0),
            "Duty Rate": item.get("duty_rate_display", ""),
            "Import Duty ($)": item.get("import_duty", 0),
            "Environmental Levy ($)": item.get("environmental_levy", 0),
            "Stamp Duty ($)": item.get("stamp_duty", 0),
            "VAT ($)": item.get("vat", 0),
            "Processing Fee ($)": item.get("processing_fee", 0),
            "Total Landed Cost ($)": item.get("total_landed_cost", 0)
        })
    
    df = pd.DataFrame(export_data)
    
    if format == "xlsx":
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Vehicle Imports')
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=vehicle_batch_{batch_id[:8]}.xlsx"}
        )
    else:
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=vehicle_batch_{batch_id[:8]}.csv"}
        )

@api_router.get("/vehicle/checklist")
async def get_vehicle_checklist(user: dict = Depends(get_current_user)):
    """Get vehicle clearance checklist for client and broker"""
    return {
        "client_checklist": [
            {
                "category": "Vehicle Documents",
                "items": [
                    {"item": "Original Title/Ownership Document", "required": True, "notes": "Must be in client's name or endorsed"},
                    {"item": "Bill of Sale/Invoice", "required": True, "notes": "Showing purchase price and seller details"},
                    {"item": "Vehicle Registration (current)", "required": True, "notes": "From country of export"},
                    {"item": "Export Certificate/Deregistration", "required": True, "notes": "Proof vehicle was legally exported"},
                    {"item": "VIN Verification Report", "required": False, "notes": "Recommended for used vehicles"}
                ]
            },
            {
                "category": "Shipping Documents",
                "items": [
                    {"item": "Bill of Lading (Original)", "required": True, "notes": "Shows consignee and vehicle details"},
                    {"item": "Commercial Invoice", "required": True, "notes": "For customs valuation"},
                    {"item": "Packing List", "required": False, "notes": "If vehicle shipped with accessories"}
                ]
            },
            {
                "category": "Personal Documents",
                "items": [
                    {"item": "Valid Passport", "required": True, "notes": "For identity verification"},
                    {"item": "National Insurance Number", "required": True, "notes": "For registration purposes"},
                    {"item": "Proof of Address", "required": True, "notes": "Utility bill or bank statement"},
                    {"item": "Driver's License", "required": True, "notes": "Valid Bahamas or international license"}
                ]
            },
            {
                "category": "For Concessionary Rates",
                "items": [
                    {"item": "First-time Owner Declaration", "required": False, "notes": "Notarized statement if claiming first vehicle"},
                    {"item": "Returning Resident Certificate", "required": False, "notes": "From Immigration Department"},
                    {"item": "Disability Certificate", "required": False, "notes": "From registered medical practitioner"}
                ]
            }
        ],
        "broker_checklist": [
            {
                "category": "Declaration Preparation",
                "items": [
                    {"item": "Complete Electronic Single Window Entry", "required": True, "notes": "Form C-76 or equivalent"},
                    {"item": "Calculate Duties (Import Duty, VAT, Levies)", "required": True, "notes": "Use official rate tables"},
                    {"item": "Verify HS Code Classification", "required": True, "notes": "8703.xx for passenger vehicles"},
                    {"item": "Check for Concessionary Eligibility", "required": True, "notes": "First vehicle, returning resident, etc."}
                ]
            },
            {
                "category": "Inspection & Compliance",
                "items": [
                    {"item": "Schedule Vehicle Inspection", "required": True, "notes": "Customs warehouse or port"},
                    {"item": "Verify VIN matches documentation", "required": True, "notes": "Physical inspection required"},
                    {"item": "Check for Salvage/Rebuilt Title", "required": True, "notes": "May affect duty calculation"},
                    {"item": "Environmental Compliance Check", "required": False, "notes": "For commercial vehicles"}
                ]
            },
            {
                "category": "Payment Processing",
                "items": [
                    {"item": "Collect all duties and fees from client", "required": True, "notes": "Before customs release"},
                    {"item": "Process payment at Customs Treasury", "required": True, "notes": "Keep receipt copies"},
                    {"item": "Obtain Customs Release Order", "required": True, "notes": "For port release"}
                ]
            },
            {
                "category": "Post-Clearance",
                "items": [
                    {"item": "Arrange vehicle delivery/pickup", "required": True, "notes": "Coordinate with port"},
                    {"item": "Provide client with import documentation", "required": True, "notes": "For licensing"},
                    {"item": "Advise on Road Traffic registration", "required": True, "notes": "Thompson Blvd or local office"}
                ]
            }
        ],
        "important_contacts": {
            "customs_main": "+1 (242) 325-6550",
            "customs_email": "customs@bahamas.gov.bs",
            "road_traffic": "+1 (242) 322-2610",
            "port_authority": "+1 (242) 323-2265"
        }
    }

# ============= FEEDBACK ENDPOINT =============
class FeedbackRequest(BaseModel):
    name: str
    email: str
    subject: str
    message: str
    feedback_type: str = "general"  # general, bug, feature, question

@api_router.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """Submit user feedback - sends to configured email"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    # Store feedback in database
    feedback_id = str(uuid.uuid4())
    feedback_record = {
        "id": feedback_id,
        "name": feedback.name,
        "email": feedback.email,
        "subject": feedback.subject,
        "message": feedback.message,
        "feedback_type": feedback.feedback_type,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.feedback.insert_one(feedback_record)
    
    # Send email notification
    FEEDBACK_EMAIL = "gfp6ixhc@yourfeedback.anonaddy.me"
    
    # Create email content
    email_body = f"""
New Feedback Received - Class-B HS Code Agent

Type: {feedback.feedback_type.upper()}
From: {feedback.name} ({feedback.email})
Subject: {feedback.subject}

Message:
{feedback.message}

---
Feedback ID: {feedback_id}
Timestamp: {datetime.now(timezone.utc).isoformat()}
"""
    
    # Try to send via SMTP (will work if SMTP is configured, otherwise just log)
    try:
        # Store for admin review regardless of email success
        print(f"Feedback received from {feedback.email}: {feedback.subject}")
        
        # Attempt to use local mail or configured SMTP
        smtp_host = os.environ.get('SMTP_HOST', 'localhost')
        smtp_port = int(os.environ.get('SMTP_PORT', 25))
        
        msg = MIMEMultipart()
        msg['From'] = f"Class-B Agent <noreply@classb-agent.com>"
        msg['To'] = FEEDBACK_EMAIL
        msg['Subject'] = f"[Class-B Feedback] {feedback.feedback_type.upper()}: {feedback.subject}"
        msg.attach(MIMEText(email_body, 'plain'))
        
        # Only try SMTP if explicitly configured
        if os.environ.get('SMTP_HOST'):
            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                server.sendmail(msg['From'], [FEEDBACK_EMAIL], msg.as_string())
    except Exception as e:
        # Log the error but don't fail - feedback is stored in DB
        print(f"Email notification failed (feedback still saved): {str(e)}")
    
    return {
        "message": "Thank you for your feedback! We'll review it shortly.",
        "feedback_id": feedback_id
    }

@api_router.get("/feedback")
async def get_feedback(user: dict = Depends(get_current_user)):
    """Get feedback history (admin only in future)"""
    feedback_list = await db.feedback.find(
        {},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return feedback_list

# ============= ROOT ROUTE =============
@api_router.get("/")
async def root():
    return {"message": "Bahamas HS Code Classification API", "version": "1.0.0"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy"}

# ============= WEEKLY ACCOUNT LOG SCHEDULER =============
import asyncio
from contextlib import asynccontextmanager

async def send_weekly_account_log():
    """Send weekly log of newly created accounts to admin email"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    ADMIN_EMAIL = "gfp6ixhc@yourfeedback.anonaddy.me"
    
    # Calculate date range (last 7 days)
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=7)
    
    try:
        # Get accounts created in the last week
        users = await db.users.find(
            {
                "created_at": {
                    "$gte": start_date.isoformat(),
                    "$lte": end_date.isoformat()
                }
            },
            {"_id": 0, "name": 1, "email": 1, "created_at": 1, "company": 1}
        ).to_list(1000)
        
        if not users:
            logger.info("Weekly account log: No new accounts this week")
            return
        
        # Build email content
        account_list = ""
        for i, user in enumerate(users, 1):
            account_list += f"{i}. {user.get('name', 'N/A')} - {user.get('email', 'N/A')}"
            if user.get('company'):
                account_list += f" ({user.get('company')})"
            account_list += f"\n   Created: {user.get('created_at', 'Unknown')}\n\n"
        
        email_body = f"""
Weekly Account Creation Report - Class-B HS Code Agent

Report Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}
Total New Accounts: {len(users)}

New Accounts:
{account_list}
---
Generated: {datetime.now(timezone.utc).isoformat()}
This is an automated weekly report.
"""
        
        logger.info(f"Weekly account log: {len(users)} new accounts")
        print(f"Weekly Account Log - {len(users)} accounts created this week")
        
        # Store log in database for reference
        await db.weekly_logs.insert_one({
            "id": str(uuid.uuid4()),
            "type": "account_creation",
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "account_count": len(users),
            "accounts": [{"name": u.get("name"), "email": u.get("email")} for u in users],
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Send email
        smtp_host = os.environ.get('SMTP_HOST', 'localhost')
        smtp_port = int(os.environ.get('SMTP_PORT', 25))
        
        msg = MIMEMultipart()
        msg['From'] = f"Class-B Agent <noreply@classb-agent.com>"
        msg['To'] = ADMIN_EMAIL
        msg['Subject'] = f"[Class-B Agent] Weekly Account Report - {len(users)} New Accounts"
        msg.attach(MIMEText(email_body, 'plain'))
        
        if os.environ.get('SMTP_HOST'):
            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                server.sendmail(msg['From'], [ADMIN_EMAIL], msg.as_string())
                
    except Exception as e:
        logger.error(f"Weekly account log failed: {str(e)}")
        print(f"Weekly account log error: {str(e)}")

async def weekly_log_scheduler():
    """Background task to run weekly account log every 7 days"""
    while True:
        try:
            # Wait for 7 days (604800 seconds)
            # For testing, you can change this to a shorter interval
            await asyncio.sleep(604800)  # 7 days in seconds
            await send_weekly_account_log()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Weekly scheduler error: {str(e)}")
            await asyncio.sleep(3600)  # Retry in 1 hour on error

# Manual trigger for weekly log (for testing or admin use)
@api_router.post("/admin/trigger-weekly-log")
async def trigger_weekly_log(user: dict = Depends(require_admin)):
    """Manually trigger weekly account log (admin only)"""
    await send_weekly_account_log()
    return {"message": "Weekly account log triggered successfully"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Background task holder
weekly_log_task = None

@app.on_event("startup")
async def startup_event():
    """Start background tasks on app startup"""
    global weekly_log_task
    weekly_log_task = asyncio.create_task(weekly_log_scheduler())
    logger.info("Weekly account log scheduler started")
    
    # Seed super admin account
    await seed_super_admin()
    
    # Send initial log on startup (captures any accounts created before scheduler was running)
    # Comment this out if you don't want immediate log on startup
    # await send_weekly_account_log()

@app.on_event("shutdown")
async def shutdown_db_client():
    global weekly_log_task
    if weekly_log_task:
        weekly_log_task.cancel()
        try:
            await weekly_log_task
        except asyncio.CancelledError:
            pass
    client.close()
