#!/usr/bin/env bash
set -euo pipefail

# Cost-conscious frontend deployment to S3 + CloudFront.
# - PriceClass_100 limits CloudFront edge locations to reduce cost.
# - Uses your existing backend ApiUrl output from CloudFormation.
#
# Usage:
#   chmod +x scripts/deploy_frontend_s3_cloudfront.sh
#   AWS_PROFILE=kelvinchau AWS_REGION=ap-southeast-2 ./scripts/deploy_frontend_s3_cloudfront.sh
#
# Optional env vars:
#   STACK_NAME=ai-product-pipeline-dev
#   FRONTEND_BUCKET_NAME=your-unique-bucket-name
#   WAIT_FOR_DEPLOY=true

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
STACK_NAME="${STACK_NAME:-ai-product-pipeline-dev}"
AWS_REGION="${AWS_REGION:-$(aws configure get region || true)}"
WAIT_FOR_DEPLOY="${WAIT_FOR_DEPLOY:-false}"

if [[ -z "$AWS_REGION" ]]; then
  echo "ERROR: AWS_REGION is not set and no default region is configured."
  exit 1
fi

if ! aws sts get-caller-identity >/dev/null 2>&1; then
  echo "ERROR: AWS credentials are not valid. Run: aws sso login --profile <your-profile>"
  exit 1
fi

echo "==> Using region: $AWS_REGION"
echo "==> Resolving ApiUrl from stack: $STACK_NAME"
API_URL="$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$AWS_REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue | [0]" \
  --output text)"

if [[ -z "$API_URL" || "$API_URL" == "None" ]]; then
  echo "ERROR: Could not find ApiUrl output in stack $STACK_NAME"
  exit 1
fi

echo "==> Building frontend with VITE_API_URL=$API_URL"
echo "VITE_API_URL=$API_URL" > "$FRONTEND_DIR/.env.production"
(
  cd "$FRONTEND_DIR"
  npm install
  npm run build
)

if [[ -n "${FRONTEND_BUCKET_NAME:-}" ]]; then
  BUCKET_NAME="$FRONTEND_BUCKET_NAME"
else
  RAND_SUFFIX="$(date +%Y%m%d)-$RANDOM"
  BUCKET_NAME="ai-product-pipeline-frontend-$RAND_SUFFIX"
fi

echo "==> Creating S3 bucket: $BUCKET_NAME"
if [[ "$AWS_REGION" == "us-east-1" ]]; then
  aws s3api create-bucket --bucket "$BUCKET_NAME" --region "$AWS_REGION"
else
  aws s3api create-bucket \
    --bucket "$BUCKET_NAME" \
    --region "$AWS_REGION" \
    --create-bucket-configuration "LocationConstraint=$AWS_REGION"
fi

# Allow public reads for static hosting.
aws s3api put-public-access-block \
  --bucket "$BUCKET_NAME" \
  --public-access-block-configuration \
  "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

aws s3api put-bucket-website \
  --bucket "$BUCKET_NAME" \
  --website-configuration '{"IndexDocument":{"Suffix":"index.html"},"ErrorDocument":{"Key":"index.html"}}'

cat > /tmp/frontend-bucket-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": ["s3:GetObject"],
      "Resource": ["arn:aws:s3:::$BUCKET_NAME/*"]
    }
  ]
}
EOF
aws s3api put-bucket-policy --bucket "$BUCKET_NAME" --policy file:///tmp/frontend-bucket-policy.json

echo "==> Uploading frontend build to S3"
aws s3 sync "$FRONTEND_DIR/dist" "s3://$BUCKET_NAME" --delete

if [[ "$AWS_REGION" == "us-east-1" ]]; then
  WEBSITE_DOMAIN="$BUCKET_NAME.s3-website-us-east-1.amazonaws.com"
else
  WEBSITE_DOMAIN="$BUCKET_NAME.s3-website-$AWS_REGION.amazonaws.com"
fi

CALLER_REF="$(date +%s)-$RANDOM"
cat > /tmp/cloudfront-config.json <<EOF
{
  "CallerReference": "$CALLER_REF",
  "Comment": "AI Product Pipeline frontend",
  "Enabled": true,
  "PriceClass": "PriceClass_100",
  "DefaultRootObject": "index.html",
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "s3-website-origin",
        "DomainName": "$WEBSITE_DOMAIN",
        "CustomOriginConfig": {
          "HTTPPort": 80,
          "HTTPSPort": 443,
          "OriginProtocolPolicy": "http-only",
          "OriginSslProtocols": {
            "Quantity": 1,
            "Items": ["TLSv1.2"]
          }
        }
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "s3-website-origin",
    "ViewerProtocolPolicy": "redirect-to-https",
    "TrustedSigners": {
      "Enabled": false,
      "Quantity": 0
    },
    "AllowedMethods": {
      "Quantity": 2,
      "Items": ["GET", "HEAD"],
      "CachedMethods": {
        "Quantity": 2,
        "Items": ["GET", "HEAD"]
      }
    },
    "Compress": true,
    "ForwardedValues": {
      "QueryString": false,
      "Cookies": { "Forward": "none" }
    },
    "MinTTL": 0,
    "DefaultTTL": 86400,
    "MaxTTL": 31536000
  },
  "CustomErrorResponses": {
    "Quantity": 2,
    "Items": [
      {
        "ErrorCode": 403,
        "ResponsePagePath": "/index.html",
        "ResponseCode": "200",
        "ErrorCachingMinTTL": 0
      },
      {
        "ErrorCode": 404,
        "ResponsePagePath": "/index.html",
        "ResponseCode": "200",
        "ErrorCachingMinTTL": 0
      }
    ]
  },
  "ViewerCertificate": {
    "CloudFrontDefaultCertificate": true
  }
}
EOF

echo "==> Creating CloudFront distribution (PriceClass_100)"
DIST_CREATE_JSON="$(aws cloudfront create-distribution --distribution-config file:///tmp/cloudfront-config.json)"
DIST_ID="$(echo "$DIST_CREATE_JSON" | python3 -c 'import sys, json; print(json.load(sys.stdin)["Distribution"]["Id"])')"
DIST_DOMAIN="$(echo "$DIST_CREATE_JSON" | python3 -c 'import sys, json; print(json.load(sys.stdin)["Distribution"]["DomainName"])')"

if [[ "$WAIT_FOR_DEPLOY" == "true" ]]; then
  echo "==> Waiting for CloudFront deployment to complete (can take several minutes)"
  aws cloudfront wait distribution-deployed --id "$DIST_ID"
fi

echo
echo "Deployment complete"
echo "Stack name:        $STACK_NAME"
echo "API URL:           $API_URL"
echo "S3 bucket:         $BUCKET_NAME"
echo "S3 website:        http://$WEBSITE_DOMAIN"
echo "CloudFront ID:     $DIST_ID"
echo "CloudFront URL:    https://$DIST_DOMAIN"
echo
echo "Budget note: CloudFront and S3 can incur charges beyond free tier."
echo "For strict cost control, remove unused distributions and bucket objects after demos."
