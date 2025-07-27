#!/bin/bash

# Script to generate TLS certificate files from environment variables
# Used to create certificate files from environment variables for nginx

set -e

CERT_DIR="/action-server/actions"
COMBINED_CERT_PATH="${CERT_DIR}/combined-tls.crt"
KEY_PATH="${CERT_DIR}/tls.key"

# Check if TLS_CRT and TLS_KEY environment variables are set
if [ -z "$TLS_CRT" ] || [ -z "$TLS_KEY" ]; then
  echo "Warning: TLS_CRT or TLS_KEY environment variables are not set."
  echo "Will create self-signed certificate for development purposes."
  
  # Create a self-signed certificate for development
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$KEY_PATH" \
    -out "$COMBINED_CERT_PATH" \
    -subj "/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
else
  # Create certificate files from environment variables
  echo "Creating TLS certificate files from environment variables..."
  
  # Ensure the directory exists
  mkdir -p "$CERT_DIR"
  
  # Write certificate and key from environment variables
  echo "$TLS_CRT" > "$COMBINED_CERT_PATH"
  echo "$TLS_KEY" > "$KEY_PATH"
fi

# Set appropriate permissions
chmod 600 "$COMBINED_CERT_PATH" "$KEY_PATH"
chown as-user:as-user "$COMBINED_CERT_PATH" "$KEY_PATH"

echo "TLS certificate files have been generated successfully."