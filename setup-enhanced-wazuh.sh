#!/bin/bash

# Enhanced Wazuh Setup Script with Trust Engine Integration
# This script helps you integrate your working Wazuh with Trust Engine

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Enhanced Wazuh + Trust Engine Setup${NC}"
echo "=========================================="

# Check if working Wazuh directory exists
WAZUH_DIR="$HOME/wazuh-docker/single-node"
if [ ! -d "$WAZUH_DIR" ]; then
    echo -e "${RED}❌ Working Wazuh directory not found at: $WAZUH_DIR${NC}"
    echo "Please ensure your working Wazuh setup exists there."
    exit 1
fi

echo -e "${GREEN}✅ Found working Wazuh directory${NC}"

# Check if Trust Engine directory exists
TRUST_ENGINE_DIR="$HOME/Apps/trust_engine_app"
if [ ! -d "$TRUST_ENGINE_DIR" ]; then
    echo -e "${RED}❌ Trust Engine directory not found at: $TRUST_ENGINE_DIR${NC}"
    echo "Please ensure your Trust Engine setup exists there."
    exit 1
fi

echo -e "${GREEN}✅ Found Trust Engine directory${NC}"

# Stop any running containers from both setups
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
cd "$TRUST_ENGINE_DIR"
docker compose down 2>/dev/null || true

cd "$WAZUH_DIR"
docker compose down 2>/dev/null || true

echo -e "${GREEN}✅ Stopped existing containers${NC}"

# Copy .env file from Trust Engine to Wazuh directory
echo -e "${YELLOW}📋 Copying environment variables...${NC}"
if [ -f "$TRUST_ENGINE_DIR/.env" ]; then
    cp "$TRUST_ENGINE_DIR/.env" "$WAZUH_DIR/.env"
    echo -e "${GREEN}✅ Copied .env file${NC}"
else
    echo -e "${RED}❌ .env file not found in Trust Engine directory${NC}"
    echo "Please ensure your .env file exists with Supabase and Okta credentials."
    exit 1
fi

# Copy enhanced docker-compose.yml
echo -e "${YELLOW}📋 Setting up enhanced docker-compose.yml...${NC}"
if [ -f "$TRUST_ENGINE_DIR/enhanced-wazuh-compose.yml" ]; then
    cp "$TRUST_ENGINE_DIR/enhanced-wazuh-compose.yml" "$WAZUH_DIR/docker-compose-enhanced.yml"
    echo -e "${GREEN}✅ Copied enhanced docker-compose.yml${NC}"
else
    echo -e "${RED}❌ Enhanced docker-compose.yml not found${NC}"
    exit 1
fi

# Check SSL certificates
echo -e "${YELLOW}🔐 Checking SSL certificates...${NC}"
if [ -d "$WAZUH_DIR/config/wazuh_indexer_ssl_certs" ]; then
    echo -e "${GREEN}✅ SSL certificates found${NC}"
else
    echo -e "${RED}❌ SSL certificates not found${NC}"
    echo "Please run wazuh-certs-tool.sh first to generate SSL certificates."
    exit 1
fi

# Create a migration docker-compose with new ports
echo -e "${YELLOW}🔧 Creating port-adjusted setup...${NC}"

cat > "$WAZUH_DIR/docker-compose-integrated.yml" << 'EOF'
# Integrated Wazuh + Trust Engine Docker Compose
# This avoids port conflicts by using different ports
version: '3.7'

services:
  # Working Wazuh Manager (existing, keep on 55000)
  wazuh.manager:
    image: wazuh/wazuh-manager:4.12.0
    hostname: wazuh.manager
    restart: always
    ulimits:
      memlock:
        soft: -1
        hard: -1
      nofile:
        soft: 655360
        hard: 655360
    ports:
      - "1514:1514"
      - "1515:1515"
      - "514:514/udp"
      - "55000:55000"
    environment:
      - INDEXER_URL=https://wazuh.indexer:9200
      - INDEXER_USERNAME=admin
      - INDEXER_PASSWORD=SecretPassword
      - FILEBEAT_SSL_VERIFICATION_MODE=full
      - SSL_CERTIFICATE_AUTHORITIES=/etc/ssl/root-ca.pem
      - SSL_CERTIFICATE=/etc/ssl/filebeat.pem
      - SSL_KEY=/etc/ssl/filebeat.key
      - API_USERNAME=wazuh-wui
      - API_PASSWORD=MyS3cr37P450r.*-
    volumes:
      - wazuh_api_configuration:/var/ossec/api/configuration
      - wazuh_etc:/var/ossec/etc
      - wazuh_logs:/var/ossec/logs
      - wazuh_queue:/var/ossec/queue
      - wazuh_var_multigroups:/var/ossec/var/multigroups
      - wazuh_integrations:/var/ossec/integrations
      - wazuh_active_response:/var/ossec/active-response/bin
      - wazuh_agentless:/var/ossec/agentless
      - wazuh_wodles:/var/ossec/wodles
      - filebeat_etc:/etc/filebeat
      - filebeat_var:/var/lib/filebeat
      - ./config/wazuh_indexer_ssl_certs/root-ca-manager.pem:/etc/ssl/root-ca.pem
      - ./config/wazuh_indexer_ssl_certs/wazuh.manager.pem:/etc/ssl/filebeat.pem
      - ./config/wazuh_indexer_ssl_certs/wazuh.manager-key.pem:/etc/ssl/filebeat.key
      - ./config/wazuh_cluster/wazuh_manager.conf:/wazuh-config-mount/etc/ossec.conf
    networks:
      - integrated-network

  # Working Wazuh Indexer (move to port 9202 to avoid conflict)
  wazuh.indexer:
    image: wazuh/wazuh-indexer:4.12.0
    hostname: wazuh.indexer
    restart: always
    ports:
      - "9202:9200"  # Changed from 9200 to 9202
    environment:
      - "OPENSEARCH_JAVA_OPTS=-Xms1g -Xmx1g"
    ulimits:
      memlock:
        soft: -1
        hard: -1
      nofile:
        soft: 65536
        hard: 65536
    volumes:
      - wazuh-indexer-data:/var/lib/wazuh-indexer
      - ./config/wazuh_indexer_ssl_certs/root-ca.pem:/usr/share/wazuh-indexer/certs/root-ca.pem
      - ./config/wazuh_indexer_ssl_certs/wazuh.indexer-key.pem:/usr/share/wazuh-indexer/certs/wazuh.indexer.key
      - ./config/wazuh_indexer_ssl_certs/wazuh.indexer.pem:/usr/share/wazuh-indexer/certs/wazuh.indexer.pem
      - ./config/wazuh_indexer_ssl_certs/admin.pem:/usr/share/wazuh-indexer/certs/admin.pem
      - ./config/wazuh_indexer_ssl_certs/admin-key.pem:/usr/share/wazuh-indexer/certs/admin-key.pem
      - ./config/wazuh_indexer/wazuh.indexer.yml:/usr/share/wazuh-indexer/opensearch.yml
      - ./config/wazuh_indexer/internal_users.yml:/usr/share/wazuh-indexer/opensearch-security/internal_users.yml
    networks:
      - integrated-network

  # Working Wazuh Dashboard (keep on 443)
  wazuh.dashboard:
    image: wazuh/wazuh-dashboard:4.12.0
    hostname: wazuh.dashboard
    restart: always
    ports:
      - 443:5601
    environment:
      - INDEXER_USERNAME=admin
      - INDEXER_PASSWORD=SecretPassword
      - WAZUH_API_URL=https://wazuh.manager
      - DASHBOARD_USERNAME=kibanaserver
      - DASHBOARD_PASSWORD=kibanaserver
      - API_USERNAME=wazuh-wui
      - API_PASSWORD=MyS3cr37P450r.*-
    volumes:
      - ./config/wazuh_indexer_ssl_certs/wazuh.dashboard.pem:/usr/share/wazuh-dashboard/certs/wazuh-dashboard.pem
      - ./config/wazuh_indexer_ssl_certs/wazuh.dashboard-key.pem:/usr/share/wazuh-dashboard/certs/wazuh-dashboard-key.pem
      - ./config/wazuh_indexer_ssl_certs/root-ca.pem:/usr/share/wazuh-dashboard/certs/root-ca.pem
      - ./config/wazuh_dashboard/opensearch_dashboards.yml:/usr/share/wazuh-dashboard/config/opensearch_dashboards.yml
      - ./config/wazuh_dashboard/wazuh.yml:/usr/share/wazuh-dashboard/data/wazuh/config/wazuh.yml
      - wazuh-dashboard-config:/usr/share/wazuh-dashboard/data/wazuh/config
      - wazuh-dashboard-custom:/usr/share/wazuh-dashboard/plugins/wazuh/public/assets/custom
    depends_on:
      - wazuh.indexer
    networks:
      - integrated-network

  # Trust Engine Elasticsearch (on port 9200)
  trust-elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.17.9
    container_name: trust-elasticsearch
    hostname: trust-elasticsearch
    environment:
      - node.name=trust-elasticsearch
      - cluster.name=trust-engine-cluster
      - discovery.type=single-node
      - bootstrap.memory_lock=true
      - "ES_JAVA_OPTS=-Xms1g -Xmx2g"
      - xpack.security.enabled=true
      - ELASTIC_PASSWORD=trust-engine-elastic-password
      - xpack.security.authc.api_key.enabled=true
      - xpack.security.http.ssl.enabled=false
      - xpack.security.transport.ssl.enabled=false
    ulimits:
      memlock:
        soft: -1
        hard: -1
    volumes:
      - trust-elasticsearch-data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"  # Trust Engine gets port 9200
      - "9300:9300"
    networks:
      - integrated-network
    healthcheck:
      test: ["CMD-SHELL", "curl -u elastic:trust-engine-elastic-password -f http://localhost:9200/_cluster/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Trust Engine Kibana
  trust-kibana:
    image: docker.elastic.co/kibana/kibana:7.17.9
    container_name: trust-kibana
    hostname: trust-kibana
    environment:
      - SERVERNAME=trust-kibana
      - ELASTICSEARCH_HOSTS=http://trust-elasticsearch:9200
      - ELASTICSEARCH_USERNAME=elastic
      - ELASTICSEARCH_PASSWORD=trust-engine-elastic-password
      - xpack.security.enabled=true
      - xpack.encryptedSavedObjects.encryptionKey=trust-engine-kibana-encryption-key-32-chars
      - server.ssl.enabled=false
    volumes:
      - trust-kibana-data:/usr/share/kibana/data
    ports:
      - "5601:5601"
    networks:
      - integrated-network
    depends_on:
      trust-elasticsearch:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:5601/api/status || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Trust Engine Application
  trust-engine-app:
    build:
      context: /Users/knight/Apps/trust_engine_app
      dockerfile: docker/Dockerfile
    container_name: trust-engine-app
    hostname: trust-engine-app
    environment:
      - FLASK_ENV=development
      - FLASK_DEBUG=1
      - FLASK_USE_SSL=false
      - ELASTICSEARCH_URL=http://trust-elasticsearch:9200
      - ELASTICSEARCH_USERNAME=elastic
      - ELASTICSEARCH_PASSWORD=trust-engine-elastic-password
      - ELASTICSEARCH_SSL_VERIFY=false
      - WAZUH_API_URL=https://wazuh.manager:55000
      - WAZUH_API_USERNAME=wazuh-wui
      - WAZUH_API_PASSWORD=MyS3cr37P450r.*-
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_API_KEY=${SUPABASE_API_KEY}
      - OKTA_ISSUER=${OKTA_ISSUER}
      - OKTA_CLIENT_ID=${OKTA_CLIENT_ID}
      - OKTA_CLIENT_SECRET=${OKTA_CLIENT_SECRET}
      - OKTA_REDIRECT_URI=http://localhost:5001/authorization-code/callback
      - OKTA_AUDIENCE=${OKTA_AUDIENCE}
    ports:
      - "5001:5001"
    volumes:
      - /Users/knight/Apps/trust_engine_app:/app
    networks:
      - integrated-network
    depends_on:
      trust-elasticsearch:
        condition: service_healthy
      wazuh.manager:
        condition: service_started
    command: ["python", "run.py"]

networks:
  integrated-network:
    driver: bridge

volumes:
  # Existing Wazuh volumes
  wazuh_api_configuration:
  wazuh_etc:
  wazuh_logs:
  wazuh_queue:
  wazuh_var_multigroups:
  wazuh_integrations:
  wazuh_active_response:
  wazuh_agentless:
  wazuh_wodles:
  filebeat_etc:
  filebeat_var:
  wazuh-indexer-data:
  wazuh-dashboard-config:
  wazuh-dashboard-custom:

  # New Trust Engine volumes
  trust-elasticsearch-data:
    driver: local
  trust-kibana-data:
    driver: local
EOF

echo -e "${GREEN}✅ Created integrated docker-compose.yml${NC}"

# Display next steps
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "1. Navigate to your Wazuh directory:"
echo "   cd $WAZUH_DIR"
echo ""
echo "2. Start the integrated setup:"
echo "   docker compose -f docker-compose-integrated.yml up -d"
echo ""
echo -e "${BLUE}🌐 Access Points:${NC}"
echo "• Wazuh Dashboard (SSL):    https://localhost"
echo "• Trust Engine API:         http://localhost:5001"
echo "• Trust Engine Elasticsearch: http://localhost:9200"
echo "• Trust Engine Kibana:      http://localhost:5601"
echo "• Wazuh Indexer:           http://localhost:9202"
echo "• Wazuh Manager API:       https://localhost:55000"
echo ""
echo -e "${BLUE}🔧 Port Mapping:${NC}"
echo "• 443  → Wazuh Dashboard (HTTPS)"
echo "• 5001 → Trust Engine App"
echo "• 5601 → Trust Engine Kibana"
echo "• 9200 → Trust Engine Elasticsearch"
echo "• 9202 → Wazuh Indexer (moved from 9200)"
echo "• 55000 → Wazuh Manager API"
echo ""
echo -e "${GREEN}🎉 Setup completed successfully!${NC}"
echo -e "${YELLOW}💡 Your working Wazuh SSL certificates will be preserved.${NC}"

# Set execute permission on this script
chmod +x "$0"
