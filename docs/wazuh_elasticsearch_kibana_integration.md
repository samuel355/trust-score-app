# Trust Engine - Wazuh, Elasticsearch & Kibana Integration Guide

## Overview

This guide explains how to integrate your Wazuh Docker setup with Elasticsearch and Kibana for the Trust Engine application. The integration provides real-time security monitoring, threat analysis, and comprehensive dashboards for adaptive authentication.

## Architecture


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


## Prerequisites

- Docker and Docker Compose installed
- Minimum 8GB RAM (16GB recommended)
- At least 50GB free disk space
- Linux system with sudo access
- Trust Engine application codebase

## Quick Start

### 1. Setup Environment

bash
# Clone or navigate to Trust Engine directory
cd trust_engine_app

# Run the automated setup script
./setup_trust_engine.sh


### 2. Manual Setup (Alternative)

If you prefer manual setup or need customization:

bash
# 1. Set system limits for Elasticsearch
sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf

# 2. Create Docker network
docker network create trust-engine-network

# 3. Start services
cd docker
docker-compose up -d

# 4. Wait for services to initialize
sleep 120

# 5. Setup Elasticsearch templates
curl -X PUT "localhost:9200/_index_template/trust-engine-telemetry" \
     -H "Content-Type: application/json" \
     -u elastic:trust-engine-elastic-password \
     -d @elasticsearch/templates/telemetry-template.json


## Service Configuration

### Elasticsearch Configuration

The Elasticsearch instance is configured with:

- Cluster Name: `trust-engine-cluster`
- Memory: 512MB heap (adjustable via ES_JAVA_OPTS)
- Security: Enabled with basic authentication
- Username: `elastic`
- Password: `trust-engine-elastic-password`
- Port: `9200`

Key features:
- Time-based indices for efficient data management
- Custom mappings for Trust Engine data types
- Optimized for real-time ingestion and analytics

### Kibana Configuration

Kibana provides the visualization layer:

- Port: `5601`
- Authentication: Integrated with Elasticsearch
- Dashboards: Pre-configured for Trust Engine analytics
- Index Patterns: Auto-created for telemetry, trust scores, and alerts

### Wazuh Integration

The Wazuh stack includes:

- Wazuh Manager: Core log analysis and alerting
- Wazuh Indexer: OpenSearch-based storage
- Wazuh Dashboard: Security-focused visualizations
- API Access: RESTful API for Trust Engine integration

## Data Flow

### 1. Telemetry Ingestion

python
# Trust Engine receives telemetry from VM agents
POST /telemetry
{
    "session_id": "session_123",
    "vm_id": "vm_001",
    "features": { ... },  # CICIDS2017 features
    "timestamp": "2024-01-15T10:30:00Z"
}

# Data flows to:
# 1. Supabase (primary storage)
# 2. Elasticsearch (analytics)
# 3. Trust scoring engine


### 2. Wazuh Alert Processing

python
# Wazuh generates security alerts
{
    "id": "alert_456",
    "agent": {"name": "vm_001", "ip": "192.168.1.100"},
    "rule": {"id": 31100, "level": 10, "description": "SSH brute force"},
    "full_log": "sshd: Failed password for root from 192.168.1.200",
    "timestamp": "2024-01-15T10:31:00Z"
}

# Trust Engine processes alert:
# 1. Maps to STRIDE category
# 2. Updates trust score
# 3. Triggers MFA step-up if needed
# 4. Indexes to Elasticsearch


### 3. Real-time Analytics

Data is indexed to Elasticsearch with time-based indices:

- `telemetrydata-YYYY-MM-DD`: Raw telemetry data
- `trustscore-YYYY-MM-DD`: Trust score calculations
- `wazuh_alerts-YYYY-MM-DD`: Security alerts

## Elasticsearch Index Patterns

### Telemetry Data Index

json
{
  "index_patterns": ["telemetrydata-*"],
  "mappings": {
    "properties": {
      "@timestamp": {"type": "date"},
      "session_id": {"type": "keyword"},
      "vm_id": {"type": "keyword"},
      "event_type": {"type": "keyword"},
      "stride_category": {"type": "keyword"},
      "risk_level": {"type": "integer"},
      "trust_score": {"type": "float"},
      "features": {"type": "object"},
      "wazuh_alert_id": {"type": "keyword"},
      "wazuh_agent_ip": {"type": "ip"}
    }
  }
}


### Trust Score Index

json
{
  "index_patterns": ["trustscore-*"],
  "mappings": {
    "properties": {
      "@timestamp": {"type": "date"},
      "session_id": {"type": "keyword"},
      "user_id": {"type": "keyword"},
      "trust_score": {"type": "float"},
      "mfa_level": {"type": "keyword"},
      "action_taken": {"type": "keyword"},
      "stride_scores": {"type": "object"}
    }
  }
}


## Kibana Dashboards

### 1. Trust Engine Overview Dashboard

Panels:
- Trust Score Timeline (Line chart)
- STRIDE Threat Breakdown (Pie chart)
- MFA Level Distribution (Bar chart)
- Top VM Agents by Activity (Horizontal bar)
- Authentication Success Rate (Gauge)

Access: `http://localhost:5601/app/dashboards`

### 2. Threat Analysis Dashboard

Panels:
- Wazuh Alerts Timeline (Area chart)
- Rule Severity Levels (Histogram)
- MITRE ATT&CK Tactics (Tag cloud)
- Threat Correlation Table
- Agent Security Status (Metrics)

### 3. Real-time Monitoring

Features:
- Auto-refresh every 30 seconds
- Drill-down capabilities
- Time range filtering
- Alert notifications

## API Integration

### Trust Engine Elasticsearch Client

python
from app.elasticsearch_integration import elasticsearch_integration

# Index telemetry data
elasticsearch_integration.index_telemetry({
    "session_id": "session_123",
    "vm_id": "vm_001",
    "trust_score": 0.75,
    "timestamp": datetime.utcnow().isoformat()
})

# Search telemetry
results = elasticsearch_integration.search_telemetry({
    "query": {
        "range": {
            "@timestamp": {"gte": "now-1h"}
        }
    }
})

# Get analytics
analytics = elasticsearch_integration.get_trust_score_analytics(
    session_id="session_123",
    hours=24
)


### Wazuh Integration

python
from app.wazuh_integration import wazuh_integration

# Get recent alerts
alerts = wazuh_integration.get_alerts(limit=100)

# Process alerts for Trust Engine
for alert in alerts:
    telemetry = wazuh_integration.convert_wazuh_alert_to_telemetry(alert)
    # Process through Trust Engine...


## Environment Variables

Add these to your `.env` file:

bash
# Elasticsearch Configuration
ELASTICSEARCH_URL=http://elasticsearch:9200
ELASTICSEARCH_USERNAME=elastic
ELASTICSEARCH_PASSWORD=trust-engine-elastic-password

# Wazuh Configuration
WAZUH_API_URL=https://wazuh-manager:55000
WAZUH_API_USERNAME=wazuh-wui
WAZUH_API_PASSWORD=MyS3cr37P450r.*-

# Trust Engine Configuration
DEBUG=true
SECRET_KEY=your-secret-key-change-in-production

# External Services (Required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_API_KEY=your-supabase-key
OKTA_ISSUER=https://your-domain.okta.com/oauth2/default
OKTA_CLIENT_ID=your-client-id
OKTA_CLIENT_SECRET=your-client-secret


## Service URLs and Credentials

After setup completion:

| Service | URL | Credentials |
|---------|-----|-------------|
| Trust Engine | http://localhost:5001 | Okta authentication |
| Kibana | http://localhost:5601 | elastic / trust-engine-elastic-password |
| Wazuh Dashboard | http://localhost:5602 | admin / SecretPassword |
| Elasticsearch API | http://localhost:9200 | elastic / trust-engine-elastic-password |
| Wazuh Manager API | https://localhost:55000 | wazuh-wui / MyS3cr37P450r.*- |

## Monitoring and Maintenance

### Health Checks

bash
# Check all services
./setup_trust_engine.sh status

# View service logs
./setup_trust_engine.sh logs

# Check Elasticsearch health
curl -u elastic:trust-engine-elastic-password http://localhost:9200/_cluster/health

# Check Wazuh API
curl -k https://localhost:55000/


### Index Management

bash
# List indices
curl -u elastic:trust-engine-elastic-password http://localhost:9200/_cat/indices?v

# Check index size
curl -u elastic:trust-engine-elastic-password http://localhost:9200/_cat/indices/*trust*?v&s=store.size:desc

# Delete old indices (automated via elasticsearch_integration.py)
python -c "from app.elasticsearch_integration import elasticsearch_integration; elasticsearch_integration.cleanup_old_indices(days_to_keep=30)"


### Performance Tuning

#### Elasticsearch Optimization

1. Memory Settings:
   yaml
   # In docker-compose.yml
   environment:
     - "ES_JAVA_OPTS=-Xms1g -Xmx1g"  # Increase for production
   

2. Index Settings:
   json
   {
     "settings": {
       "refresh_interval": "5s",    # Increase for higher throughput
       "number_of_replicas": 0      # No replicas for single-node
     }
   }
   

#### Kibana Optimization

1. Memory: Increase container memory limit
2. Caching: Enable query caching for dashboards
3. Refresh Intervals: Optimize based on data freshness needs

## Troubleshooting

### Common Issues

#### 1. Elasticsearch Won't Start

bash
# Check system limits
sysctl vm.max_map_count

# Should be >= 262144
sudo sysctl -w vm.max_map_count=262144

# Check disk space
df -h

# Check logs
docker logs trust-engine-elasticsearch


#### 2. Kibana Connection Issues

bash
# Verify Elasticsearch is running
curl -u elastic:trust-engine-elastic-password http://localhost:9200/_cluster/health

# Check Kibana logs
docker logs trust-engine-kibana

# Reset Kibana data
docker-compose down
docker volume rm docker_kibana-data
docker-compose up -d


#### 3. Wazuh Integration Issues

bash
# Test Wazuh API
curl -k -u wazuh-wui:MyS3cr37P450r.*- https://localhost:55000/

# Check Wazuh Manager logs
docker logs trust-engine-wazuh-manager

# Verify agent connectivity
# In Wazuh Dashboard: Management > Agents


#### 4. Trust Engine Application Issues

bash
# Check application logs
docker logs trust-engine-app

# Test database connections
python test_supabase.py
python test_wazuh_credentials.py

# Verify environment variables
docker exec trust-engine-app env | grep -E "(ELASTICSEARCH|WAZUH|SUPABASE|OKTA)"


### Performance Issues

#### High CPU Usage

bash
# Check container resource usage
docker stats

# Optimize Elasticsearch queries
# Add more specific filters to reduce data processing


#### High Memory Usage

bash
# Monitor memory usage
free -h

# Reduce Elasticsearch heap size if needed
# Increase refresh intervals
# Implement index lifecycle management


#### Slow Queries

bash
# Check slow queries in Elasticsearch
curl -u elastic:trust-engine-elastic-password http://localhost:9200/_cluster/settings?include_defaults=true

# Optimize index mappings
# Add appropriate filters to Kibana visualizations
# Consider index sharding for large datasets


## Security Considerations

### Production Deployment

1. Change Default Passwords:
   bash
   # Generate strong passwords
   ELASTIC_PASSWORD=$(openssl rand -base64 32)
   WAZUH_PASSWORD=$(openssl rand -base64 32)
   

2. Enable HTTPS:
   - Configure SSL certificates for all services
   - Use proper certificate authorities
   - Enable certificate verification

3. Network Security:
   - Use Docker secrets for sensitive data
   - Implement network segmentation
   - Configure firewall rules

4. Access Control:
   - Implement role-based access control
   - Use strong authentication methods
   - Regular security audits

### Data Protection

1. Encryption at Rest: Enable for Elasticsearch
2. Encryption in Transit: HTTPS/TLS for all communications
3. Data Retention: Implement lifecycle policies
4. Backup Strategy: Regular data backups

## Advanced Configuration

### Custom Wazuh Rules

Create custom rules for Trust Engine specific events:

xml
<!-- Local rules for Trust Engine -->
<group name="trust_engine,">
  
  <!-- Trust Score Low Alert -->
  <rule id="100001" level="8">
    <if_group>authentication_success</if_group>
    <field name="trust_score">^0\.[0-4]</field>
    <description>Low trust score detected: $(trust_score)</description>
    <mitre>
      <id>T1078</id>
    </mitre>
  </rule>

  <!-- MFA Step-up Required -->
  <rule id="100002" level="10">
    <if_group>authentication_failed</if_group>
    <field name="mfa_required">true</field>
    <description>MFA step-up required for session: $(session_id)</description>
  </rule>
  
</group>


### Elasticsearch Ingest Pipelines

Process data before indexing:

bash
# Create ingest pipeline for geolocation
curl -X PUT "localhost:9200/_ingest/pipeline/geoip-pipeline" \
     -H "Content-Type: application/json" \
     -u elastic:trust-engine-elastic-password \
     -d '{
       "description": "Add geoip info to logs",
       "processors": [
         {
           "geoip": {
             "field": "wazuh_agent_ip",
             "target_field": "geoip"
           }
         }
       ]
     }'


### Custom Kibana Visualizations

1. Heat Maps: Show threat intensity by location
2. Network Graphs: Visualize agent relationships
3. Time Series: Trend analysis for trust scores
4. Sankey Diagrams: Show authentication flow

## Integration Testing

### Automated Tests

python
# test_integration.py
import requests
import json
from datetime import datetime

def test_elasticsearch_integration():
    """Test Elasticsearch indexing and searching"""
    # Index test document
    doc = {
        "session_id": "test_session",
        "trust_score": 0.8,
        "@timestamp": datetime.utcnow().isoformat()
    }
    
    response = requests.post(
        "http://localhost:9200/trustscore-test/_doc",
        json=doc,
        auth=("elastic", "trust-engine-elastic-password")
    )
    assert response.status_code == 201

def test_wazuh_api():
    """Test Wazuh API connectivity"""
    response = requests.get(
        "https://localhost:55000/agents",
        auth=("wazuh-wui", "MyS3cr37P450r.*-"),
        verify=False
    )
    assert response.status_code == 200

def test_kibana_health():
    """Test Kibana health"""
    response = requests.get("http://localhost:5601/api/status")
    assert response.status_code == 200


### Manual Testing

bash
# Send test telemetry
curl -X POST http://localhost:5001/telemetry \
     -H "Content-Type: application/json" \
     -d '{
       "session_id": "test_session",
       "vm_id": "test_vm",
       "event_type": "login_attempt",
       "features": {"feature_1": 10.5, "feature_2": 20.1}
     }'

# Verify in Elasticsearch
curl -u elastic:trust-engine-elastic-password \
     "http://localhost:9200/telemetrydata-*/_search?q=session_id:test_session"

# Check in Kibana
# Navigate to Discover tab and search for test_session


## Conclusion

This integration provides a comprehensive security monitoring and adaptive authentication system. The combination of Wazuh's security monitoring, Elasticsearch's analytics capabilities, and Kibana's visualization tools creates a powerful platform for the Trust Engine.

Key benefits:
- Real-time Monitoring: Immediate visibility into security events
- Advanced Analytics: Deep insights into authentication patterns
- Scalable Architecture: Handles high-volume telemetry data
- Flexible Dashboards: Customizable visualizations for different stakeholders
- Automated Response: Dynamic MFA adjustments based on threat levels

For production deployment, ensure proper security hardening, performance tuning, and monitoring procedures are in place.