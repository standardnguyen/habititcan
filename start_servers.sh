#!/bin/bash

# start_servers.sh
# Complete script to start all servers and set up Tailscale

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
FRONTEND_PORT=3000
STACK_PORT=5000
AUDIO_PORT=5001

# File to store PIDs
PID_FILE="server_pids.txt"

echo -e "${BLUE}🚀 Audio Stack Monitor - Server Startup${NC}"
echo "========================================"

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to kill servers
cleanup_servers() {
    echo -e "${YELLOW}🧹 Cleaning up servers...${NC}"
    
    if [ -f "$PID_FILE" ]; then
        echo "Stopping servers from PID file..."
        while read pid; do
            if kill -0 $pid 2>/dev/null; then
                echo "  Killing process $pid"
                kill $pid 2>/dev/null || true
            fi
        done < "$PID_FILE"
        rm -f "$PID_FILE"
    fi
    
    # Also kill by port if needed
    for port in $FRONTEND_PORT $STACK_PORT $AUDIO_PORT; do
        pid=$(lsof -ti:$port 2>/dev/null || true)
        if [ ! -z "$pid" ]; then
            echo "  Killing process on port $port (PID: $pid)"
            kill $pid 2>/dev/null || true
        fi
    done
    
    echo -e "${GREEN}✅ Cleanup complete${NC}"
}

# Function to start a server
start_server() {
    local script=$1
    local port=$2
    local name=$3
    
    if [ ! -f "$script" ]; then
        echo -e "${RED}❌ Error: $script not found${NC}"
        return 1
    fi
    
    if check_port $port; then
        echo -e "${YELLOW}⚠️  Port $port already in use. Killing existing process...${NC}"
        pid=$(lsof -ti:$port)
        kill $pid 2>/dev/null || true
        sleep 2
    fi
    
    echo -e "${BLUE}📡 Starting $name server...${NC}"
    python "$script" &
    local pid=$!
    echo $pid >> "$PID_FILE"
    
    # Wait a bit and check if it started successfully
    sleep 3
    if kill -0 $pid 2>/dev/null && check_port $port; then
        echo -e "${GREEN}✅ $name server started (PID: $pid, Port: $port)${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to start $name server${NC}"
        return 1
    fi
}

# Function to setup Tailscale
setup_tailscale() {
    echo -e "${BLUE}🔗 Setting up Tailscale serves...${NC}"
    
    # Clear existing serves
    echo "Resetting existing Tailscale serves..."
    tailscale serve reset
    
    # Set up new serves
    echo "Setting up new serves..."
    tailscale serve --bg --https=443 --set-path=/ http://localhost:$FRONTEND_PORT
    tailscale serve --bg --https=443 --set-path=/api/stack http://localhost:$STACK_PORT
    tailscale serve --bg --https=443 --set-path=/api/audio http://localhost:$AUDIO_PORT
    
    echo -e "${GREEN}✅ Tailscale serves configured${NC}"
}

# Function to show status
show_status() {
    echo -e "${BLUE}📊 Current Status${NC}"
    echo "=================="
    
    # Check servers
    echo "Server Status:"
    for port in $FRONTEND_PORT $STACK_PORT $AUDIO_PORT; do
        if check_port $port; then
            echo -e "  ✅ Port $port: ${GREEN}Running${NC}"
        else
            echo -e "  ❌ Port $port: ${RED}Not running${NC}"
        fi
    done
    
    echo ""
    echo "Tailscale Status:"
    tailscale serve status 2>/dev/null || echo "No serves configured"
    
    echo ""
    echo "Your Tailscale URL:"
    tailscale status --self 2>/dev/null | grep -E "(Name|tailscale)" || echo "Tailscale not connected"
}

# Function to show URLs
show_urls() {
    local machine_name=$(tailscale status --self --json 2>/dev/null | grep -o '"Name":"[^"]*"' | cut -d'"' -f4 2>/dev/null || echo "unknown")
    
    echo -e "${GREEN}🌐 Your services are available at:${NC}"
    echo "Local access:"
    echo "  Frontend: http://localhost:$FRONTEND_PORT"
    echo "  Stack:    http://localhost:$STACK_PORT"
    echo "  Audio:    http://localhost:$AUDIO_PORT"
    echo ""
    echo "Tailscale access:"
    echo "  Frontend: https://$machine_name.ts.net/"
    echo "  Stack:    https://$machine_name.ts.net/api/stack/status"
    echo "  Audio:    https://$machine_name.ts.net/api/audio/list"
}

# Handle script arguments
case "${1:-start}" in
    "start")
        echo -e "${BLUE}Starting all servers...${NC}"
        
        # Clean up any existing servers
        cleanup_servers
        
        # Create fresh PID file
        rm -f "$PID_FILE"
        touch "$PID_FILE"
        
        # Start servers
        start_server "frontend_server.py" $FRONTEND_PORT "Frontend" || exit 1
        start_server "stack_server.py" $STACK_PORT "Stack" || exit 1
        start_server "audio_server.py" $AUDIO_PORT "Audio" || exit 1
        
        # Setup Tailscale
        setup_tailscale
        
        # Show status and URLs
        echo ""
        show_status
        echo ""
        show_urls
        
        echo ""
        echo -e "${GREEN}🎉 All servers started successfully!${NC}"
        echo -e "${YELLOW}💡 Use './start_servers.sh stop' to stop all servers${NC}"
        echo -e "${YELLOW}💡 Use './start_servers.sh status' to check status${NC}"
        ;;
        
    "stop")
        cleanup_servers
        tailscale serve reset
        echo -e "${GREEN}🛑 All servers stopped and Tailscale serves cleared${NC}"
        ;;
        
    "restart")
        echo -e "${BLUE}🔄 Restarting all servers...${NC}"
        $0 stop
        sleep 2
        $0 start
        ;;
        
    "status")
        show_status
        echo ""
        show_urls
        ;;
        
    "tailscale")
        setup_tailscale
        show_status
        ;;
        
    *)
        echo "Usage: $0 {start|stop|restart|status|tailscale}"
        echo ""
        echo "Commands:"
        echo "  start     - Start all servers and configure Tailscale"
        echo "  stop      - Stop all servers and clear Tailscale"
        echo "  restart   - Stop and start all servers"
        echo "  status    - Show current status"
        echo "  tailscale - Reconfigure Tailscale serves only"
        exit 1
        ;;
esac
