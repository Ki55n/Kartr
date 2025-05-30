import os
import sys

def set_email_config():
    """
    Set email configuration for OTP sending.
    This script should be run before starting the application.
    """
    print("Setting up email configuration for OTP functionality")
    print("Note: For Gmail, you need to use an App Password if 2FA is enabled.")
    print("Visit https://myaccount.google.com/apppasswords to generate one.")
    
    email = input("Enter Gmail address: ")
    password = input("Enter Gmail password or App Password: ")
    
    # Set environment variables
    os.environ['EMAIL_USER'] = email
    os.environ['EMAIL_PASSWORD'] = password
    
    print("\nEmail configuration set successfully!")
    print("These settings will only persist for the current terminal session.")
    print("To make them permanent, add them to your environment variables.")

if __name__ == "__main__":
    set_email_config()