# TariffExpert - Bahamas HS Code Classification System

## Problem Statement
Build an AI HS Code Classification web application for imports into The Bahamas, compliant with the Customs Management Act (CMA) and Bahamas Customs procedures. The system must accept Excel, CSV, and PDF uploads, extract item data, normalize descriptions, and assign accurate HS codes using GRI 1–6, with explanations, confidence scoring, audit trails, and ASYCUDA-ready outputs.

## Architecture

### Tech Stack
- **Frontend**: React 19, Tailwind CSS, Shadcn/UI, React Router
- **Backend**: FastAPI (Python), Motor (async MongoDB driver)
- **Database**: MongoDB
- **AI**: OpenAI GPT-5.2 via Emergent LLM Key
- **Auth**: JWT with bcrypt password hashing

### API Endpoints
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user
- `POST /api/documents/upload` - Upload Excel/CSV/PDF
- `GET /api/documents` - List user documents
- `POST /api/classifications/process/{doc_id}` - AI classification
- `GET /api/classifications` - List classifications
- `GET /api/classifications/{id}` - Get classification details
- `PUT /api/classifications/{id}/items/{index}` - Update item
- `GET /api/classifications/{id}/export` - Export CSV/XLSX
- `GET/POST/PUT/DELETE /api/hs-codes` - HS code library CRUD
- `GET /api/dashboard/stats` - Dashboard statistics
- `POST /api/alcohol/calculate` - Alcohol duty calculation
- `GET /api/alcohol/calculations` - Alcohol calculation history
- `GET /api/alcohol/calculations/{id}/export` - Export alcohol calculation
- `GET /api/alcohol/rates` - Current duty rates

## User Personas
1. **Customs Broker** - Primary user, needs fast accurate HS classification
2. **Freight Forwarder** - Bulk imports, needs batch processing
3. **Courier Company** - High volume, needs efficiency
4. **Importer** - Occasional use, needs simplicity

## Core Requirements (Static)
- [x] CMA Compliance
- [x] GRI Rules 1-6 Application
- [x] HS Code 6-10 digit classification
- [x] Confidence scoring
- [x] Audit trail with reasoning
- [x] ASYCUDA-compatible export

## What's Been Implemented

### MVP Features (Jan 30, 2026)
- [x] User authentication (JWT)
- [x] Document upload (Excel, CSV, PDF support)
- [x] AI-powered HS code classification with GPT-5.2
- [x] Classification results with confidence scores
- [x] GRI rule explanations
- [x] CMA compliance flags (restricted items, permits)
- [x] Export to CSV/Excel
- [x] HS Code library management (CRUD)
- [x] Classification history
- [x] Dashboard with statistics
- [x] Professional dark mode UI
- [x] Mobile responsive design

### B-CLASS Alcohol Calculator Module (Jan 31, 2026)
- [x] Automated duty calculation for Wine, Beer, Spirits, Liqueur
- [x] Import duty calculation (35-45% based on type)
- [x] Excise duty calculation (per liter or per LPA)
- [x] VAT calculation (10% on CIF + duties)
- [x] License fee calculation
- [x] Total landed cost breakdown
- [x] Warning flags (high ABV, permits, volume limits)
- [x] Calculation history
- [x] Export to printable PDF format
- [x] Current Bahamas duty rates display
- [x] **Bulk Upload** - CSV/Excel file upload for batch processing
- [x] **Downloadable Template** - Pre-formatted CSV with sample data
- [x] **Batch Results** - Summary view with totals and per-item breakdown
- [x] **Batch Export** - Export as CSV or Excel

### Bulk HS Code Classification (Jan 31, 2026)
- [x] **Item List Upload** - CSV/Excel upload for bulk HS classification
- [x] **Downloadable Template** - Pre-formatted CSV with 8 sample items
- [x] **AI Classification** - GPT-5.2 powered HS code assignment
- [x] **Results Table** - Description, HS code, confidence scores
- [x] **Export Options** - CSV and Excel export for classified items
- [x] **Tabbed Interface** - Document Upload + Bulk Item List tabs

### Bahamas HS Code Library (Jan 31, 2026)
- [x] **Pre-loaded Database** - 63 Bahamas-specific HS codes
- [x] **Detailed Information** - Duty rates, chapter, section, notes
- [x] **Restriction Flags** - Visual indicators for restricted items
- [x] **Permit Requirements** - Flags for items requiring permits
- [x] **Searchable** - Full-text search by code or description
- [x] **Editable** - Add, edit, delete codes as needed
- [x] **Import from Template** - Bulk import HS codes via CSV/Excel (Jan 31, 2026)

### CMA Reference Module (Jan 31, 2026)
- [x] **21 Regulations** - Comprehensive CMA coverage
- [x] **Categories**: Preliminary, Administration, Importation, Duties, Exemptions, Procedures, Enforcement, Appeals, Special Provisions, Trade Agreements
- [x] **Full-text Search** - Search by keyword or phrase
- [x] **Quick Search Tags** - One-click common searches
- [x] **Expandable Content** - Accordion-style regulation display
- [x] **Keyword Navigation** - Click keywords to search related content

### Classi AI Helpdesk (Jan 31, 2026)
- [x] **Floating Chat Widget** - Accessible from all pages after login
- [x] **Bahamian Flag Avatar** - National colors (#00778B, #FFC72C, #000)
- [x] **GPT-5.2 Powered** - Intelligent responses via Emergent LLM Key
- [x] **Bahamas Customs Knowledge** - Ports of entry, forms, procedures, contact info
- [x] **Quick Action Buttons** - Pre-defined common questions
- [x] **App Help** - Guidance on using all features
- [x] **Contact Info** - Bahamas Customs phone, email, address

### HS Code Auto-Suggest (Jan 31, 2026)
- [x] **Smart Search** - Type description to find matching HS codes
- [x] **Instant Results** - Debounced 300ms search with dropdown
- [x] **Rich Information** - Shows code, description, duty rate, flags
- [x] **One-Click Apply** - Select to auto-fill code and description
- [x] **Classification Edit Integration** - Available when editing items
- [x] **Global HS Codes Imported** - 6,941 total codes in library

### Customs Forms Module (Jan 31, 2026)
- [x] **104 Official Forms** - Complete Bahamas Customs forms list
- [x] **Categories** - Reporting, Import, Export, Transit, Warehousing, Bonds, IPR, etc.
- [x] **Form Details** - Number, name, description, usage, where to obtain
- [x] **Searchable** - Find forms by number or name

### Country Codes Module (Jan 31, 2026)
- [x] **241 Countries** - Official Bahamas Customs numeric codes
- [x] **Customs Code** - 3-digit numeric code for declarations
- [x] **ISO Code** - 2-letter country code
- [x] **Trade Agreements** - CARICOM member identification
- [x] **Regional Groupings** - Caribbean, North America, Europe, Asia, Africa, etc.

### Tariffs & Duties Module (Jan 31, 2026)
- [x] **Overview Tab** - Key info cards (rate range, VAT, EPA), tariff structure, common rates
- [x] **Sections Tab** - All 22 HS sections with chapters and descriptions
- [x] **Excise Tab** - Alcohol, tobacco, petroleum excise duties
- [x] **GRI Rules Tab** - 10 General Rules of Interpretation with examples
- [x] **Exemptions Tab** - Chapter 98 duty exemptions by category
- [x] **Bahamas 2023 Tariff Rates** - 1,584 codes imported with actual duty rates

### Vehicle Brokering Calculator (Jan 31, 2026)
- [x] **Single Vehicle Calculator** - Calculate duties for individual vehicle imports
- [x] **Duty Rate Tiers** - Electric/Hybrid (10-25%), Gasoline/Diesel (45-65%), Commercial (65-85%)
- [x] **Engine Size Detection** - Automatic duty tier based on engine displacement (cc)
- [x] **Value-Based Tiers** - Different rates for vehicles ≤$50k vs >$50k
- [x] **Complete Breakdown** - Import Duty, Environmental Levy (1%), Stamp Duty (7%), VAT (10%), Processing Fee
- [x] **Concessionary Rates** - Support for first-time owner, returning resident, disabled exemptions
- [x] **Vehicle Types** - Electric, Hybrid, Gasoline, Diesel, Commercial
- [x] **HS Code Assignment** - Automatic HS code (8703.xx) based on vehicle type
- [x] **Bulk Upload** - CSV/Excel upload for batch vehicle calculations
- [x] **Downloadable Template** - Pre-formatted CSV with sample vehicle data
- [x] **Batch Results** - Summary with per-vehicle duty breakdown and totals
- [x] **Batch Export** - Export results as CSV or Excel
- [x] **Clearance Checklist** - Client and Broker checklists with required documents
- [x] **Important Contacts** - Customs, Road Traffic, Port Authority phone numbers
- [x] **Calculation History** - View and reload past calculations
- [x] **Warning Flags** - Age-based inspection requirements, high mileage, permits

### API Endpoints - Vehicle Module
- `POST /api/vehicle/calculate` - Calculate single vehicle duties
- `GET /api/vehicle/calculations` - List calculation history
- `GET /api/vehicle/calculations/{id}` - Get specific calculation
- `GET /api/vehicle/rates` - Get current duty rates
- `GET /api/vehicle/template` - Download bulk upload template
- `POST /api/vehicle/upload` - Bulk vehicle upload and calculation
- `GET /api/vehicle/batches` - List batch history
- `GET /api/vehicle/batches/{id}` - Get batch details
- `GET /api/vehicle/batches/{id}/export` - Export batch results
- `GET /api/vehicle/checklist` - Get clearance checklist

### Design
- Dark mode with Electric Teal (#2DD4BF) accents
- Chivo (headings), Inter (body), JetBrains Mono (code) fonts
- Glassmorphism login card with shipping port background
- Bento grid dashboard layout
- **Branding: Class-B HS Code Agent** (updated Jan 31, 2026)
- **Electronic Single Window Ready** (replaced ASYCUDA references)

## Prioritized Backlog

### P0 (Critical) - Done
- [x] Core classification flow
- [x] B-CLASS Alcohol Calculator
- [x] Vehicle Brokering Calculator

### P1 (High Priority)
- [ ] PDF invoice extraction with AI (Gemini 2.5 Flash)
- [ ] Admin dashboard for user management
- [ ] Bulk document processing
- [ ] Save/reuse approved HS codes for repeat shipments
- [ ] Batch alcohol shipment processing

### P2 (Medium Priority)
- [ ] Electronic Single Window direct integration
- [ ] Classification comparison (before/after edit)
- [ ] Team/organization accounts
- [ ] API rate limiting
- [ ] Email notifications for flagged items
- [ ] Scenario comparison for alcohol shipments

### P3 (Low Priority)
- [ ] Light mode theme toggle
- [ ] Advanced search filters
- [ ] Classification analytics/reports
- [ ] Mobile app version
- [ ] Real-time duty rate API integration

## Next Tasks
1. Finalize NotationsPage.jsx UI (currently a scaffold)
2. Add HS Library search link from classification item edit dialog
3. Create downloadable Alcohol Calculation PDF guide
4. Implement PDF extraction with AI (FileContentWithMimeType + Gemini)
5. Create admin dashboard for user management
