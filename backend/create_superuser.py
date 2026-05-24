#!/usr/bin/env python
"""
Script to create a Django superuser.
Usage: python create_superuser.py [username] [email] [password]
If no arguments provided, uses defaults: admin/admin@example.com/admin123
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_app.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_superuser(username=None, email=None, password=None):
    """Create a Django superuser."""
    # Default credentials
    username = username or "admin"
    email = email or "admin@example.com"
    password = password or "admin123"
    
    # Check if user already exists
    if User.objects.filter(username=username).exists():
        print(f"[ERROR] User '{username}' already exists!")
        print(f"   To reset password, use: python manage.py changepassword {username}")
        return False
    
    # Create superuser
    try:
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print("[SUCCESS] Superuser created successfully!")
        print(f"   Username: {username}")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        print(f"\n   Access Django admin at: http://localhost:8000/admin/")
        return True
    except Exception as e:
        print(f"[ERROR] Error creating superuser: {e}")
        return False

if __name__ == "__main__":
    # Get arguments from command line
    username = sys.argv[1] if len(sys.argv) > 1 else None
    email = sys.argv[2] if len(sys.argv) > 2 else None
    password = sys.argv[3] if len(sys.argv) > 3 else None
    
    create_superuser(username, email, password)
