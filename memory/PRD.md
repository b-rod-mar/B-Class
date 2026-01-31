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
- `DELETE /api/classifications/{id}` - Delete classification
- `DELETE /api/classifications/{id}/items/{index}` - Delete item
- `GET /api/classifications/{id}/export` - Export CSV/XLSX
- `GET/POST/PUT/DELETE /api/hs-codes` - HS code library CRUD
- `GET /api/dashboard/stats` - Dashboard statistics
- `POST /api/alcohol/calculate` - Alcohol duty calculation
- `GET /api/alcohol/calculations` - Alcohol calculation history
- `DELETE /api/alcohol/calculations/{id}` - Delete alcohol calculation
- `GET /api/alcohol/calculations/{id}/export` - Export alcohol calculation
- `GET /api/alcohol/rates` - Current duty rates
- `POST /api/vehicle/calculate` - Vehicle duty calculation
- `GET /api/vehicle/calculations` - Vehicle calculation history
- `DELETE /api/vehicle/calculations/{id}` - Delete vehicle calculation
- `GET /api/vehicle/rates` - Current vehicle duty rates
- `GET /api/vehicle/template` - Download bulk upload template
- `POST /api/vehicle/upload` - Bulk vehicle upload
- `GET /api/vehicle/batches` - Batch history
- `GET /api/vehicle/checklist` - Clearance checklists
- `POST /api/feedback` - Submit user feedback
- `GET /api/feedback` - Get feedback history

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
- [x] **Environmental Levy** - Flat $250 for new/standard, 20% for >10 years, $200 for antique, $5/tire
- [x] **Processing Fee** - 1% of CIF (min $10, max $750)
- [x] **Complete Breakdown** - CIF → Duty → Levy → Processing → Landed Cost → VAT (10% of LC)
- [x] **Concessionary Rates** - First-time owner (20% reduction), Returning resident (15% reduction), Disabled (10% flat)
- [x] **Vehicle Types** - Electric, Hybrid, Gasoline, Diesel, Commercial
- [x] **HS Code Assignment** - Automatic HS code (8703.xx) based on vehicle type
- [x] **Bulk Upload** - CSV/Excel upload for batch vehicle calculations
- [x] **Downloadable Template** - Pre-formatted CSV with sample vehicle data
- [x] **Batch Results** - Summary with per-vehicle duty breakdown and totals
- [x] **Batch Export** - Export results as CSV or Excel
- [x] **Clearance Checklist** - Client and Broker checklists with required documents
- [x] **Important Contacts** - Customs, Road Traffic, Port Authority phone numbers
- [x] **Calculation History** - View and reload past calculations with DELETE
- [x] **Warning Flags** - Age-based inspection requirements, Ministry approval needed
- [x] **Antique/Vintage Option** - Special $200 levy for classic cars

### Hawksbill Creek Agreement (Jan 31, 2026)
- [x] **CMA Reference Updated** - 4 entries on Hawksbill Creek Agreement added
- [x] **Overview** - What it is, Grand Bahama Port Authority, Freeport establishment
- [x] **Historical Background** - 1955 origins, Wallace Groves, 99-year concession
- [x] **Duty & Tax Exemptions** - C14 form, Port Area duty-free imports
- [x] **Implications for Brokers** - Licensee verification, transfer rules

### Feedback System (Jan 31, 2026)
- [x] **Share Feedback Button** - In sidebar user section
- [x] **Feedback Dialog** - Name, email, type, subject, message
- [x] **Feedback Types** - General, Bug Report, Feature Request, Question
- [x] **Email Notification** - Forwards to gfp6ixhc@yourfeedback.anonaddy.me
- [x] **Database Storage** - All feedback saved for review

### Professional Disclaimer (Jan 31, 2026)
- [x] **Disclaimer Banner** - Always visible at sidebar bottom
- [x] **Full Legal Text** - Secondary support tool, not legal advice
- [x] **User Responsibility** - Verify HS codes, final amounts by Customs
- [x] **Official Contacts** - Bahamas Customs phone, email, website links

### Delete Functionality (Jan 31, 2026)
- [x] **Classification History** - Delete entire classification from dropdown
- [x] **Classification Items** - Delete individual items from results table
- [x] **Alcohol Calculations** - Delete from history list
- [x] **Vehicle Calculations** - Delete from history list
- [x] **Notations** - Already had delete functionality

### API Endpoints - Vehicle Module
- `POST /api/vehicle/calculate` - Calculate single vehicle duties
- `GET /api/vehicle/calculations` - List calculation history
- `GET /api/vehicle/calculations/{id}` - Get specific calculation
- `GET /api/vehicle/calculations/{id}/invoice` - Generate Excel invoice
- `DELETE /api/vehicle/calculations/{id}` - Delete calculation
- `GET /api/vehicle/rates` - Get current duty rates
- `GET /api/vehicle/template` - Download bulk upload template
- `POST /api/vehicle/upload` - Bulk vehicle upload and calculation
- `GET /api/vehicle/batches` - List batch history
- `GET /api/vehicle/batches/{id}` - Get batch details
- `GET /api/vehicle/batches/{id}/export` - Export batch results
- `GET /api/vehicle/checklist` - Get clearance checklist

### Invoice & Export Features (Jan 31, 2026)
- [x] **Generate Invoice (Vehicle)** - Excel export with complete duty breakdown
- [x] **Generate Invoice (Alcohol)** - Excel export with product and duty details
- [x] **Invoice Disclaimer** - Includes "estimate only" disclaimer and generation timestamp

### Terms of Use (Jan 31, 2026)
- [x] **Dashboard Integration** - Terms of Use button at dashboard footer
- [x] **Estimates Disclaimer** - "informational purposes only"
- [x] **No Guarantee of Classification** - "sole responsibility of user/broker"
- [x] **Non-Affiliation** - "not affiliated with or endorsed by Bahamas Customs"
- [x] **Limitation of Liability** - "do so at their own risk"
- [x] **Official Resources** - Links to Bahamas Customs website, phone, email

### Environmental Levy UI Improvements (Jan 31, 2026)
- [x] **Quick-Apply Buttons** - Antique ($200) and Over 10 Years (20%) buttons
- [x] **Auto-Detection Warning** - Shows "11 years or older" when vehicle exceeds 10 years
- [x] **Antique Auto-Fill** - Suggests vintage year when antique selected
- [x] **MOF Approval Button** - For vehicles >10 years old, toggles approval status
- [x] **Body Style Dropdown** - Categorized vehicle body types (Sedan, SUV, Pickup, etc.)
- [x] **Updated Bulk Template** - Vehicle template includes body_style column

### HS Code Library UI Improvements (Jan 31, 2026)
- [x] **Flag Legend** - Icon legend in header explaining Restricted Item (shield) and Requires Permit (warning) icons

### Password Reset Feature (Jan 31, 2026)
- [x] **Forgot Password Page** - Enter email to receive reset link
- [x] **Reset Password Page** - Enter new password using token from email
- [x] **Login Page Link** - "Forgot password?" link on login page
- [x] **Secure Token** - 1-hour expiry, single-use reset tokens
- [x] **Email Notification** - Reset link sent to user email

### Weekly Account Report (Jan 31, 2026)
- [x] **Automated Scheduler** - Runs every 7 days
- [x] **Account Log Email** - Sends to gfp6ixhc@yourfeedback.anonaddy.me
- [x] **Report Contents** - User name, email, company, creation date
- [x] **Database Logging** - All logs stored in weekly_logs collection
- [x] **Admin Trigger** - Manual trigger endpoint for testing

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
1. Finalize NotationsPage UI (scaffold exists, needs full build-out)
2. Add HS Library search link from item edit dialog in ClassificationResultPage
3. Create downloadable PDF for Alcohol calculation formula guide
4. Add manual entry option (single item form) to calculators alongside bulk upload
5. Implement PDF invoice extraction with AI
6. Create admin dashboard for user management

## Completed This Session (Jan 31, 2026)
- [x] Verified body_style dropdown saves to DB and appears in history/invoice
- [x] Added MOF Approval Granted button for vehicles >10 years old
- [x] Added HS Code Library flag legend (Restricted/Requires Permit icons)
- [x] Updated vehicle bulk upload template with body_style column
- [x] Updated frontend template info with body_style documentation
- [x] Fixed Environmental Levy warning to say "11 years or older" (not dynamic age)
- [x] Added Forgot Password feature (email entry → reset link)
- [x] Added Reset Password page (new password entry with token)
- [x] Added "Forgot password?" link to Login page
- [x] Implemented weekly account creation log (auto-emails to admin)
- [x] Added Alcohol Calculation Guide PDF download (Download Guide button)
- [x] Added Country of Origin dropdown with 195 countries (Vehicle Calculator)
- [x] Added Vehicle Calculation Guide PDF download (Download Guide button)
- [x] Added Currency selector (USD/BSD) for CIF Value in Vehicle Calculator
- [x] Fixed country dropdown duplication issue
- [x] Finalized NotationsPage UI with stats cards (Total Notes, Entry Refs, Tariff Codes, General Notes)
- [x] Added "Search HS Library" link to Classification edit dialog
- [x] Added "User Updated" status with yellow highlighting for edited classification items
- [x] Auto-sets status to "user_updated" when saving changes from "needs_review"
- [x] Added "User Updated" count summary card to classification results

### Notations Page UI (Jan 31, 2026)
- [x] **Stats Cards** - Total Notes, Entry Refs, Tariff Codes, General Notes counts
- [x] **Search & Filter** - Search notations, filter by reference type
- [x] **Note Cards** - Color-coded by type with label, content preview, date
- [x] **CRUD Operations** - Create, edit, delete notations
- [x] **100-Word Limit** - Word counter in dialog with validation

### Classification Result Enhancements (Jan 31, 2026)
- [x] **User Updated Status** - New status option for edited items
- [x] **Yellow Highlighting** - Visual indicator for user-updated rows
- [x] **Search HS Library Link** - Opens HS Library in new tab from edit dialog
- [x] **Auto Status Update** - Changes "needs_review" to "user_updated" on save
- [x] **User Updated Summary Card** - Shows count of user-edited items
### Alcohol Calculator Enhancements (Jan 31, 2026)
- [x] **Download Guide PDF** - "Download Guide" button next to "View History"
- [x] **PDF Content** - Duty rates, excise calculations, LPA formula, VAT, license fees
- [x] **Example Calculation** - Step-by-step example with 12 bottles of rum
- [x] **Auto-download** - Generates and downloads PDF instantly on click

### Vehicle Calculator Enhancements (Jan 31, 2026)
- [x] **Country Dropdown** - Select dropdown with all 195 recognized countries
- [x] **Popular Countries** - Quick access to Japan, USA, Germany, South Korea, China, etc.
- [x] **A-Z Full List** - Scrollable list of all countries alphabetically
- [x] **Download Guide PDF** - "Download Guide" button generates comprehensive PDF
- [x] **PDF Content** - Duty rates by vehicle type/engine, environmental levy rules, fees, example calculation
- [x] **Currency Selector** - USD $ or BSD $ dropdown for CIF Value (1:1 pegged)