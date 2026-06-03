#!/bin/bash
# run_distributed_test.sh - Helper script to run Locust in distributed mode with Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
USER_TYPE="WebSocketUser"
WORKERS=4
ACTION="up"

# Function to print colored output
print_header() {
    echo -e "\n${BLUE}==== $1 ====${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Function to show usage
show_usage() {
    cat << EOF
${BLUE}Locust Distributed Testing - Docker Compose Helper${NC}

Usage: $0 [OPTIONS]

OPTIONS:
    -u, --user USER_TYPE     User type to run (default: WebSocketUser)
                             Options: WebSocketUser, GraphQLUser, Adspace
    
    -w, --workers NUM        Number of workers to scale (default: 4)
    
    -a, --action ACTION      Action to perform (default: up)
                             Options: up, down, logs, ps, restart, clean
    
    -h, --help              Show this help message

EXAMPLES:
    # Run WebSocket test with 4 workers
    $0 --user WebSocketUser --workers 4

    # Run GraphQL test with 2 workers
    $0 --user GraphQLUser --workers 2

    # Run HTTP test with 5 workers
    $0 --user Adspace --workers 5

    # View logs
    $0 --action logs

    # Stop and remove containers
    $0 --action down

    # Clean everything (including volumes)
    $0 --action clean

EOF
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--user)
            USER_TYPE="$2"
            shift 2
            ;;
        -w|--workers)
            WORKERS="$2"
            shift 2
            ;;
        -a|--action)
            ACTION="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            ;;
    esac
done

# Validate user type
case $USER_TYPE in
    WebSocketUser|GraphQLUser|Adspace)
        print_success "User type: $USER_TYPE"
        ;;
    *)
        print_error "Invalid user type: $USER_TYPE"
        echo "Valid options: WebSocketUser, GraphQLUser, Adspace"
        exit 1
        ;;
esac

# Execute action
case $ACTION in
    up)
        print_header "Starting Locust - $USER_TYPE with $WORKERS workers"
        print_info "Master will be available at: http://localhost:8089"
        print_info "Press Ctrl+C to stop\n"
        
        export LOCUST_USER=$USER_TYPE
        docker compose up --scale worker=$WORKERS
        ;;
    
    down)
        print_header "Stopping Locust containers"
        docker compose down
        print_success "Containers stopped"
        ;;
    
    clean)
        print_header "Cleaning up everything"
        print_info "This will remove all containers, volumes, and data"
        read -p "Are you sure? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker compose down -v
            print_success "Everything cleaned up"
        else
            print_info "Cleanup cancelled"
        fi
        ;;
    
    logs)
        print_header "Showing Locust logs"
        print_info "Press Ctrl+C to stop\n"
        docker compose logs -f
        ;;
    
    ps)
        print_header "Running containers"
        docker compose ps
        ;;
    
    restart)
        print_header "Restarting Locust - $USER_TYPE"
        export LOCUST_USER=$USER_TYPE
        docker compose restart
        print_success "Containers restarted"
        ;;
    
    *)
        print_error "Unknown action: $ACTION"
        echo "Valid options: up, down, logs, ps, restart, clean"
        exit 1
        ;;
esac
