#!/usr/bin/env python3
"""
Direct upload using Supabase Storage REST API
"""

import requests

def main():
    supabase_url = 'https://cycnichledvqbxevrwnt.storage.supabase.co'
    service_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN5Y25pY2hsZWR2cWJ4ZXZyd250Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NjAzMzU5NiwiZXhwIjoyMDgxNjA5NTk2fQ.Sdc2cOACcemGPdn4pCp-7LlbmvT3yfOwnLliJr-ZJd0'
    
    bucket_name = 'posts'
    file_path = '/Users/mohanakrishnanarsupalli/Downloads/new_posts.json'
    object_name = 'new_posts.json'
    
    # Read file
    with open(file_path, 'rb') as f:
        file_content = f.read()
    file_size = len(file_content)
    
    print("=" * 50)
    print("Direct REST API Upload")
    print("=" * 50)
    print(f"File: {file_path} ({file_size} bytes)")
    
    # Method 1: POST to create object
    print("\n1. Trying POST upload...")
    url = f"{supabase_url}/storage/v1/object/{bucket_name}/{object_name}"
    headers = {
        'Authorization': f'Bearer {service_key}',
        'Content-Type': 'application/octet-stream',
        'Content-Length': str(file_size)
    }
    
    resp = requests.post(url, data=file_content, headers=headers)
    print(f"   Status: {resp.status_code}")
    print(f"   Response: {resp.text[:200]}")
    
    if resp.status_code in [200, 201]:
        print("\n✓ Upload successful!")
        print(f"URL: {supabase_url}/storage/v1/object/public/{bucket_name}/{object_name}")
        return
    
    # Method 2: Use authenticated URL
    print("\n2. Trying authenticated URL...")
    auth_url = f"{supabase_url}/storage/v1/object/auth/{bucket_name}/{object_name}"
    resp = requests.get(auth_url, headers={'Authorization': f'Bearer {service_key}'})
    print(f"   Status: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        signed_url = data.get('signed_url')
        if signed_url:
            print(f"   Got signed URL: {signed_url[:50]}...")
            upload_resp = requests.put(signed_url, data=file_content)
            print(f"   Upload status: {upload_resp.status_code}")
    
    print("\n" + "=" * 50)

if __name__ == '__main__':
    main()
