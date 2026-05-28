# AI Product Pipeline

[![CI](https://github.com/kelvinchau34/ai-product-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/kelvinchau34/ai-product-pipeline/actions/workflows/ci.yml)

Lightweight pipeline to transform supplier product data into Shopify-ready CSV using deterministic processing with optional AI enhancement.

This repository is set up for:

- Python backend suitable for AWS Lambda
- Static frontend for upload and status checks
- GitHub Actions CI/CD with staging and production environments

## Project Structure

- src/: Backend code (Lambda handler and processing modules)
- tests/: Unit tests
- frontend/: Static frontend assets
- docs/: Product and architecture docs
- .github/workflows/: CI workflow definitions
- input_examples/: Sample input files
- output_examples/: Sample output files
- ref/: Existing reference scripts and data

## Quick Start

1. Create and activate a virtual environment.
2. Install dependencies:

   pip install -r requirements.txt

3. Run tests:

   pytest -q

4. Run local Lambda event test:

   python -m src.lambda_handler

## Environment Variables

Copy .env.example to .env and fill values as needed.

## AWS MVP Notes

- API Gateway triggers Lambda.
- Lambda reads supplier input from S3 and writes Shopify CSV output to S3.
- CloudWatch captures job logs by job_id.
- Secrets are environment variables only.

## Frontend

The static UI lives in [frontend/](frontend/).

Local run:

1. `cd frontend`
2. `npm install`
3. Set `VITE_API_URL` in `.env` or export it in your shell.
4. `npm run dev`

Production build:

1. `cd frontend`
2. `npm run build`
3. Serve the generated `dist/` directory from any static host.

## Deploy with AWS SAM (MVP)

1. Install AWS SAM CLI and configure AWS credentials.
2. Build and deploy:

   sam build
   sam deploy --guided

3. Save the output values from deployment:
   - ApiUrl
   - BucketName

4. Upload an input file to S3 (default input prefix: input/):

   aws s3 cp input_examples/sample-input-15.csv s3://<BucketName>/input/sample-input-15.csv

5. Call API Gateway endpoint:

   curl -X POST "<ApiUrl>" \\
   -H "Content-Type: application/json" \\
   -d '{
   "input_key": "input/sample-input-15.csv",
   "output_key": "output/shopify_import.csv",
   "export_csv": true,
   "upload_shopify": false
   }'

6. Download generated CSV from S3:

   aws s3 cp s3://<BucketName>/output/shopify_import.csv output_examples/shopify_import_from_aws.csv

### Event Payload (MVP)

POST /process accepts either direct file path or S3 key style payload:

- bucket (optional if PIPELINE_BUCKET is configured)
- input_key (e.g. input/sample-input-15.csv)
- output_key (e.g. output/shopify_import.csv)
- export_csv (default: true)
- upload_shopify (default from env var)
- ai_provider (optional)

See sample events:

- events/process-api-event.json
- events/process-direct-event.json

## Update Workflow

Day-to-day process for shipping a code change:

```
1. Make changes locally
   └── edit src/, frontend/src/, tests/, etc.

2. Test locally before pushing
   ├── pytest -q                          (backend)
   └── cd frontend && npm test -- --run   (frontend)

3. Push to a feature branch
   └── git push origin feature/my-change

4. Open a Pull Request → main
   └── CI runs automatically:
       ├── backend: ruff lint + pytest
       └── frontend: vitest + build
       (PR is blocked until both pass)

5. Merge PR → main
   └── deploy.yml triggers automatically:
       ├── re-runs CI as a gate
       ├── deploys to staging (auto)
       └── deploys to production (requires manual approval in GitHub)
```

### One-time GitHub setup (required before first deploy)

1. **Create two GitHub Environments** in repo Settings → Environments:
   - `staging` — no protection rules (auto-deploys)
   - `production` — add yourself as a required reviewer

2. **Add secret** in repo Settings → Secrets → Actions:
   - `AWS_GITHUB_ACTIONS_ROLE_ARN` — the IAM role ARN GitHub assumes to deploy

3. **Bootstrap SAM** (run once locally, then commit `samconfig.toml`):
   ```bash
   sam build
   sam deploy --guided --config-env staging
   ```

## Incremental Build Plan

1. Deterministic normalize and validate pipeline
2. CSV generation aligned with Shopify schema
3. Optional AI enhancement step with strict validation
4. API integration and frontend upload flow
5. Deployment and monitoring hardening
