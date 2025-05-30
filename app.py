import os
import logging
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user
from sqlalchemy.orm import DeclarativeBase
from os import environ as env
from dotenv import find_dotenv, load_dotenv
from dotenv import load_dotenv
from post import post_to_bluesky, list_images

# Load environment variables from .env file
load_dotenv()

# ENV_FILE = find_dotenv()
# if ENV_FILE:
#     load_dotenv(ENV_FILE)
# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "kartr_secret_key_for_development")

# Configure database - for development using SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///kartr.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Set YouTube API key from environment variable
app.config["YOUTUBE_API_KEY"] = os.environ.get("YOUTUBE_API_KEY", "")

# Import email configuration if available
try:
    from config import EMAIL_CONFIG
    # Set email configuration in app config
    app.config["EMAIL_USER"] = os.environ.get("EMAIL_USER", EMAIL_CONFIG.get("EMAIL_USER", ""))
    app.config["EMAIL_PASSWORD"] = os.environ.get("EMAIL_PASSWORD", EMAIL_CONFIG.get("EMAIL_PASSWORD", ""))
except ImportError:
    # No config file found, use environment variables only
    app.config["EMAIL_USER"] = os.environ.get("EMAIL_USER", "")
    app.config["EMAIL_PASSWORD"] = os.environ.get("EMAIL_PASSWORD", "")

# Initialize the database with the app
db.init_app(app)

# Set up Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Import models and create tables
with app.app_context():
    from models import User
    db.create_all()
    logger.debug("Database tables created")

# Load user from user ID (required by Flask-Login)
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# --------------------------------------
# API Route: Toggle Email Visibility
# --------------------------------------
@app.route('/api/toggle-email-visibility', methods=['POST'])
@login_required
def toggle_email_visibility():
    """API endpoint to toggle email visibility setting"""
    try:
        logger.debug("Toggle email visibility endpoint called")

        # Log user information
        logger.debug(f"Current user: {current_user.username}, {current_user.email}")

        # Get and validate request data
        data = request.get_json()
        logger.debug(f"Request data: {data}")

        if not data or "email_visible" not in data:
            logger.error("Invalid data in request")
            return jsonify({"error": "Invalid data"}), 400

        is_visible = data["email_visible"]
        logger.debug(f"Setting email visibility to: {is_visible}")

        # Update the database model
        current_user.email_visible = is_visible
        db.session.commit()
        logger.debug("Database updated successfully")

        # Update the CSV file
        from youtube_utils import update_email_visibility
        logger.debug("Calling update_email_visibility function")
        success = update_email_visibility(current_user.email, is_visible)

        if success:
            logger.debug(f"Email visibility successfully set to: {is_visible}")
            return jsonify({"success": True, "email_visible": is_visible}), 200
        else:
            logger.error("Failed to update email visibility in CSV file")
            # Rollback the database change if CSV update failed
            current_user.email_visible = not is_visible
            db.session.commit()
            logger.debug("Database change rolled back")
            return jsonify({"success": False, "message": "Failed to update email visibility in CSV file"}), 500
    except Exception as e:
        logger.error(f"Error in toggle-email-visibility: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Something went wrong: {str(e)}"}), 500



# --------------------------------------
# Optional: Handle 404 errors with JSON
# --------------------------------------
@app.errorhandler(404)
def not_found(e):
    return jsonify(error="Not found"), 404




@app.route('/api/post-to-bluesky', methods=['POST'])
def post_to_bluesky_route():
    return post_to_bluesky()

@app.route('/api/list-images', methods=['GET'])
def list_images_route():
    return list_images()
