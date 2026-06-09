# Product Requirements Document

## Vision

An internal operations portal for small teams that combines AI-powered product data processing with staff time-tracking — all behind a secure, role-based login. Built serverless on AWS to showcase production-grade architecture at minimal running cost.

---

## User Roles

| Role | Who | Access |
|---|---|---|
| **Colleague** | Operations staff | Product pipeline, submit own hours |
| **Manager** | Team lead / admin | All colleague access + view all hours, approve, export |

---

## Module 1 — Product Pipeline (existing)

**Goal:** Transform raw supplier CSV exports into Shopify-ready product listings with AI enhancement and manual review.

### Features

- Upload vendor CSV (47-column supplier format)
- Auto-detect and map columns to Shopify schema
- Deterministic normalisation: titles, prices, weights, dimensions, images
- AI enhancement step (descriptions, SEO, tags) via Claude API — optional
- Validation summary: ready / needs review / missing fields
- Per-product review page: full-width, rendered HTML preview, inline field editing
- Bulk actions: set vendor, product type, tags, lead time, generate handles
- Export Shopify-ready CSV (all / selected / ready only)

### User Flow (Colleague / Manager)

1. Log in to portal
2. Navigate to Product Pipeline
3. Upload supplier CSV
4. Review auto-mapped columns (auto-confirmed, editable if needed)
5. Click Process — pipeline runs in Lambda, ~10–30 seconds
6. Review validation summary and per-product issues
7. Edit fields inline, apply bulk actions
8. Export Shopify CSV or download from S3 signed URL

---

## Module 2 — Authentication & Main Portal (new)

**Goal:** Centralised login and navigation hub. All modules live behind auth.

### Features

- Login / logout via Cognito Hosted UI or embedded form
- JWT token attached to every API request
- Role-based routing: colleagues see their modules, managers see everything
- Simple nav: Portal home → Product Pipeline | Hours Logging
- Session persists across page refresh (Cognito token refresh)
- Password reset and email verification via Cognito

### User Flow

1. User visits portal URL
2. Redirected to login if unauthenticated
3. On success: JWT stored in memory / sessionStorage
4. Navbar shows available modules based on group membership
5. Logout clears token and redirects to login

---

## Module 3 — Working Hours Logging (new)

**Goal:** Replace manual spreadsheet tracking with a structured fortnightly submission and approval workflow.

### Features

#### Colleague view
- Auto-calculated current fortnight period shown on load
- Enter daily hours (Mon–Fri) for the fortnight, plus a notes field
- Total auto-calculated as they type
- Submit button locks the entry (can't re-submit same period)
- History tab: past 6 fortnights with status chips (Submitted / Approved / Rejected)

#### Manager view
- Dashboard: all submissions for the current fortnight
- Filter by period, colleague name, or status
- Approve or reject individual entries with an optional comment
- Export current period or any past period as CSV
- Bulk approve selected entries

### Fortnightly Periods

Periods are calculated from a fixed anchor date (e.g. 1 Jan 2024 = period 1). Each period has a human-readable label: `"26 May – 8 Jun 2025"`. The app auto-selects the active period on load.

### Entry States

```
[Not submitted] → [Submitted] → [Approved]
                              → [Rejected] → colleague can resubmit
```

---

## Non-Goals (MVP)

- Leave / absence tracking
- Payroll integration
- Multi-tenancy (single company instance)
- Mobile app (responsive web is sufficient)
- Real-time notifications (email on approve/reject is a stretch goal)

---

## Success Criteria

| Criteria | Target |
|---|---|
| Login and token validation working | Auth blocks unauthenticated requests at API Gateway |
| Colleague can submit hours | Entry stored in DynamoDB, status = Submitted |
| Manager can view and export | CSV export matches submitted data |
| Product pipeline unchanged | All existing pipeline tests pass |
| Deployed on AWS free tier | Monthly cost < $1 at low usage |
