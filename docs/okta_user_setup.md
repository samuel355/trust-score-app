# Okta User Setup Guide

## Overview
This guide explains how to set up different types of users in Okta for your Trust Engine application.

## 🎯 User Types in Trust Engine

### 1. Regular Users (Security Analysts)
- Purpose: Web browser access for security analysts
- Authentication: OAuth2 flow via browser
- Access: View telemetry data, trust scores, run tests

### 2. VM Agents (Service Accounts)
- Purpose: Automated telemetry data ingestion
- Authentication: Password-based API authentication
- Access: Send telemetry data only

## 🔧 Setting Up Users in Okta

### Step 1: Create Regular Users

1. Go to Okta Admin Console
2. Navigate to Directory → People
3. Click "Add Person"
4. Fill in user details:


First Name: John
Last Name: Analyst
Email: john.analyst@yourdomain.com
Username: john.analyst
Password: [Strong password]


5. Click "Save"

### Step 2: Create VM Agent Users

1. Go to Directory → People
2. Click "Add Person"
3. Fill in VM agent details:


First Name: VM-Agent
Last Name: 001
Email: vm-agent-001@yourdomain.com
Username: vm-agent-001
Password: [Strong, unique password]


4. Click "Save"

### Step 3: Assign Users to Application

1. Go to Applications → Applications
2. Click on your "Trust Engine API" application
3. Go to "Assignments" tab
4. Click "Assign" → "Assign to People"
5. Select all users (both regular users and VM agents)
6. Set role to "User"

## 🏷️ User Type Detection

The Trust Engine automatically detects user types based on:

### 1. Email Pattern
- VM Agents: `vm-agent-001@yourdomain.com`
- Regular Users: `john.analyst@yourdomain.com`

### 2. Group Membership (Recommended)
- VM Agents: Members of `VM_Agents` group
- Regular Users: Members of `Security_Analysts` group

## 📋 Setting Up Groups (Recommended)

### Step 1: Create Groups

1. Go to Directory → Groups
2. Click "Add Group"
3. Create two groups:

#### VM_Agents Group

Name: VM_Agents
Description: VM agents for telemetry data ingestion


#### Security_Analysts Group

Name: Security_Analysts
Description: Security analysts and administrators


### Step 2: Assign Users to Groups

1. Click on VM_Agents group
2. Go to "People" tab
3. Click "Add People"
4. Select all VM agent users
5. Repeat for Security_Analysts group

## 🚀 Testing User Types

### Test Regular User Login

1. Visit: `http://localhost:5001/auth/login`
2. Sign in with regular user credentials
3. Check user type: `http://localhost:5001/auth/user`

Expected Response:
json
{
  "user": {
    "id": "user-id",
    "email": "john.analyst@yourdomain.com",
    "name": "John Analyst",
    "groups": ["Security_Analysts"],
    "user_type": "user"
  }
}


### Test VM Agent Login

bash
curl -X POST http://localhost:5001/auth/vm-agent/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "vm-agent-001@yourdomain.com",
    "password": "your-password"
  }'


Expected Response:
json
{
  "message": "Vm Agent login successful",
  "user": {
    "id": "user-id",
    "email": "vm-agent-001@yourdomain.com",
    "name": "VM-Agent 001",
    "user_type": "vm_agent",
    "groups": ["VM_Agents"]
  }
}


## 🔐 Access Control

### Regular Users Can Access:
- ✅ `/auth/user` - Get user info
- ✅ `/trust_score` - Get trust scores
- ✅ `/generate_synthetic_telemetry` - Generate test data
- ✅ `/test_sample_data` - Test with sample data
- ❌ `/telemetry` - Cannot send telemetry (VM agents only)

### VM Agents Can Access:
- ✅ `/auth/user` - Get user info
- ✅ `/telemetry` - Send telemetry data
- ❌ `/trust_score` - Cannot view trust scores
- ❌ `/generate_synthetic_telemetry` - Cannot generate test data

## 📊 User Management Best Practices

### 1. Naming Conventions
- VM Agents: `vm-agent-001`, `vm-agent-002`, etc.
- Regular Users: `firstname.lastname@yourdomain.com`

### 2. Password Policies
- VM Agents: Strong, unique passwords, rotate regularly
- Regular Users: Standard password policy

### 3. Group Management
- Use groups for access control
- Assign users to appropriate groups
- Monitor group membership

### 4. Security
- Enable MFA for regular users
- Use strong passwords for VM agents
- Monitor login attempts

## 🚨 Troubleshooting

### "User type detection failed"
- Check email patterns
- Verify group membership
- Ensure groups are configured in Okta

### "Access denied"
- Verify user is assigned to application
- Check group membership
- Ensure correct user type detection

### "Authentication failed"
- Check user credentials
- Verify user is active
- Ensure user is assigned to application

## 📈 Scaling Users

### Multiple VM Agents
- Create unique service accounts for each VM
- Use consistent naming: `vm-agent-001`, `vm-agent-002`
- Monitor agent activity

### Multiple Analysts
- Create individual accounts for each analyst
- Use descriptive names and emails
- Assign to Security_Analysts group

Your Okta user setup is now complete! 🎉 