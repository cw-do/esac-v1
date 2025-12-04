#!/bin/bash

# Set SSL certificate file path for HTTPS connections
export SSL_CERT_FILE=/etc/ssl/certs/ca-bundle.crt

# Run the ESAC v1 executable
./dist/main
