#!/bin/bash
# Setup script for Voice Assistant service
# Run with: sudo ./scripts/setup_voice_service.sh

set -e

echo "=========================================="
echo "Voice Assistant Setup"
echo "=========================================="
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo)"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Project directory: $PROJECT_DIR"
echo

# Install Python dependencies
echo "Installing Python dependencies..."
sudo -u ec2-user python3.11 -m pip install flask websockets --quiet
echo "Done."
echo

# Copy systemd service files
echo "Installing systemd services..."
cp "$PROJECT_DIR/systemd/voice-service.service" /etc/systemd/system/
cp "$PROJECT_DIR/systemd/voice-gateway.service" /etc/systemd/system/
echo "Done."
echo

# Reload systemd
echo "Reloading systemd..."
systemctl daemon-reload
echo "Done."
echo

# Enable services
echo "Enabling services..."
systemctl enable voice-service.service
systemctl enable voice-gateway.service
echo "Done."
echo

# Start services
echo "Starting services..."
systemctl start voice-gateway.service
sleep 2
systemctl start voice-service.service
echo "Done."
echo

# Check status
echo "Service status:"
echo
systemctl status voice-gateway.service --no-pager || true
echo
systemctl status voice-service.service --no-pager || true
echo

# Nginx configuration
echo "=========================================="
echo "Nginx Configuration"
echo "=========================================="
echo
echo "Add the following to your nginx configuration:"
echo
echo "    include $PROJECT_DIR/nginx/av.conf;"
echo
echo "Then reload nginx:"
echo "    sudo nginx -t && sudo systemctl reload nginx"
echo
echo "=========================================="
echo "Access"
echo "=========================================="
echo
echo "URL: https://yourdomain.com/av"
echo "Password: TheVoiceYouWantToHearToday"
echo
echo "=========================================="
echo "Management Commands"
echo "=========================================="
echo
echo "Start:   sudo systemctl start voice-service voice-gateway"
echo "Stop:    sudo systemctl stop voice-service voice-gateway"
echo "Restart: sudo systemctl restart voice-service voice-gateway"
echo "Status:  sudo systemctl status voice-service voice-gateway"
echo "Logs:    sudo journalctl -u voice-service -u voice-gateway -f"
echo
echo "Setup complete!"
