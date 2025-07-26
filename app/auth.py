from flask import Blueprint, request, jsonify, redirect, url_for, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from functools import wraps
import requests
import json
from app.config import Config

auth_bp = Blueprint('auth', __name__)
login_manager = LoginManager()

class User(UserMixin):
    def __init__(self, user_id, email, name, groups=None):
        self.id = user_id
        self.email = email
        self.name = name
        self.groups = groups or []

@login_manager.user_loader
def load_user(user_id):
    if 'user_info' in session:
        user_data = session['user_info']
        return User(
            user_id=user_data.get('sub'),
            email=user_data.get('email'),
            name=user_data.get('name'),
            groups=user_data.get('groups', [])
        )
    return None

def require_auth(f):
    """Decorator to require Okta authentication for endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login')
def login():
    """Initiate Okta login"""
    auth_url = f"{Config.OKTA_ISSUER}/v1/authorize"
    params = {
        'client_id': Config.OKTA_CLIENT_ID,
        'response_type': 'code',
        'scope': 'openid profile email',  # Removed 'groups' scope
        'redirect_uri': Config.OKTA_REDIRECT_URI,
        'state': 'some-random-state-value'
    }
    
    auth_url_with_params = f"{auth_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
    return redirect(auth_url_with_params)

@auth_bp.route('/authorization-code/callback')
def callback():
    """Handle Okta authorization callback"""
    code = request.args.get('code')
    if not code:
        return jsonify({'error': 'Authorization code not received'}), 400
    
    # Exchange code for tokens
    token_url = f"{Config.OKTA_ISSUER}/v1/token"
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': Config.OKTA_REDIRECT_URI,
        'client_id': Config.OKTA_CLIENT_ID,
        'client_secret': Config.OKTA_CLIENT_SECRET
    }
    
    response = requests.post(token_url, data=token_data)
    if response.status_code != 200:
        return jsonify({'error': 'Token exchange failed'}), 400
    
    tokens = response.json()
    access_token = tokens.get('access_token')
    id_token = tokens.get('id_token')
    
    # Get user info from ID token or userinfo endpoint
    userinfo_url = f"{Config.OKTA_ISSUER}/v1/userinfo"
    headers = {'Authorization': f'Bearer {access_token}'}
    userinfo_response = requests.get(userinfo_url, headers=headers)
    
    if userinfo_response.status_code == 200:
        user_info = userinfo_response.json()
        
        # Store user info in session
        session['user_info'] = user_info
        session['access_token'] = access_token
        
        # Create user object and log in
        user = User(
            user_id=user_info.get('sub'),
            email=user_info.get('email'),
            name=user_info.get('name'),
            groups=user_info.get('groups', [])
        )
        login_user(user)
        
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'groups': user.groups
            }
        })
    
    return jsonify({'error': 'Failed to get user info'}), 400

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    session.clear()
    
    # Redirect to Okta logout
    logout_url = f"{Config.OKTA_ISSUER}/v1/logout"
    params = {
        'client_id': Config.OKTA_CLIENT_ID,
        'post_logout_redirect_uri': 'http://localhost:5001/'
    }
    
    logout_url_with_params = f"{logout_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
    return redirect(logout_url_with_params)

@auth_bp.route('/user')
@login_required
def get_user():
    """Get current user information"""
    return jsonify({
        'user': {
            'id': current_user.id,
            'email': current_user.email,
            'name': current_user.name,
            'groups': current_user.groups
        }
    })

@auth_bp.route('/protected')
@login_required
def protected():
    """Example protected endpoint"""
    return jsonify({
        'message': 'This is a protected endpoint',
        'user': current_user.email
    }) 