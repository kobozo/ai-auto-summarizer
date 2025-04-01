#!/bin/bash
# Generates a base64-encoded 256-bit (32-byte) symmetric key
# Usage: ./generate_symmetric_key.sh

KEY=$(openssl rand -base64 32)
echo "Generated symmetric key:"
echo $KEY 