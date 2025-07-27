#!/bin/bash

# Script to generate TLS certificate files from environment variables
# Used to create certificate files from environment variables for nginx


set -e
echo "[generate-certs] Starting certificate generation script..."
echo "[generate-certs] Current user: $(whoami)"
echo "[generate-certs] CERT_DIR: $CERT_DIR"
echo "[generate-certs] COMBINED_CERT_PATH: $COMBINED_CERT_PATH"
echo "[generate-certs] KEY_PATH: $KEY_PATH"
echo "[generate-certs] TLS_CRT length: ${#TLS_CRT}"
echo "[generate-certs] TLS_KEY length: ${#TLS_KEY}"
echo "[generate-certs] SERVER_URL: $SERVER_URL"

CERT_DIR="/action-server/actions/certs"
COMBINED_CERT_PATH="/action-server/actions/combined-tls.crt"
KEY_PATH="/action-server/actions/tls.key"

# Check if TLS_CRT and TLS_KEY environment variables are set
if [ -z "$TLS_CRT" ] || [ -z "$TLS_KEY" ]; then
  echo "[generate-certs] Warning: TLS_CRT or TLS_KEY environment variables are not set."
  echo "[generate-certs] Will create self-signed certificate for development purposes."
  
  # Create a self-signed certificate for development
  # Include SERVER_URL in SAN if available
  if [ -n "$SERVER_URL" ]; then
    SANS="DNS:localhost,DNS:$SERVER_URL,IP:127.0.0.1"
  else
    SANS="DNS:localhost,IP:127.0.0.1"
  fi
  
  echo "[generate-certs] Running openssl to create self-signed cert..."
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$KEY_PATH" \
    -out "$COMBINED_CERT_PATH" \
    -subj "/CN=localhost" \
    -addext "subjectAltName=$SANS"
else
  # Create certificate files from environment variables
  echo "[generate-certs] Creating TLS certificate files from environment variables..."
  
  # Ensure the directory exists
  echo "[generate-certs] Ensuring CERT_DIR exists..."
  mkdir -p "$CERT_DIR"
  
  # Write certificate and key from environment variables
  # Since we're reading from an env file where the certificate is already properly formatted with newlines,
  # we don't need to use echo -e, which might actually cause issues with escaped characters
  echo "[generate-certs] Writing TLS_CRT to $COMBINED_CERT_PATH..."
  printf "%s" "$TLS_CRT" > "$COMBINED_CERT_PATH"
  echo "[generate-certs] Writing TLS_KEY to $KEY_PATH..."
  printf "%s" "$TLS_KEY" > "$KEY_PATH"
fi

# Set appropriate permissions
echo "[generate-certs] Setting permissions..."
chmod 644 "$COMBINED_CERT_PATH"
chmod 600 "$KEY_PATH"
# Set ownership if running as root, otherwise skip
if [ "$(id -u)" -eq 0 ]; then
  chown as-user:as-user "$COMBINED_CERT_PATH" "$KEY_PATH" || true
fi

# Verify files exist and have content
if [ -s "$COMBINED_CERT_PATH" ] && [ -s "$KEY_PATH" ]; then
  echo "[generate-certs] TLS certificate files have been generated successfully."
else
  echo "[generate-certs] ERROR: Certificate files are missing or empty!"
  ls -l "$CERT_DIR"
  exit 1
fi

echo "[generate-certs] Certificate generation completed successfully."