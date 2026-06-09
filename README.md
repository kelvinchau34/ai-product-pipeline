# AI Product Pipeline — Internal Operations Portal

[![CI](https://github.com/kelvinchau34/ai-product-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/kelvinchau34/ai-product-pipeline/actions/workflows/ci.yml)

A serverless internal portal built on AWS that combines AI-powered product data processing with staff time-tracking and role-based access. Designed as a showcase of production-grade architecture using AWS free-tier services.

---

## Modules

### 1. Product Pipeline
Upload supplier CSV exports, auto-normalise product fields, run optional AI enhancement, review per-product issues, and export a Shopify-ready CSV. See [docs/prd.md](docs/prd.md) for full feature list.

### 2. Authentication & Portal (planned)
Centralised login via Amazon Cognito with two roles — Colleague and Manager. JWT-based auth gates every API call via API Gateway Cognito Authorizer.

### 3. Working Hours Logging (planned)
Fortnightly hour submission for colleagues. Managers can review, approve/reject, and export CSV. Data stored in DynamoDB.

---

## Architecture

```
                        ┌─────────────────────────┐
                        │   React SPA (S3 + CDN)  │
                        └────────────┬────────────┘
                                     │ HTTPS
                        ┌────────────▼────────────┐
                        │   Amazon Cognito        │
                        │   (login / JWT / roles) │
                        └────────────┬────────────┘
                                     │ JWT Bearer token
                        ┌────────────▼────────────┐
                        │   API Gateway           │
                        │   (Cognito Authorizer)  │
                        └──┬─────────────────┬───┘
                           │                 │
              ┌────────────▼──┐        ┌─────▼────────────┐
              │ Pipeline      │        │ Hours Lambda      │
              │ Lambda        │        │ (CRUD + export)   │
              └──────┬────────┘        └──────┬────────────┘
                     │                        │
              ┌──────▼────────┐        ┌──────▼────────────┐
              │ S3            │        │ DynamoDB          │
              │ (CSV in/out)  │        │ (TimeEntries)     │
              └───────────────┘        └───────────────────┘
```

---

## AWS Services & Free Tier

All services stay within free tier for a small team (< 50 users, < 1000 API calls/day).

| Service | Use | Free Tier |
|---|---|---|
| **S3** | Frontend hosting, CSV input/output | 5 GB storage, 20K GET/2K PUT per month |
| **Lambda** | Pipeline processing, Hours API | 1M requests/month, 400K GB-s compute — always free |
| **API Gateway** | REST API routing + auth | 1M calls/month (first 12 months) |
| **Cognito** | Login, JWT, user groups | 50,000 MAUs — always free |
| **DynamoDB** | Time entry storage | 25 GB storage, 25 RCU/WCU — always free |
| **CloudWatch** | Logs and monitoring | 5 GB logs, 10 metrics — always free |
| **SAM / CloudFormation** | Infrastructure as code | Free |

**Estimated monthly cost at low usage: $0–1.**

Services deliberately avoided (cost or complexity):
- ~~RDS~~ → DynamoDB (no idle instance cost)
- ~~EC2~~ → Lambda (no idle server cost)
- ~~Amplify hosting~~ → S3 static (already set up)
- ~~SES for email~~ → stretch goal only

---

## Implementation Plan

### Phase 1 — Auth (Cognito + React Router)
1. Create Cognito User Pool with two groups: `managers`, `colleagues`
2. Add `CognitoUserPoolId` and `CognitoClientId` to SAM template outputs
3. Install `amazon-cognito-identity-js` (or AWS Amplify Auth only) in the frontend
4. Add React Router with protected routes — redirect to `/login` if no valid token
5. Add API Gateway Cognito Authorizer to existing `ProcessFunction` route
6. Test: unauthenticated request returns 401

### Phase 2 — Portal Shell
1. Create `/login` page (Cognito Hosted UI redirect or embedded form)
2. Create `/portal` layout with top nav: Pipeline | Hours
3. Hide Hours nav item for colleagues without manager group claim
4. Store Cognito tokens in memory; use refresh token to silently re-auth

### Phase 3 — Working Hours Backend
1. Add `TimeEntries` DynamoDB table to `template.yaml`:
   - Partition key: `userId` (Cognito sub)
   - Sort key: `period` (e.g. `2025-W01`)
   - GSI: `period-index` (PK: period) for manager queries
2. Add Lambda functions:
   - `POST /hours` — colleague submits entry (validates period not already submitted)
   - `GET /hours/me` — colleague fetches own history
   - `GET /hours` — manager fetches all entries, filterable by period
   - `PATCH /hours/{userId}/{period}` — manager approves/rejects
   - `GET /hours/export?period=...` — manager downloads CSV
3. Lambda reads Cognito group from JWT claims to enforce role checks

### Phase 4 — Working Hours Frontend
1. Colleague view: fortnight date grid (Mon–Fri × 2 weeks), total counter, submit button
2. Submission history: table of past periods with status chip
3. Manager view: submissions table with filter controls, approve/reject buttons, export button
4. Shared: `usePeriod()` hook to calculate active fortnight from anchor date

---

## DynamoDB Table Design

```
Table: TimeEntries
PK:   userId       (Cognito sub — string)
SK:   period       (e.g. "2025-P01" — string)

Attributes:
  userName        string    display name from Cognito
  periodLabel     string    "26 May – 8 Jun 2025"
  dailyHours      map       { "Mon1": 8, "Tue1": 8, ... "Fri2": 7.5 }
  totalHours      number    auto-summed on submit
  notes           string    optional colleague notes
  status          string    submitted | approved | rejected
  submittedAt     string    ISO 8601
  reviewedBy      string    manager userId (optional)
  reviewedAt      string    ISO 8601 (optional)
  reviewNote      string    manager comment on reject (optional)

GSI: period-index
  PK:  period
  SK:  submittedAt
```

---

## Project Structure

```
.
├── src/                        # Python Lambda handlers
│   ├── lambda_handler.py       # Pipeline Lambda entry point
│   ├── pipeline.py             # Orchestrates processing stages
│   ├── ingest.py               # CSV/JSON parsing (stdlib, no pandas)
│   ├── normalise.py            # Field normalisation
│   ├── validate.py             # Validation rules
│   ├── ai_enhancer.py          # AI enhancement stub
│   ├── export.py               # Shopify CSV generation
│   └── logger.py               # Structured logging
├── src/hours/                  # (planned) Hours Lambda handlers
│   ├── submit.py
│   ├── list.py
│   └── export.py
├── tests/                      # pytest unit + integration tests
├── frontend/src/               # React 18 + Vite 5 SPA
│   ├── App.jsx                 # Main app and state
│   ├── components/             # UI components
│   └── utils/                  # Pure business logic
├── docs/
│   ├── prd.md                  # Full product requirements
│   └── architecture.md         # Architecture notes
├── template.yaml               # AWS SAM infrastructure
├── samconfig.toml              # SAM deploy config (staging + prod)
└── .github/workflows/
    ├── ci.yml                  # Lint + test on PR
    └── deploy.yml              # Staging → prod pipeline
```

---

## Local Development

### Backend

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q
python -m src.lambda_handler     # test with local event
```

### Frontend

```bash
cd frontend
npm install
# set VITE_API_URL in .env
npm run dev                      # http://localhost:5174
npm test -- --run
```

---

## CI/CD Workflow

```
local change
  └── git push origin feature/...
        └── CI: ruff + pytest + vitest + build
              └── PR merge → main
                    └── deploy.yml:
                          ├── staging auto-deploy (SAM)
                          ├── frontend sync → S3
                          └── production deploy (manual approval gate)
```

### Required GitHub setup

1. **Environments**: `staging` (auto) and `production` (required reviewer: you)
2. **Secret**: `AWS_GITHUB_ACTIONS_ROLE_ARN` — IAM role for OIDC deploy
3. **Secret**: `VITE_API_URL` — API Gateway endpoint for frontend build

---

## Deploy with SAM

```bash
sam build
sam deploy --guided --config-env staging   # first time
sam deploy --config-env staging             # subsequent
```

Outputs: `ApiUrl`, `BucketName`, `FrontendBucketName`

---

## Skills Demonstrated

| Skill | Where |
|---|---|
| Serverless architecture | Lambda + API Gateway + SAM |
| Authentication & authorisation | Cognito + JWT + role-based API guards |
| NoSQL data modelling | DynamoDB table + GSI design |
| AI integration | Claude API for content enhancement |
| CI/CD pipeline | GitHub Actions with staged environments |
| Infrastructure as code | AWS SAM / CloudFormation |
| Frontend state management | React 18, hooks, context |
| Test coverage | pytest (backend) + Vitest (frontend) |
| Code quality | ruff linting, type hints |
