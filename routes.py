import logging
import os
import subprocess
import pandas as pd
from datetime import datetime
from flask import render_template, url_for, flash, redirect, request, jsonify, session
from flask_login import login_user, current_user, logout_user, login_required
from app import app, db
from forms import RegistrationForm, LoginForm, YouTubeStatsForm, YouTubeDemoForm, ForgotPasswordForm, OTPVerificationForm
from models import User, YouTubeChannel, Search
from youtube_api import get_video_stats, get_channel_stats, extract_video_info
from youtube_utils import save_user_to_csv, validate_user_login, save_analysis_to_csv
from googleapiclient.discovery import build
from os import environ as env
from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from urllib.parse import quote_plus, urlencode

from email_utils import generate_otp, store_otp, verify_otp, send_otp_email

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)
oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration',
)
@app.route('/contact')
def contact():
    """Route for the contact us page"""
    return render_template('contact.html', title='Contact Us')

@app.route('/')
@app.route('/home')
def home():
    """Route for the landing page"""
    if current_user.is_authenticated:
        return redirect(url_for('stats'))

    # Get real-time stats from database.csv
    stats = get_platform_stats()
    return render_template('landing.html', title='Kartr - Connect Influencers and Sponsors', stats=stats)

@app.route('/landing')
def landing():
    """Explicit route for the landing page"""
    if current_user.is_authenticated:
        return redirect(url_for('stats'))

    # Get real-time stats from database.csv
    stats = get_platform_stats()
    return render_template('landing.html', title='Kartr - Connect Influencers and Sponsors', stats=stats)

def get_platform_stats():
    """Get real-time platform statistics from database.csv"""
    try:
        import pandas as pd
        import os

        # Check if database.csv exists
        db_path = os.path.join('data', 'database.csv')
        if not os.path.exists(db_path):
            logger.warning(f"Database file not found at {db_path}")
            return {
                'influencers': 0,
                'sponsors': 0,
                'total_users': 0
            }

        # Read the CSV file
        df = pd.read_csv(db_path)

        # Count users by type
        influencers = len(df[df['user_type'] == 'influencer'])
        sponsors = len(df[df['user_type'] == 'sponsor'])
        total_users = len(df)

        # Get stats from analysis.csv if it exists
        analysis_path = os.path.join('data', 'ANALYSIS.CSV')
        partnerships = 0
        if os.path.exists(analysis_path):
            try:
                analysis_df = pd.read_csv(analysis_path)
                # Count unique partnerships (this is an estimate based on available data)
                partnerships = len(analysis_df)
            except Exception as e:
                logger.error(f"Error reading analysis.csv: {str(e)}")

        return {
            'influencers': influencers,
            'sponsors': sponsors,
            'total_users': total_users,
            'partnerships': partnerships
        }
    except Exception as e:
        logger.error(f"Error getting platform stats: {str(e)}")
        return {
            'influencers': 0,
            'sponsors': 0,
            'total_users': 0,
            'partnerships': 0
        }

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('stats'))

    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # First create user in local database
            user = User(username=form.username.data, email=form.email.data, user_type=form.user_type.data)
            user.set_password(form.password.data)  # Hash password for local auth

            # Save to database
            db.session.add(user)
            db.session.commit()

            # Also save to CSV file for validation
            save_user_to_csv(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data,
                user_type=form.user_type.data
            )

            # Try to create user in Auth0 (but don't block registration if it fails)
            try:
                # Import Auth0 helper functions
                from auth0_helpers import create_auth0_user
                from auth0_config import config as auth0_config

                # Create user in Auth0
                success, auth0_user = create_auth0_user(
                    email=form.email.data,
                    password=form.password.data,
                    username=form.username.data
                )

                if not success:
                    # If Auth0 registration fails, log the error but continue with local registration
                    if hasattr(auth0_config, 'last_auth_error') and auth0_config.last_auth_error:
                        if 'already exists' in auth0_config.last_auth_error.lower():
                            logger.info(f"User {form.email.data} already exists in Auth0")
                        elif 'connection' in auth0_config.last_auth_error.lower():
                            logger.error(f"Auth0 connection error: {auth0_config.last_auth_error}")
                            flash('Account created locally. Auth0 integration is currently unavailable.', 'warning')
                        else:
                            logger.error(f"Auth0 registration error: {auth0_config.last_auth_error}")
                    else:
                        logger.warning("Auth0 registration failed without specific error")
                else:
                    logger.info(f"User {form.email.data} successfully registered in Auth0")
            except ImportError:
                logger.warning("Auth0 helpers module could not be imported")
                flash('Account created locally. Auth0 integration is currently unavailable.', 'warning')
            except Exception as auth0_err:
                logger.error(f"Error during Auth0 registration: {str(auth0_err)}")
                flash('Account created locally. Auth0 integration encountered an error.', 'warning')

            flash(f'Account created for {form.username.data}! You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            logger.error(f"Error during registration: {str(e)}")
            flash(f'Error during registration. Please try again.', 'danger')

    return render_template('register.html', title='Register', form=form)

@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    user_info = oauth.auth0.userinfo()

    session["user"] = user_info
    user = User.query.filter_by(email=user_info["email"]).first()
    if not user:
        user = User(username=user_info["nickname"], email=user_info["email"],password_hash=user_info["nickname"],user_type=user_info["nickname"])
        db.session.add(user)
        db.session.commit()

    # Log in the user using Flask-Login
    login_user(user)
    return redirect(url_for('stats'))

@app.route('/googleLogin',methods=['GET','POST'])
def googleLogin():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback",_external=True)
    )
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('stats'))

    form = LoginForm()
    if form.validate_on_submit():
        # First try local authentication directly
        user = User.query.filter_by(email=form.email.data).first()

        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('stats'))

        # If local authentication fails, try CSV validation
        is_valid, user_type = validate_user_login(form.email.data, form.password.data)
        if is_valid:
            # Create a user in the database if not exists
            if not user:
                try:
                    # Try to get username from CSV if available
                    username = form.email.data.split('@')[0] if '@' in form.email.data else form.email.data

                    try:
                        df = pd.read_csv('data/database.csv')
                        user_data = df[df['email'] == form.email.data]
                        if not user_data.empty:
                            username = user_data.iloc[0]['username']
                    except Exception as csv_error:
                        logger.warning(f"Could not read from CSV: {str(csv_error)}")
                    
                    # Create user in database
                    user = User(username=username, email=form.email.data, user_type=user_type)
                    user.set_password(form.password.data)
                    db.session.add(user)
                    db.session.commit()
                    
                    # Get the user again
                    user = User.query.filter_by(email=form.email.data).first()

                    if user:
                        login_user(user)
                        flash('Login successful via CSV validation!', 'success')
                        return redirect(url_for('stats'))
                except Exception as e:
                    logger.error(f"Error creating user from CSV: {str(e)}")
                    flash('Error during login. Please try again.', 'danger')
                    return render_template('login.html', title='Login', form=form)

        # If local and CSV authentication fails, try Auth0
        try:
            # Import Auth0 helper functions
            from auth0_helpers import user_exists_in_auth0
            from auth0_config import config as auth0_config

            # Try to authenticate with Auth0
            exists, auth0_user = user_exists_in_auth0(
                email=form.email.data,
                password=form.password.data
            )

            if exists and auth0_user:
                # If Auth0 authentication is successful, check if user exists in our database
                user = User.query.filter_by(email=form.email.data).first()
                
                if user:
                    # User exists in our database, log them in
                    login_user(user)
                    flash('Login successful via Auth0!', 'success')
                    return redirect(url_for('stats'))
                else:
                    # User exists in Auth0 but not in our database
                    # Create a new user in our database
                    try:
                        # Try to get username and user_type from CSV if available
                        username = form.email.data.split('@')[0] if '@' in form.email.data else form.email.data
                        user_type = 'influencer'  # Default

                        try:
                            df = pd.read_csv('data/database.csv')
                            user_data = df[df['email'] == form.email.data]
                            if not user_data.empty:
                                username = user_data.iloc[0]['username']
                                user_type = user_data.iloc[0]['user_type']
                        except Exception as csv_error:
                            logger.warning(f"Could not read from CSV: {str(csv_error)}")

                        # Create user in database
                        user = User(username=username, email=form.email.data, user_type=user_type)
                        user.set_password(form.password.data)  # Still hash password for local auth
                        db.session.add(user)
                        db.session.commit()

                        # Log in the user
                        login_user(user)
                        flash('Login successful via Auth0!', 'success')
                        return redirect(url_for('stats'))
                    except Exception as e:
                        logger.error(f"Error creating user from Auth0: {str(e)}")
                        flash('Error during login. Please try again.', 'danger')
                        return render_template('login.html', title='Login', form=form)
            else:
                # Check if this is a connection configuration error
                if hasattr(auth0_config, 'last_auth_error') and auth0_config.last_auth_error and 'connection' in auth0_config.last_auth_error.lower():
                    logger.error(f"Auth0 connection error: {auth0_config.last_auth_error}")
                    flash('Authentication service configuration error. Please contact support.', 'danger')
                else:
                    flash('Invalid email or password.', 'danger')

        except ImportError:
            logger.error("Auth0 helpers module could not be imported")
            flash('Authentication service unavailable. Using local authentication only.', 'warning')
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            if "connection" in str(e).lower() or "auth0" in str(e).lower():
                flash('Authentication service temporarily unavailable. Please try again later.', 'warning')
            else:
                flash('Invalid email or password.', 'danger')

    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    session.clear()
    return redirect(
        f'https://{env.get("AUTH0_DOMAIN")}/v2/logout?'
        + urlencode({
            'returnTo': url_for('home', _external=True),
            'client_id': env.get("AUTH0_CLIENT_ID"),
        })
    )

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('stats'))
    
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        
        if user:
            try:
                # Import Auth0 helper functions
                from auth0_helpers import send_password_reset_email
                
                # Send password reset email via Auth0
                success, error_message = send_password_reset_email(email)

                if success:
                    flash('Password reset link has been sent. Please check your inbox and follow the instructions.', 'success')
                    return redirect(url_for('login'))
                else:
                    logger.error(f"Auth0 password reset error: {error_message}")

                    # Fall back to OTP method if Auth0 fails
                    # Generate OTP
                    otp = generate_otp()

                    # Store OTP with expiration time
                    if store_otp(email, otp):
                        # Send OTP to user's email
                        success, message = send_otp_email(email, otp)

                        if success:
                            flash('OTP has been sent to your email. Please check your inbox.', 'success')
                            # Create OTP verification form with email pre-filled
                            verify_form = OTPVerificationForm()
                            verify_form.email.data = email
                            return render_template('verify_otp.html', form=verify_form)
                        else:
                            flash(f'Failed to send OTP: {message}. Please try again.', 'danger')
                    else:
                        flash('Failed to generate OTP. Please try again.', 'danger')
            except Exception as e:
                logger.error(f"Password reset error: {str(e)}")

                # Fall back to OTP method
                otp = generate_otp()
                
                # Store OTP with expiration time
                if store_otp(email, otp):
                    # Send OTP to user's email
                    success, message = send_otp_email(email, otp)
                    
                    if success:
                        flash('OTP has been sent to your email. Please check your inbox.', 'success')
                        # Create OTP verification form with email pre-filled
                        verify_form = OTPVerificationForm()
                        verify_form.email.data = email
                        return render_template('verify_otp.html', form=verify_form)
                    else:
                        flash(f'Failed to send OTP: {message}. Please try again.', 'danger')
                else:
                    flash('Failed to generate OTP. Please try again.', 'danger')
        else:
            flash('Email not found. Please check your email or register.', 'danger')
    
    return render_template('forgot_password.html', title='Forgot Password', form=form)

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if current_user.is_authenticated:
        return redirect(url_for('stats'))
    
    form = OTPVerificationForm()
    
    if form.validate_on_submit():
        email = form.email.data
        otp = form.otp.data
        
        # Verify OTP
        if verify_otp(email, otp):
            # OTP is valid, log in the user
            user = User.query.filter_by(email=email).first()
            
            if user:
                login_user(user)
                flash('Login successful via OTP!', 'success')
                return redirect(url_for('stats'))
            else:
                flash('User not found. Please register.', 'danger')
                return redirect(url_for('register'))
        else:
            flash('Invalid or expired OTP. Please try again.', 'danger')
    
    return render_template('verify_otp.html', title='Verify OTP', form=form)


# Keep the old route for backward compatibility, redirecting to the new one
@app.route('/dashboard')
@login_required
def dashboard():
    return redirect(url_for('visualizations'))

@app.route('/stats', methods=['GET', 'POST'])
@login_required
def stats():
    form = YouTubeStatsForm()
    video_stats = None
    channel_stats = None
    error = None
    is_first_time = False
    auto_update = False

    # Check if user has any YouTube channels
    user_channels = YouTubeChannel.query.filter_by(user_id=current_user.id).all()
    
    # If user has no channels and is an influencer, this is their first time
    if not user_channels and current_user.user_type == 'influencer':
        is_first_time = True
        flash('Welcome! Please enter your YouTube channel URL to get started.', 'info')
    
    # If user has channels, check if we need to auto-update
    elif user_channels and current_user.user_type == 'influencer':
        # Check if any channel needs updating (older than 24 hours)
        for channel in user_channels:
            if (datetime.utcnow() - channel.date_updated).total_seconds() > 86400:  # 24 hours
                auto_update = True
                break
    
    if form.validate_on_submit():
        youtube_url = form.youtube_url.data
        try:
            # Get video stats
            video_data = get_video_stats(youtube_url)
            if video_data:
                video_stats = video_data

                # Get channel stats using the enhanced stats.py
                from stats import get_channel_stats, API_KEY
                channel_data = get_channel_stats(youtube_url, API_KEY)
                
                if isinstance(channel_data, dict):  # Make sure we got valid data
                    channel_stats = channel_data

                    # Save the search
                    try:
                        # Only use fields that exist in the database
                        search = Search(
                            user_id=current_user.id,
                            search_term=youtube_url,
                            date_searched=datetime.utcnow()
                        )
                        db.session.add(search)
                        db.session.commit()
                    except Exception as e:
                        db.session.rollback()
                        logger.error(f"Error saving search history: {str(e)}")

                    # Check if channel already exists
                    existing_channel = YouTubeChannel.query.filter_by(
                        channel_id=channel_data['channel_id'],
                        user_id=current_user.id
                    ).first()

                    if not existing_channel:
                        # Save channel data
                        new_channel = YouTubeChannel(
                            channel_id=channel_data['channel_id'],
                            title=channel_data['title'],
                            subscriber_count=channel_data['subscriber_count'],
                            video_count=channel_data['video_count'],
                            view_count=channel_data['view_count'],
                            user_id=current_user.id
                        )
                        db.session.add(new_channel)
                        flash('Channel added successfully!', 'success')
                    else:
                        # Update existing channel
                        existing_channel.subscriber_count = channel_data['subscriber_count']
                        existing_channel.video_count = channel_data['video_count']
                        existing_channel.view_count = channel_data['view_count']
                        existing_channel.date_updated = datetime.utcnow()
                        flash('Channel statistics updated!', 'success')

                    db.session.commit()

                    # We're not saving stats data to ANALYSIS.CSV anymore
                    # ANALYSIS.CSV is only updated from the demo page
                else:
                    error = "Could not retrieve channel information."
            else:
                error = "Could not retrieve video information."
        except Exception as e:
            logger.error(f"Error processing YouTube URL: {str(e)}")
            error = f"Error processing YouTube URL: {str(e)}"
    
    # Auto-update channel statistics if needed
    elif auto_update and user_channels:
        try:
            from stats import get_channel_stats
            api_key = app.config.get('YOUTUBE_API_KEY', '')
            if not api_key:
                logger.warning("YouTube API key not set. Please add it to your environment variables.")
                
            for channel in user_channels:
                channel_url = f"https://www.youtube.com/channel/{channel.channel_id}"
                channel_data = get_channel_stats(channel_url, api_key)
                
                if isinstance(channel_data, dict):
                    # Update channel data
                    channel.subscriber_count = channel_data['subscriber_count']
                    channel.video_count = channel_data['video_count']
                    channel.view_count = channel_data['view_count']
                    channel.date_updated = datetime.utcnow()
                    
                    # Get the most recent video for stats
                    if channel_data.get('recent_videos'):
                        video_id = channel_data['recent_videos'][0]['video_id']
                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                        video_data = get_video_stats(video_url)
                        if video_data:
                            video_stats = video_data
                            channel_stats = channel_data
                            break
            
            db.session.commit()
            flash('Channel statistics automatically updated!', 'success')
        except Exception as e:
            logger.error(f"Error auto-updating channel statistics: {str(e)}")
            flash('Could not automatically update channel statistics.', 'warning')
    
    # If user has channels but no video_stats, get the most recent video
    elif user_channels and not video_stats:
        try:
            # Get the most recently updated channel
            recent_channel = max(user_channels, key=lambda x: x.date_updated)
            
            # Get recent videos for this channel
            from stats import get_recent_videos
            api_key = app.config.get('YOUTUBE_API_KEY', '')
            if not api_key:
                logger.warning("YouTube API key not set. Please add it to your environment variables.")
                flash('YouTube API key is not set. Some features may not work properly.', 'warning')
                return render_template('stats.html', title='YouTube Stats', form=form)
            
            youtube = build('youtube', 'v3', developerKey=api_key)
            
            recent_videos = get_recent_videos(youtube, recent_channel.channel_id, api_key)
            
            if recent_videos:
                video_id = recent_videos[0]['video_id']
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                video_data = get_video_stats(video_url)
                
                if video_data:
                    video_stats = video_data
                    
                    # Get channel stats
                    from stats import get_channel_stats
                    channel_url = f"https://www.youtube.com/channel/{recent_channel.channel_id}"
                    channel_data = get_channel_stats(channel_url, api_key)
                    
                    if isinstance(channel_data, dict):
                        channel_stats = channel_data
        except Exception as e:
            logger.error(f"Error getting recent video: {str(e)}")

    return render_template('stats.html', title='YouTube Stats', 
                          form=form, 
                          video_stats=video_stats, 
                          channel_stats=channel_stats,
                          error=error,
                          user_type=current_user.user_type,
                          is_first_time=is_first_time,
                          auto_update=auto_update,
                          min=min)  # Add the min function to the template context

@app.route('/demo', methods=['GET', 'POST'])
@login_required
def demo():
    form = YouTubeDemoForm()
    video_info = None
    error = None

    if form.validate_on_submit():
        youtube_url = form.youtube_url.data
        try:
            # Extract information from the video using youtube_api.py
            info = extract_video_info(youtube_url)
            if info:
                video_info = info

                # Save the search
                try:
                    # Try to create a Search with only the columns that exist in the database
                    search = Search(
                        user_id=current_user.id,
                        search_term=youtube_url,  # Changed from url to youtube_url
                        date_searched=datetime.utcnow()
                    )
                    db.session.add(search)
                    db.session.commit()
                except Exception as e:
                    # If there's an error, roll back the session
                    db.session.rollback()
                    print(f"Error saving search history: {str(e)}")

                # Also run demo.py functionality to extract transcript and save to ANALYSIS.CSV
                try:
                    # Use the analyze_influencer_sponsors function from demo.py
                    result = analyze_influencer_sponsors(youtube_url)
                    if result and not "error" in result:
                        # Add influencer analysis to video_info
                        video_info['influencer_analysis'] = result
                        logger.info(f"Added influencer analysis for URL: {youtube_url}")
                except Exception as demo_error:
                    logger.error(f"Error running influencer analysis: {str(demo_error)}")
            else:
                error = "Could not extract information from the video."
        except Exception as e:
            logger.error(f"Error extracting video info: {str(e)}")
            error = f"Error extracting video info: {str(e)}"

    return render_template('demo.html', title='YouTube Demo',
                          form=form, 
                          video_info=video_info,
                          min=min)

# Virtual Influencer routes
@app.route('/virtual-influencer')
@login_required
def virtual_influencer():
    # Import from virtual_influencer.py
    from virtual_influencer import get_available_virtual_influencers
    
    # Get available virtual influencers
    influencers = get_available_virtual_influencers()
    
    return render_template('virtual_influencer.html', 
                          title='Rent a Virtual Influencer',
                          influencers=influencers)

@app.route('/social-media-agents')
@login_required
def social_media_agents():
    # Import from social_media_agents.py
    from social_media_agents import get_available_agents
    
    # Get available social media agents
    agents = get_available_agents()
    
    return render_template('social_media_agents.html',
                          title='Social Media Agents',
                          agents=agents)

@app.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('visualizations'))
    
    # Search in YouTube channels
    channels = YouTubeChannel.query.filter(
        YouTubeChannel.title.ilike(f'%{query}%')
    ).all()
    
    # Save the search to the database
    search = Search(
        user_id=current_user.id,
        search_term=query,
        date_searched=datetime.utcnow()
    )
    db.session.add(search)
    db.session.commit()
    
    # Get searchable users from database.csv (those with public_email enabled)
    users = []
    # Define the database CSV path
    DATABASE_CSV = os.path.join(os.getcwd(), 'data/database.csv')
    
    if os.path.exists(DATABASE_CSV):
        try:
            import pandas as pd
            df = pd.read_csv(DATABASE_CSV)
            # Filter users with public email that match query
            if 'public_email' in df.columns:
                # Only show users who have toggled public_email to True
                user_matches = df[
                    (df['username'].str.contains(query, case=False, na=False) | 
                     df['email'].str.contains(query, case=False, na=False)) &
                    (df['public_email'].astype(str) == 'True')
                ]
                
                if not user_matches.empty:
                    # Convert to dictionary records
                    users = user_matches.to_dict('records')
                    
                    # Debug logging
                    logger.debug(f"Found {len(users)} users with public email matching '{query}'")
                else:
                    logger.debug(f"No users with public email found matching '{query}'")
            else:
                logger.warning("public_email column not found in database.csv")
        except Exception as e:
            logger.error(f"Error searching users in CSV: {str(e)}")
    
    return render_template('search_results.html', 
                         title='Search Results',
                         query=query,
                         channels=channels,
                         users=users)

@app.route('/api/search_suggestions', methods=['GET'])
def api_search_suggestions():
    """API endpoint for search suggestions (autocomplete)"""
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    suggestions = []
    
    # Get YouTube channel suggestions
    channels = YouTubeChannel.query.filter(
        YouTubeChannel.title.ilike(f'%{query}%')
    ).limit(5).all()
    
    for channel in channels:
        suggestions.append({
            'id': f"channel_{channel.id}",
            'text': channel.title,
            'type': 'channel'
        })
    
    # Get user suggestions from database.csv (respecting privacy settings)
    from youtube_utils import search_users
    user_results = search_users(query, respect_privacy=True)
    
    for user in user_results:
        suggestions.append({
            'id': f"user_{user.get('username')}",
            'text': user.get('username'),
            'email': user.get('email'),
            'type': user.get('user_type')
        })
    
    return jsonify(suggestions)

    
# Import functions from demo.py - fix the imports to match what's actually in demo.py
from demo import analyze_influencer_sponsors, batch_analyze_channel

# Add these functions to your demo.py file or import them from elsewhere if they exist
import csv

@app.route('/analyze_video', methods=['POST'])
@login_required
def analyze_video():
    """Analyze a YouTube video for influencer and sponsor information"""
    data = request.json
    video_url = data.get('video_url')
    
    if not video_url:
        return jsonify({"error": "No video URL provided"}), 400
    
    try:
        # Use the analyze_influencer_sponsors function from demo.py
        result = analyze_influencer_sponsors(video_url)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analyze_channel', methods=['POST'])
def analyze_channel():
    """Analyze a YouTube channel for influencer and sponsor information"""
    data = request.json
    channel_id = data.get('channel_id')
    max_videos = int(data.get('max_videos', 5))
    
    if not channel_id:
        return jsonify({"error": "No channel ID provided"}), 400
    
    try:
        # Use the batch_analyze_channel function from demo.py
        result = batch_analyze_channel(channel_id, max_videos=max_videos)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/save_analysis', methods=['POST'])
def save_analysis():
    """Save analysis data to CSV file"""
    data = request.json
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # CSV file path
    csv_file = 'data/analysis_results.csv'
    file_exists = os.path.isfile(csv_file)
    
    try:
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header if file doesn't exist
            if not file_exists:
                writer.writerow([
                    'Date', 'User ID', 'Video/Channel Title', 'Channel Name',
                    'Creator Name', 'Creator Industry', 'Sponsor Name', 'Sponsor Industry'
                ])
            
            # Write creator row with no sponsor
            if not data.get('sponsors'):
                writer.writerow([
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    current_user.id,
                    data.get('video_title', 'Unknown'),
                    data.get('channel_name', 'Unknown'),
                    data.get('creator_name', 'Unknown'),
                    data.get('creator_industry', 'Unknown'),
                    'No Sponsor',
                    'N/A'
                ])
            else:
                # Write a row for each sponsor
                for sponsor in data.get('sponsors', []):
                    writer.writerow([
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        current_user.id,
                        data.get('video_title', 'Unknown'),
                        data.get('channel_name', 'Unknown'),
                        data.get('creator_name', 'Unknown'),
                        data.get('creator_industry', 'Unknown'),
                        sponsor.get('name', 'Unknown'),
                        sponsor.get('industry', 'Unknown')
                    ])
        
        return jsonify({"success": True, "message": "Analysis saved to CSV"})
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500



@app.route('/api/creator_sponsor_graph')
def api_creator_sponsor_graph():
    return jsonify(load_creator_sponsor_graph())

@app.route('/api/industry_graph')
def api_industry_graph():
    return jsonify(load_industry_graph())



from gemini_imagen import generate_image_llm


from video_creator import create_promotional_image_colab, enhance_prompt_with_brand

@app.route('/generate_image', methods=['POST'])
def generate_image():
    face_image = request.files.get('face_image')
    brand_image = request.files.get('brand_image')
    prompt = request.form.get('prompt')
    brand_name = request.form.get('brand_name', 'YourBrand')

    if not all([face_image, brand_image, prompt]):
        return jsonify({'error': 'Missing required fields'}), 400

    # Save images temporarily
    face_path = 'temp_face.png'
    brand_path = 'temp_brand.png'
    face_image.save(face_path)
    brand_image.save(brand_path)

    prompt = enhance_prompt_with_brand(prompt, brand_name)

    try:
        result = create_promotional_image_colab(
            face_path,
            brand_path,
            prompt,
            brand_name
        )
        if 'image_base64' in result:
            return jsonify({'image_base64': result['image_base64']})
        else:
            return jsonify({'error': result.get('error', 'Unknown error from backend.')})
    finally:
        # Clean up temp files
        if os.path.exists(face_path):
            os.remove(face_path)
        if os.path.exists(brand_path):
            os.remove(brand_path)

@app.route('/generate_llm_influencer', methods=['POST'])
def generate_llm_influencer():
    data = request.get_json()
    prompt = data.get('prompt')
    if not prompt:
        return jsonify({"error": "Prompt is required."}), 400
    result = generate_image_llm(prompt)
    return jsonify(result)




from graph import load_creator_sponsor_graph, load_industry_graph
@app.route('/visualization')
def visualization():
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)

    # CSV file path
    csv_file = 'data/analysis_results.csv'
    file_exists = os.path.isfile(csv_file)

    with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Write header if file doesn't exist
            if not file_exists:
                writer.writerow([
                    'Date', 'User ID', 'Video/Channel Title', 'Channel Name',
                    'Creator Name', 'Creator Industry', 'Sponsor Name', 'Sponsor Industry'
                ])

    return render_template('visualization.html')






from flask import request, jsonify

@app.route('/ask_graph_question', methods=['POST'])
def ask_graph_question():
    question = request.json.get('question', '')
    # TODO: Implement retrieval/answer logic based on your graph data
    answer = f"You asked: {question} (answer logic goes here)"
    return jsonify({'answer': answer})

from rag_ques import retrieve_relevant_rows, generate_gemini_answer

@app.route('/ask_question', methods=['POST'])
def ask_question():
    data = request.get_json()
    question = data.get('question', '')
    results = retrieve_relevant_rows(question)
    context = results.to_string(index=False) if not results.empty else "No relevant data found."
    answer = generate_gemini_answer(question, context)
    return jsonify({'answer': answer})



