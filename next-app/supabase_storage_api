#!/usr/bin/env python3
"""
Supabase Storage REST API Uploader using service_role key
"""

import os
import requests
import json

def upload_to_supabase_storage(file_path, supabase_url, service_role_key, bucket_name, object_name):
    """
    Upload file to Supabase Storage using REST API
    """
    # Read file content
    with open(file_path, 'rb') as f:
        file_content = f.read()
    
    file_size = len(file_content)
    
    # Supabase Storage REST API endpoint
    # Using the object upload endpoint with service_role auth
    url = f"{supabase_url}/object/{bucket_name}/{object_name}"
    
    headers = {
        'Authorization': f'Bearer {service_role_key}',
        'Content-Type': 'application/json',
        'Content-Length': str(file_size)
    }
    
    print(f"Uploading {file_path} ({file_size} bytes)...")
    print(f"URL: {url}")
    
    # Try POST to upload
    response = requests.post(
        url,
        data=file_content,
        headers=headers
    )
    
    result = {
        'status_code': response.status_code,
        'response': response.text[:500] if response.text else 'No response body',
        'success': response.status_code in [200, 201],
        'url': f"{supabase_url}/object/public/{bucket_name}/{object_name}"
    }
    
    return result


def upload_using_post_object(file_path, supabase_url, service_role_key, bucket_name, object_name):
    """
    Alternative: Use POST to create upload URL then upload
    """
    # Step 1: Create upload URL
    create_url = f"{supabase_url}/object/upload/sign/{bucket_name}/{object_name}"
    
    headers = {
        'Authorization': f'Bearer {service_role_key}',
        'Content-Type': 'application/json'
    }
    
    print(f"\nCreating upload URL...")
    print(f"URL: {create_url}")
    
    response = requests.post(create_url, headers=headers)
    print(f"Response: {response.status_code} - {response.text[:200]}")
    
    if response.status_code == 200:
        data = response.json()
        upload_url = data.get('url')
        if upload_url:
            print(f"Got upload URL: {upload_url}")
            return upload_url
    
    return None


def list_buckets(supabase_url, service_role_key):
    """List all buckets"""
    url = f"{supabase_url}/bucket"
    
    headers = {
        'Authorization': f'Bearer {service_role_key}'
    }
    
    print(f"\nListing buckets...")
    response = requests.get(url, headers=headers)
    print(f"Response: {response.status_code} - {response.text[:500]}")
    return response


def create_bucket(supabase_url, service_role_key, bucket_name):
    """Create a new bucket"""
    url = f"{supabase_url}/bucket"
    
    headers = {
        'Authorization': f'Bearer {service_role_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'id': bucket_name,
        'name': bucket_name,
        'public': True
    }
    
    print(f"\nCreating bucket '{bucket_name}'...")
    response = requests.post(url, headers=headers, json=data)
    print(f"Response: {response.status_code} - {response.text[:500]}")
    return response


def main():
    # Configuration
    supabase_url = 'https://cycnichledvqbxevrwnt.storage.supabase.co/storage/v1'
    
    # The key format suggests this is an S3 credential
    # For Supabase Storage REST API, we need a service_role key
    # But let's try with the provided credentials in different formats
    
    key_input = 'visakey:57cdc4296f52ea5078cbfdb138395166'
    
    # Try different key formats
    keys_to_try = [
        key_input,  # Full format
        '57cdc4296f52ea5078cbfdb138395166',  # Just the UUID
        '',  # Empty (anon key)
    ]
    
    bucket_name = 'posts'
    file_path = '/Users/mohanakrishnanarsupalli/Downloads/new_posts.json'
    object_name = 'new_posts.json'
    
    print("=" * 50)
    print("Supabase Storage Upload")
    print("=" * 50)
    print(f"File: {file_path}")
    print(f"Bucket: {bucket_name}")
    print(f"Object: {object_name}")
    print()
    
    # First, let's list existing buckets to see what's available
    for key in keys_to_try:
        if key:
            print(f"\n--- Trying with key: {key[:10]}... ---")
            result = list_buckets(supabase_url, key)
            if result.status_code == 200:
                print("Success listing buckets!")
                break
    else:
        # If no key worked, try without auth
        print("\n--- Trying without authentication ---")
        result = list_buckets(supabase_url, '')
        print(f"Response: {result.status_code} - {result.text[:500]}")
    
    print("\n" + "=" * 50)
    print("Upload result will be available above")
    print("=" * 50)


if __name__ == '__main__':
    main()
