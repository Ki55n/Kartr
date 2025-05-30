import os
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# Import email configuration
try:
    from config import EMAIL_CONFIG
except ImportError:
    EMAIL_CONFIG = {}

# Dictionary to store OTPs with expiration times
otp_store = {}

def generate_otp(length=6):
    """Generate a random OTP of specified length"""
    return ''.join(random.choices(string.digits, k=length))

def store_otp(email, otp, expiry_minutes=10):
    """Store OTP with expiration time"""
    expiry_time = datetime.now() + timedelta(minutes=expiry_minutes)
    otp_store[email] = {
        'otp': otp,
        'expiry': expiry_time
    }
    return True

def verify_otp(email, otp):
    """Verify if OTP is valid and not expired"""
    if email not in otp_store:
        return False
    
    stored_data = otp_store[email]
    if stored_data['expiry'] < datetime.now():
        # OTP expired, remove it
        del otp_store[email]
        return False
    
    if stored_data['otp'] == otp:
        # OTP verified, remove it to prevent reuse
        del otp_store[email]
        return True
    
    return False

def send_otp_email(recipient_email, otp):
    """Send OTP to user's email"""
    try:
        # Try to get credentials from Flask app config first
        from app import app
        sender_email = app.config.get('EMAIL_USER', '')
        sender_password = app.config.get('EMAIL_PASSWORD', '')
    except (ImportError, RuntimeError):
        # Fallback to environment variables or config file
        sender_email = os.environ.get('EMAIL_USER', EMAIL_CONFIG.get('EMAIL_USER', ''))
        sender_password = os.environ.get('EMAIL_PASSWORD', EMAIL_CONFIG.get('EMAIL_PASSWORD', ''))
    
    # If credentials are not set, return error
    if not sender_email or not sender_password:
        return False, "Email credentials not configured"
    
    # Create message
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = "Your Login OTP for Kartr"
    
    # Email body
    body = f"""
    <html>
    <body>
        <h2>Kartr - Login OTP</h2>
        <p>Hello,</p>
        <p>You requested to login using OTP. Here is your One-Time Password:</p>
        <h1 style="color: #4CAF50; font-size: 32px;">{otp}</h1>
        <p>This OTP will expire in 10 minutes.</p>
        <p>If you didn't request this OTP, please ignore this email.</p>
        <p>Best regards,<br>Kartr Team</p>
    </body>
    </html>
    """
    
    # Attach body to message
    message.attach(MIMEText(body, 'html'))
    
    try:
        # Connect to SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()  # Identify ourselves to the server
        server.starttls()  # Secure the connection
        server.ehlo()  # Re-identify ourselves over TLS connection
        
        # Login to the server
        server.login(sender_email, sender_password)
        
        # Send email
        text = message.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()
        
        return True, "OTP sent successfully"
    except Exception as e:
        print("unable to send otp:", e)
        return False, str(e)