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

## What's Been Implemented (Jan 30, 2026)

### MVP Features
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

### Design
- Dark mode with Electric Teal (#2DD4BF) accents
- Chivo (headings), Inter (body), JetBrains Mono (code) fonts
- Glassmorphism login card with shipping port background
- Bento grid dashboard layout

## Prioritized Backlog

### P0 (Critical) - Done
- [x] Core classification flow

### P1 (High Priority)
- [ ] PDF invoice extraction with AI (Gemini 2.5 Flash)
- [ ] Admin dashboard for user management
- [ ] Bulk document processing
- [ ] Save/reuse approved HS codes for repeat shipments

### P2 (Medium Priority)
- [ ] ASYCUDA World direct integration
- [ ] Classification comparison (before/after edit)
- [ ] Team/organization accounts
- [ ] API rate limiting
- [ ] Email notifications for flagged items

### P3 (Low Priority)
- [ ] Light mode theme toggle
- [ ] Advanced search filters
- [ ] Classification analytics/reports
- [ ] Mobile app version

## Next Tasks
1. Implement PDF extraction with AI (FileContentWithMimeType + Gemini)
2. Add bulk upload support for multiple files
3. Create admin dashboard for user management
4. Add learning from user approvals (improve AI suggestions)
5. Integrate duty rate calculation based on HS codes
