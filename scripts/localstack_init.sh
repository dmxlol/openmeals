#!/bin/bash
set -e

awslocal s3 mb s3://openmeals-local --region eu-central-1
awslocal s3api put-bucket-cors --bucket openmeals-local --cors-configuration '{
  "CORSRules": [{
    "AllowedOrigins": ["*"],
    "AllowedMethods": ["GET", "PUT"],
    "AllowedHeaders": ["*"],
    "MaxAgeSeconds": 3000
  }]
}'

echo "LocalStack S3 bucket 'openmeals-local' ready."
