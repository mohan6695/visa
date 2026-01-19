#!/usr/bin/env python3
"""
Supabase S3 Storage Uploader - Final version
Using the full key as access key for S3 authentication
"""

import os
import hmac
import hashlib
import datetime
import requests

def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

def upload_file_to_supabase_s3(file_path, host, access_key, secret_key, bucket, object_name):
    """
    Upload file to Supabase S3 using AWS Signature V4
    """
    region = 'us-east-1'
    service = 's3'
    
    # File details
    with open(file_path, 'rb') as f:
        file_content = f.read()
    file_size = len(file_content)
    
    # HTTP request details
    method = 'PUT'
    path = f'/{bucket}/{object_name}'
    url = f'https://{host}{path}'
    
    # Timestamp
    now = datetime.datetime.now(datetime.UTC)
    amz_date = now.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = now.strftime('%Y%m%d')
    
    # Create canonical request
    payload_hash = hashlib.sha256(file_content).hexdigest()
    
    headers = {
        'host': host,
        'x-amz-content-sha256': payload_hash,
        'x-amz-date': amz_date
    }
    
    signed_headers = ';'.join(sorted(headers.keys()))
    
    canonical_headers = '\n'.join([f"{k.lower()}:{v}" for k, v in sorted(headers.items())]) + '\n'
    
    canonical_request = '\n'.join([
        method,
        path,
        '',
        canonical_headers,
        signed_headers,
        payload_hash
    ])
    
    # Create string to sign
    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    
    string_to_sign = '\n'.join([
        algorithm,
        amz_date,
        credential_scope,
        hashlib.sha256(canonical_request.encode()).hexdigest()
    ])
    
    # Create signing key
    k_date = sign(('AWS4' + secret_key).encode(), date_stamp)
    k_region = sign(k_date, region)
    k_service = sign(k_region, service)
    k_signing = sign(k_service, 'aws4_request')
    
    # Calculate signature
    signature = hmac.new(k_signing, string_to_sign.encode(), hashlib.sha256).hexdigest()
    
    # Create authorization header
    authorization = (
        f"{algorithm} "
        f"Credential={access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, "
        f"Signature={signature}"
    )
    
    # Prepare request headers
    request_headers = {
        'Authorization': authorization,
        'x-amz-content-sha256': payload_hash,
        'x-amz-date': amz_date,
        'Content-Type': 'application/octet-stream',
        'Content-Length': str(file_size)
    }
    
    print(f"Uploading {file_path} ({file_size} bytes)...")
    print(f"URL: {url}")
    print(f"Access Key: {access_key}")
    
    # Send request
    response = requests.put(url, data=file_content, headers=request_headers)
    
    result = {
        'status_code': response.status_code,
        'response': response.text[:500] if response.text else 'No response body',
        'success': response.status_code in [200, 204],
        'url': f"https://{host}/object/public/{bucket}/{object_name}"
    }
    
    return result


def main():
    # Configuration
    host = 'cycnichledvqbxevrwnt.storage.supabase.co'
    
    # The key format: visakey:57cdc4296f52ea5078cbfdb138395166
    # Try both formats for access key
    key_input = 'visakey:57cdc4296f52ea5078cbfdb138395166'
    secret_key = '57cdc4296f52ea5078cbfdb138395166'
    
    # Try different access key formats
    access_keys_to_try = [
        ('visakey', 'visakey'),  # access_key, display name
        (key_input, 'full_key'),  # Full key as access key
    ]
    
    bucket = 'posts'
    file_path = '/Users/mohanakrishnanarsupalli/Downloads/new_posts.json'
    object_name = f'new_posts_{datetime.datetime.now(datetime.UTC).strftime("%Y%m%d_%H%M%S")}.json'
    
    print("=" * 50)
    print("Supabase S3 Upload - Trying different access keys")
    print("=" * 50)
    print(f"File: {file_path}")
    print(f"Bucket: {bucket}")
    print()
    
    for access_key, key_name in access_keys_to_try:
        print(f"\n--- Trying with access key: {key_name} ({access_key[:15]}...) ---")
        result = upload_file_to_supabase_s3(file_path, host, access_key, secret_key, bucket, object_name)
        print(f"Status: {result['status_code']}")
        print(f"Success: {result['success']}")
        
        if result['success']:
            print(f"Public URL: {result['url']}")
            break
        else:
            print(f"Response: {result['response'][:200]}")
    
    return result


if __name__ == '__main__':
    main()
