#!/usr/bin/env python3
"""
Friday Digest Email Sender

This script sends personalized activity recommendation emails to all users.
Run it via cron on Fridays, e.g.:
    0 9 * * 5 cd /path/to/activity_planner/backend && python send_friday_digest.py

Requires environment variables:
- SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD for email
- FRONTEND_URL for links in emails
"""

import os
import sys

# Add the backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app import send_all_friday_digests

if __name__ == '__main__':
    print("=" * 50)
    print("Friday Digest Email Sender")
    print("=" * 50)
    
    # Check SMTP configuration
    smtp_host = os.environ.get('SMTP_HOST', '')
    if not smtp_host:
        print("WARNING: SMTP_HOST not configured. Emails will not be sent.")
        print("Set SMTP_HOST, SMTP_USER, SMTP_PASSWORD environment variables.")
    
    sent_count = send_all_friday_digests()
    
    print("=" * 50)
    print(f"Complete! Sent {sent_count} digest emails.")
    print("=" * 50)
