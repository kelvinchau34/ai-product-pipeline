# Architecture

AWS serverless MVP flow:

Static Frontend -> API Gateway -> Lambda -> S3 Output

Core backend steps:

1. Parse input
2. Normalize fields
3. Validate required values
4. Optional AI enhancement
5. Re-validate output
6. Generate Shopify CSV
7. Save output to S3

Services:

- Frontend: S3 + CloudFront
- API: API Gateway
- Compute: AWS Lambda
- Storage: S3 input/output buckets
- Monitoring: CloudWatch logs

Principle:

Code handles structure. AI enhances content. Validate everything.
