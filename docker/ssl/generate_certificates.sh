#!/bin/bash

# SSL Certificate Generation Script for Trust Engine HTTPS Setup
# This script generates self-signed certificates for all Trust Engine services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SSL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERTS_DIR="$SSL_DIR/certs"
KEYS_DIR="$SSL_DIR/private"
CA_DIR="$SSL_DIR/ca"

# Certificate configuration
COUNTRY="US"
STATE="CA"
CITY="San Francisco"
ORG="Trust Engine"
OU="Security Department"
EMAIL="admin@trustengine.local"

# Certificate validity (days)
CA_DAYS=3650
CERT_DAYS=365

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

# Create directory structure
create_directories() {
    print_step "Creating SSL directory structure..."

    mkdir -p "$CERTS_DIR"
    mkdir -p "$KEYS_DIR"
    mkdir -p "$CA_DIR"

    # Set secure permissions
    chmod 700 "$KEYS_DIR"
    chmod 755 "$CERTS_DIR"
    chmod 755 "$CA_DIR"

    print_status "SSL directories created successfully."
}

# Generate Certificate Authority (CA)
generate_ca() {
    print_step "Generating Certificate Authority (CA)..."

    # Generate CA private key
    openssl genrsa -out "$CA_DIR/ca-key.pem" 4096
    chmod 400 "$CA_DIR/ca-key.pem"

    # Generate CA certificate
    openssl req -new -x509 -days $CA_DAYS -key "$CA_DIR/ca-key.pem" \
        -out "$CA_DIR/ca-cert.pem" \
        -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/OU=$OU CA/CN=Trust Engine CA/emailAddress=$EMAIL"

    chmod 444 "$CA_DIR/ca-cert.pem"

    print_status "Certificate Authority created successfully."
}

# Generate server certificate
generate_server_cert() {
    local service_name="$1"
    local common_name="$2"
    local san_entries="$3"

    print_step "Generating certificate for $service_name..."

    # Generate private key
    openssl genrsa -out "$KEYS_DIR/${service_name}-key.pem" 2048
    chmod 400 "$KEYS_DIR/${service_name}-key.pem"

    # Create certificate signing request
    openssl req -new -key "$KEYS_DIR/${service_name}-key.pem" \
        -out "$SSL_DIR/${service_name}-csr.pem" \
        -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/OU=$OU/CN=$common_name/emailAddress=$EMAIL"

    # Create extensions file for SAN
    cat > "$SSL_DIR/${service_name}-extensions.cnf" << EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
$san_entries
EOF

    # Generate certificate signed by CA
    openssl x509 -req -in "$SSL_DIR/${service_name}-csr.pem" \
        -CA "$CA_DIR/ca-cert.pem" \
        -CAkey "$CA_DIR/ca-key.pem" \
        -CAcreateserial \
        -out "$CERTS_DIR/${service_name}-cert.pem" \
        -days $CERT_DAYS \
        -extensions v3_req \
        -extfile "$SSL_DIR/${service_name}-extensions.cnf"

    chmod 444 "$CERTS_DIR/${service_name}-cert.pem"

    # Clean up temporary files
    rm "$SSL_DIR/${service_name}-csr.pem"
    rm "$SSL_DIR/${service_name}-extensions.cnf"

    print_status "Certificate for $service_name created successfully."
}

# Generate certificates for all services
generate_all_certificates() {
    print_step "Generating certificates for all Trust Engine services..."

    # Elasticsearch certificate
    generate_server_cert "elasticsearch" "elasticsearch" \
"DNS.1=elasticsearch
DNS.2=localhost
DNS.3=trust-engine-elasticsearch
IP.1=127.0.0.1
IP.2=::1"

    # Kibana certificate
    generate_server_cert "kibana" "kibana" \
"DNS.1=kibana
DNS.2=localhost
DNS.3=trust-engine-kibana
IP.1=127.0.0.1
IP.2=::1"

    # Trust Engine application certificate
    generate_server_cert "trust-engine" "trust-engine" \
"DNS.1=trust-engine
DNS.2=localhost
DNS.3=trust-engine-app
IP.1=127.0.0.1
IP.2=::1"

    # Wazuh Manager certificate
    generate_server_cert "wazuh-manager" "wazuh-manager" \
"DNS.1=wazuh-manager
DNS.2=localhost
DNS.3=trust-engine-wazuh-manager
IP.1=127.0.0.1
IP.2=::1"

    # Wazuh Dashboard certificate
    generate_server_cert "wazuh-dashboard" "wazuh-dashboard" \
"DNS.1=wazuh-dashboard
DNS.2=localhost
DNS.3=trust-engine-wazuh-dashboard
IP.1=127.0.0.1
IP.2=::1"

    # Wazuh Indexer certificate
    generate_server_cert "wazuh-indexer" "wazuh-indexer" \
"DNS.1=wazuh-indexer
DNS.2=localhost
DNS.3=trust-engine-wazuh-indexer
IP.1=127.0.0.1
IP.2=::1"
}

# Create combined certificate files for some services
create_combined_certs() {
    print_step "Creating combined certificate files..."

    # Combined cert + CA for Elasticsearch
    cat "$CERTS_DIR/elasticsearch-cert.pem" "$CA_DIR/ca-cert.pem" > "$CERTS_DIR/elasticsearch-fullchain.pem"

    # Combined cert + CA for Kibana
    cat "$CERTS_DIR/kibana-cert.pem" "$CA_DIR/ca-cert.pem" > "$CERTS_DIR/kibana-fullchain.pem"

    # Combined cert + CA for Trust Engine
    cat "$CERTS_DIR/trust-engine-cert.pem" "$CA_DIR/ca-cert.pem" > "$CERTS_DIR/trust-engine-fullchain.pem"

    # Combined cert + CA for Wazuh services
    cat "$CERTS_DIR/wazuh-manager-cert.pem" "$CA_DIR/ca-cert.pem" > "$CERTS_DIR/wazuh-manager-fullchain.pem"
    cat "$CERTS_DIR/wazuh-dashboard-cert.pem" "$CA_DIR/ca-cert.pem" > "$CERTS_DIR/wazuh-dashboard-fullchain.pem"
    cat "$CERTS_DIR/wazuh-indexer-cert.pem" "$CA_DIR/ca-cert.pem" > "$CERTS_DIR/wazuh-indexer-fullchain.pem"

    print_status "Combined certificate files created."
}

# Generate PKCS#12 keystores for Java applications
generate_keystores() {
    print_step "Generating PKCS#12 keystores..."

    # Elasticsearch keystore
    openssl pkcs12 -export -in "$CERTS_DIR/elasticsearch-cert.pem" \
        -inkey "$KEYS_DIR/elasticsearch-key.pem" \
        -out "$CERTS_DIR/elasticsearch-keystore.p12" \
        -name elasticsearch \
        -CAfile "$CA_DIR/ca-cert.pem" \
        -caname "Trust Engine CA" \
        -password pass:trust-engine-keystore-password

    # Wazuh Indexer keystore
    openssl pkcs12 -export -in "$CERTS_DIR/wazuh-indexer-cert.pem" \
        -inkey "$KEYS_DIR/wazuh-indexer-key.pem" \
        -out "$CERTS_DIR/wazuh-indexer-keystore.p12" \
        -name wazuh-indexer \
        -CAfile "$CA_DIR/ca-cert.pem" \
        -caname "Trust Engine CA" \
        -password pass:trust-engine-keystore-password

    print_status "PKCS#12 keystores created."
}

# Generate client certificates for authentication
generate_client_certs() {
    print_step "Generating client certificates..."

    # Admin client certificate
    generate_server_cert "admin-client" "admin" \
"DNS.1=admin
DNS.2=localhost"

    # Trust Engine client certificate
    generate_server_cert "trust-engine-client" "trust-engine-client" \
"DNS.1=trust-engine-client
DNS.2=localhost"

    print_status "Client certificates created."
}

# Create certificate information file
create_cert_info() {
    print_step "Creating certificate information file..."

    cat > "$SSL_DIR/certificate_info.txt" << EOF
Trust Engine SSL Certificate Information
========================================

Generated: $(date)
Validity: $CERT_DAYS days
CA Validity: $CA_DAYS days

Certificate Authority (CA):
- Certificate: $CA_DIR/ca-cert.pem
- Private Key: $CA_DIR/ca-key.pem

Service Certificates:
- Elasticsearch: $CERTS_DIR/elasticsearch-cert.pem ($KEYS_DIR/elasticsearch-key.pem)
- Kibana: $CERTS_DIR/kibana-cert.pem ($KEYS_DIR/kibana-key.pem)
- Trust Engine: $CERTS_DIR/trust-engine-cert.pem ($KEYS_DIR/trust-engine-key.pem)
- Wazuh Manager: $CERTS_DIR/wazuh-manager-cert.pem ($KEYS_DIR/wazuh-manager-key.pem)
- Wazuh Dashboard: $CERTS_DIR/wazuh-dashboard-cert.pem ($KEYS_DIR/wazuh-dashboard-key.pem)
- Wazuh Indexer: $CERTS_DIR/wazuh-indexer-cert.pem ($KEYS_DIR/wazuh-indexer-key.pem)

Client Certificates:
- Admin Client: $CERTS_DIR/admin-client-cert.pem ($KEYS_DIR/admin-client-key.pem)
- Trust Engine Client: $CERTS_DIR/trust-engine-client-cert.pem ($KEYS_DIR/trust-engine-client-key.pem)

Keystores:
- Elasticsearch: $CERTS_DIR/elasticsearch-keystore.p12 (password: trust-engine-keystore-password)
- Wazuh Indexer: $CERTS_DIR/wazuh-indexer-keystore.p12 (password: trust-engine-keystore-password)

Installation Notes:
1. Add the CA certificate to your system's trusted root certificates
2. For browsers, import ca-cert.pem as a trusted CA
3. Use the service certificates in Docker Compose configuration
4. Update application configurations to use HTTPS URLs

Security Notes:
- These are self-signed certificates suitable for development/testing
- For production, use certificates from a trusted CA
- Keep private keys secure and never share them
- Regularly rotate certificates before expiration

Commands to verify certificates:
openssl x509 -in $CERTS_DIR/elasticsearch-cert.pem -text -noout
openssl verify -CAfile $CA_DIR/ca-cert.pem $CERTS_DIR/elasticsearch-cert.pem
EOF

    print_status "Certificate information file created."
}

# Set proper file permissions
set_permissions() {
    print_step "Setting proper file permissions..."

    # CA files
    chmod 400 "$CA_DIR/ca-key.pem"
    chmod 444 "$CA_DIR/ca-cert.pem"

    # Private keys (read-only for owner)
    find "$KEYS_DIR" -name "*.pem" -exec chmod 400 {} \;

    # Certificates (world-readable)
    find "$CERTS_DIR" -name "*.pem" -exec chmod 444 {} \;

    # Keystores (read-only for owner)
    find "$CERTS_DIR" -name "*.p12" -exec chmod 400 {} \;

    print_status "File permissions set correctly."
}

# Verify generated certificates
verify_certificates() {
    print_step "Verifying generated certificates..."

    local services=("elasticsearch" "kibana" "trust-engine" "wazuh-manager" "wazuh-dashboard" "wazuh-indexer")
    local verification_failed=0

    for service in "${services[@]}"; do
        if openssl verify -CAfile "$CA_DIR/ca-cert.pem" "$CERTS_DIR/${service}-cert.pem" > /dev/null 2>&1; then
            print_status "✓ $service certificate verified successfully"
        else
            print_error "✗ $service certificate verification failed"
            verification_failed=1
        fi
    done

    if [ $verification_failed -eq 0 ]; then
        print_status "All certificates verified successfully!"
    else
        print_error "Some certificates failed verification. Please check the logs."
        return 1
    fi
}

# Main execution
main() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Trust Engine SSL Certificate Generator${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    print_status "Starting SSL certificate generation for Trust Engine HTTPS setup..."
    echo ""

    # Check if OpenSSL is available
    if ! command -v openssl &> /dev/null; then
        print_error "OpenSSL is not installed. Please install OpenSSL first."
        exit 1
    fi

    # Ask for confirmation if certificates already exist
    if [ -d "$CERTS_DIR" ] && [ "$(ls -A $CERTS_DIR 2>/dev/null)" ]; then
        print_warning "Existing certificates found. This will overwrite them."
        read -p "Continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Certificate generation cancelled."
            exit 0
        fi
        rm -rf "$CERTS_DIR"/* "$KEYS_DIR"/* "$CA_DIR"/*
    fi

    # Generate all certificates
    create_directories
    generate_ca
    generate_all_certificates
    generate_client_certs
    create_combined_certs
    generate_keystores
    create_cert_info
    set_permissions
    verify_certificates

    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}SSL Certificate Generation Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""

    print_status "Certificates have been generated successfully."
    print_status "Certificate information saved to: $SSL_DIR/certificate_info.txt"
    print_warning "For browsers to trust these certificates, add $CA_DIR/ca-cert.pem as a trusted CA."
    print_warning "For production use, replace these self-signed certificates with ones from a trusted CA."

    echo ""
    print_step "Next steps:"
    echo "1. Update Docker Compose configuration to use these certificates"
    echo "2. Update application environment variables to use HTTPS URLs"
    echo "3. Import the CA certificate in your browser/system"
    echo "4. Restart the Trust Engine services"
    echo ""
}

# Handle script arguments
case "${1:-}" in
    "clean")
        print_step "Cleaning up SSL certificates..."
        rm -rf "$CERTS_DIR" "$KEYS_DIR" "$CA_DIR"
        rm -f "$SSL_DIR/certificate_info.txt"
        print_status "SSL certificates cleaned up."
        ;;
    "verify")
        if [ -f "$CA_DIR/ca-cert.pem" ]; then
            verify_certificates
        else
            print_error "No certificates found. Run without arguments to generate certificates first."
            exit 1
        fi
        ;;
    "info")
        if [ -f "$SSL_DIR/certificate_info.txt" ]; then
            cat "$SSL_DIR/certificate_info.txt"
        else
            print_error "Certificate information file not found. Generate certificates first."
            exit 1
        fi
        ;;
    "")
        main
        ;;
    *)
        echo "Usage: $0 [clean|verify|info]"
        echo ""
        echo "Commands:"
        echo "  (no args)  - Generate SSL certificates for all services"
        echo "  clean      - Remove all generated certificates"
        echo "  verify     - Verify existing certificates"
        echo "  info       - Show certificate information"
        exit 1
        ;;
esac
