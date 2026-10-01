#!/bin/bash
# testing-data/download-test-data.sh
#
# Download script for dvm-dos-tem testing data
# Downloads data from GCP bucket to appropriate testing-data directories
#
# Usage:
#   ./download-test-data.sh comprehensive # Download comprehensive testing data (~500+MB)
#   ./download-test-data.sh clean         # Remove downloaded data (keeps minimal/)
#   ./download-test-data.sh --help        # Show help

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Configuration
GCP_BUCKET="gs://dvmdostem-testing-data-comprehensive"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTING_DATA_ROOT="$SCRIPT_DIR"  # Parent of comprehensive/
LOCKFILE="$TESTING_DATA_ROOT/.download_lock"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Show help
show_help() {
    cat << EOF
dvm-dos-tem Testing Data Download Script

USAGE:
    $0 <command>

COMMANDS:
    comprehensive   Download comprehensive testing data (~500+MB)
                   Includes full temporal/spatial datasets for validation
                   
    clean          Remove all downloaded data (keeps minimal/ intact)
    
    status         Show current data availability and sizes
    
    --help, -h     Show this help message

EXAMPLES:
    
    # Download comprehensive data for full validation
    $0 comprehensive
    
    # Check what's currently available
    $0 status
    
    # Clean up to save disk space
    $0 clean

REQUIREMENTS:
    - gsutil (Google Cloud SDK) must be installed and configured
    - Internet connection for downloading from GCP bucket
    - ~500MB+ free space for comprehensive data

DATA ORGANIZATION:
    testing-data/
    ├── minimal/        ✅ Always available (shipped with repo)
    ├── standard/       ✅ Always available (shipped with repo)
    ├── comprehensive/  ⬇️  Downloaded via this script
    └── download-test-data.sh  # This script

EOF
}

# Check if gsutil is available
check_gsutil() {
    if ! command -v gsutil &> /dev/null; then
        log_error "gsutil not found. Please install Google Cloud SDK:"
        echo "  macOS: brew install google-cloud-sdk"
        echo "  Linux: https://cloud.google.com/sdk/docs/install"
        echo "  Docker: Use google/cloud-sdk image"
        exit 1
    fi
}

# Check if bucket is accessible
check_bucket_access() {
    log_info "Checking access to GCP bucket..."
    if ! gsutil ls "$GCP_BUCKET" > /dev/null 2>&1; then
        log_error "Cannot access bucket $GCP_BUCKET"
        echo "This could be due to:"
        echo "  1. Authentication: Run 'gcloud auth login'"
        echo "  2. Network connectivity issues"
        echo "  3. Bucket permissions or name changes"
        exit 1
    fi
    log_success "Bucket access confirmed"
}

# Download data for a specific tier
download_data() {
    local tier=$1
    local target_dir="$TESTING_DATA_ROOT/$tier"
    local bucket_path="$GCP_BUCKET/$tier/"
    
    # Create lock file to prevent concurrent downloads
    if [[ -f "$LOCKFILE" ]]; then
        log_error "Another download is in progress (lockfile exists)"
        log_info "If no download is running, remove: $LOCKFILE"
        exit 1
    fi
    echo "$$" > "$LOCKFILE"
    
    # Ensure target directory exists
    mkdir -p "$target_dir"
    
    log_info "Downloading $tier data from $bucket_path"
    log_info "Target directory: $target_dir"
    
    # Check if data already exists
    if [[ -d "$target_dir/inputs" ]] && [[ -n "$(ls -A "$target_dir/inputs" 2>/dev/null)" ]]; then
        log_warn "$tier data already exists. Use 'clean' first to re-download."
        rm -f "$LOCKFILE"
        return 0
    fi
    
    # Download with progress and resume capability
    if gsutil -m rsync -r -u "$bucket_path" "$target_dir/"; then
        log_success "$tier data downloaded successfully"
        log_info "Data location: $target_dir"
        
        # Show what was downloaded
        if [[ -d "$target_dir/inputs" ]]; then
            log_info "Downloaded datasets:"
            find "$target_dir/inputs" -name "*.nc" -exec basename {} \; | sort | sed 's/^/  - /'
        fi
        
        # Show size
        local size=$(du -sh "$target_dir" 2>/dev/null | cut -f1 || echo "unknown")
        log_info "Total size: $size"
        
    else
        log_error "Failed to download $tier data"
        rm -f "$LOCKFILE"
        exit 1
    fi
    
    rm -f "$LOCKFILE"
}

# Clean downloaded data
clean_data() {
    log_info "Cleaning downloaded testing data..."
    
    local cleaned=false
        
    # Remove comprehensive data  
    if [[ -d "$TESTING_DATA_ROOT/comprehensive/inputs" ]]; then
        # Keep the script but remove data
        find "$TESTING_DATA_ROOT/comprehensive" -delete
        log_success "Removed comprehensive/ data"
        cleaned=true
    fi
    
    if [[ "$cleaned" == "false" ]]; then
        log_info "No downloaded data found to clean"
    fi
    
    # Remove any stale lock files
    rm -f "$LOCKFILE"
    
    log_success "Cleanup complete. Minimal and standard data preserved."
}

# Show current status
show_status() {
    log_info "dvm-dos-tem Testing Data Status"
    echo "================================"
    
    # Check minimal data
    if [[ -d "$TESTING_DATA_ROOT/minimal/" ]]; then
        local minimal_size=$(du -sh "$TESTING_DATA_ROOT/minimal" 2>/dev/null | cut -f1)
        echo -e "${GREEN}✅ minimal/${NC}     $minimal_size (always available)"
    else
        echo -e "${RED}❌ minimal/${NC}     Missing (should be in repository)"
    fi

    # Check standard data
    if [[ -d "$TESTING_DATA_ROOT/standard/" ]]; then
        local standard_size=$(du -sh "$TESTING_DATA_ROOT/standard" 2>/dev/null | cut -f1)
        echo -e "${GREEN}✅ standard/${NC}     $standard_size (always available)"
    else
        echo -e "${RED}❌ standard/${NC}     Missing (should be in repository)"
    fi

    # Check comprehensive data
    if [[ -d "$TESTING_DATA_ROOT/comprehensive/inputs" ]] && [[ -n "$(ls -A "$TESTING_DATA_ROOT/comprehensive/inputs" 2>/dev/null)" ]]; then
        local comp_size=$(du -sh "$TESTING_DATA_ROOT/comprehensive" 2>/dev/null | cut -f1)
        echo -e "${GREEN}✅ comprehensive/${NC} $comp_size (downloaded)"
    else
        echo -e "${YELLOW}⬇️  comprehensive/${NC} Not downloaded (run: $0 comprehensive)"
    fi
    
    echo ""
    log_info "Total testing-data size: $(du -sh "$TESTING_DATA_ROOT" 2>/dev/null | cut -f1)"
}

# Main script logic
main() {
    case "${1:-}" in
        "comprehensive") 
            check_gsutil
            check_bucket_access
            download_data "comprehensive"
            ;;
        "clean")
            clean_data
            ;;
        "status")
            show_status
            ;;
        "--help"|"-h"|"help")
            show_help
            ;;
        "")
            log_error "No command specified"
            echo "Run '$0 --help' for usage information"
            exit 1
            ;;
        *)
            log_error "Unknown command: $1"
            echo "Run '$0 --help' for usage information"
            exit 1
            ;;
    esac
}

# Handle script interruption
cleanup_on_exit() {
    if [[ -f "$LOCKFILE" ]]; then
        rm -f "$LOCKFILE"
        log_warn "Download interrupted, lockfile removed"
    fi
}
trap cleanup_on_exit EXIT INT TERM

# Execute main function
main "$@"