# Architecture

## Overview

Serverless, event-driven architecture on AWS. Three modules share the same auth layer and API Gateway but have independent Lambda functions and storage backends.

---

## Request Flow

```
Browser (React SPA on S3)
  │
  ├── /login  →  Cognito Hosted UI
  │               └── returns JWT (id token + access token)
  │
  └── /portal/...  →  API Gateway
                        └── Cognito Authorizer validates JWT
                              ├── Pipeline Lambda  →  S3
                              └── Hours Lambda     →  DynamoDB
```

---

## Auth Design

- **Cognito User Pool** with two groups: `managers`, `colleagues`
- **JWT claims** include `cognito:groups` — Lambda reads this to enforce role checks
- **API Gateway Cognito Authorizer** rejects unauthenticated requests with 401 before Lambda is invoked
- **Frontend** stores tokens in memory only (no localStorage); uses Cognito refresh token for silent re-auth

---

## Module 1 — Product Pipeline

```
POST /process  →  PipelineLambda
  1. Parse CSV (stdlib csv, no pandas)
  2. Apply column mapping
  3. Normalise: titles, prices, weights, images
  4. Validate required fields
  5. AI enhancement (optional, Claude API)
  6. Generate Shopify CSV rows
  7. Upload output to S3
  8. Return presigned download URL
```

Storage: S3 bucket (`input/`, `output/` prefixes)

---

## Module 2 — Auth & Portal

```
GET /  →  React Router
  ├── unauthenticated  →  /login
  └── authenticated
        ├── /portal/pipeline  →  Product Pipeline UI
        └── /portal/hours
              ├── colleague  →  submit + history
              └── manager   →  all entries + approve + export
```

No Lambda needed for auth itself — Cognito handles token issuance.

---

## Module 3 — Working Hours

```
POST   /hours                  →  HoursSubmitLambda (colleague)
GET    /hours/me               →  HoursListLambda   (colleague)
GET    /hours?period=...       →  HoursListLambda   (manager only)
PATCH  /hours/{userId}/{period}→  HoursReviewLambda (manager only)
GET    /hours/export           →  HoursExportLambda (manager only)
```

Storage: DynamoDB `TimeEntries` table
- Partition key: `userId`, Sort key: `period`
- GSI `period-index` for manager queries across all users by period

---

## Infrastructure as Code

All resources defined in `template.yaml` (AWS SAM):

| Resource | Type |
|---|---|
| `PipelineBucket` | `AWS::S3::Bucket` |
| `PipelineFunction` | `AWS::Serverless::Function` |
| `TimeEntriesTable` | `AWS::DynamoDB::Table` |
| `HoursFunctions` | `AWS::Serverless::Function` × 4 |
| `UserPool` | `AWS::Cognito::UserPool` |
| `UserPoolClient` | `AWS::Cognito::UserPoolClient` |
| `ApiGateway` | `AWS::Serverless::Api` (with Cognito Authorizer) |

---

## Principles

- **Code handles structure. AI enhances content. Validate everything.**
- Lambda functions are single-responsibility and independently deployable
- Role enforcement happens in Lambda (not just frontend routing)
- All data access goes through API Gateway — no direct S3/DynamoDB from browser
- Costs stay within free tier at small team scale (< 50 users, < 1000 req/day)
