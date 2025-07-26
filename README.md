# Trust Engine API

A Python Flask-based microservice for adaptive, context-aware authentication using real-time telemetry data from virtual machine endpoints.

## 🚀 Features

- **Real-time Telemetry Processing**: Ingests 62 features aligned with CICIDS2017 dataset
- **STRIDE Threat Mapping**: Maps telemetry to security threat categories
- **Dynamic Trust Scoring**: Computes adaptive trust scores for user sessions
- **Okta Integration**: Enterprise-grade authentication and user management
- **Supabase Backend**: Modern database for telemetry and trust score storage
- **Wazuh Integration Ready**: Prepared for endpoint security monitoring

## 📋 Prerequisites

- Python 3.8+
- Okta Developer Account
- Supabase Project
- (Optional) Wazuh Server

## 🛠️ Quick Setup

### 1. Clone and Install Dependencies

```bash
git clone <your-repo-url>
cd trust_engine_app
pip3 install -r requirements.txt
```

### 2. Configure Credentials

```bash
# Copy the example environment file
cp env.example .env

# Edit .env with your actual credentials
nano .env
```

### 3. Required Credentials

You need to configure these services:

#### **Supabase Setup**
1. Create a project at [supabase.com](https://supabase.com)
2. Get your project URL and API key
3. Create tables using `app/supabase_schema.md`

#### **Okta Setup**
1. Create an Okta Developer account
2. Follow the setup guide in `docs/okta_setup.md`
3. Get your Client ID and Client Secret

### 4. Run the Application

```bash
python3 run.py
```

The app will start on `http://localhost:5001`

## 🔐 Credential Management

### Environment Variables Structure

```env
# Flask Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
DEBUG=True

# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_API_KEY=your-supabase-anon-key-here

# Okta Configuration
OKTA_ISSUER=https://your-domain.okta.com/oauth2/default
OKTA_CLIENT_ID=your-okta-client-id-here
OKTA_CLIENT_SECRET=your-okta-client-secret-here
OKTA_REDIRECT_URI=http://localhost:5001/authorization-code/callback
OKTA_AUDIENCE=api://default
```

### Security Best Practices

- ✅ **Use `.env` files** for local development
- ✅ **Never commit** `.env` files to version control
- ✅ **Use environment variables** in production
- ✅ **Rotate secrets** regularly
- ❌ **Never hardcode** credentials in code

## 📚 API Endpoints

### Public Endpoints
- `GET /` - API information and documentation
- `GET /auth/login` - Initiate Okta authentication
- `GET /auth/logout` - Logout user

### Protected Endpoints (require authentication)
- `GET /auth/user` - Get current user information
- `POST /telemetry` - Ingest telemetry data
- `GET /trust_score` - Get trust score for session
- `POST /generate_synthetic_telemetry` - Generate test data
- `GET/POST /test_sample_data` - Test with sample CICIDS2017 data

## 🔄 Usage Examples

### 1. Authentication Flow

```bash
# 1. Visit login endpoint
curl http://localhost:5001/auth/login

# 2. After Okta login, get user info
curl http://localhost:5001/auth/user
```

### 2. Telemetry Ingestion

```bash
# Send telemetry data (requires authentication)
curl -X POST http://localhost:5001/telemetry \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session_123",
    "vm_id": "vm_001",
    "event_type": "login_attempt",
    "Flow Duration": 0.123,
    "Total Fwd Packets": 45
  }'
```

### 3. Trust Score Retrieval

```bash
# Get trust score for a session
curl "http://localhost:5001/trust_score?session_id=session_123"
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   VM Endpoints  │───▶│  Trust Engine   │───▶│    Supabase     │
│   (Wazuh)       │    │   (Flask API)   │    │   (Database)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │      Okta       │
                       │ (Authentication)│
                       └─────────────────┘
```

## 🔧 Development

### Project Structure

```
trust_engine_app/
├── app/
│   ├── __init__.py          # Flask app initialization
│   ├── config.py            # Configuration management
│   ├── auth.py              # Okta authentication
│   ├── routes.py            # API endpoints
│   ├── telemetry.py         # Telemetry processing
│   ├── turest_score.py      # Trust score calculation
│   ├── utils.py             # Utility functions
│   └── models.py            # Data models
├── data/
│   └── sample_cicids2017_data.json
├── docs/
│   └── okta_setup.md
├── requirements.txt
├── run.py
├── env.example
└── README.md
```

### Running Tests

```bash
# Run the application
python3 run.py

# Test endpoints
curl http://localhost:5001/
curl http://localhost:5001/test_sample_data
```

## 🚨 Troubleshooting

### Common Issues

1. **"Credentials not configured"**
   - Copy `env.example` to `.env`
   - Fill in your actual credentials

2. **"Import errors"**
   - Install dependencies: `pip3 install -r requirements.txt`

3. **"Port already in use"**
   - Change port in `run.py` or kill existing process

4. **"Okta authentication failed"**
   - Check Okta configuration in `docs/okta_setup.md`
   - Verify redirect URIs match exactly

### Debug Mode

Enable debug mode in `.env`:
```env
DEBUG=True
```

## 📖 Documentation

- [Okta Setup Guide](docs/okta_setup.md)
- [Supabase Schema](app/supabase_schema.md)
- [API Documentation](http://localhost:5001/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the documentation
3. Open an issue on GitHub

---

**Trust Engine API** - Secure, adaptive authentication for modern applications 🔐 