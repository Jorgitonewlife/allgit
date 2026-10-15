#!/usr/bin/env bash
# docker-fix-wsl.sh - Fix common Docker on WSL 2 issues
# Usage: bash docker-fix-wsl.sh [--full] [--reset] [--help]

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

show_help() {
    cat <<EOF
Usage: bash docker-fix-wsl.sh [OPTIONS]

Options:
  --full      Run all fixes (update WSL, shutdown, restart Docker, test)
  --reset     Nuclear option: reset Docker Desktop data (DANGEROUS)
  --test      Only run connectivity tests
  --help      Show this help

Examples:
  bash docker-fix-wsl.sh --full
  bash docker-fix-wsl.sh --test
  bash docker-fix-wsl.sh --reset
EOF
}

# Check if running in WSL
check_wsl() {
    if ! grep -qi microsoft /proc/version 2>/dev/null; then
        log_error "Not running inside WSL!"
        exit 1
    fi
    log_ok "Running in WSL"
}

# Check if Docker Desktop is installed
check_docker_desktop() {
    if ! command -v docker &>/dev/null; then
        log_error "Docker not found in PATH. Install Docker Desktop first."
        exit 1
    fi
    log_ok "Docker CLI found"
}

# Update WSL kernel
update_wsl() {
    log_info "Updating WSL kernel (requires Windows Admin)..."
    if powershell.exe -Command "wsl --update" 2>&1 | grep -q "Error"; then
        log_warn "WSL update failed (may need to run as Admin in PowerShell)"
        return 1
    fi
    log_ok "WSL update completed"
}

# Shutdown WSL
shutdown_wsl() {
    log_info "Shutting down WSL..."
    wsl.exe --shutdown
    sleep 3
    log_ok "WSL shutdown completed"
}

# Restart Docker Desktop
restart_docker_desktop() {
    log_info "Restarting Docker Desktop..."
    
    # Try to stop Docker Desktop
    powershell.exe -Command "Stop-Process -Name 'Docker Desktop' -Force -ErrorAction SilentlyContinue" 2>/dev/null
    sleep 3
    
    # Start Docker Desktop
    powershell.exe -Command "Start-Process 'C:\Program Files\Docker\Docker\Docker Desktop.exe'" 2>/dev/null || \
    powershell.exe -Command "Start-Process 'C:\Program Files (x86)\Docker\Docker\Docker Desktop.exe'" 2>/dev/null || \
    log_warn "Could not auto-start Docker Desktop. Please start manually."
    
    # Wait for Docker to be ready
    log_info "Waiting for Docker daemon..."
    for i in {1..30}; do
        if docker info &>/dev/null; then
            log_ok "Docker daemon is ready"
            return 0
        fi
        sleep 2
    done
    log_error "Docker daemon not ready after 60s"
    return 1
}

# Test Docker connectivity
test_docker() {
    log_info "Testing Docker connectivity..."
    
    # Test 1: Docker daemon
    if docker info &>/dev/null; then
        log_ok "Docker daemon responding"
    else
        log_error "Docker daemon not responding"
        return 1
    fi
    
    # Test 2: Pull hello-world
    log_info "Testing image pull..."
    if docker pull hello-world:latest &>/dev/null; then
        log_ok "Image pull successful"
    else
        log_error "Image pull failed"
        return 1
    fi
    
    # Test 3: Run container
    log_info "Testing container run..."
    if docker run --rm hello-world &>/dev/null; then
        log_ok "Container run successful"
    else
        log_error "Container run failed"
        return 1
    fi
    
    # Test 4: Network connectivity
    log_info "Testing network..."
    if docker run --rm alpine:latest wget -q --spider http://google.com 2>/dev/null; then
        log_ok "Network connectivity OK"
    else
        log_warn "Network test failed (may be proxy/firewall)"
    fi
    
    # Test 5: Volume mount
    log_info "Testing volume mount..."
    if docker run --rm -v "$(pwd):/test" alpine:latest ls /test &>/dev/null; then
        log_ok "Volume mount working"
    else
        log_warn "Volume mount failed"
    fi
    
    log_ok "All Docker tests passed!"
}

# Clean Docker (free space)
clean_docker() {
    log_info "Cleaning Docker (removing unused images/containers/volumes)..."
    docker system prune -af --volumes 2>/dev/null || true
    log_ok "Docker cleanup completed"
}

# Reset Docker Desktop (nuclear)
reset_docker() {
    log_warn "NUCLEAR OPTION: This will DELETE all Docker data!"
    read -p "Type 'YES' to confirm: " confirm
    if [[ "$confirm" != "YES" ]]; then
        log_info "Cancelled"
        return 1
    fi
    
    log_info "Resetting Docker Desktop..."
    powershell.exe -Command "Stop-Process -Name 'Docker Desktop' -Force -ErrorAction SilentlyContinue" 2>/dev/null
    sleep 2
    
    # Remove Docker data
    rm -rf ~/.docker 2>/dev/null || true
    rm -rf /var/lib/docker 2>/dev/null || true
    rm -rf /var/run/docker.sock 2>/dev/null || true
    
    # Reset via Docker Desktop CLI if available
    if command -v docker &>/dev/null; then
        docker system prune -af --volumes 2>/dev/null || true
    fi
    
    log_ok "Docker data cleaned. Restart Docker Desktop manually."
}

# Main
main() {
    local FULL=false
    local RESET=false
    local TEST_ONLY=false
    
    for arg in "$@"; do
        case $arg in
            --full) FULL=true ;;
            --reset) RESET=true ;;
            --test) TEST_ONLY=true ;;
            --help) show_help; exit 0 ;;
            *) log_error "Unknown option: $arg"; show_help; exit 1 ;;
        esac
    done
    
    echo "=========================================="
    echo "  Docker WSL 2 Fix Script"
    echo "=========================================="
    
    check_wsl
    check_docker_desktop
    
    if [[ "$RESET" == true ]]; then
        reset_docker
        exit $?
    fi
    
    if [[ "$TEST_ONLY" == true ]]; then
        test_docker
        exit $?
    fi
    
    if [[ "$FULL" == true ]]; then
        update_wsl || true
        shutdown_wsl
        restart_docker_desktop || exit 1
        test_docker || exit 1
        log_ok "Full fix completed!"
        exit 0
    fi
    
    # Default: interactive menu
    echo ""
    echo "Select action:"
    echo "  1) Full fix (update WSL + restart Docker + test)"
    echo "  2) Test Docker only"
    echo "  3) Clean Docker (free space)"
    echo "  4) Reset Docker (NUCLEAR)"
    echo "  5) Exit"
    echo ""
    read -p "Choice [1-5]: " choice
    
    case $choice in
        1) 
            update_wsl || true
            shutdown_wsl
            restart_docker_desktop || exit 1
            test_docker || exit 1
            ;;
        2) test_docker ;;
        3) clean_docker ;;
        4) reset_docker ;;
        5) exit 0 ;;
        *) log_error "Invalid choice"; exit 1 ;;
    esac
    
    log_ok "Done!"
}

main "$@"