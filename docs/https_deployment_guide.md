# Trust Engine HTTPS Deployment Guide

## Overview

This guide covers the complete HTTPS deployment setup for the Trust Engine application with SSL/TLS encryption for all services including Elasticsearch, Kibana, Wazuh, and the Trust Engine application itself.

## 🔒 HTTPS Architecture


┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   VM Agents     │    │  Wazuh Manager  │    │  Trust Engine   │
│                 │───▶│   (HTTPS:55000) │───▶│  (HTTPS:5001)   │
│ • SSL Certs     │    │ • SSL Enabled   │    │ • SSL Enabled   │
│ • CA Trusted    │    │ • Client Auth   │    │ • Certificate   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Kibana       │◀───│  Elasticsearch  │◀───│   Data Storage  │
│ (HTTPS:5601)    │    │  (HTTPS:9200)   │    │                 │
│ • SSL Dashboard │    │ • SSL API       │    │ • Encrypted     │
│ • Secure Auth   │    │ • TLS Transport │    │ • Authenticated │
└─────────────────┘    └─────────────────┘    └─────────────────┘


## 🚀 Quick HTTPS Setup

### 1. Automated Setup (Recommended)

bash
# Clone and navigate to Trust Engine
cd trust_engine_app

# Run automated HTTPS setup
./setup_trust_engine.sh

# This will:
# - Generate SSL certificates
# - Configure all services for HTTPS
# - Start encrypted services
# - Import CA certificate


### 2. Manual HTTPS Setup

bash
# Step 1: Generate SSL certificates
cd docker/ssl
./generate_certificates.sh

# Step 2: Update environment variables
cp env.example .env
# Edit .env with HTTPS URLs

# Step 3: Start HTTPS services
cd ../
docker-compose up -d

# Step 4: Verify HTTPS connectivity
curl -k https://localhost:9200/_cluster/health
curl -k https://localhost:5601/api/status
curl -k https://localhost:5001/health


## 🔐 SSL Certificate Management

### Certificate Generation

The Trust Engine uses a self-signed Certificate Authority (CA) to generate certificates for all services:

bash
# Generate all certificates
cd docker/ssl
./generate_certificates.sh

# Certificate structure created:
ssl/
├── ca/
│   ├── ca-cert.pem          # Certificate Authority
│   └── ca-key.pem           # CA Private Key
├── certs/
│   ├── elasticsearch-cert.pem
│   ├── kibana-cert.pem
│   ├── trust-engine-cert.pem
│   ├── wazuh-manager-cert.pem
│   └── *.p12               # PKCS#12 keystores
└── private/
    ├── elasticsearch-key.pem
    ├── kibana-key.pem
    ├── trust-engine-key.pem
    └── wazuh-manager-key.pem


### Certificate Verification

bash
# Verify certificate validity
cd docker/ssl
./generate_certificates.sh verify

# Manual verification
openssl x509 -in certs/elasticsearch-cert.pem -text -noout
openssl verify -CAfile ca/ca-cert.pem certs/elasticsearch-cert.pem


### Certificate Information

bash
# View certificate details
cd docker/ssl
./generate_certificates.sh info

# Check certificate expiration
openssl x509 -in certs/elasticsearch-cert.pem -noout -dates


## ⚙️ Service Configuration

### Elasticsearch HTTPS Configuration

Location: `docker/elasticsearch/config/elasticsearch.yml`

yaml
# HTTP SSL settings
xpack.security.http.ssl.enabled: true
xpack.security.http.ssl.key: /usr/share/elasticsearch/config/ssl/private/elasticsearch-key.pem
xpack.security.http.ssl.certificate: /usr/share/elasticsearch/config/ssl/certs/elasticsearch-cert.pem
xpack.security.http.ssl.certificate_authorities: /usr/share/elasticsearch/config/ssl/ca-cert.pem

# Transport SSL settings
xpack.security.transport.ssl.enabled: true
xpack.security.transport.ssl.verification_mode: certificate


Testing:
bash
# Health check
curl -k -u elastic:trust-engine-elastic-password https://localhost:9200/_cluster/health

# Index operations
curl -k -u elastic:trust-engine-elastic-password https://localhost:9200/_cat/indices


### Kibana HTTPS Configuration

Location: `docker/kibana/config/kibana.yml`

yaml
# Server HTTPS
server.ssl.enabled: true
server.ssl.key: /usr/share/kibana/config/ssl/private/kibana-key.pem
server.ssl.certificate: /usr/share/kibana/config/ssl/certs/kibana-cert.pem

# Elasticsearch HTTPS connection
elasticsearch.hosts: ["https://elasticsearch:9200"]
elasticsearch.ssl.certificateAuthorities: ["/usr/share/kibana/config/ssl/ca-cert.pem"]
elasticsearch.ssl.verificationMode: certificate


Access:
- URL: `https://localhost:5601`
- Credentials: `elastic / trust-engine-elastic-password`

### Trust Engine Application HTTPS

Configuration: `app/config.py`

python
# HTTPS settings
FLASK_USE_SSL = True
FLASK_SSL_CERT = 'docker/ssl/certs/trust-engine-cert.pem'
FLASK_SSL_KEY = 'docker/ssl/private/trust-engine-key.pem'

# External service HTTPS URLs
ELASTICSEARCH_URL = 'https://elasticsearch:9200'
WAZUH_API_URL = 'https://wazuh-manager:55000'
OKTA_REDIRECT_URI = 'https://localhost:5001/authorization-code/callback'


Testing:
bash
# Health check
curl -k https://localhost:5001/health

# API endpoints
curl -k https://localhost:5001/
curl -k https://localhost:5001/auth/login


### Wazuh HTTPS Configuration

Wazuh services are configured with HTTPS by default:

- Wazuh Manager API: `https://localhost:55000`
- Wazuh Dashboard: `https://localhost:5602`
- Wazuh Indexer: `https://localhost:9201`

## 🌐 Environment Variables

### HTTPS Environment Configuration

bash
# Flask HTTPS
FLASK_USE_SSL=true
FLASK_SSL_CERT=docker/ssl/certs/trust-engine-cert.pem
FLASK_SSL_KEY=docker/ssl/private/trust-engine-key.pem

# Elasticsearch HTTPS
ELASTICSEARCH_URL=https://elasticsearch:9200
ELASTICSEARCH_USERNAME=elastic
ELASTICSEARCH_PASSWORD=trust-engine-elastic-password
ELASTICSEARCH_SSL_VERIFY=false
ELASTICSEARCH_CA_CERT=docker/ssl/ca/ca-cert.pem

# Wazuh HTTPS
WAZUH_API_URL=https://wazuh-manager:55000
WAZUH_API_USERNAME=wazuh-wui
WAZUH_API_PASSWORD=MyS3cr37P450r.*-
WAZUH_SSL_VERIFY=false

# Okta HTTPS Redirect
OKTA_REDIRECT_URI=https://localhost:5001/authorization-code/callback


## 🏆 Browser Trust Setup

### Import CA Certificate

For browsers to trust the self-signed certificates:

#### Chrome/Chromium
1. Open `chrome://settings/certificates`
2. Go to "Authorities" tab
3. Click "Import"
4. Select `docker/ssl/ca/ca-cert.pem`
5. Check "Trust this certificate for identifying websites"

#### Firefox
1. Open `about:preferences#privacy`
2. Scroll to "Certificates" → "View Certificates"
3. Go to "Authorities" tab
4. Click "Import"
5. Select `docker/ssl/ca/ca-cert.pem`
6. Check "Trust this CA to identify websites"

#### Safari (macOS)
1. Double-click `docker/ssl/ca/ca-cert.pem`
2. Add to "System" keychain
3. Double-click the certificate in Keychain Access
4. Expand "Trust" section
5. Set "When using this certificate" to "Always Trust"

#### System-wide (Linux)
bash
# Ubuntu/Debian
sudo cp docker/ssl/ca/ca-cert.pem /usr/local/share/ca-certificates/trust-engine-ca.crt
sudo update-ca-certificates

# CentOS/RHEL
sudo cp docker/ssl/ca/ca-cert.pem /etc/pki/ca-trust/source/anchors/trust-engine-ca.crt
sudo update-ca-trust


## 🔧 API Client Configuration

### Python Requests

python
import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure session with retries
session = requests.Session()
retry_strategy = Retry(
    total=3,
    status_forcelist=[429, 500, 502, 503, 504],
    method_whitelist=["HEAD", "GET", "OPTIONS"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)

# Make HTTPS requests
response = session.get(
    'https://localhost:9200/_cluster/health',
    auth=('elastic', 'trust-engine-elastic-password'),
    verify=False  # Set to 'docker/ssl/ca/ca-cert.pem' for verification
)


### cURL Examples

bash
# Elasticsearch
curl -k -u elastic:trust-engine-elastic-password \
     https://localhost:9200/_cluster/health

# Kibana
curl -k https://localhost:5601/api/status

# Trust Engine
curl -k https://localhost:5001/health

# Wazuh Manager
curl -k -u wazuh-wui:MyS3cr37P450r.*- \
     https://localhost:55000/


## 🛡️ Security Considerations

### Development vs Production

#### Development (Current Setup)
- ✅ Self-signed certificates
- ✅ SSL verification disabled (`verify=false`)
- ✅ Default passwords
- ✅ Local access only

#### Production Requirements
- 🔄 Certificates from trusted CA (Let's Encrypt, etc.)
- 🔄 SSL verification enabled (`verify=true`)
- 🔄 Strong, unique passwords
- 🔄 Firewall and network security
- 🔄 Regular certificate rotation

### Hardening for Production

1. Replace Self-signed Certificates:
   bash
   # Example with Let's Encrypt
   certbot certonly --standalone -d your-domain.com
   
   # Copy certificates to Trust Engine
   cp /etc/letsencrypt/live/your-domain.com/fullchain.pem docker/ssl/certs/
   cp /etc/letsencrypt/live/your-domain.com/privkey.pem docker/ssl/private/
   

2. Enable SSL Verification:
   bash
   # In .env file
   ELASTICSEARCH_SSL_VERIFY=true
   WAZUH_SSL_VERIFY=true
   

3. Change Default Passwords:
   bash
   # Generate strong passwords
   ELASTICSEARCH_PASSWORD=$(openssl rand -base64 32)
   WAZUH_API_PASSWORD=$(openssl rand -base64 32)
   SECRET_KEY=$(openssl rand -base64 64)
   

4. Network Security:
   - Configure firewall rules
   - Use VPN for remote access
   - Implement IP whitelisting
   - Enable audit logging

## 🔍 Troubleshooting

### Common HTTPS Issues

#### 1. Certificate Errors

Problem: Browser shows "Not Secure" or certificate warnings

Solution:
bash
# Regenerate certificates
cd docker/ssl
./generate_certificates.sh clean
./generate_certificates.sh

# Import CA certificate in browser
# Restart services
docker-compose restart


#### 2. Connection Refused

Problem: `curl: (7) Failed to connect`

Solution:
bash
# Check if services are running
docker-compose ps

# Check service logs
docker-compose logs elasticsearch
docker-compose logs kibana
docker-compose logs trust-engine-app

# Verify SSL configuration
./setup_trust_engine.sh status


#### 3. SSL Handshake Failures

Problem: `SSL: CERTIFICATE_VERIFY_FAILED`

Solution:
bash
# For development, disable SSL verification
export ELASTICSEARCH_SSL_VERIFY=false
export WAZUH_SSL_VERIFY=false

# Or use CA certificate
export REQUESTS_CA_BUNDLE=docker/ssl/ca/ca-cert.pem


#### 4. Port Access Issues

Problem: Cannot access `https://localhost:5001`

Solution:
bash
# Check if SSL certificates exist
ls -la docker/ssl/certs/trust-engine-cert.pem
ls -la docker/ssl/private/trust-engine-key.pem

# Check application logs
docker logs trust-engine-app

# Verify port binding
netstat -tlnp | grep :5001


### Diagnostic Commands

bash
# Test all HTTPS endpoints
./setup_trust_engine.sh status

# Check certificate validity
openssl s_client -connect localhost:9200 -servername localhost
openssl s_client -connect localhost:5601 -servername localhost
openssl s_client -connect localhost:5001 -servername localhost

# Verify SSL configuration
curl -k -v https://localhost:9200/
curl -k -v https://localhost:5601/api/status
curl -k -v https://localhost:5001/health


## 📊 Monitoring HTTPS

### SSL Certificate Monitoring

bash
# Check certificate expiration
cd docker/ssl
for cert in certs/*.pem; do
    echo "=== $cert ==="
    openssl x509 -in "$cert" -noout -dates
done

# Automated monitoring script
cat > check_ssl_expiry.sh << 'EOF'
#!/bin/bash
for cert in docker/ssl/certs/*.pem; do
    expiry=$(openssl x509 -in "$cert" -noout -enddate | cut -d= -f2)
    expiry_epoch=$(date -d "$expiry" +%s)
    current_epoch=$(date +%s)
    days_left=$(( (expiry_epoch - current_epoch) / 86400 ))
    
    if [ $days_left -lt 30 ]; then
        echo "WARNING: $cert expires in $days_left days"
    else
        echo "OK: $cert expires in $days_left days"
    fi
done
EOF
chmod +x check_ssl_expiry.sh


### HTTPS Performance Monitoring

bash
# Monitor SSL handshake time
curl -k -w "@-" -o /dev/null https://localhost:9200/ << 'EOF'
     time_namelookup:  %{time_namelookup}\n
        time_connect:  %{time_connect}\n
     time_appconnect:  %{time_appconnect}\n
       time_redirect:  %{time_redirect}\n
    time_pretransfer:  %{time_pretransfer}\n
        time_total:  %{time_total}\n
EOF


## 🎯 Service URLs Summary

After HTTPS deployment, all services are accessible via encrypted connections:

| Service | HTTPS URL | Default Credentials |
|---------|-----------|-------------------|
| Trust Engine App | https://localhost:5001 | Okta authentication |
| Kibana Dashboard | https://localhost:5601 | elastic / trust-engine-elastic-password |
| Wazuh Dashboard | https://localhost:5602 | admin / SecretPassword |
| Elasticsearch API | https://localhost:9200 | elastic / trust-engine-elastic-password |
| Wazuh Manager API | https://localhost:55000 | wazuh-wui / MyS3cr37P450r.*- |
| Wazuh Indexer | https://localhost:9201 | admin / SecretPassword |

## 🔄 Maintenance

### Certificate Renewal

bash
# For development (self-signed)
cd docker/ssl
./generate_certificates.sh clean
./generate_certificates.sh
docker-compose restart

# For production (Let's Encrypt)
certbot renew
# Copy new certificates to docker/ssl/
docker-compose restart


### Backup SSL Configuration

bash
# Backup certificates and keys
tar -czf trust-engine-ssl-backup-$(date +%Y%m%d).tar.gz docker/ssl/

# Restore from backup
tar -xzf trust-engine-ssl-backup-20240115.tar.gz


### Updates and Upgrades

bash
# Update Trust Engine with HTTPS preserved
git pull origin main
./setup_trust_engine.sh restart

# Upgrade Docker images
docker-compose pull
docker-compose up -d


## 📚 Additional Resources

- [Elasticsearch Security Configuration](https://www.elastic.co/guide/en/elasticsearch/reference/current/security-settings.html)
- [Kibana Security Settings](https://www.elastic.co/guide/en/kibana/current/security-settings-kb.html)
- [Wazuh HTTPS Configuration](https://documentation.wazuh.com/current/user-manual/manager/wazuh-cluster.html#configuring-https)
- [Flask SSL Context](https://flask.palletsprojects.com/en/2.0.x/deploying/wsgi-standalone/#ssl-context)
- [Let's Encrypt SSL Certificates](https://letsencrypt.org/getting-started/)

---

Trust Engine HTTPS Deployment - Secure, encrypted communications for enterprise-grade security 🔒🛡️