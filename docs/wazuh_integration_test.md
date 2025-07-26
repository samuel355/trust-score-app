# Wazuh Integration Test Guide

## Overview
This guide helps you test the integration between your Trust Engine and the Wazuh Docker instance running on `https://localhost`.

## 🔧 **Prerequisites**

### **1. Wazuh Docker Instance**
- ✅ Wazuh running on `https://localhost`
- ✅ Wazuh API accessible
- ✅ Default credentials: `wazuh` / `MyS3cureP4ssw0rd`

### **2. Trust Engine Setup**
- ✅ Trust Engine running on `http://localhost:5001`
- ✅ Okta authentication configured
- ✅ Supabase database configured

## 🚀 **Testing Steps**

### **Step 1: Test Wazuh Connection**

First, test if the Trust Engine can connect to your Wazuh instance:

```bash
# Test Wazuh connection (requires authentication)
curl -X GET http://localhost:5001/wazuh/test \
  -H "Cookie: session=your-session-cookie"
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Wazuh connection successful",
  "agents_count": 1,
  "recent_alerts_count": 5,
  "wazuh_url": "https://localhost"
}
```

### **Step 2: Get Wazuh Agents**

List all Wazuh agents:

```bash
# Get Wazuh agents
curl -X GET http://localhost:5001/wazuh/agents \
  -H "Cookie: session=your-session-cookie"
```

**Expected Response:**
```json
{
  "status": "success",
  "agents": [
    {
      "id": "001",
      "name": "wazuh-agent",
      "ip": "192.168.1.100",
      "os": {
        "name": "Ubuntu 20.04"
      },
      "status": "active"
    }
  ],
  "count": 1
}
```

### **Step 3: Get Wazuh Alerts**

Retrieve recent alerts from Wazuh:

```bash
# Get recent alerts
curl -X GET "http://localhost:5001/wazuh/alerts?limit=10" \
  -H "Cookie: session=your-session-cookie"
```

**Expected Response:**
```json
{
  "status": "success",
  "alerts": [
    {
      "id": "123456",
      "timestamp": "2024-01-15T10:30:00Z",
      "agent": {
        "id": "001",
        "name": "wazuh-agent"
      },
      "rule": {
        "id": "100001",
        "level": 5,
        "description": "SSH authentication failure"
      },
      "full_log": "sshd[1234]: Failed password for user admin from 192.168.1.50"
    }
  ],
  "count": 1
}
```

### **Step 4: Process Wazuh Alerts as Telemetry**

Convert Wazuh alerts to Trust Engine telemetry:

```bash
# Process Wazuh alerts
curl -X POST http://localhost:5001/wazuh/process-alerts \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your-session-cookie" \
  -d '{
    "agent_id": "001",
    "limit": 5
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Processed 1 Wazuh alerts",
  "processed_count": 1,
  "results": [
    {
      "wazuh_alert_id": "123456",
      "agent_name": "wazuh-agent",
      "rule_description": "SSH authentication failure",
      "stride_category": "Spoofing",
      "risk_level": 3,
      "trust_score": 65,
      "mfa_required": true
    }
  ]
}
```

## 🔍 **What Happens During Processing**

### **1. Alert Conversion**
- Wazuh alerts are converted to CICIDS2017 format
- Network features are extracted from alert content
- 62 CICIDS2017 features are populated

### **2. STRIDE Analysis**
- Alert content is analyzed for threat patterns
- STRIDE category is determined
- Risk level is calculated

### **3. Trust Score Calculation**
- Dynamic trust score is computed
- MFA requirements are determined
- Data is stored in Supabase

## 📊 **Testing Different Alert Types**

### **SSH Brute Force Attack**
```bash
# This should result in:
# - STRIDE Category: Spoofing
# - Risk Level: 4-5
# - MFA Level: Password + OTP or higher
```

### **File System Changes**
```bash
# This should result in:
# - STRIDE Category: Tampering
# - Risk Level: 3-4
# - MFA Level: Password + OTP
```

### **Network Anomaly**
```bash
# This should result in:
# - STRIDE Category: Information Disclosure
# - Risk Level: 2-3
# - MFA Level: Password + OTP
```

## 🚨 **Troubleshooting**

### **Connection Issues**
```bash
# Check if Wazuh is accessible
curl -k https://localhost

# Check Wazuh API directly
curl -k -u wazuh:MyS3cureP4ssw0rd https://localhost/security/user/authenticate
```

### **Authentication Issues**
- Verify Wazuh credentials in `.env` file
- Check if Wazuh API is enabled
- Ensure HTTPS certificates are valid

### **No Alerts Found**
- Generate some test alerts in Wazuh
- Check Wazuh agent status
- Verify alert rules are active

## 🔧 **Generating Test Alerts**

### **SSH Login Attempts**
```bash
# On a Wazuh agent, try:
ssh nonexistent@localhost
```

### **File System Changes**
```bash
# Create/modify files in monitored directories
touch /var/log/test.log
```

### **Network Activity**
```bash
# Generate network traffic
curl http://google.com
```

## 📈 **Monitoring Results**

### **Check Trust Scores**
```bash
# Get trust score for processed session
curl "http://localhost:5001/trust_score?session_id=wazuh_123456" \
  -H "Cookie: session=your-session-cookie"
```

### **View Supabase Data**
- Check `TelemetryData` table for processed alerts
- Check `TrustScore` table for calculated scores
- Monitor MFA requirement changes

## 🎯 **Expected Outcomes**

### **Successful Integration**
- ✅ Wazuh alerts are converted to telemetry
- ✅ STRIDE analysis is performed
- ✅ Trust scores are calculated
- ✅ MFA requirements are determined
- ✅ Data is stored in Supabase

### **Real-time Processing**
- ✅ New alerts trigger trust score updates
- ✅ MFA requirements adapt to threats
- ✅ Security posture improves dynamically

Your Wazuh integration is now ready for testing! 🚀 