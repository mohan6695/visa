#!/usr/bin/env python3
"""
Check Supabase Storage and get correct public URL
"""

import requests

def main():
    supabase_url = 'https://cycnichledvqbxevrwnt.storage.supabase.co'
    service_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN5Y25pY2hsZWR2cWJ4ZXZyd250Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NjAzMzU5NiwiZXhwIjoyMDgxNjA5NTk2fQ.Sdc2cOACcemGPdn4pCp-7LlbmvT3yfOwnLliJr-ZJd0'
    
    bucket_name = 'posts'
    object_name = 'new_posts.json'
    
    # List buckets
    print("1. Listing buckets...")
    resp = requests.get(
        f"{supabase_url}/storage/v1/bucket",
        headers={'Authorization': f'Bearer {service_key}'}
    )
    print(f"   Status: {resp.status_code}")
    print(f"   Response: {resp.text[:500]}")
    buckets = resp.json() if resp.status_code == 200 else []
    print(f"   Buckets: {[b.get('name') for b in buckets]}")
    
    # Try different URL formats
    print("\n2. Testing different URL formats...")
    
    urls_to_try = [
        f"{supabase_url}/storage/v1/object/public/{bucket_name}/{object_name}",
        f"{supabase_url}/object/public/{bucket_name}/{object_name}",
        f"https://{supabase_url.split('//')[1]}/object/public/{bucket_name}/{object_name}",
    ]
    
    for url in urls_to_try:
        print(f"   Testing: {url[:60]}...")
        resp = requests.get(url)
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"   ✓ Success! File is accessible.")
            break
    else:
        print("   ✗ All URL formats failed")
    
    # Try direct download URL
    print("\n3. Getting authenticated download URL...")
    resp = requests.get(
        f"{supabase_url}/storage/v1/object/auth/{bucket_name}/{object_name}",
        headers={'Authorization': f'Bearer {service_key}'}
    )
    print(f"   Status: {resp.status_code}")
    print(f"   Response: {resp.text[:500]}")
    
    if resp.status_code == 200:
        data = resp.json()
        signed_url = data.get('signed_url')
        if signed_url:
            print(f"   ✓ Download URL: {signed_url[:80]}...")

if __name__ == '__main__':
    main()
