"""
Firebase Configuration

This file contains the Firebase configuration and initialization code.
"""
import pyrebase
import logging

logger = logging.getLogger(__name__)

# Firebase configuration
config = {
    'apiKey': "AIzaSyAXAM1-aFmM-_nBXyfhgar1uoJ25N3Yvyg",
    'authDomain': "influencerkartr.firebaseapp.com",
    'projectId': "influencerkartr",
    'storageBucket': "influencerkartr.firebasestorage.app",
    'messagingSenderId': "3408915311",
    'appId': "1:3408915311:web:f3431d19508025872a969a",
    'measurementId': "G-SW7VBFSCRY",
    'databaseURL': ""
}

# Initialize Firebase
try:
    firebase = pyrebase.initialize_app(config)
    auth = firebase.auth()
    logger.info("Firebase initialized successfully")
except Exception as e:
    logger.error(f"Error initializing Firebase: {str(e)}")
    firebase = None
    auth = None