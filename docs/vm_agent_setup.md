# VM Agent Authentication Setup Guide

## Overview
This guide explains how to set up authentication for VM agents that will send telemetry data to your Trust Engine.

## 🎯 **Authentication Strategy**

### **Two Types of Authentication:**

1. **Regular Users** - Web browser login for security analysts
2. **VM Agents** - Service accounts for automated telemetry ingestion

## 🔧 **Setting Up VM Agent Credentials**

### **Step 1: Create Service Accounts in Okta**

1. **Log into Okta Admin Console**
2. **Go to Directory** → **People**
3. **Click "Add Person"**
4. **Create service accounts for each VM:**

#### **Example VM Agent Setup:**
```
First Name: VM-Agent
Last Name: 001
Email: vm-agent-001@yourdomain.com
Username: vm-agent-001
Password: [Strong, unique password]
```

#### **Create Multiple Agents:**
- `vm-agent-001@yourdomain.com` (for VM 1)
- `vm-agent-002@yourdomain.com` (for VM 2)
- `vm-agent-003@yourdomain.com` (for VM 3)

### **Step 2: Assign VM Agents to Your Application**

1. **Go to Applications** → **Applications**
2. **Click on your "Trust Engine API" application**
3. **Go to "Assignments" tab**
4. **Click "Assign"** → **"Assign to People"**
5. **Select all your VM agents**
6. **Set role to "User"**

### **Step 3: Configure VM Agent Permissions**

1. **Go to Directory** → **People**
2. **Click on a VM agent**
3. **Go to "Applications" tab**
4. **Ensure "Trust Engine API" is assigned**
5. **Set appropriate permissions**

## 🚀 **VM Agent Authentication Flow**

### **1. VM Agent Login**

VM agents authenticate using the `/auth/vm-agent/login` endpoint:

```bash
curl -X POST http://localhost:5001/auth/vm-agent/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "vm-agent-001@yourdomain.com",
    "password": "your-vm-agent-password"
  }'
```

### **2. Send Telemetry Data**

After authentication, VM agents can send telemetry:

```bash
curl -X POST http://localhost:5001/telemetry \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your-session-cookie" \
  -d '{
    "session_id": "session_123",
    "vm_id": "vm_001",
    "event_type": "network_flow",
    "Flow Duration": 0.123,
    "Total Fwd Packets": 45,
    "Total Backward Packets": 23
  }'
```

## 📋 **VM Agent Configuration Examples**

### **Wazuh Agent Integration**

In your Wazuh agent configuration, add custom rules to send data to Trust Engine:

```xml
<!-- Wazuh agent custom rule -->
<rule id="100001" level="0">
  <if_sid>0</if_sid>
  <match>^ossec: Output: 'trust_engine_telemetry:</match>
  <description>Trust Engine telemetry data</description>
</rule>

<!-- Custom command to send to Trust Engine -->
<command>
  <name>trust_engine_telemetry</name>
  <executable>curl</executable>
  <expect>srcip</expect>
  <timeout_allowed>yes</timeout_allowed>
</command>
```

### **Python Script for VM Agent**

```python
import requests
import json
import time

class TrustEngineAgent:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with Trust Engine"""
        login_data = {
            "username": self.username,
            "password": self.password
        }
        
        response = self.session.post(
            f"{self.base_url}/auth/vm-agent/login",
            json=login_data
        )
        
        if response.status_code == 200:
            print("VM Agent authenticated successfully")
        else:
            raise Exception("Authentication failed")
    
    def send_telemetry(self, telemetry_data):
        """Send telemetry data to Trust Engine"""
        response = self.session.post(
            f"{self.base_url}/telemetry",
            json=telemetry_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Telemetry sent: Trust Score = {result['trust_score']}")
            return result
        else:
            print(f"Failed to send telemetry: {response.text}")
            return None

# Usage example
agent = TrustEngineAgent(
    base_url="http://localhost:5001",
    username="vm-agent-001@yourdomain.com",
    password="your-password"
)

# Send telemetry data
telemetry = {
    "session_id": "session_123",
    "vm_id": "vm_001",
    "event_type": "network_flow",
    "Flow Duration": 0.123,
    "Total Fwd Packets": 45
}

result = agent.send_telemetry(telemetry)
```

## 🔐 **Security Best Practices**

### **1. Password Management**
- ✅ Use strong, unique passwords for each VM agent
- ✅ Store passwords securely (environment variables, vault)
- ✅ Rotate passwords regularly
- ❌ Never hardcode passwords in scripts

### **2. Network Security**
- ✅ Use HTTPS in production
- ✅ Implement IP whitelisting if possible
- ✅ Use VPN for secure communication
- ❌ Don't expose Trust Engine on public internet

### **3. Access Control**
- ✅ Limit VM agent permissions to minimum required
- ✅ Monitor agent access logs
- ✅ Implement rate limiting
- ❌ Don't give VM agents admin privileges

## 📊 **Monitoring VM Agents**

### **Check Agent Status**

```bash
# Get current user info (for authenticated agents)
curl http://localhost:5001/auth/user

# Check VM agent specific endpoint
curl http://localhost:5001/auth/vm-agent/protected
```

### **View Telemetry Data**

```bash
# Get trust score for a session
curl "http://localhost:5001/trust_score?session_id=session_123"
```

## 🚨 **Troubleshooting**

### **Common Issues**

1. **"Authentication failed"**
   - Check VM agent credentials
   - Verify agent is assigned to application
   - Ensure agent account is active

2. **"VM agent access required"**
   - Use VM agent login endpoint
   - Don't use regular user login for agents

3. **"Invalid credentials"**
   - Check username/password
   - Verify Okta configuration
   - Check network connectivity

### **Debug Mode**

Enable debug mode to see detailed logs:
```env
DEBUG=True
```

## 📈 **Scaling VM Agents**

### **Multiple VMs**
- Create unique service accounts for each VM
- Use consistent naming convention
- Monitor resource usage

### **Load Balancing**
- Consider multiple Trust Engine instances
- Implement proper session management
- Use database for session storage in production

Your VM agents are now ready to send telemetry data securely! 🚀 