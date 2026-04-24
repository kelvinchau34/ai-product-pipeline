# AI Product Pipeline

Lightweight pipeline to transform supplier product data into Shopify-ready CSV using deterministic processing with optional AI enhancement.

This repository is set up for:

- Python backend suitable for AWS Lambda
- Static frontend for upload and status checks
- GitHub Actions CI

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

## Incremental Build Plan

1. Deterministic normalize and validate pipeline
2. CSV generation aligned with Shopify schema
3. Optional AI enhancement step with strict validation
4. API integration and frontend upload flow
5. Deployment and monitoring hardening
