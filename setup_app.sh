#!/bin/bash

print_step() {
    echo -e "\033[1;34m[STEP]\033[0m $1"
}
print_status() {
    echo -e "\033[1;32m[INFO]\033[0m $1"
}
print_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

# 1. Set up Python virtual environment
print_step "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# 2. Install requirements
print_step "Installing Python requirements..."
pip install --upgrade pip
pip install -r requirements.txt

# 3. Generate SSL certificates (if needed)
SSL_DIR="docker/ssl"
if [ ! -f "$SSL_DIR/ca/ca-cert.pem" ]; then
    print_step "Generating SSL certificates..."
    cd $SSL_DIR
    ./generate_certificates.sh
    cd ../../
else
    print_status "SSL certificates already exist."
fi

# 4. Initialize/check Trust Engine DB tables
print_step "Initializing/checking Trust Engine database tables..."
python check_table_schema.py

# 5. Start Trust Engine Flask app
print_step "Starting Trust Engine Flask app..."
python run.py
