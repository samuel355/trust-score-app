from flask import Blueprint, request, jsonify, redirect, url_for, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from functools import wraps
import requests
import json
from app.config import Config

auth_bp = Blueprint('auth', __name__)
login_manager = LoginManager()

class User(UserMixin):
    def __init__(self, user_id, email, name, groups=None, user_type='user'):
        self.id = user_id
        self.email = email
        self.name = name
        self.groups = groups or []
        self.user_type = user_type  # 'user' or 'vm_agent'

@login_manager.user_loader
def load_user(user_id):
    if 'user_info' in session:
        user_data = session['user_info']
        return User(
            user_id=user_data.get('sub'),
            email=user_data.get('email'),
            name=user_data.get('name'),
            groups=user_data.get('groups', []),
            user_type=user_data.get('user_type', 'user')
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

def require_vm_agent(f):
    """Decorator to require VM agent authentication for endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        if current_user.user_type != 'vm_agent':
            return jsonify({'error': 'VM agent access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def detect_user_type(email, groups=None):
    """Detect if user is a VM agent based on email pattern or group membership"""
    groups = groups or []
    
    # Check if user is in VM_Agents group
    if 'VM_Agents' in groups:
        return 'vm_agent'
    
    # Check email pattern for VM agents
    if email and email.startswith('vm-agent-'):
        return 'vm_agent'
    
    # Check email pattern for VM agents (alternative)
    if email and 'vm-agent' in email.lower():
        return 'vm_agent'
    
    # Default to regular user
    return 'user'

@auth_bp.route('/login')
def login():
    """Initiate Okta login for regular users"""
    auth_url = f"{Config.OKTA_ISSUER}/v1/authorize"
    params = {
        'client_id': Config.OKTA_CLIENT_ID,
        'response_type': 'code',
        'scope': 'openid profile email groups',  # Added groups back
        'redirect_uri': Config.OKTA_REDIRECT_URI,
        'state': 'some-random-state-value'
    }
    
    auth_url_with_params = f"{auth_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
    return redirect(auth_url_with_params)

@auth_bp.route('/vm-agent/login', methods=['POST'])
def vm_agent_login():
    """VM agent authentication using service account credentials"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    # Authenticate with Okta using resource owner password flow
    token_url = f"{Config.OKTA_ISSUER}/v1/token"
    token_data = {
        'grant_type': 'password',
        'username': username,
        'password': password,
        'client_id': Config.OKTA_CLIENT_ID,
        'client_secret': Config.OKTA_CLIENT_SECRET,
        'scope': 'openid profile email groups'
    }
    
    response = requests.post(token_url, data=token_data)
    if response.status_code != 200:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    tokens = response.json()
    access_token = tokens.get('access_token')
    
    # Get user info
    userinfo_url = f"{Config.OKTA_ISSUER}/v1/userinfo"
    headers = {'Authorization': f'Bearer {access_token}'}
    userinfo_response = requests.get(userinfo_url, headers=headers)
    
    if userinfo_response.status_code == 200:
        user_info = userinfo_response.json()
        
        # Detect user type based on email or groups
        user_type = detect_user_type(
            user_info.get('email'), 
            user_info.get('groups', [])
        )
        user_info['user_type'] = user_type
        
        # Store user info in session
        session['user_info'] = user_info
        session['access_token'] = access_token
        
        # Create user object and log in
        user = User(
            user_id=user_info.get('sub'),
            email=user_info.get('email'),
            name=user_info.get('name'),
            groups=user_info.get('groups', []),
            user_type=user_type
        )
        login_user(user)
        
        return jsonify({
            'message': f'{user_type.replace("_", " ").title()} login successful',
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'user_type': user.user_type,
                'groups': user.groups
            }
        })
    
    return jsonify({'error': 'Failed to get user info'}), 400

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
        
        # Detect user type based on email or groups
        user_type = detect_user_type(
            user_info.get('email'), 
            user_info.get('groups', [])
        )
        user_info['user_type'] = user_type
        
        # Store user info in session
        session['user_info'] = user_info
        session['access_token'] = access_token
        
        # Create user object and log in
        user = User(
            user_id=user_info.get('sub'),
            email=user_info.get('email'),
            name=user_info.get('name'),
            groups=user_info.get('groups', []),
            user_type=user_type
        )
        login_user(user)
        
        return jsonify({
            'message': f'{user_type.replace("_", " ").title()} login successful',
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'groups': user.groups,
                'user_type': user.user_type
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
            'groups': current_user.groups,
            'user_type': current_user.user_type
        }
    })

@auth_bp.route('/protected')
@login_required
def protected():
    """Example protected endpoint"""
    return jsonify({
        'message': 'This is a protected endpoint',
        'user': current_user.email,
        'user_type': current_user.user_type
    })

@auth_bp.route('/vm-agent/protected')
@require_vm_agent
def vm_agent_protected():
    """Example VM agent only endpoint"""
    return jsonify({
        'message': 'This is a VM agent only endpoint',
        'vm_id': current_user.email,
        'user_type': current_user.user_type
    }) 