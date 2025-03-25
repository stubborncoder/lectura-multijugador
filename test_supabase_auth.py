"""
Test script to directly test Supabase authentication
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import json

# Load environment variables
load_dotenv()

# Get Supabase credentials from environment or input
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url:
    supabase_url = input("Enter Supabase URL: ")
if not supabase_key:
    supabase_key = input("Enter Supabase key: ")

print(f"Using Supabase URL: {supabase_url}")
print(f"Using Supabase key: {supabase_key[:5]}...{supabase_key[-5:]}")

# Initialize Supabase client
try:
    supabase = create_client(supabase_url, supabase_key)
    print("Supabase client initialized successfully")
except Exception as e:
    print(f"Error initializing Supabase client: {e}")
    exit(1)

# Test authentication
email = input("Enter email: ")
password = input("Enter password: ")

print(f"\nAttempting to authenticate with email: {email}")

try:
    # Try authentication
    auth_response = supabase.auth.sign_in_with_password({"email": email, "password": password})
    
    # Print response details
    print("\nAuthentication successful!")
    print(f"User ID: {auth_response.user.id}")
    print(f"Email: {auth_response.user.email}")
    print(f"Email confirmed: {auth_response.user.email_confirmed_at is not None}")
    
    # Print session details
    print("\nSession details:")
    print(f"Access token: {auth_response.session.access_token[:10]}...{auth_response.session.access_token[-10:]}")
    print(f"Refresh token: {auth_response.session.refresh_token[:5]}...{auth_response.session.refresh_token[-5:]}")
    
    # Print user metadata
    print("\nUser metadata:")
    print(json.dumps(auth_response.user.user_metadata, indent=2) if auth_response.user.user_metadata else "No metadata")
    
except Exception as e:
    print(f"\nAuthentication failed: {e}")
    print(f"Error type: {type(e).__name__}")
    
    # Try to get more details about the error
    if hasattr(e, 'message'):
        print(f"Error message: {e.message}")
    if hasattr(e, 'code'):
        print(f"Error code: {e.code}")
