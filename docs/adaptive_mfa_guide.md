# Adaptive MFA Guide

## Overview
The Trust Engine implements Adaptive Multi-Factor Authentication (MFA) that dynamically adjusts authentication requirements based on real-time trust scores and STRIDE threat analysis.

## 🎯 How Adaptive MFA Works

### 1. Trust Score Calculation
- Base Trust Score: Calculated from telemetry data (0-100)
- STRIDE Analysis: Maps threats to security categories
- Adaptive Score: Adjusted based on threat multipliers

### 2. MFA Levels
- Level 1: Password Only (High trust: 80-100)
- Level 2: Password + OTP (Medium trust: 60-79)
- Level 3: Password + OTP + Device Fingerprint (Low trust: 40-59)
- Level 4: Access Blocked (Very low trust: 0-39)

### 3. STRIDE Threat Multipliers
- Spoofing: 1.5x (Identity threats)
- Tampering: 1.4x (Data integrity threats)
- Repudiation: 1.3x (Logging/audit threats)
- Information Disclosure: 1.2x (Data exposure threats)
- Denial of Service: 1.1x (Availability threats)
- Elevation of Privilege: 1.6x (Authorization threats - highest risk)

## 🔄 Authentication Flow

### Step 1: User Login
bash
# User logs in via Okta
GET /auth/login


### Step 2: Check MFA Requirements
bash
# Check what MFA is required based on current context
POST /auth/mfa/check
Content-Type: application/json

{
  "telemetry": {
    "session_id": "session_123",
    "vm_id": "vm_001",
    "event_type": "login_attempt",
    "Flow Duration": 0.123,
    "Total Fwd Packets": 45
  }
}


# Response
json
{
  "mfa_requirement": {
    "mfa_level": 2,
    "mfa_level_name": "PASSWORD_OTP",
    "required_factors": ["password", "otp"],
    "trust_score": 75,
    "adaptive_trust_score": 65,
    "stride_category": "Spoofing",
    "risk_level": 3,
    "description": "Medium trust - Password + OTP",
    "access_granted": true,
    "reasoning": "Medium base trust score; STRIDE threat detected: Spoofing; Elevated risk level (3); Trust score reduced to 65 due to threats"
  },
  "telemetry_analysis": {
    "stride_category": "Spoofing",
    "risk_level": 3,
    "trust_score": 75
  }
}


### Step 3: Get MFA Challenge
bash
# Get the specific MFA challenge
POST /auth/mfa/challenge


Response:
json
{
  "challenge": {
    "mfa_level": 2,
    "required_factors": ["password", "otp"],
    "challenge_id": "challenge_user123_12345",
    "expires_in": 300,
    "otp": "123456",
    "otp_message": "Your OTP is: 123456"
  },
  "mfa_requirement": {
    "mfa_level": 2,
    "mfa_level_name": "PASSWORD_OTP",
    "required_factors": ["password", "otp"]
  }
}


### Step 4: Verify MFA
bash
# Submit MFA factors
POST /auth/mfa/verify
Content-Type: application/json

{
  "otp": "123456",
  "device_fingerprint": "abc123def456"  // Only if required
}


Response:
json
{
  "message": "MFA verification successful",
  "access_granted": true,
  "mfa_level": "PASSWORD_OTP"
}


## 📊 MFA Decision Examples

### Example 1: High Trust User
json
{
  "trust_score": 90,
  "stride_category": "Unknown",
  "risk_level": 1,
  "mfa_level": "PASSWORD_ONLY",
  "reasoning": "High base trust score"
}


### Example 2: Medium Trust with Spoofing Threat
json
{
  "trust_score": 75,
  "stride_category": "Spoofing",
  "risk_level": 3,
  "adaptive_trust_score": 65,
  "mfa_level": "PASSWORD_OTP",
  "reasoning": "Medium base trust score; STRIDE threat detected: Spoofing; Elevated risk level (3); Trust score reduced to 65 due to threats"
}


### Example 3: Low Trust with Elevation of Privilege
json
{
  "trust_score": 50,
  "stride_category": "Elevation of Privilege",
  "risk_level": 5,
  "adaptive_trust_score": 35,
  "mfa_level": "PASSWORD_OTP_DEVICE",
  "reasoning": "Low base trust score; STRIDE threat detected: Elevation of Privilege; High risk level (5); Trust score reduced to 35 due to threats"
}


### Example 4: Very Low Trust - Blocked
json
{
  "trust_score": 30,
  "stride_category": "Elevation of Privilege",
  "risk_level": 5,
  "adaptive_trust_score": 15,
  "mfa_level": "BLOCKED",
  "access_granted": false,
  "reasoning": "Very low base trust score; STRIDE threat detected: Elevation of Privilege; High risk level (5); Trust score reduced to 15 due to threats"
}


## 🔧 Integration with VM Agents

### VM Agent Telemetry Flow
1. VM Agent sends telemetry → `/telemetry`
2. Trust Engine calculates trust score and STRIDE analysis
3. MFA requirement determined based on telemetry
4. User gets appropriate authentication challenge

### Real-time Adaptation
- Normal behavior → Password only
- Suspicious activity → Password + OTP
- High-risk threats → Password + OTP + Device fingerprint
- Critical threats → Access blocked

## 🛡️ Security Features

### 1. Dynamic Risk Assessment
- Real-time telemetry analysis
- STRIDE threat categorization
- Adaptive trust scoring

### 2. Multi-Factor Options
- Password: Standard authentication
- OTP: Time-based one-time password
- Device Fingerprint: Hardware/software fingerprinting

### 3. Threat-Based Adjustments
- STRIDE multipliers reduce trust scores
- Risk levels add penalties
- Automatic MFA escalation

## 📋 API Endpoints

### MFA Management
- `POST /auth/mfa/check` - Check MFA requirements
- `POST /auth/mfa/challenge` - Get MFA challenge
- `POST /auth/mfa/verify` - Verify MFA factors

### Telemetry Integration
- `POST /telemetry` - Send telemetry (VM agents)
- `GET /trust_score` - Get trust score for session

## 🚀 Usage Examples

### Complete Authentication Flow
bash
# 1. Login via Okta
curl http://localhost:5001/auth/login

# 2. Check MFA requirements
curl -X POST http://localhost:5001/auth/mfa/check \
  -H "Content-Type: application/json" \
  -d '{
    "telemetry": {
      "session_id": "session_123",
      "vm_id": "vm_001",
      "event_type": "login_attempt"
    }
  }'

# 3. Get MFA challenge
curl -X POST http://localhost:5001/auth/mfa/challenge

# 4. Verify MFA
curl -X POST http://localhost:5001/auth/mfa/verify \
  -H "Content-Type: application/json" \
  -d '{
    "otp": "123456"
  }'


### VM Agent Integration
bash
# VM agent sends telemetry
curl -X POST http://localhost:5001/telemetry \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session_123",
    "vm_id": "vm_001",
    "event_type": "network_anomaly",
    "Flow Duration": 0.123,
    "Total Fwd Packets": 1000
  }'


## 🔍 Monitoring and Analytics

### Trust Score Tracking
- Monitor trust score changes over time
- Track STRIDE threat patterns
- Analyze MFA requirement distribution

### Security Metrics
- Authentication success/failure rates
- MFA level distribution
- Threat detection accuracy

Your Trust Engine now provides intelligent, adaptive authentication! 🚀 