#!/bin/bash

set -e

# Set directory structure
ROOT_DIR="$(dirname "$0")/../.."
SSL_DIR="$ROOT_DIR/ssl"
CA_DIR="$SSL_DIR/ca"
CERTS_DIR="$SSL_DIR/certs"
PRIVATE_DIR="$SSL_DIR/private"

# Create directories
mkdir -p "$CA_DIR" "$CERTS_DIR" "$PRIVATE_DIR"

# Function to generate a certificate
generate_cert() {
  local SERVICE_NAME="$1"
  local COMMON_NAME="$2"

  echo "Generating certificate for $SERVICE_NAME..."

  # Generate key
  openssl genrsa -out "$PRIVATE_DIR/$SERVICE_NAME-key.pem" 2048
  if [ $? -ne 0 ]; then
    echo "Error generating key for $SERVICE_NAME" >&2
    exit 1
  fi
  chmod 400 "$PRIVATE_DIR/$SERVICE_NAME-key.pem"

  # Generate CSR
  openssl req -new -key "$PRIVATE_DIR/$SERVICE_NAME-key.pem" \
    -out "$PRIVATE_DIR/$SERVICE_NAME.csr" \
    -subj "/C=US/ST=California/L=San Francisco/O=Trust Engine/OU=Security/CN=$COMMON_NAME"

  if [ $? -ne 0 ]; then
    echo "Error generating CSR for $SERVICE_NAME" >&2
    exit 1
  fi

  # Generate certificate
  openssl x509 -req -in "$PRIVATE_DIR/$SERVICE_NAME.csr" \
    -CA "$CA_DIR/ca-cert.pem" \
    -CAkey "$CA_DIR/ca-key.pem" \
    -CAcreateserial \
    -out "$CERTS_DIR/$SERVICE_NAME-cert.pem" \
    -days 365

  if [ $? -ne 0 ]; then
    echo "Error generating certificate for $SERVICE_NAME" >&2
    exit 1
  fi

  chmod 400 "$PRIVATE_DIR/$SERVICE_NAME-key.pem"
  chmod 444 "$CERTS_DIR/$SERVICE_NAME-cert.pem"

  echo "Certificate generated for $SERVICE_NAME"
  rm "$PRIVATE_DIR/$SERVICE_NAME.csr"
}

# Generate CA certificate
echo "Generating CA certificate..."
openssl genrsa -out "$CA_DIR/ca-key.pem" 4096
if [ $? -ne 0 ]; then
  echo "Error generating CA key" >&2
  exit 1
fi

openssl req -x509 -new -nodes -key "$CA_DIR/ca-key.pem" \
  -out "$CA_DIR/ca-cert.pem" \
  -days 3650 \
  -subj "/C=US/ST=California/L=San Francisco/O=Trust Engine/OU=Security/CN=TrustEngine CA"

if [ $? -ne 0 ]; then
  echo "Error generating CA certificate" >&2
  exit 1
fi
chmod 400 "$CA_DIR/ca-key.pem"
chmod 444 "$CA_DIR/ca-cert.pem"

echo "CA certificate generated"

# Generate service certificates
generate_cert "elasticsearch" "elasticsearch"
generate_cert "kibana" "kibana"
generate_cert "trust-engine" "trust-engine"
generate_cert "wazuh-manager" "wazuh-manager"
generate_cert "wazuh-dashboard" "wazuh-dashboard"
generate_cert "wazuh-indexer" "wazuh-indexer"

echo "✅ All certificates generated!"
