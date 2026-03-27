# backend/app/core/email.py
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime

# 🌟 ADD THESE TWO LINES TO LOAD THE .env FILE!
from dotenv import load_dotenv
load_dotenv() 

# --- CONFIGURATION ---
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME") 
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD") 
SENDER_EMAIL = os.getenv("SENDER_EMAIL", SMTP_USERNAME)
SENDER_NAME = "accqudo Security"

# ... rest of the file remains exactly the same!

def send_email(to_email: str, subject: str, html_content: str):
    """Core function to send an email via SMTP securely."""
    # If no password is provided in .env, skip attempting to send to save time
    if not SMTP_PASSWORD:
        print("⚠️ No SMTP_PASSWORD found in .env. Skipping real email send.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
    msg["To"] = to_email

    part = MIMEText(html_content, "html")
    msg.attach(part)

    try:
        # Create a secure SSL context
        context = ssl.create_default_context()
        
        # Using 'with' ensures the connection is closed automatically
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()
            server.starttls(context=context) # Secure the connection
            server.ehlo()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
            
        print(f"✅ Email successfully sent to {to_email}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("❌ SMTP Auth Error: Google rejected the credentials. You MUST use a 16-character App Password.")
        return False
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

# --- PROFESSIONAL HTML TEMPLATES ---
# (The templates remain exactly the same!)

def send_otp_email(to_email: str, otp_code: str, purpose: str):
    action = "verify your account registration" if purpose == "register" else "reset your password"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-w-md: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 10px;">
        <h2 style="color: #0f172a; margin-bottom: 5px;">acc<span style="color: #4f46e5;">qudo</span></h2>
        <p style="color: #64748b; font-size: 14px; margin-top: 0; border-bottom: 1px solid #e2e8f0; padding-bottom: 20px;">Academic Identity Platform</p>
        <h3 style="color: #1e293b; margin-top: 30px;">Verification Code</h3>
        <p style="color: #334155; line-height: 1.6;">You requested a code to {action}. Please use the following 6-digit One-Time Password (OTP) to proceed. This code will expire in 10 minutes.</p>
        <div style="background-color: #f8fafc; padding: 15px; text-align: center; border-radius: 8px; margin: 25px 0;">
            <span style="font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #4f46e5;">{otp_code}</span>
        </div>
        <p style="color: #64748b; font-size: 12px; margin-top: 30px;">If you did not request this, please ignore this email or contact support.</p>
    </div>
    """
    return send_email(to_email, f"Your accqudo Verification Code: {otp_code}", html)

def send_welcome_email(to_email: str, name: str):
    html = f"""
    <div style="font-family: Arial, sans-serif; max-w-md: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 10px;">
        <h2 style="color: #0f172a; margin-bottom: 5px;">acc<span style="color: #4f46e5;">qudo</span></h2>
        <h3 style="color: #1e293b; margin-top: 30px;">Welcome to accqudo, {name}! 🎉</h3>
        <p style="color: #334155; line-height: 1.6;">Your academic portfolio is officially active. You can now access your dashboard, connect your custom domain, and utilize our AI suite.</p>
        <div style="margin-top: 30px;">
            <a href="http://localhost:3000/dashboard" style="background-color: #0f172a; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Go to Dashboard</a>
        </div>
    </div>
    """
    return send_email(to_email, "Welcome to accqudo!", html)

def send_login_alert(to_email: str, ip_address: str, user_agent: str):
    time_now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    html = f"""
    <div style="font-family: Arial, sans-serif; max-w-md: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 10px;">
        <h2 style="color: #0f172a; margin-bottom: 5px;">acc<span style="color: #4f46e5;">qudo</span></h2>
        <h3 style="color: #b91c1c; margin-top: 30px;">⚠️ New Login Detected</h3>
        <p style="color: #334155; line-height: 1.6;">We detected a new login to your accqudo account.</p>
        <table style="width: 100%; margin-top: 20px; border-collapse: collapse; font-size: 14px; color: #475569;">
            <tr><td style="padding: 8px; border-bottom: 1px solid #f1f5f9;"><strong>Time:</strong></td><td style="padding: 8px; border-bottom: 1px solid #f1f5f9;">{time_now}</td></tr>
            <tr><td style="padding: 8px; border-bottom: 1px solid #f1f5f9;"><strong>IP Address:</strong></td><td style="padding: 8px; border-bottom: 1px solid #f1f5f9;">{ip_address}</td></tr>
            <tr><td style="padding: 8px; border-bottom: 1px solid #f1f5f9;"><strong>Device:</strong></td><td style="padding: 8px; border-bottom: 1px solid #f1f5f9;">{user_agent}</td></tr>
        </table>
    </div>
    """
    return send_email(to_email, "Security Alert: New Login Detected", html)