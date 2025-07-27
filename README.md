# Trust Engine - Adaptive Context-Aware Authentication System

A comprehensive Python Flask microservice that delivers adaptive, context-aware authentication for remote users accessing organizational resources. The Trust Engine integrates real-time telemetry data from virtual machine endpoints with advanced security monitoring using Wazuh, Elasticsearch, and Kibana.

## 🎯 Overview

The Trust Engine application ingests real-time telemetry data from VM endpoints, maps security events to STRIDE threat categories, computes dynamic trust scores, and enforces adaptive Multi-Factor Authentication (MFA) based on risk assessment. The system provides real-time analytics and monitoring through integrated Elasticsearch and Kibana dashboards.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   VM Agents     │    │  Wazuh Manager  │    │  Trust Engine   │
│                 │───▶│                 │───▶│   Application   │
│ • File Monitor  │    │ • Log Analysis  │    │ • STRIDE Mapping│
│ • Network Mon   │    │ • Rule Engine   │    │ • Trust Scoring │
│ • Process Mon   │    │ • Alert Gen     │    │ • MFA Decision  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Kibana       │◀───│  Elasticsearch  │◀───│   Data Storage  │
│                 │    │                 │    │                 │
│ • Dashboards    │    │ • Log Storage   │    │ • Telemetry     │
│ • Visualizations│    │ • Search Engine │    │ • Trust Scores  │
│ • Analytics     │    │ • Aggregations  │    │ • Wazuh Alerts │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Features

### Core Functionality
- **Real-time Telemetry Processing**: Ingests 62 features aligned with CICIDS2017 dataset
- **STRIDE Threat Mapping**: Maps security events to 6 STRIDE categories (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege)
- **Dynamic Trust Scoring**: Computes adaptive trust scores using weighted threat models
- **Adaptive MFA**: Enforces step-up authentication based on risk levels
- **Session Management**: Tracks user sessions with continuous risk assessment

### Security Monitoring
- **Wazuh Integration**: Real-time log analysis and security event detection
- **Elasticsearch Analytics**: Advanced search and aggregation capabilities
- **Kibana Dashboards**: Comprehensive security visualizations and monitoring
- **MITRE ATT&CK Mapping**: Integration with MITRE framework for threat intelligence
- **Anomaly Detection**: Machine learning-based anomaly identification

### Authentication & Authorization
- **Okta Integration**: Enterprise-grade identity management
- **Dual Authentication**: Support for users and VM agents
- **Role-based Access**: Differentiated access for administrators and agents
- **OAuth2/OIDC**: Industry-standard authentication protocols

## 📋 Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended)
- **Memory**: Minimum 8GB RAM (16GB recommended)
- **Storage**: At least 50GB free disk space
- **Docker**: Docker and Docker Compose installed
- **Python**: Python 3.8+ for development

### External Services
- **Supabase Account**: For primary data storage
- **Okta Developer Account**: For authentication services
- **SSL Certificates**: For production deployment (optional for development)

## 🛠️ Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd trust_engine_app

# Run the automated setup script
./setup_trust_engine.sh
```

The setup script will:
- Check dependencies and system requirements
- Configure environment variables
- Set up Docker services (Wazuh, Elasticsearch, Kibana)
- Create Elasticsearch index templates
- Import Kibana dashboards
- Start all services

### Option 2: Manual Setup

```bash
# 1. Install Python dependencies
pip3 install -r requirements.txt

# 2. Configure environment
cp env.example .env
# Edit .env with your credentials

# 3. Set system limits for Elasticsearch
sudo sysctl -w vm.max_map_count=262144

# 4. Start Docker services
cd docker
docker-compose up -d

# 5. Wait for services to initialize (2-3 minutes)
sleep 180

# 6. Run the Trust Engine application
cd ..
python3 run.py
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following configuration:

```bash
# Flask Configuration
DEBUG=true
SECRET_KEY=your-secret-key-change-in-production

# Supabase Configuration (Required)
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_API_KEY=your-supabase-anon-key

# Okta Configuration (Required)
OKTA_ISSUER=https://your-domain.okta.com/oauth2/default
OKTA_CLIENT_ID=your-okta-client-id
OKTA_CLIENT_SECRET=your-okta-client-secret
OKTA_REDIRECT_URI=http://localhost:5001/authorization-code/callback
OKTA_AUDIENCE=api://default

# Elasticsearch Configuration (Auto-configured for Docker)
ELASTICSEARCH_URL=http://elasticsearch:9200
ELASTICSEARCH_USERNAME=elastic
ELASTICSEARCH_PASSWORD=trust-engine-elastic-password

# Wazuh Configuration (Auto-configured for Docker)
WAZUH_API_URL=https://wazuh-manager:55000
WAZUH_API_USERNAME=wazuh-wui
WAZUH_API_PASSWORD=MyS3cr37P450r.*-
```

### Service URLs and Credentials

After deployment, the following services will be available:

| Service | URL | Default Credentials |
|---------|-----|-------------------|
| **Trust Engine App** | http://localhost:5001 | Okta authentication |
| **Kibana Dashboard** | http://localhost:5601 | elastic / trust-engine-elastic-password |
| **Wazuh Dashboard** | http://localhost:5602 | admin / SecretPassword |
| **Elasticsearch API** | http://localhost:9200 | elastic / trust-engine-elastic-password |
| **Wazuh Manager API** | https://localhost:55000 | wazuh-wui / MyS3cr37P450r.*- |

## 📊 Kibana Dashboards

The system includes pre-configured Kibana dashboards for comprehensive monitoring:

### 1. Trust Engine Overview Dashboard
- **Trust Score Timeline**: Real-time trust score trends
- **STRIDE Threat Breakdown**: Distribution of detected threat categories
- **MFA Level Distribution**: Analysis of authentication requirements
- **Top VM Agents**: Most active virtual machine agents
- **Authentication Success Rate**: Overall system security metrics

### 2. Threat Analysis Dashboard
- **Wazuh Alerts Timeline**: Security events over time
- **Rule Severity Levels**: Distribution of alert severity
- **MITRE ATT&CK Tactics**: Threat intelligence mapping
- **Threat Correlation Table**: Agent-threat relationships
- **Geographic Threat Distribution**: Location-based security analysis

### 3. Real-time Monitoring
- **Live Data Streaming**: Auto-refresh every 30 seconds
- **Anomaly Detection**: Automated identification of unusual patterns
- **Alert Notifications**: Real-time security alerts
- **Drill-down Analysis**: Detailed investigation capabilities

## 🔌 API Endpoints

### Authentication Endpoints
```bash
GET  /auth/login          # Initiate Okta authentication
GET  /auth/logout         # User logout
GET  /auth/user           # Get current user information
POST /auth/callback       # OAuth callback (internal)
```

### Telemetry Endpoints
```bash
POST /telemetry           # Ingest telemetry data (VM agents)
GET  /trust_score         # Get trust score for session
POST /generate_synthetic  # Generate test telemetry data
GET  /test_sample_data    # Test with CICIDS2017 sample data
```

### Wazuh Integration Endpoints
```bash
GET  /wazuh/agents        # List Wazuh agents
GET  /wazuh/alerts        # Get security alerts
POST /wazuh/process       # Process Wazuh alerts
GET  /wazuh/test          # Test Wazuh connection
```

### Analytics Endpoints
```bash
GET  /analytics/threats   # Threat intelligence summary
GET  /analytics/trust     # Trust score analytics
GET  /analytics/anomalies # Anomaly detection results
GET  /health              # System health check
```

## 🔄 Usage Examples

### 1. Authentication Flow

```bash
# Initiate login
curl http://localhost:5001/auth/login

# Check authentication status
curl http://localhost:5001/auth/user
```

### 2. Telemetry Ingestion

```bash
# Send telemetry data from VM agent
curl -X POST http://localhost:5001/telemetry \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <vm-agent-token>" \
  -d '{
    "session_id": "session_123",
    "vm_id": "vm_001",
    "event_type": "login_attempt",
    "Flow Duration": 0.123,
    "Total Fwd Packets": 45,
    "Total Backward Packets": 23,
    "Flow Bytes/s": 1500.5,
    ...
  }'
```

### 3. Trust Score Analysis

```bash
# Get trust score for a session
curl "http://localhost:5001/trust_score?session_id=session_123"

# Response:
{
  "trust_score": 0.75,
  "mfa_required": "password_otp",
  "risk_level": "medium",
  "stride_category": "Information Disclosure"
}
```

### 4. Wazuh Alert Processing

```bash
# Get recent Wazuh alerts
curl http://localhost:5001/wazuh/alerts?limit=10

# Process alerts through Trust Engine
curl -X POST http://localhost:5001/wazuh/process
```

## 🎛️ Management Commands

### Service Management

```bash
# Start all services
./setup_trust_engine.sh

# Stop all services
./setup_trust_engine.sh stop

# Restart services
./setup_trust_engine.sh restart

# View service logs
./setup_trust_engine.sh logs

# Check service status
./setup_trust_engine.sh status

# Clean up (removes all data)
./setup_trust_engine.sh clean
```

### Health Monitoring

```bash
# Check system health
curl http://localhost:5001/health

# Check Elasticsearch cluster health
curl -u elastic:trust-engine-elastic-password http://localhost:9200/_cluster/health

# Check Wazuh Manager status
curl -k https://localhost:55000/

# View container status
docker-compose -f docker/docker-compose.yml ps
```

## 🔧 Development

### Project Structure

```
trust_engine_app/
├── app/                              # Main application code
│   ├── __init__.py                   # Flask app initialization
│   ├── adaptive_mfa.py               # MFA logic and enforcement
│   ├── auth.py                       # Okta authentication
│   ├── config.py                     # Configuration management
│   ├── elasticsearch_integration.py  # Enhanced Elasticsearch client
│   ├── models.py                     # Data models
│   ├── routes.py                     # API endpoints
│   ├── telemetry.py                  # STRIDE threat mapping
│   ├── turest_score.py               # Trust score calculation
│   ├── utils.py                      # Utility functions
│   ├── wazuh_integration.py          # Wazuh API integration
│   └── wazuh_simulation.py           # Wazuh testing simulation
├── data/                             # Sample data and configurations
│   └── sample_cicids2017_data.json   # CICIDS2017 test data
├── docker/                           # Docker configurations
│   ├── docker-compose.yml            # Service orchestration
│   ├── Dockerfile                    # Trust Engine container
│   ├── elasticsearch/                # Elasticsearch configs
│   └── kibana/                       # Kibana configs
├── docs/                             # Documentation
│   ├── adaptive_mfa_guide.md         # MFA configuration guide
│   ├── implementation_status.md      # Development progress
│   ├── okta_setup.md                 # Okta configuration guide
│   ├── vm_agent_setup.md             # VM agent deployment
│   └── wazuh_elasticsearch_kibana_integration.md
├── kibana/                           # Kibana dashboard configs
│   └── trust_engine_dashboards.json # Pre-built dashboards
├── scripts/                          # Utility scripts
├── tests/                            # Test files
├── requirements.txt                  # Python dependencies
├── run.py                            # Application entry point
├── setup_trust_engine.sh             # Automated setup script
└── README.md                         # This file
```

### Adding New Features

1. **STRIDE Categories**: Modify `app/telemetry.py` to add new threat mappings
2. **Trust Scoring**: Update `app/turest_score.py` for new scoring algorithms
3. **MFA Levels**: Extend `app/adaptive_mfa.py` for additional authentication methods
4. **Dashboards**: Add new visualizations in `kibana/trust_engine_dashboards.json`

### Testing

```bash
# Test individual components
python test_supabase.py
python test_wazuh_credentials.py
python test_trust_engine_config.py

# Test API endpoints
curl http://localhost:5001/test_sample_data
curl http://localhost:5001/wazuh/test

# Generate synthetic data for testing
curl -X POST http://localhost:5001/generate_synthetic_telemetry
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Services Won't Start
```bash
# Check system resources
free -h
df -h

# Check Docker status
docker ps
docker-compose -f docker/docker-compose.yml logs

# Set Elasticsearch memory limits
sudo sysctl -w vm.max_map_count=262144
```

#### 2. Elasticsearch Issues
```bash
# Check cluster health
curl -u elastic:trust-engine-elastic-password http://localhost:9200/_cluster/health

# View Elasticsearch logs
docker logs trust-engine-elasticsearch

# Reset Elasticsearch data
docker-compose down
docker volume rm docker_elasticsearch-data
docker-compose up -d elasticsearch
```

#### 3. Kibana Connection Problems
```bash
# Check Kibana status
curl http://localhost:5601/api/status

# View Kibana logs
docker logs trust-engine-kibana

# Verify Elasticsearch connectivity
docker exec trust-engine-kibana curl -u elastic:trust-engine-elastic-password http://elasticsearch:9200/_cluster/health
```

#### 4. Wazuh Integration Issues
```bash
# Test Wazuh API
curl -k -u wazuh-wui:MyS3cr37P450r.*- https://localhost:55000/

# Check Wazuh Manager logs
docker logs trust-engine-wazuh-manager

# Verify agent connectivity
curl http://localhost:5001/wazuh/test
```

#### 5. Trust Engine Application Issues
```bash
# Check application logs
docker logs trust-engine-app

# Verify environment variables
docker exec trust-engine-app env | grep -E "(SUPABASE|OKTA|ELASTICSEARCH|WAZUH)"

# Test database connections
curl http://localhost:5001/health
```

### Performance Optimization

#### For High-Volume Environments
1. **Increase Elasticsearch heap size**:
   ```yaml
   environment:
     - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
   ```

2. **Optimize index refresh intervals**:
   ```bash
   curl -X PUT "localhost:9200/telemetrydata-*/_settings" \
        -H "Content-Type: application/json" \
        -u elastic:trust-engine-elastic-password \
        -d '{"refresh_interval": "30s"}'
   ```

3. **Enable bulk processing**:
   - Use `elasticsearch_integration.bulk_index()` for high-volume data
   - Implement batch processing for telemetry ingestion

## 🔒 Security Considerations

### Production Deployment

1. **Change Default Passwords**:
   ```bash
   # Generate secure passwords
   ELASTIC_PASSWORD=$(openssl rand -base64 32)
   WAZUH_PASSWORD=$(openssl rand -base64 32)
   SECRET_KEY=$(openssl rand -base64 64)
   ```

2. **Enable HTTPS/TLS**:
   - Configure SSL certificates for all services
   - Update URLs to use https://
   - Enable certificate verification

3. **Network Security**:
   - Use Docker secrets for sensitive configuration
   - Implement firewall rules
   - Configure network segmentation
   - Enable audit logging

4. **Access Control**:
   - Implement role-based access control
   - Use strong authentication methods
   - Regular security audits
   - Monitor access patterns

### Data Protection

1. **Encryption**: Enable encryption at rest for Elasticsearch
2. **Backup Strategy**: Implement regular data backups
3. **Data Retention**: Configure lifecycle policies for old data
4. **Compliance**: Ensure GDPR/CCPA compliance for personal data

## 📈 Monitoring and Metrics

### Key Performance Indicators

- **Trust Score Distribution**: Monitor authentication security levels
- **Threat Detection Rate**: Track STRIDE threat identification
- **MFA Success Rate**: Monitor authentication effectiveness
- **System Performance**: Response times and throughput
- **Alert Volume**: Wazuh alert generation trends

### Alerting

Configure alerts for:
- High-risk trust scores (< 0.3)
- Elevated threat levels
- System performance degradation
- Service availability issues
- Unusual authentication patterns

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add comprehensive docstrings
- Include unit tests for new features
- Update documentation for API changes
- Test integration with all services

## 📚 Documentation

- [**Wazuh Integration Guide**](docs/wazuh_elasticsearch_kibana_integration.md) - Complete integration setup
- [**Okta Setup Guide**](docs/okta_setup.md) - Authentication configuration
- [**MFA Configuration**](docs/adaptive_mfa_guide.md) - Multi-factor authentication setup
- [**VM Agent Setup**](docs/vm_agent_setup.md) - Deploy monitoring agents
- [**Implementation Status**](docs/implementation_status.md) - Development progress

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues and questions:

1. **Documentation**: Check the comprehensive guides in `/docs`
2. **Health Checks**: Use `curl http://localhost:5001/health`
3. **Logs**: View with `./setup_trust_engine.sh logs`
4. **Community**: Open an issue on GitHub
5. **Enterprise Support**: Contact for commercial support options

## 🏆 Acknowledgments

- **CICIDS2017 Dataset**: For network flow feature definitions
- **STRIDE Framework**: For threat modeling methodology
- **MITRE ATT&CK**: For threat intelligence integration
- **Elastic Stack**: For analytics and visualization capabilities
- **Wazuh**: For security monitoring and log analysis

---

**Trust Engine** - Advanced Adaptive Authentication for Modern Security 🔐🛡️