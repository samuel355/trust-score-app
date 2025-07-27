# Okta Integration Setup Guide

## Overview
This guide will help you set up Okta authentication for your Trust Engine Flask application.

## Prerequisites
- Okta Developer Account (free at https://developer.okta.com)
- Your Trust Engine Flask application running

## Step 1: Create Okta Application

### 1.1 Log into Okta Developer Console
1. Go to https://developer.okta.com
2. Sign in to your Okta Developer account
3. Navigate to your Okta Developer Console

### 1.2 Create a New Application
1. Click Applications → Applications
2. Click Create App Integration
3. Choose OIDC - OpenID Connect
4. Choose Web application
5. Click Next

### 1.3 Configure Application Settings
1. App name: `Trust Engine API`
2. App logo: (optional)
3. Grant type: Check the following:
   - [x] Authorization Code
   - [x] Refresh Token
4. Sign-in redirect URIs: `http://localhost:5001/authorization-code/callback`
5. Sign-out redirect URIs: `http://localhost:5001/`
6. Trust level: `Single-tenant app`
7. Click Save

### 1.4 Get Application Credentials
After saving, you'll see:
- Client ID: Copy this value
- Client Secret: Click "Show client secret" and copy this value
- Okta Domain: Your Okta domain (e.g., `https://your-domain.okta.com`)

## Step 2: Configure Environment Variables

Create a `.env` file in your project root with the following variables:

env
# Flask Configuration
SECRET_KEY=your-secret-key-here
DEBUG=True

# Supabase Configuration
SUPABASE_URL=your-supabase-url
SUPABASE_API_KEY=your-supabase-api-key

# Okta Configuration
OKTA_ISSUER=https://your-domain.okta.com/oauth2/default
OKTA_CLIENT_ID=your-client-id-from-okta
OKTA_CLIENT_SECRET=your-client-secret-from-okta
OKTA_REDIRECT_URI=http://localhost:5001/authorization-code/callback
# Audience: Use 'api://default' or your Client ID - this is NOT set in Okta dashboard
OKTA_AUDIENCE=api://default


### Important Note about OKTA_AUDIENCE
The audience (`aud`) is a JWT claim that identifies the intended recipient of the token. You have two options:

1. Use the default: `api://default` (recommended for most cases)
2. Use your Client ID: Set it to the same value as `OKTA_CLIENT_ID`

You do NOT configure this in the Okta dashboard - it's a value your application uses when validating tokens.

## Step 3: Test the Integration

### 3.1 Start Your Application
bash
python3 run.py


### 3.2 Test Authentication Flow
1. Visit `http://localhost:5001/` - Should show API info
2. Visit `http://localhost:5001/auth/login` - Should redirect to Okta login
3. After login, you'll be redirected back to your app
4. Visit `http://localhost:5001/auth/user` - Should show your user info
5. Visit `http://localhost:5001/test_sample_data` - Should work (now protected)

## Step 4: API Endpoints

### Public Endpoints
- `GET /` - API information
- `GET /auth/login` - Initiate Okta login
- `GET /auth/logout` - Logout user

### Protected Endpoints (require authentication)
- `GET /auth/user` - Get current user info
- `POST /telemetry` - Ingest telemetry data
- `GET /trust_score` - Get trust score for session
- `POST /generate_synthetic_telemetry` - Generate synthetic data
- `GET/POST /test_sample_data` - Test with sample data

## Step 5: Customization

### 5.1 Add User Groups
In Okta Admin Console:
1. Go to Directory → Groups
2. Create groups (e.g., `Security_Admins`, `VM_Users`)
3. Assign users to groups
4. Groups will be available in `current_user.groups`

### 5.2 Custom Scopes
Modify the scope in `app/auth.py`:
python
'scope': 'openid profile email groups'  # Add custom scopes as needed


### 5.3 Role-Based Access
Add role checking in your endpoints:
python
@bp.route('/admin_only')
@require_auth
def admin_only():
    if 'Security_Admins' not in current_user.groups:
        return jsonify({'error': 'Admin access required'}), 403
    return jsonify({'message': 'Admin access granted'})


## Troubleshooting

### Common Issues

1. "Invalid redirect URI"
   - Ensure the redirect URI in Okta matches exactly: `http://localhost:5001/authorization-code/callback`

2. "Client authentication failed"
   - Check that your Client ID and Client Secret are correct
   - Ensure the Client Secret is properly copied (no extra spaces)

3. "Authorization code not received"
   - Check that the authorization code flow is properly configured
   - Verify the callback URL is accessible

4. Session issues
   - Ensure `SECRET_KEY` is set in your environment
   - Check that Flask sessions are working properly

5. "Audience not found"
   - The audience is NOT configured in Okta dashboard
   - Use `api://default` or your Client ID as the audience value

### Debug Mode
Enable debug mode to see detailed error messages:
env
DEBUG=True


## Security Considerations

1. Environment Variables: Never commit `.env` files to version control
2. HTTPS: Use HTTPS in production (update redirect URIs accordingly)
3. Token Storage: Access tokens are stored in session (consider Redis for production)
4. Logout: Always use the logout endpoint to properly clear sessions

## Production Deployment

For production deployment:

1. Update Redirect URIs: Change from `localhost` to your production domain
2. Use HTTPS: Update all URLs to use HTTPS
3. Session Storage: Consider using Redis or database for session storage
4. Environment Variables: Set all environment variables in your production environment
5. Logging: Implement proper logging for authentication events

## Integration with Trust Engine

The Okta integration enhances your Trust Engine by:

1. User Context: Adding user identity to telemetry data
2. Access Control: Protecting sensitive endpoints
3. Audit Trail: Tracking who accessed what data
4. Group-Based Policies: Implementing different trust levels based on user groups

Your Trust Engine now has enterprise-grade authentication! 🚀 