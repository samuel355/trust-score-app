# Okta Issuer URL Guide

## 🤔 "What should I put for OKTA_ISSUER?"

The OKTA_ISSUER is your specific Okta domain with a standard path. It's NOT a default value - you need to replace it with your actual Okta domain.

## 🔍 How to Find Your Okta Issuer

### Step 1: Log into Okta Developer Console
1. Go to https://developer.okta.com
2. Sign in to your account
3. You'll be redirected to your Okta Developer Console

### Step 2: Look at the URL
The URL in your browser will show your domain:

https://YOUR-DOMAIN.okta.com/admin/app/


### Step 3: Extract Your Domain
Take the domain part and add the standard path:

From: `https://dev-123456.okta.com/admin/app/`
To: `https://dev-123456.okta.com/oauth2/default`

## 📝 Common Okta Domain Examples

### Developer Accounts (Free Tier)
env
OKTA_ISSUER=https://dev-123456.okta.com/oauth2/default
OKTA_ISSUER=https://dev-789012.okta.com/oauth2/default


### Custom Domains
env
OKTA_ISSUER=https://yourcompany.okta.com/oauth2/default
OKTA_ISSUER=https://acme.okta.com/oauth2/default


### Enterprise Accounts
env
OKTA_ISSUER=https://company.okta.com/oauth2/default
OKTA_ISSUER=https://enterprise.okta.com/oauth2/default


## ✅ Correct Format

Always use this format:

https://YOUR-DOMAIN.okta.com/oauth2/default


Important parts:
- ✅ `https://` - Must be HTTPS
- ✅ `YOUR-DOMAIN.okta.com` - Your actual Okta domain
- ✅ `/oauth2/default` - Standard Okta path (always include this)

## ❌ Common Mistakes

env
# ❌ Wrong - missing /oauth2/default
OKTA_ISSUER=https://dev-123456.okta.com

# ❌ Wrong - using placeholder
OKTA_ISSUER=https://your-domain.okta.com/oauth2/default

# ❌ Wrong - wrong protocol
OKTA_ISSUER=http://dev-123456.okta.com/oauth2/default

# ✅ Correct
OKTA_ISSUER=https://dev-123456.okta.com/oauth2/default


## 🔧 Alternative: Find in Okta Application Settings

1. Go to Applications → Applications
2. Click on your Trust Engine API application
3. Go to General Settings tab
4. Look for Authorization server - it should show your issuer

## 📋 Quick Checklist

- [ ] Log into Okta Developer Console
- [ ] Copy your domain from the URL
- [ ] Add `/oauth2/default` to the end
- [ ] Use HTTPS protocol
- [ ] Update your `.env` file

## 🎯 Example Setup

Your Okta URL: `https://dev-123456.okta.com/admin/app/`

Your .env file:
env
OKTA_ISSUER=https://dev-123456.okta.com/oauth2/default
OKTA_CLIENT_ID=your-actual-client-id
OKTA_CLIENT_SECRET=your-actual-client-secret
OKTA_REDIRECT_URI=http://localhost:5001/authorization-code/callback
OKTA_AUDIENCE=api://default


That's it! Your issuer is unique to your Okta account. 🎉 