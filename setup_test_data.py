import os
import sys
from app import app, db
from models import User, YouTubeChannel
from werkzeug.security import generate_password_hash
from datetime import datetime

def setup_test_users():
    """Set up test users for the application"""
    with app.app_context():
        # Check if users already exist
        if User.query.count() > 0:
            print("Users already exist, skipping test data creation.")
            return
            
        # Create test influencers
        influencer1 = User(
            username="test_influencer1",
            email="influencer1@example.com",
            password_hash=generate_password_hash("password123"),
            user_type="influencer",
            date_registered=datetime.utcnow(),
            email_visible=True  # Public email
        )
        
        influencer2 = User(
            username="test_influencer2",
            email="influencer2@example.com",
            password_hash=generate_password_hash("password123"),
            user_type="influencer",
            date_registered=datetime.utcnow(),
            email_visible=False  # Private email
        )
        
        # Create test sponsors
        sponsor1 = User(
            username="test_sponsor1",
            email="sponsor1@example.com",
            password_hash=generate_password_hash("password123"),
            user_type="sponsor",
            date_registered=datetime.utcnow(),
            email_visible=True  # Public email
        )
        
        sponsor2 = User(
            username="test_sponsor2",
            email="sponsor2@example.com",
            password_hash=generate_password_hash("password123"),
            user_type="sponsor",
            date_registered=datetime.utcnow(),
            email_visible=False  # Private email
        )
        
        # Add users to database
        db.session.add(influencer1)
        db.session.add(influencer2)
        db.session.add(sponsor1)
        db.session.add(sponsor2)
        
        # Create test YouTube channels
        channel1 = YouTubeChannel(
            channel_id="UC1234567890",
            title="Tech Reviews",
            subscriber_count=100000,
            video_count=200,
            view_count=5000000,
            date_added=datetime.utcnow(),
            user_id=1
        )
        
        channel2 = YouTubeChannel(
            channel_id="UC0987654321",
            title="Gaming Adventures",
            subscriber_count=50000,
            video_count=150,
            view_count=2500000,
            date_added=datetime.utcnow(),
            user_id=2
        )
        
        # Add channels to database
        db.session.add(channel1)
        db.session.add(channel2)
        
        # Commit changes
        db.session.commit()
        
        print("Test users and channels created successfully!")
        
if __name__ == "__main__":
    setup_test_users()