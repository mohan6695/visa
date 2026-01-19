#!/usr/bin/env python3
"""
List S3 buckets using AWS Signature V4
"""

import hmac
import hashlib
import datetime
import requests

def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

def list_buckets(host, access_key, secret_key):
    """
    List S3 buckets using AWS Signature V4
    """
    region = 'us-east-1'
    service = 's3'
    
    # HTTP request details
    method = 'GET'
    path = '/'
    url = f'https://{host}/'
    
    # Timestamp
    now = datetime.datetime.now(datetime.UTC)
    amz_date = now.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = now.strftime('%Y%m%d')
    
    # Empty payload for list buckets
    payload_hash = hashlib.sha256(b'').hexdigest()
    
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
        'x-amz-date': amz_date
    }
    
    print(f"Listing buckets at: {url}")
    print(f"Access Key: {access_key}")
    
    # Send request
    response = requests.get(url, headers=request_headers)
    
    result = {
        'status_code': response.status_code,
        'response': response.text,
        'success': response.status_code == 200
    }
    
    return result


def main():
    # Configuration
    host = 'cycnichledvqbxevrwnt.storage.supabase.co'
    
    # The key format: visakey:57cdc4296f52ea5078cbfdb138395166
    key_input = 'visakey:57cdc4296f52ea5078cbfdb138395166'
    secret_key = '57cdc4296f52ea5078cbfdb138395166'
    
    print("=" * 50)
    print("Listing Supabase S3 Buckets")
    print("=" * 50)
    print()
    
    # Try different access key formats
    access_keys_to_try = [
        ('visakey', 'visakey'),
        (key_input, 'full_key'),
    ]
    
    for access_key, key_name in access_keys_to_try:
        print(f"\n--- Trying with access key: {key_name} ({access_key[:15]}...) ---")
        result = list_buckets(host, access_key, secret_key)
        print(f"Status: {result['status_code']}")
        print(f"Response: {result['response'][:500]}")
        
        if result['success']:
            print("\nSuccess! Buckets listed above.")
            break
        print("-" * 50)


if __name__ == '__main__':
    main()
