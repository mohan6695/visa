#!/usr/bin/env python3
"""
Supabase Storage REST API Uploader - Create bucket and upload
"""

import os
import requests

def list_buckets_rest(supabase_url, service_key):
    """List buckets using REST API"""
    url = f"{supabase_url}/storage/v1/bucket"
    
    headers = {
        'Authorization': f'Bearer {service_key}',
        'Content-Type': 'application/json'
    }
    
    print(f"Listing buckets: {url}")
    response = requests.get(url, headers=headers)
    return response


def create_bucket_rest(supabase_url, service_key, bucket_name, public=True):
    """Create a new bucket"""
    url = f"{supabase_url}/storage/v1/bucket"
    
    headers = {
        'Authorization': f'Bearer {service_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'id': bucket_name,
        'name': bucket_name,
        'public': public
    }
    
    print(f"Creating bucket '{bucket_name}': {url}")
    response = requests.post(url, headers=headers, json=data)
    return response


def upload_with_presigned_url(supabase_url, service_key, bucket_name, file_path, object_name):
    """Create presigned URL and upload"""
    # Step 1: Get upload URL
    sign_url = f"{supabase_url}/storage/v1/object/upload/sign/{bucket_name}/{object_name}"
    
    headers = {
        'Authorization': f'Bearer {service_key}',
        'Content-Type': 'application/json'
    }
    
    # Need to send an empty JSON body
    data = {}
    
    print(f"\nGetting presigned URL: {sign_url}")
    response = requests.post(sign_url, headers=headers, json=data)
    
    print(f"Response: {response.status_code} - {response.text[:300]}")
    
    if response.status_code == 200:
        data = response.json()
        signed_url = data.get('signed_url')
        if signed_url:
            print(f"Got signed URL: {signed_url[:80]}...")
            
            # Step 2: Upload using signed URL
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            print(f"Uploading to signed URL...")
            upload_response = requests.put(signed_url, data=file_content)
            print(f"Upload response: {upload_response.status_code}")
            return upload_response
    
    return response


def main():
    # Configuration
    supabase_url = 'https://cycnichledvqbxevrwnt.storage.supabase.co'
    
    # Service role key - should be set in environment or hardcoded
    service_key = os.environ.get('SUPABASE_SERVICE_KEY', '')
    if not service_key:
        # Use the service role key you added
        service_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN5Y25pY2hsZWR2cWJ4ZXZyd250Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NjAzMzU5NiwiZXhwIjoyMDgxNjA5NTk2fQ.Sdc2cOACcemGPdn4pCp-7LlbmvT3yfOwnLliJr-ZJd0'
    
    bucket_name = 'posts'
    file_path = '/Users/mohanakrishnanarsupalli/Downloads/new_posts.json'
    object_name = 'new_posts.json'
    
    print("=" * 60)
    print("Supabase Storage REST API - Create Bucket & Upload")
    print("=" * 60)
    print(f"File: {file_path}")
    print(f"Bucket: {bucket_name}")
    print()
    
    # Step 1: List existing buckets
    print("Step 1: Listing existing buckets...")
    response = list_buckets_rest(supabase_url, service_key)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        buckets = response.json()
        print(f"Buckets found: {len(buckets) if isinstance(buckets, list) else 0}")
        if isinstance(buckets, list):
            for b in buckets:
                print(f"  - {b.get('name', b.get('id'))}")
        
        # Check if 'posts' bucket exists
        bucket_exists = any(b.get('name') == bucket_name or b.get('id') == bucket_name for b in buckets) if isinstance(buckets, list) else False
        print(f"Bucket '{bucket_name}' exists: {bucket_exists}")
    else:
        bucket_exists = False
    
    print()
    
    # Step 2: Create bucket if it doesn't exist
    if not bucket_exists:
        print("Step 2: Creating bucket...")
        create_response = create_bucket_rest(supabase_url, service_key, bucket_name, public=True)
        print(f"Status: {create_response.status_code}")
        print(f"Response: {create_response.text[:300]}")
        
        if create_response.status_code in [200, 201]:
            print(f"✓ Bucket '{bucket_name}' created successfully!")
            bucket_exists = True
        else:
            print(f"✗ Failed to create bucket")
    else:
        print("Step 2: Bucket already exists, skipping creation")
    
    print()
    
    # Step 3: Upload file using presigned URL
    print("Step 3: Uploading file...")
    if bucket_exists:
        result = upload_with_presigned_url(supabase_url, service_key, bucket_name, file_path, object_name)
        
        print()
        print("=" * 60)
        print(f"Upload Status: {result.status_code}")
        print(f"Success: {result.status_code in [200, 201]}")
        if result.status_code in [200, 201]:
            print(f"✓ File uploaded successfully!")
            print(f"Public URL: {supabase_url}/storage/v1/object/public/{bucket_name}/{object_name}")
        else:
            print(f"Response: {result.text[:300]}")
        print("=" * 60)
    else:
        print("✗ Cannot upload - bucket not created")
        result = None
    
    return result


if __name__ == '__main__':
    main()
