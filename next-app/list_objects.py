#!/usr/bin/env python3
"""
List objects in bucket and check file
"""

import requests

def main():
    supabase_url = 'https://cycnichledvqbxevrwnt.storage.supabase.co'
    service_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN5Y25pY2hsZWR2cWJ4ZXZyd250Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NjAzMzU5NiwiZXhwIjoyMDgxNjA5NTk2fQ.Sdc2cOACcemGPdn4pCp-7LlbmvT3yfOwnLliJr-ZJd0'
    
    bucket_name = 'posts'
    object_name = 'new_posts.json'
    
    # List objects in bucket
    print("1. Listing objects in bucket...")
    resp = requests.get(
        f"{supabase_url}/storage/v1/object/list/{bucket_name}",
        headers={'Authorization': f'Bearer {service_key}'}
    )
    print(f"   Status: {resp.status_code}")
    print(f"   Response: {resp.text[:500]}")
    
    objects = resp.json() if resp.status_code == 200 else []
    print(f"   Objects found: {len(objects)}")
    for obj in objects:
        print(f"   - {obj.get('name')}")
    
    # Update bucket to be public
    print("\n2. Updating bucket to be public...")
    resp = requests.put(
        f"{supabase_url}/storage/v1/bucket/{bucket_name}",
        headers={
            'Authorization': f'Bearer {service_key}',
            'Content-Type': 'application/json'
        },
        json={'public': True, 'id': bucket_name, 'name': bucket_name}
    )
    print(f"   Status: {resp.status_code}")
    print(f"   Response: {resp.text[:300]}")
    
    # Re-check bucket public status
    print("\n3. Re-checking bucket status...")
    resp = requests.get(
        f"{supabase_url}/storage/v1/bucket/{bucket_name}",
        headers={'Authorization': f'Bearer {service_key}'}
    )
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"   Public: {data.get('public')}")
    
    # Try to get authenticated URL
    print("\n4. Getting authenticated URL for object...")
    resp = requests.get(
        f"{supabase_url}/storage/v1/object/auth/{bucket_name}/{object_name}",
        headers={'Authorization': f'Bearer {service_key}'}
    )
    print(f"   Status: {resp.status_code}")
    print(f"   Response: {resp.text[:300]}")
    
    if resp.status_code == 200:
        data = resp.json()
        signed_url = data.get('signed_url')
        print(f"   Signed URL: {signed_url[:80]}...")

if __name__ == '__main__':
    main()
