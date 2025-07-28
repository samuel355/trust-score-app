#!/bin/bash

# Trust Engine Setup Script
# This script sets up the complete Trust Engine environment with Wazuh, Elasticsearch, and Kibana integration

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TRUST_ENGINE_DIR=$(pwd)
DOCKER_DIR="$TRUST_ENGINE_DIR/docker"
KIBANA_DIR="$TRUST_ENGINE_DIR/kibana"
SSL_DIR="$DOCKER_DIR/ssl"
ENV_FILE="$TRUST_ENGINE_DIR/.env"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Trust Engine Setup Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if Docker and Docker Compose are installed
check_dependencies() {
    print_step "Checking dependencies..."

    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    print_status "Docker and Docker Compose are installed."
}

# Check if .env file exists and create if not
setup_environment() {
    print_step "Setting up environment variables..."

    if [ ! -f "$ENV_FILE" ]; then
        print_warning ".env file not found. Creating template..."
        cat > "$ENV_FILE" << EOF
# Trust Engine Environment Configuration

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

# Elasticsearch Configuration (HTTPS Auto-configured for Docker)
ELASTICSEARCH_URL=https://elasticsearch:9200
ELASTICSEARCH_USERNAME=elastic
ELASTICSEARCH_PASSWORD=trust-engine-elastic-password
ELASTICSEARCH_SSL_VERIFY=false

# Wazuh Configuration (HTTPS Auto-configured for Docker)
WAZUH_API_URL=https://wazuh-manager:55000
WAZUH_API_USERNAME=wazuh-wui
WAZUH_API_PASSWORD=MyS3cr37P450r.*-
WAZUH_SSL_VERIFY=false

# Flask HTTPS Configuration
FLASK_USE_SSL=true
FLASK_SSL_CERT=docker/ssl/certs/trust-engine-cert.pem
FLASK_SSL_KEY=docker/ssl/private/trust-engine-key.pem

# Updated Okta Redirect URI for HTTPS
OKTA_REDIRECT_URI=https://localhost:5001/authorization-code/callback
EOF
        print_warning "Please edit .env file with your actual credentials before continuing."
        print_warning "Pay special attention to SUPABASE_URL, SUPABASE_API_KEY, and OKTA_* variables."
        echo ""
        read -p "Press Enter after updating .env file to continue..."
    else
        print_status ".env file already exists."
    fi
}

# Create Docker network if it doesn't exist
setup_docker_network() {
    print_step "Setting up Docker network..."

    if ! docker network ls | grep -q "trust-engine-network"; then
        docker network create trust-engine-network
        print_status "Created trust-engine-network."
    else
        print_status "trust-engine-network already exists."
    fi
}

# Generate SSL certificates
generate_ssl_certificates() {
    print_step "Generating SSL certificates for HTTPS..."

    if [ ! -f "$SSL_DIR/ca/ca-cert.pem" ]; then
        print_status "Generating SSL certificates..."
        cd "$SSL_DIR"
        ./generate_certificates.sh
        cd "$TRUST_ENGINE_DIR"
        print_status "SSL certificates generated successfully."
    else
        print_status "SSL certificates already exist."
    fi
}

# Setup system limits for Elasticsearch
setup_system_limits() {
    print_step "Configuring system limits for Elasticsearch..."

    # Check and set vm.max_map_count
    current_limit=$(sysctl vm.max_map_count | cut -d' ' -f3)
    required_limit=262144

    if [ "$current_limit" -lt "$required_limit" ]; then
        print_warning "vm.max_map_count is too low ($current_limit). Setting to $required_limit..."
        sudo sysctl -w vm.max_map_count=$required_limit

        # Make it permanent
        echo "vm.max_map_count=$required_limit" | sudo tee -a /etc/sysctl.conf > /dev/null
        print_status "vm.max_map_count configured permanently."
    else
        print_status "vm.max_map_count is already configured correctly."
    fi
}

# Install Python dependencies
install_python_deps() {
    print_step "Installing Python dependencies..."

    if [ -f "requirements.txt" ]; then
        # Check if virtual environment exists
        if [ ! -d "venv" ]; then
            print_status "Creating Python virtual environment..."
            python3 -m venv venv
        fi

        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
        print_status "Python dependencies installed."
    else
        print_warning "requirements.txt not found. Skipping Python dependencies."
    fi
}

# Start Docker services
start_services() {
    print_step "Starting Docker services..."

    cd "$DOCKER_DIR"

    # Pull images first
    print_status "Pulling Docker images..."
    docker-compose pull

    # Start services
    print_status "Starting services..."
    docker-compose up -d

    cd "$TRUST_ENGINE_DIR"

    print_status "Docker services started."
}

# Wait for services to be ready
wait_for_services() {
    print_step "Waiting for services to be ready..."

    # Wait for Elasticsearch (HTTPS)
    print_status "Waiting for Elasticsearch..."
    timeout=300
    counter=0
    while ! curl -s -k -u elastic:trust-engine-elastic-password https://localhost:9200/_cluster/health > /dev/null; do
        sleep 5
        counter=$((counter + 5))
        if [ $counter -ge $timeout ]; then
            print_error "Elasticsearch failed to start within $timeout seconds."
            exit 1
        fi
        echo -n "."
    done
    echo ""
    print_status "Elasticsearch is ready."

    # Wait for Kibana (HTTPS)
    print_status "Waiting for Kibana..."
    counter=0
    while ! curl -s -k https://localhost:5601/api/status > /dev/null; do
        sleep 5
        counter=$((counter + 5))
        if [ $counter -ge $timeout ]; then
            print_error "Kibana failed to start within $timeout seconds."
            exit 1
        fi
        echo -n "."
    done
    echo ""
    print_status "Kibana is ready."
    # Wait for Wazuh Manager
    print_status "Waiting for Wazuh Manager..."
    counter=0
    while ! curl -s -k https://localhost:55000/ > /dev/null; do
        sleep 5
        counter=$((counter + 5))
        if [ $counter -ge $timeout ]; then
            print_warning "Wazuh Manager may not be ready yet. Continuing..."
            break
        fi
        echo -n "."
    done
    echo ""
    print_status "Wazuh Manager should be ready."
}

# Import Kibana dashboards
import_kibana_dashboards() {
    print_step "Importing Kibana dashboards..."

    if [ -f "$KIBANA_DIR/trust_engine_dashboards.json" ]; then
        # Wait a bit more for Kibana to fully initialize
        sleep 30

        # Import dashboards using curl
        curl -X POST "https://localhost:5601/api/saved_objects/_import" \
             -H "kbn-xsrf: true" \
             -H "Content-Type: application/json" \
             -k \
             --form file=@"$KIBANA_DIR/trust_engine_dashboards.json" \
             --user elastic:trust-engine-elastic-password

        if [ $? -eq 0 ]; then
            print_status "Kibana dashboards imported successfully."
        else
            print_warning "Failed to import Kibana dashboards. You can import them manually."
        fi
    else
        print_warning "Kibana dashboard file not found. Skipping dashboard import."
    fi
}

# Create Elasticsearch index templates
setup_elasticsearch_templates() {
    print_step "Setting up Elasticsearch index templates..."

    # Telemetry data template
    curl -X PUT "https://localhost:9200/_index_template/trust-engine-telemetry" \
         -H "Content-Type: application/json" \
         -u elastic:trust-engine-elastic-password \
         -k \
         -d '{
           "index_patterns": ["telemetrydata-*"],
           "template": {
             "settings": {
               "number_of_shards": 1,
               "number_of_replicas": 0,
               "refresh_interval": "1s"
             },
             "mappings": {
               "properties": {
                 "@timestamp": {"type": "date"},
                 "session_id": {"type": "keyword"},
                 "vm_id": {"type": "keyword"},
                 "vm_agent_id": {"type": "keyword"},
                 "timestamp": {"type": "date"},
                 "event_type": {"type": "keyword"},
                 "stride_category": {"type": "keyword"},
                 "risk_level": {"type": "integer"},
                 "trust_score": {"type": "float"},
                 "features": {"type": "object"},
                 "wazuh_alert_id": {"type": "keyword"},
                 "wazuh_rule_id": {"type": "integer"},
                 "wazuh_rule_level": {"type": "integer"},
                 "wazuh_agent_name": {"type": "keyword"},
                 "wazuh_agent_ip": {"type": "ip"}
               }
             }
           }
         }' > /dev/null

    # Trust score template
    curl -X PUT "https://localhost:9200/_index_template/trust-engine-trustscore" \
         -H "Content-Type: application/json" \
         -u elastic:trust-engine-elastic-password \
         -k \
         -d '{
           "index_patterns": ["trustscore-*"],
           "template": {
             "settings": {
               "number_of_shards": 1,
               "number_of_replicas": 0,
               "refresh_interval": "5s"
             },
             "mappings": {
               "properties": {
                 "@timestamp": {"type": "date"},
                 "session_id": {"type": "keyword"},
                 "user_id": {"type": "keyword"},
                 "vm_id": {"type": "keyword"},
                 "timestamp": {"type": "date"},
                 "trust_score": {"type": "float"},
                 "risk_level": {"type": "keyword"},
                 "mfa_level": {"type": "keyword"},
                 "stride_scores": {"type": "object"},
                 "action_taken": {"type": "keyword"},
                 "telemetry_count": {"type": "integer"}
               }
             }
           }
         }' > /dev/null

    # Wazuh alerts template
    curl -X PUT "https://localhost:9200/_index_template/trust-engine-wazuh-alerts" \
         -H "Content-Type: application/json" \
         -u elastic:trust-engine-elastic-password \
         -k \
         -d '{
           "index_patterns": ["wazuh_alerts-*"],
           "template": {
             "settings": {
               "number_of_shards": 1,
               "number_of_replicas": 0,
               "refresh_interval": "1s"
             },
             "mappings": {
               "properties": {
                 "@timestamp": {"type": "date"},
                 "alert_id": {"type": "keyword"},
                 "timestamp": {"type": "date"},
                 "agent_id": {"type": "keyword"},
                 "agent_name": {"type": "keyword"},
                 "agent_ip": {"type": "ip"},
                 "rule_id": {"type": "integer"},
                 "rule_level": {"type": "integer"},
                 "rule_description": {"type": "text"},
                 "full_log": {"type": "text"},
                 "location": {"type": "keyword"},
                 "stride_category": {"type": "keyword"},
                 "mitre_attack": {"type": "object"}
               }
             }
           }
         }' > /dev/null

    print_status "Elasticsearch index templates created."
}

# Test the integration
test_integration() {
    print_step "Testing Trust Engine integration..."

    # Test Elasticsearch connection (HTTPS)
    if curl -s -k -u elastic:trust-engine-elastic-password https://localhost:9200/_cluster/health | grep -q "yellow\|green"; then
        print_status "✓ Elasticsearch is healthy."
    else
        print_error "✗ Elasticsearch health check failed."
        return 1
    fi

    # Test Kibana (HTTPS)
    if curl -s -k https://localhost:5601/api/status | grep -q "All services are available"; then
        print_status "✓ Kibana is healthy."
    else
        print_warning "⚠ Kibana may not be fully ready yet."
    fi

    # Test Wazuh Manager API
    if curl -s -k https://localhost:55000/ | grep -q "Wazuh"; then
        print_status "✓ Wazuh Manager is responding."
    else
        print_warning "⚠ Wazuh Manager may not be fully ready yet."
    fi

    # Test Trust Engine application (HTTPS)
    if curl -s -k https://localhost:5001/health > /dev/null 2>&1; then
        print_status "✓ Trust Engine application is running."
    else
        print_warning "⚠ Trust Engine application is not running yet."
    fi
}

# Show service URLs and credentials
show_access_info() {
    print_step "Service Access Information"
    echo ""
    echo -e "${GREEN}Service URLs (HTTPS):${NC}"
    echo "  • Trust Engine Application: https://localhost:5001"
    echo "  • Kibana Dashboard:         https://localhost:5601"
    echo "  • Wazuh Dashboard:          https://localhost:5602"
    echo "  • Elasticsearch API:       https://localhost:9200"
    echo "  • Wazuh Manager API:        https://localhost:55000"
    echo ""
    echo -e "${GREEN}Default Credentials:${NC}"
    echo "  • Elasticsearch: elastic / trust-engine-elastic-password"
    echo "  • Wazuh API: wazuh-wui / MyS3cr37P450r.*-"
    echo "  • Wazuh Dashboard: admin / SecretPassword"
    echo ""
    echo -e "${YELLOW}Important Notes:${NC}"
    echo "  • All services are configured with HTTPS and SSL certificates"
    echo "  • For browsers: Import docker/ssl/ca/ca-cert.pem as trusted CA"
    echo "  • Make sure to update your .env file with real Supabase and Okta credentials"
    echo "  • Change default passwords in production"
    echo "  • Allow services 2-3 minutes to fully initialize"
    echo "  • Check logs with: docker-compose -f docker/docker-compose.yml logs -f"
    echo ""
}

# Main execution
main() {
    print_step "Starting Trust Engine setup..."
    echo ""

    check_dependencies
    setup_environment
    generate_ssl_certificates
    setup_system_limits
    setup_docker_network
    install_python_deps
    start_services
    wait_for_services
    setup_elasticsearch_templates
    import_kibana_dashboards
    test_integration

    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Trust Engine Setup Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""

    show_access_info
}

# Handle script arguments
case "${1:-}" in
    "stop")
        print_step "Stopping Trust Engine services..."
        cd "$DOCKER_DIR"
        docker-compose down
        print_status "Services stopped."
        ;;
    "restart")
        print_step "Restarting Trust Engine services..."
        cd "$DOCKER_DIR"
        docker-compose restart
        print_status "Services restarted."
        ;;
    "logs")
        cd "$DOCKER_DIR"
        docker-compose logs -f
        ;;
    "status")
        cd "$DOCKER_DIR"
        docker-compose ps
        ;;
    "clean")
        print_warning "This will remove all containers, volumes, and data!"
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cd "$DOCKER_DIR"
            docker-compose down -v --remove-orphans
            docker system prune -f
            print_status "Cleanup complete."
        fi
        ;;
    "")
        main
        ;;
    *)
        echo "Usage: $0 [stop|restart|logs|status|clean]"
        echo ""
        echo "Commands:"
        echo "  (no args)  - Setup and start Trust Engine"
        echo "  stop       - Stop all services"
        echo "  restart    - Restart all services"
        echo "  logs       - Show service logs"
        echo "  status     - Show service status"
        echo "  clean      - Remove all containers and data"
        exit 1
        ;;
esac
