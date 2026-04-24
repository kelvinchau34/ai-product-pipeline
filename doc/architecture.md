# architecture.md — AWS Serverless Architecture

## 1. Overview

This project uses a lightweight AWS serverless architecture to run an AI-guided product data automation workflow.

The system allows a user to upload supplier product data, process and validate it, optionally enhance product content using AI, and export a Shopify-ready CSV.

Frontend → API → Lambda Pipeline → S3 Output → Download Result

---

## 2. High-Level Architecture

User
↓
Static Web App (S3 + CloudFront)
↓
API Gateway
↓
Lambda
↓
S3 (Input/Output)
↓
AI Enhancement API
↓
CloudWatch Logs

---

## 3. AWS Services Used

### Frontend
- S3 (static hosting)
- CloudFront (CDN + HTTPS)

### Backend
- API Gateway (REST endpoints)
- Lambda (pipeline execution)

### Storage
- S3 (input/output files)

### AI
- Bedrock / OpenAI API (content enhancement only)

### Monitoring
- CloudWatch (logs & debugging)

---

## 4. User Flow

1. Upload product data
2. API request sent
3. Lambda processes data
4. Validate + AI enhance
5. Generate CSV
6. Store in S3
7. Download result

---

## 5. Backend Flow

POST /process
→ parse input
→ normalize
→ validate
→ AI enhance
→ validate AI output
→ generate CSV
→ save to S3
→ return result

---

## 6. Storage

Input:
s3://product-pipeline-input/{job_id}/input.csv

Output:
s3://product-pipeline-output/{job_id}/shopify_import.csv

---

## 7. Logging

CloudWatch logs:
- job_id
- step
- status
- warnings
- errors
- latency

---

## 8. Cost-Conscious Design

- S3 instead of servers
- Lambda instead of EC2
- minimal API usage
- no DB for MVP
- optional AI calls

---

## 9. API

POST /process  
GET /result/{job_id}  
POST /ai-enhance  

---

## 10. Security

- env variables for secrets
- IAM least privilege
- validate file input
- restrict size
- no secrets in frontend

---

## 11. Future Improvements

- DynamoDB (job tracking)
- SQS (async jobs)
- Step Functions (orchestration)
- Cognito (auth)
- dashboard (metrics)

---

## 12. Principle

Code handles structure  
AI enhances content  
Validate everything
