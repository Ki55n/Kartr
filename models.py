from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# User model for both sponsors and influencers
class User(UserMixin, db.Model):
    __tablename__ = 'users'  # Explicitly define table name to match foreign key reference
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # 'sponsor' or 'influencer'
    date_registered = db.Column(db.DateTime, default=datetime.utcnow)
    email_visible = db.Column(db.Boolean, default=False)  # Flag to control email visibility in search results
    
    # Relationships
    youtube_channels = db.relationship('YouTubeChannel', backref='user', lazy=True)
    # Remove this relationship as it's defined in the Search model
    # searches = db.relationship('Search', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

# YouTube Channel model to store channel data
class YouTubeChannel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    channel_id = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    subscriber_count = db.Column(db.Integer, nullable=True)
    video_count = db.Column(db.Integer, nullable=True)
    view_count = db.Column(db.Integer, nullable=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Updated to match User table name
    
    def __repr__(self):
        return f'<YouTubeChannel {self.title}>'

# Search history model
class Search(db.Model):
    __tablename__ = 'searches'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    search_term = db.Column(db.String(255), nullable=False)
    video_id = db.Column(db.String(20), nullable=True)
    search_type = db.Column(db.String(20), nullable=True)  # Add this field for search type
    date_searched = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship is correctly defined
    user = db.relationship('User', backref=db.backref('searches', lazy=True))
    
    def __repr__(self):
        return f'<Search {self.search_term}>'  # Changed from self.query to self.search_term
