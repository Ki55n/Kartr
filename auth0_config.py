"""
Auth0 Configuration

This file contains the Auth0 configuration and initialization code.
"""
import os
import logging
from authlib.integrations.requests_client import OAuth2Session
from jose import jwt

logger = logging.getLogger(__name__)

# Auth0 configuration
config = {
    'domain': os.environ.get('AUTH0_DOMAIN', 'dev-1ipnytneeebogaqd.us.auth0.com'),
    'client_id': os.environ.get('AUTH0_CLIENT_ID', 'sSw9meytBSWJ3UAbxoKuTM4xfpOWzHY3'),
    'client_secret': os.environ.get('AUTH0_CLIENT_SECRET', 'lx9PLgxmwpqlXaFi698aGNBjBhkl7pKrSThrs4Hp0dfiSVlyKR20KcuznBXcDJu0'),
    'api_audience': os.environ.get('AUTH0_API_AUDIENCE', 'https://dev-1ipnytneeebogaqd.us.auth0.com/api/v2/'),
    'algorithm': ['RS256'],
    'connection': os.environ.get('AUTH0_CONNECTION', 'Username-Password-Authentication')  # Default connection
}

# Function to verify Auth0 connection
def verify_auth0_connection():
    """
    Verify that the Auth0 connection is properly configured
    
    Returns:
        bool: True if the connection is verified, False otherwise
    """
    try:
        import requests
        
        # First, test basic connectivity to Auth0
        test_response = requests.get(f"https://{config['domain']}/", timeout=5, verify=True)
        logger.info(f"Auth0 connection test: {test_response.status_code}")
        
        # Get a management API token to verify client credentials
        token = get_management_api_token()
        if not token:
            logger.warning("Could not get Auth0 management API token. Check your client credentials.")
            return False
            
        # Verify the connection exists
        connections_url = f"https://{config['domain']}/api/v2/connections"
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        response = requests.get(connections_url, headers=headers, timeout=10, verify=True)
        
        if response.status_code == 200:
            connections = response.json()
            connection_names = [conn.get('name') for conn in connections]
            
            if config['connection'] in connection_names:
                logger.info(f"Auth0 connection '{config['connection']}' verified successfully")
                return True
            else:
                logger.error(f"Auth0 connection '{config['connection']}' not found in tenant")
                logger.error(f"Available connections: {', '.join(connection_names)}")
                return False
        else:
            logger.error(f"Failed to get Auth0 connections. Status: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error verifying Auth0 connection: {str(e)}")
        return False

# Initialize Auth0 client
try:
    import requests
    
    auth0_client = OAuth2Session(
        client_id=config['client_id'],
        client_secret=config['client_secret']
    )
    logger.info("Auth0 client initialized successfully")
    
    # Verify the Auth0 connection (but don't block initialization if it fails)
    try:
        verify_auth0_connection()
    except Exception as verify_err:
        logger.warning(f"Auth0 connection verification failed: {str(verify_err)}")
        
except requests.exceptions.SSLError as ssl_err:
    logger.error(f"SSL Error connecting to Auth0: {str(ssl_err)}")
    logger.error("SSL verification failed. Please check your SSL certificates and configuration.")
    auth0_client = None
except Exception as e:
    logger.error(f"Error initializing Auth0 client: {str(e)}")
    auth0_client = None

# Function to get Auth0 Management API token
def get_management_api_token():
    """
    Get a token for the Auth0 Management API
    
    Returns:
        str: The access token if successful, None otherwise
    """
    try:
        import requests
        
        token_url = f"https://{config['domain']}/oauth/token"
        token_payload = {
            'grant_type': 'client_credentials',
            'client_id': config['client_id'],
            'client_secret': config['client_secret'],
            'audience': config['api_audience'],
            "realm":"Username-Password-Authentication"
            # Note: connection parameter is not needed for client credentials grant
        }
        
        # Always use SSL verification for security
        response = requests.post(
            token_url, 
            json=token_payload,
            timeout=10,  # Add timeout
            verify=True  # Verify SSL certificates
        )
        
        if response.status_code == 200:
            return response.json().get('access_token')
        else:
            logger.error(f"Failed to get token. Status: {response.status_code}, Response: {response.text}")
            # Log more detailed error information
            try:
                error_data = response.json()
                if 'error_description' in error_data:
                    logger.error(f"Auth0 error description: {error_data['error_description']}")
            except:
                pass
            return None
    except requests.exceptions.SSLError as ssl_err:
        logger.error(f"SSL Error connecting to Auth0: {str(ssl_err)}")
        # SSL errors should be fixed properly rather than bypassed
        logger.error("SSL verification failed. Please check your SSL certificates and configuration.")
        return None
    except Exception as e:
        logger.error(f"Error getting Auth0 Management API token: {str(e)}")
        return None