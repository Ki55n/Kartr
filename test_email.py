import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_gmail_connection(email, password, recipient):
    """Test Gmail SMTP connection with provided credentials"""
    try:
        # Create message
        message = MIMEMultipart()
        message['From'] = email
        message['To'] = recipient
        message['Subject'] = "Test Email from Kartr App"
        
        # Email body
        body = """
        <html>
        <body>
            <h2>Test Email</h2>
            <p>This is a test email to verify SMTP connection.</p>
            <p>If you received this email, your email configuration is working correctly.</p>
        </body>
        </html>
        """
        
        # Attach body to message
        message.attach(MIMEText(body, 'html'))
        
        # Connect to SMTP server with detailed debugging
        print("Connecting to SMTP server...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.set_debuglevel(1)  # Enable verbose debug output
        
        print("Sending EHLO...")
        server.ehlo()
        
        print("Starting TLS...")
        server.starttls()
        
        print("Sending EHLO again...")
        server.ehlo()
        
        print(f"Attempting login with email: {email}")
        server.login(email, password)
        
        print("Login successful! Sending email...")
        text = message.as_string()
        server.sendmail(email, recipient, text)
        
        print("Email sent successfully!")
        server.quit()
        
        return True, "Email sent successfully"
    except Exception as e:
        print(f"Error: {e}")
        return False, str(e)

if __name__ == "__main__":
    # Import email configuration
    try:
        from config import EMAIL_CONFIG
        email = EMAIL_CONFIG.get('EMAIL_USER', '')
        password = EMAIL_CONFIG.get('EMAIL_PASSWORD', '')
    except ImportError:
        import os
        email = os.environ.get('EMAIL_USER', '')
        password = os.environ.get('EMAIL_PASSWORD', '')
    
    if not email or not password:
        print("Email credentials not configured. Please set them in config.py or as environment variables.")
        exit(1)
    
    # Test sending to the same email address
    recipient = email
    
    print(f"Testing email connection with: {email}")
    success, message = test_gmail_connection(email, password, recipient)
    
    if success:
        print("✅ Email test successful!")
    else:
        print(f"❌ Email test failed: {message}")
        print("\nTroubleshooting tips:")
        print("1. Make sure you're using an App Password if 2FA is enabled on your Google account")
        print("2. Check that the email address is correct")
        print("3. Ensure you've allowed less secure apps if not using an App Password")
        print("4. Verify that your Google account doesn't have any security blocks")