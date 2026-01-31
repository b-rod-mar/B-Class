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

### Design
- Dark mode with Electric Teal (#2DD4BF) accents
- Chivo (headings), Inter (body), JetBrains Mono (code) fonts
- Glassmorphism login card with shipping port background
- Bento grid dashboard layout

## Prioritized Backlog

### P0 (Critical) - Done
- [x] Core classification flow
- [x] B-CLASS Alcohol Calculator

### P1 (High Priority)
- [ ] PDF invoice extraction with AI (Gemini 2.5 Flash)
- [ ] Admin dashboard for user management
- [ ] Bulk document processing
- [ ] Save/reuse approved HS codes for repeat shipments
- [ ] Batch alcohol shipment processing

### P2 (Medium Priority)
- [ ] ASYCUDA World direct integration
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
1. Implement PDF extraction with AI (FileContentWithMimeType + Gemini)
2. Add bulk upload support for multiple files
3. Create admin dashboard for user management
4. Add learning from user approvals (improve AI suggestions)
5. Integrate real-time duty rate updates from Bahamas Customs
