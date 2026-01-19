#!/usr/bin/env python3
"""
Create bucket using Supabase S3 API with AWS Signature V4
"""

import hmac
import hashlib
import datetime
import requests

def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

def create_bucket_s3(host, access_key, secret_key, bucket_name):
    """
    Create bucket using S3 API with AWS Signature V4
    """
    region = 'us-east-1'
    service = 's3'
    
    # HTTP request details for CreateBucket
    method = 'PUT'
    path = f'/{bucket_name}'
    url = f'https://{host}{path}'
    
    # For bucket creation, we need XML body for some