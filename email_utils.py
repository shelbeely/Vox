import os
import requests

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RESEND_API_URL = "https://api.resend.com/emails"
FROM_EMAIL = os.getenv("FROM_EMAIL", "Vox App <noreply@yourdomain.com>")

def send_verification_email(email: str, token: str):
    """Send email verification link via Resend API."""
    verify_url = f"https://yourapp.com/verify?token={token}"
    subject = "Verify your email for Vox"
    html = f"<p>Click <a href='{verify_url}'>here</a> to verify your email address.</p>"
    text = f"Visit {verify_url} to verify your email address."

    return _send_email(email, subject, html, text)

def send_password_reset_email(email: str, token: str):
    """Send password reset link via Resend API."""
    reset_url = f"https://yourapp.com/reset-password?token={token}"
    subject = "Reset your Vox password"
    html = f"<p>Click <a href='{reset_url}'>here</a> to reset your password.</p>"
    text = f"Visit {reset_url} to reset your password."

    return _send_email(email, subject, html, text)

def _send_email(to_email: str, subject: str, html: str, text: str):
    if not RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY not set in environment variables")

    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "from": FROM_EMAIL,
        "to": to_email,
        "subject": subject,
        "html": html,
        "text": text
    }

    response = requests.post(RESEND_API_URL, json=payload, headers=headers)
    if response.status_code >= 400:
        print(f"Failed to send email to {to_email}: {response.status_code} {response.text}")
    else:
        print(f"Sent email to {to_email}: {subject}")
    return response
