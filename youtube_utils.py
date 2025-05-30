import os
import csv
import pandas as pd
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from werkzeug.security import generate_password_hash, check_password_hash

# CSV file paths
DATABASE_CSV = os.path.join(os.getcwd(), 'data/database.csv')
ANALYSIS_CSV = os.path.join(os.getcwd(), 'data/ANALYSIS.CSV')

def save_user_to_csv(username, email, password, user_type, public_email=False):
    """
    Save user information to database.csv
    Ensures records are properly appended one below the other

    Parameters:
    - username: The user's username
    - email: The user's email
    - password: The user's password (will be hashed)
    - user_type: 'influencer' or 'sponsor'
    - public_email: Boolean indicating if the email should be public in searches
    """
    # Hash the password for security
    hashed_password = generate_password_hash(password)

    # Make sure directory exists
    os.makedirs(os.path.dirname(DATABASE_CSV), exist_ok=True)

    # Check if file exists and create with headers if not
    if not os.path.exists(DATABASE_CSV):
        with open(DATABASE_CSV, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['username', 'email', 'password', 'user_type', 'date_registered', 'public_email'])

    # Read the file to check existing headers
    existing_headers = []
    existing_data = []
    try:
        with open(DATABASE_CSV, 'r', newline='') as file:
            reader = csv.reader(file)
            all_rows = list(reader)
            if all_rows:
                existing_headers = all_rows[0]
                existing_data = all_rows[1:] if len(all_rows) > 1 else []
    except Exception as e:
        print(f"Error reading existing headers: {e}")

    # Update file if 'public_email' is missing from headers
    headers_updated = False
    if 'public_email' not in existing_headers and existing_headers:
        headers_updated = True
        existing_headers.append('public_email')
        # Add False to all existing records
        for row in existing_data:
            row.append('False')

    # Prepare new record
    new_record = [
        username,
        email,
        hashed_password,
        user_type,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        str(public_email)
    ]

    # If headers were updated or for safety, rewrite the entire file
    with open(DATABASE_CSV, 'w', newline='') as file:
        writer = csv.writer(file)
        # Write headers
        writer.writerow(existing_headers if existing_headers else
                        ['username', 'email', 'password', 'user_type', 'date_registered', 'public_email'])

        # Write existing data
        for row in existing_data:
            writer.writerow(row)

        # Write the new record
        writer.writerow(new_record)

    print(f"Successfully added user {username} to {DATABASE_CSV}")
    return True

def validate_user_login(email, password):
    """
    Validate user login against database.csv
    Returns (is_valid, user_type) tuple
    """
    if not os.path.exists(DATABASE_CSV):
        return False, None

    try:
        df = pd.read_csv(DATABASE_CSV)
        user = df[df['email'] == email]

        if not user.empty:
            stored_hash = user.iloc[0]['password']
            if check_password_hash(stored_hash, password):
                return True, user.iloc[0]['user_type']
    except Exception as e:
        print(f"Error validating user: {e}")

    return False, None

def extract_video_id(youtube_url):
    """
    Extract video ID from YouTube URL
    """
    try:
        parsed_url = urlparse(youtube_url)
        if parsed_url.hostname in ('www.youtube.com', 'youtube.com', 'm.youtube.com'):
            if parsed_url.path == '/watch':
                query_params = parse_qs(parsed_url.query)
                if 'v' in query_params:
                    return query_params['v'][0]
            elif parsed_url.path.startswith('/embed/'):
                return parsed_url.path.split('/')[2]
            elif parsed_url.path.startswith('/shorts/'):
                return parsed_url.path.split('/')[2]
        elif parsed_url.hostname == 'youtu.be':
            return parsed_url.path[1:]

        return None
    except Exception as e:
        print(f"Error extracting video ID: {e}")
        return None

def save_analysis_to_csv(video_link, transcript, analysis_data, source="demo"):
    """
    Save analysis data to ANALYSIS.CSV
    Ensures data is appended correctly below previous records
    Only updates when source is 'demo' (meaning it's called from the demo page)
    """
    # Only proceed if this is from the demo page
    if source != "demo":
        print(f"Analysis data not saved: source '{source}' is not 'demo'")
        return False

    # Check if file exists and create with headers if not
    if not os.path.exists(ANALYSIS_CSV):
        os.makedirs(os.path.dirname(ANALYSIS_CSV), exist_ok=True)
        with open(ANALYSIS_CSV, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['video_link', 'transcript', 'analysis_data', 'date_analyzed'])

    # Make sure to properly format transcript and analysis data for CSV storage
    # by removing any internal newlines that might break CSV formatting
    transcript_formatted = transcript.replace('\n', ' ') if transcript else ''
    analysis_formatted = analysis_data.replace('\n', ' ') if analysis_data else ''

    # Append the analysis data with proper newline formatting
    with open(ANALYSIS_CSV, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            video_link,
            transcript_formatted,
            analysis_formatted,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ])

    print(f"Successfully appended analysis data to {ANALYSIS_CSV}")
    return True

def update_email_visibility(email, is_visible):
    """
    Update email visibility setting in database.csv

    Parameters:
    - email: The user's email
    - is_visible: Boolean indicating if the email should be public in searches

    Returns:
    - Boolean indicating success/failure
    """
    print(f"Attempting to update email visibility for {email} to {is_visible}")
    print(f"DATABASE_CSV path: {os.path.abspath(DATABASE_CSV)}")

    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(DATABASE_CSV), exist_ok=True)

    # If file doesn't exist, create it with headers
    if not os.path.exists(DATABASE_CSV):
        print(f"Creating new database file at {DATABASE_CSV}")
        with open(DATABASE_CSV, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['username', 'email', 'password', 'user_type', 'date_registered', 'public_email'])

    try:
        # Read the data file directly with CSV to ensure we handle all fields correctly
        users = []
        headers = []
        user_found = False

        with open(DATABASE_CSV, 'r', newline='') as file:
            reader = csv.reader(file)
            headers = next(reader)  # Get the header row
            print(f"CSV Headers: {headers}")

            # Check if public_email is in headers
            if 'public_email' not in headers:
                print("Adding 'public_email' to headers")
                headers.append('public_email')

            for row in reader:
                print(f"Processing row: {row}")
                # Make sure row has enough elements
                while len(row) < len(headers):
                    row.append('')

                if len(row) > 0 and row[1] == email:  # Email is in column index 1
                    # Find the index of public_email in headers
                    public_email_index = headers.index('public_email')
                    # Update the public_email field
                    row[public_email_index] = str(is_visible)
                    user_found = True
                    print(f"Updated row: {row}")
                users.append(row)

        if not user_found:
            print(f"User with email {email} not found in CSV. Adding user.")
            # Get user info from database and add to CSV
            from app import db
            from models import User
            user = User.query.filter_by(email=email).first()
            if user:
                new_row = [''] * len(headers)
                new_row[0] = user.username
                new_row[1] = user.email
                new_row[2] = user.password_hash
                new_row[3] = user.user_type
                new_row[4] = user.date_registered.strftime('%Y-%m-%d %H:%M:%S')
                new_row[headers.index('public_email')] = str(is_visible)
                users.append(new_row)
                user_found = True
                print(f"Added user to CSV: {new_row}")
            else:
                print(f"Error: User with email {email} not found in database")
                return False

        # Write back the updated data
        with open(DATABASE_CSV, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            writer.writerows(users)

        print(f"Successfully updated email visibility for {email} to {is_visible}")
        return True
    except Exception as e:
        print(f"Error updating email visibility: {e}")
        import traceback
        traceback.print_exc()
        return False

def search_users(query, respect_privacy=True):
    """
    Search for users by username or email

    Parameters:
    - query: Search query string
    - respect_privacy: If True, only returns users with public_email=True

    Returns:
    - List of user dictionaries matching the query
    """
    if not os.path.exists(DATABASE_CSV):
        print(f"Error: {DATABASE_CSV} not found")
        return []

    try:
        # Read the data file directly with CSV to ensure we handle all fields correctly
        users = []
        with open(DATABASE_CSV, 'r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                users.append(row)

        # Apply privacy filter if needed
        if respect_privacy:
            # Only return users with public_email set to True
            users = [user for user in users if str(user.get('public_email', '')).lower() == 'true']

        # Search by username or email
        results = []
        for user in users:
            username = user.get('username', '').lower()
            email = user.get('email', '').lower()
            if query.lower() in username or query.lower() in email:
                results.append(user)

        if not results:
            print(f"No users with public email found matching '{query}'")
            return []

        print(f"Found {len(results)} users matching '{query}'")
        return results
    except Exception as e:
        print(f"Error searching users: {e}")
        import traceback
        traceback.print_exc()
        return []