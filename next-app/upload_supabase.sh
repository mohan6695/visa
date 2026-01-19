#!/bin/bash
# Supabase Storage Upload Script
# Uploads new_posts.json to Supabase S3 storage

ENDPOINT="https://cycnichledvqbxevrwnt.storage.supabase.co/storage/v1/s3"
KEY_ID="visakey:57cdc4296f52ea5078cbfdb138395166"
BUCKET="posts"
FILE_PATH="/Users/mohanakrishnanarsupalli/Downloads/new_posts.json"
OBJECT_NAME="new_posts_$(date +%Y%m%d_%H%M%S).json"

echo "Uploading $FILE_PATH to Supabase S3..."
echo "Endpoint: $ENDPOINT"
echo "Bucket: $BUCKET"
echo "Object: $OBJECT_NAME"
echo ""

# Try to upload using Supabase Storage REST API
# First, get a signed URL for upload
RESPONSE=$(curl -s -X POST \
  "$ENDPOINT/object/sign/$BUCKET/$OBJECT_NAME" \
  -H "Authorization: Bearer $KEY_ID" \
  -H "Content-Type: application/json" \
  -d '{"expires": 3600}')

echo "Sign response: $RESPONSE"

# Extract signed URL
SIGNED_URL=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('signedUrl', ''))")

if [ -n "$SIGNED_URL" ]; then
  echo "Uploading to signed URL..."
  curl -s -X PUT \
    "$SIGNED_URL" \
    -H "Content-Type: application/json" \
    --data-binary @"$FILE_PATH"
  
  if [ $? -eq 0 ]; then
    echo ""
    echo "Upload successful!"
    echo "Public URL: https://cycnichledvqbxevrwnt.storage.supabase.co/object/public/$BUCKET/$OBJECT_NAME"
  else
    echo "Upload failed"
  fi
else
  echo "Failed to get signed URL"
fi
