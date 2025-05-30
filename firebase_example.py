"""
Simple Firebase Authentication Example

This is a standalone Flask application that demonstrates basic Firebase Authentication.
You can run this separately from your main application to test Firebase functionality.

Features:
- User sign up (registration)
- User sign in (login)
- User logout
- Forgot password

To run:
python firebase_example_simple.py
"""

from flask import Flask, session, render_template_string, request, redirect, flash
import pyrebase

app = Flask(__name__)
app.secret_key = "firebase_secret_key"

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
firebase = pyrebase.initialize_app(config=config)
auth = firebase.auth()

# HTML template for all pages
template = """
<!DOCTYPE html>
<html>
<head>
    <title>Firebase Auth Example</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #f5f7fa 0%, #e4efe9 100%);
            background-attachment: fixed;
        }
        .container {
            border: 1px solid #ddd;
            padding: 20px;
            border-radius: 10px;
            background-color: rgba(255, 255, 255, 0.9);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
        }
        input[type="email"], input[type="password"] {
            width: 100%;
            padding: 10px;
            box-sizing: border-box;
            border: 1px solid #ddd;
            border-radius: 5px;
            transition: border 0.3s;
        }
        input[type="email"]:focus, input[type="password"]:focus {
            border-color: #4CAF50;
            outline: none;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: #3e8e41;
        }
        .error {
            color: #e74c3c;
            margin-bottom: 15px;
            padding: 8px;
            background-color: rgba(231, 76, 60, 0.1);
            border-radius: 4px;
        }
        .success {
            color: #2ecc71;
            margin-bottom: 15px;
            padding: 8px;
            background-color: rgba(46, 204, 113, 0.1);
            border-radius: 4px;
        }
        .tabs {
            display: flex;
            margin-bottom: 20px;
        }
        .tab {
            padding: 10px 20px;
            cursor: pointer;
            border: 1px solid #ddd;
            background-color: #f1f1f1;
            transition: background-color 0.3s;
        }
        .tab:hover {
            background-color: #e9e9e9;
        }
        .tab.active {
            background-color: #fff;
            border-bottom: none;
        }
        #register-form, #forgot-password-form {
            display: none;
        }
        .forgot-password-link {
            display: block;
            text-align: right;
            margin-top: 5px;
            font-size: 0.9em;
            color: #3498db;
            text-decoration: none;
        }
        .forgot-password-link:hover {
            text-decoration: underline;
        }
        .social-icons {
            display: flex;
            justify-content: center;
            margin-top: 20px;
            gap: 15px;
        }
        .social-icon {
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            color: white;
            font-size: 20px;
            transition: transform 0.3s;
        }
        .social-icon:hover {
            transform: scale(1.1);
        }
        .facebook {
            background-color: #3b5998;
        }
        .twitter {
            background-color: #1da1f2;
        }
        .instagram {
            background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%);
        }
        .linkedin {
            background-color: #0077b5;
        }
        .youtube {
            background-color: #ff0000;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Firebase Authentication Example</h1>
        
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        
        {% if success %}
        <div class="success">{{ success }}</div>
        {% endif %}
        
        {% if user %}
            <h2>Welcome, {{ user }}</h2>
            <p>You are logged in with Firebase Authentication.</p>
            <a href="/logout"><button>Logout</button></a>
        {% else %}
            <div class="tabs">
                <div class="tab active" id="login-tab" onclick="showLogin()">Login</div>
                <div class="tab" id="register-tab" onclick="showRegister()">Register</div>
                <div class="tab" id="forgot-password-tab" onclick="showForgotPassword()">Forgot Password</div>
            </div>
            
            <form id="login-form" method="POST" action="/login">
                <div class="form-group">
                    <label for="email">Email:</label>
                    <input type="email" id="email" name="email" required>
                </div>
                <div class="form-group">
                    <label for="password">Password:</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <button type="submit">Login</button>
            </form>
            
            <form id="register-form" method="POST" action="/register">
                <div class="form-group">
                    <label for="reg-email">Email:</label>
                    <input type="email" id="reg-email" name="email" required>
                </div>
                <div class="form-group">
                    <label for="reg-password">Password:</label>
                    <input type="password" id="reg-password" name="password" required>
                </div>
                <div class="form-group">
                    <label for="confirm-password">Confirm Password:</label>
                    <input type="password" id="confirm-password" name="confirm_password" required>
                </div>
                <button type="submit">Register</button>
            </form>
            
            <form id="forgot-password-form" method="POST" action="/reset-password">
                <div class="form-group">
                    <label for="reset-email">Email:</label>
                    <input type="email" id="reset-email" name="email" required>
                </div>
                <button type="submit">Send Reset Link</button>
            </form>
        {% endif %}
        
        <div class="social-icons">
            <a href="#" class="social-icon facebook"><i class="fab fa-facebook-f"></i></a>
            <a href="#" class="social-icon twitter"><i class="fab fa-twitter"></i></a>
            <a href="#" class="social-icon instagram"><i class="fab fa-instagram"></i></a>
            <a href="#" class="social-icon linkedin"><i class="fab fa-linkedin-in"></i></a>
            <a href="#" class="social-icon youtube"><i class="fab fa-youtube"></i></a>
        </div>
    </div>
    
    <script>
        function showLogin() {
            document.getElementById('login-form').style.display = 'block';
            document.getElementById('register-form').style.display = 'none';
            document.getElementById('forgot-password-form').style.display = 'none';
            document.getElementById('login-tab').classList.add('active');
            document.getElementById('register-tab').classList.remove('active');
            document.getElementById('forgot-password-tab').classList.remove('active');
        }
        
        function showRegister() {
            document.getElementById('login-form').style.display = 'none';
            document.getElementById('register-form').style.display = 'block';
            document.getElementById('forgot-password-form').style.display = 'none';
            document.getElementById('login-tab').classList.remove('active');
            document.getElementById('register-tab').classList.add('active');
            document.getElementById('forgot-password-tab').classList.remove('active');
        }
        
        function showForgotPassword() {
            document.getElementById('login-form').style.display = 'none';
            document.getElementById('register-form').style.display = 'none';
            document.getElementById('forgot-password-form').style.display = 'block';
            document.getElementById('login-tab').classList.remove('active');
            document.getElementById('register-tab').classList.remove('active');
            document.getElementById('forgot-password-tab').classList.add('active');
        }
        
        // Show register form if there was a registration error
        {% if reg_error %}
        showRegister();
        {% endif %}
        
        // Show forgot password form if there was a reset error
        {% if reset_error %}
        showForgotPassword();
        {% endif %}
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Home page"""
    if 'user' in session:
        return render_template_string(template, user=session['user'])
    return render_template_string(template)

@app.route('/login', methods=['POST'])
def login():
    """Login with Firebase"""
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not email or not password:
        return render_template_string(template, error="Email and password are required")
    
    try:
        # Sign in with Firebase
        user = auth.sign_in_with_email_and_password(email, password)
        session['user'] = email
        session['token'] = user['idToken']
        return redirect('/')
    except Exception as e:
        error_message = str(e)
        if "INVALID_PASSWORD" in error_message:
            error = "Invalid password. Please try again."
        elif "EMAIL_NOT_FOUND" in error_message:
            error = "Email not found. Please register first."
        else:
            error = f"Login failed: {error_message}"
        return render_template_string(template, error=error)

@app.route('/register', methods=['POST'])
def register():
    """Register a new user with Firebase"""
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    
    if not email or not password:
        return render_template_string(template, reg_error="Email and password are required")
    
    if password != confirm_password:
        return render_template_string(template, reg_error="Passwords do not match")
    
    try:
        # Create user in Firebase
        user = auth.create_user_with_email_and_password(email, password)
        return render_template_string(template, success="Registration successful! You can now login.")
    except Exception as e:
        error_message = str(e)
        if "EMAIL_EXISTS" in error_message:
            reg_error = "Email already exists. Please use a different email or login."
        elif "WEAK_PASSWORD" in error_message:
            reg_error = "Password is too weak. Please use a stronger password (at least 6 characters)."
        else:
            reg_error = f"Registration failed: {error_message}"
        return render_template_string(template, reg_error=reg_error)

@app.route('/reset-password', methods=['POST'])
def reset_password():
    """Send password reset email"""
    email = request.form.get('email')
    
    if not email:
        return render_template_string(template, reset_error="Email is required")
    
    try:
        # Send password reset email
        auth.send_password_reset_email(email)
        return render_template_string(template, success="Password reset email sent. Please check your inbox.")
    except Exception as e:
        error_message = str(e)
        if "EMAIL_NOT_FOUND" in error_message:
            reset_error = "Email not found. Please register first."
        else:
            reset_error = f"Password reset failed: {error_message}"
        return render_template_string(template, reset_error=reset_error)

@app.route('/logout')
def logout():
    """Logout from Firebase"""
    session.pop('user', None)
    session.pop('token', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(port=1111, debug=True)