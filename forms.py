from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Regexp
from models import User
import re

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(), 
        Length(min=8, message="Password must be at least 8 characters long")
    ])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    user_type = SelectField('Account Type', choices=[('influencer', 'Influencer'), ('sponsor', 'Sponsor')], validators=[DataRequired()])
    submit = SubmitField('Sign Up')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
            
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one or login.')
            
    def validate_password(self, password):
        """
        Validate password complexity:
        - At least 8 characters
        - At least 3 of the following: lowercase, uppercase, numbers, special characters
        """
        pwd = password.data
        
        # Check length (already done by Length validator, but we'll check again)
        if len(pwd) < 8:
            raise ValidationError('Password must be at least 8 characters long.')
            
        # Check complexity
        complexity_count = 0
        if re.search(r'[a-z]', pwd):  # Has lowercase
            complexity_count += 1
        if re.search(r'[A-Z]', pwd):  # Has uppercase
            complexity_count += 1
        if re.search(r'[0-9]', pwd):  # Has number
            complexity_count += 1
        if re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', pwd):  # Has special char
            complexity_count += 1
            
        if complexity_count < 3:
            raise ValidationError('Password must include at least 3 of the following: lowercase letters, uppercase letters, numbers, and special characters.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Link')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if not user:
            raise ValidationError('Email not registered. Please check your email or register.')

class OTPVerificationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    otp = StringField('OTP', validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField('Verify & Login')

class YouTubeStatsForm(FlaskForm):
    youtube_url = StringField('YouTube URL', validators=[DataRequired()])
    submit = SubmitField('Analyze')

class YouTubeDemoForm(FlaskForm):
    youtube_url = StringField('YouTube URL', validators=[DataRequired()])
    submit = SubmitField('Extract Info')
