"""
Helper functions for Firebase authentication
"""
import logging

logger = logging.getLogger(__name__)

def user_exists_in_firebase(auth, email, password):
    """
    Check if a user exists in Firebase by attempting to sign in
    
    Args:
        auth: Firebase auth instance
        email: User email
        password: User password
        
    Returns:
        tuple: (exists, user_data)
            - exists: Boolean indicating if user exists
            - user_data: Firebase user data if exists, None otherwise
    """
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        return True, user
    except Exception as e:
        error_message = str(e)
        # Check if the error is because the user doesn't exist
        if "EMAIL_NOT_FOUND" in error_message or "INVALID_PASSWORD" in error_message:
            return False, None
        else:
            logger.error(f"Error checking if user exists in Firebase: {error_message}")
            return False, None

def create_firebase_user(auth, email, password):
    """
    Create a new user in Firebase
    
    Args:
        auth: Firebase auth instance
        email: User email
        password: User password
        
    Returns:
        tuple: (success, user_data)
            - success: Boolean indicating if creation was successful
            - user_data: Firebase user data if successful, None otherwise
    """
    try:
        user = auth.create_user_with_email_and_password(email, password)
        return True, user
    except Exception as e:
        error_message = str(e)
        # Check if the error is because the user already exists
        if "EMAIL_EXISTS" in error_message:
            logger.info(f"User {email} already exists in Firebase")
            return False, None
        else:
            logger.error(f"Error creating user in Firebase: {error_message}")
            return False, None
            
def send_password_reset_email(auth, email):
    """
    Send a password reset email to the user
    
    Args:
        auth: Firebase auth instance
        email: User email
        
    Returns:
        tuple: (success, error_message)
            - success: Boolean indicating if the email was sent successfully
            - error_message: Error message if not successful, None otherwise
    """
    try:
        auth.send_password_reset_email(email)
        logger.info(f"Password reset email sent to {email}")
        return True, None
    except Exception as e:
        error_message = str(e)
        if "EMAIL_NOT_FOUND" in error_message:
            logger.warning(f"Email not found when sending password reset: {email}")
            return False, "Email not found. Please check your email address or register a new account."
        else:
            logger.error(f"Error sending password reset email: {error_message}")
            return False, f"Error sending password reset email: {error_message}"