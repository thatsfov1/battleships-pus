#!/bin/bash
# Skrypt do generowania self-signed certyfikatu TLS dla serwera Statki

set -e

CERT_DIR="$(dirname "$0")"
KEY_FILE="$CERT_DIR/server.key"
CERT_FILE="$CERT_DIR/server.crt"

echo "Generowanie prywatnego klucza i certyfikatu self-signed..."

openssl req -x509 -newkey rsa:4096 -keyout "$KEY_FILE" -out "$CERT_FILE" \
    -days 365 -nodes -subj "/C=PL/ST=Malopolska/L=Krakow/O=PK/CN=localhost"

chmod 600 "$KEY_FILE"
chmod 644 "$CERT_FILE"

echo "Certyfikaty zostały wygenerowane:"
echo "  Klucz: $KEY_FILE"
echo "  Certyfikat: $CERT_FILE"
