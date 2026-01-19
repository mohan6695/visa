#!/usr/bin/env python3
"""
Direct S3 upload using provided credentials
"""

import hmac
import hashlib
import datetime
import requests

def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

def upload_s3(file_path, host, access_key, secret_key, bucket, object_name):
    """Upload file using AWS Signature V4"""
    region = 'us-east-1'
    service = 's3'
    
    with open(file_path, 'rb') as f:
        file_content = f.read()
    file_size = len(file_content)
    
    method = 'PUT'
    path = f'/{bucket}/{object_name}'
    url = f'https://{host}{path}'
    
    now = datetime.datetime.now(datetime.UTC)
    amz_date = now.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = now.strftime('%Y%m%d')
    
    payload_hash = hashlib.sha256(file_content).hexdigest()
    
    headers = {
        'host': host,
        'x-amz-content-sha256': payload_hash,
        'x-amz-date': amz_date,
        'Content-Type': 'application/octet-stream',
        'Content-Length': str(file_size)
    }
    
    signed_headers = ';'.join(sorted(headers.keys()))
    canonical_headers = '\n'.join([f"{k.lower()}:{v}" for k, v in sorted(headers.items())]) + '\n'
    
    canonical_request = '\n'.join([
        method, path, '', canonical_headers, signed_headers, payload_hash
    ])
    
    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    
    string_to_sign = '\n'.join([
        algorithm, amz_date, credential_scope,
        hashlib.sha256(canonical_request.encode()).hexdigest()
    ])
    
    k_date = sign(('AWS4' + secret_key).encode(), date_stamp)
    k_region = sign(k_date, region)
    k_service = sign(k_region, service)
    k_signing = sign(k_service, 'aws4_request')
    
    signature = hmac.new(k_signing, string_to_sign.encode(), hashlib.sha256).hexdigest()
    
    authorization = (
        f"{algorithm} "
        f"Credential={access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, "
        f"Signature={signature}"
    )
    
    headers['Authorization'] = authorization
    
    print(f"Uploading {file_path} ({file_size} bytes) to {url}")
    response = requests.put(url, data=file_content, headers=headers)
    
    return response

# Configuration
host = 'cycnichledvqbxevrwnt.storage.supabase.co'
access_key = 'visakey'
secret_key = '57cdc4296f52ea5078cbfdb138395166'
bucket = 'posts'
file_path = '/Users/mohanakrishnanarsupalli/Downloads/new_posts.json'
object_name = 'new_posts.json'

print("=" * 50)
print("Direct S3 Upload")
print("=" * 50)

resp = upload_s3(file_path, host, access_key, secret_key, bucket, object_name)

print(f"\nStatus: {resp.status_code}")
print(f"Response: {resp.text[:300] if resp.text else 'No response body'}")

if resp.status_code in [200, 204]:
    print("\n✓ Upload successful!")
    print(f"URL: https://{host}/object/public/{bucket}/{object_name}")
else:
    print("\n✗ Upload failed")
