#!/bin/bash

# preflight_cleanup.sh - Clean up before running the main script

echo "🧹 Pre-flight Tailscale Cleanup"
echo "==============================="

# Check current Tailscale status
echo "1. Checking current Tailscale serve status..."
tailscale serve status

echo ""
echo "2. Resetting all Tailscale serves..."
# Reset without sudo - this should clear everything
tailscale serve reset

echo ""
echo "3. Checking if reset worked..."
tailscale serve status

# Kill any hanging Tailscale processes (if needed)
echo ""
echo "4. Checking for any stuck processes..."
ps aux | grep tailscale | grep -v grep

# Check Tailscale connection
echo ""
echo "5. Verifying Tailscale connection..."
tailscale status

echo ""
echo "✅ Pre-flight cleanup complete!"
echo ""
echo "🚀 Now you can run: ./start_servers.sh start"