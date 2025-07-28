#!/bin/bash

set -e

# Set directory structure
ROOT_DIR="$(dirname "$0")/../.."
SSL_DIR="$ROOT_DIR/ssl"
CA_DIR="$SSL_DIR/ca"
CERTS_DIR="$SSL_DIR/certs"
PRIVATE_DIR="$SSL_DIR/private"

mkdir -p "$CA_DIR" "$CERTS_DIR" "$PRIVATE_DIR"

# 1. Generate CA key and cert
openssl req -new -x509 -days 3650 \
  -keyout "$CA_DIR/ca-key.pem" \
  -out "$CA_DIR/ca-cert.pem" \
  -nodes -subj "/CN=TrustEngine-CA"

# 2. Elasticsearch key, CSR, and cert
openssl req -newkey rsa:2048 -nodes \
  -keyout "$PRIVATE_DIR/elasticsearch-key.pem" \
  -out "$PRIVATE_DIR/elasticsearch.csr" \
  -subj "/CN=elasticsearch"

openssl x509 -req -in "$PRIVATE_DIR/elasticsearch.csr" \
  -CA "$CA_DIR/ca-cert.pem" \
  -CAkey "$CA_DIR/ca-key.pem" \
  -CAcreateserial \
  -out "$CERTS_DIR/elasticsearch-cert.pem" \
  -days 365

# 3. Kibana key, CSR, and cert
openssl req -newkey rsa:2048 -nodes \
  -keyout "$PRIVATE_DIR/kibana-key.pem" \
  -out "$PRIVATE_DIR/kibana.csr" \
  -subj "/CN=kibana"

openssl x509 -req -in "$PRIVATE_DIR/kibana.csr" \
  -CA "$CA_DIR/ca-cert.pem" \
  -CAkey "$CA_DIR/ca-key.pem" \
  -CAcreateserial \
  -out "$CERTS_DIR/kibana-cert.pem" \
  -days 365

# 4. Clean up
rm "$PRIVATE_DIR/elasticsearch.csr" "$PRIVATE_DIR/kibana.csr" "$CA_DIR/ca-key.pem" "$CA_DIR/ca-cert.srl"

echo "✅ All certificates generated!"
