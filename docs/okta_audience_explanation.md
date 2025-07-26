# Okta Audience (aud) Explained

## 🤔 "I can't find audience in the Okta dashboard!"

This is a common confusion! The **audience** is **NOT** a setting you configure in the Okta dashboard. It's a concept used in OAuth2/OIDC tokens.

## 🎯 What is Audience?

The **audience** (`aud`) is a claim in JWT tokens that identifies the intended recipient of the token. Think of it as the "addressee" on an envelope.

## 📝 How to Set Audience

You have **two options** for the `OKTA_AUDIENCE` in your `.env` file:

### Option 1: Use Default (Recommended)
```env
OKTA_AUDIENCE=api://default
```

### Option 2: Use Your Client ID
```env
OKTA_AUDIENCE=your-okta-client-id-here
```

## 🔍 Where to Find Your Client ID

1. Go to your **Okta Developer Console**
2. Navigate to **Applications** → **Applications**
3. Click on your **Trust Engine API** application
4. Copy the **Client ID** from the **General Settings** tab

## ✅ Recommended Setup

For most applications, use the default:

```env
# Okta Configuration
OKTA_ISSUER=https://your-domain.okta.com/oauth2/default
OKTA_CLIENT_ID=your-client-id-from-okta
OKTA_CLIENT_SECRET=your-client-secret-from-okta
OKTA_REDIRECT_URI=http://localhost:5001/authorization-code/callback
OKTA_AUDIENCE=api://default  # ← Use this default value
```

## 🚨 Common Mistakes

❌ **Don't look for audience in Okta dashboard** - it doesn't exist there
❌ **Don't leave it blank** - use `api://default`
❌ **Don't use random values** - stick to the recommended options

✅ **Do use `api://default`** for most cases
✅ **Do use your Client ID** if you need specific audience validation

## 🔧 Technical Details

The audience is used when your application validates JWT tokens. It ensures that tokens intended for your application are only accepted by your application.

```python
# In your JWT validation logic
if token['aud'] != 'api://default':
    raise Exception("Invalid audience")
```

## 📚 Summary

- **Audience is NOT in Okta dashboard**
- **Use `api://default`** for most cases
- **It's a JWT claim** for token validation
- **Set it in your `.env` file**

That's it! No need to configure anything in Okta for audience. 🎉 