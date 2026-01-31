#!/bin/bash

# Arch Linux System Cleaner
# Comprehensive cleaning script for package residuals and system data
# https://wiki.archlinux.org/title/Pacman#Cleaning_the_package_cache

set -euo pipefail

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Script configuration
readonly SCRIPT_NAME="arch-cleaner"
readonly VERSION="1.0"

# Functions for colored output
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Check if running as root for system-wide operations
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This operation requires root privileges."
        error "Please run: sudo $0"
        exit 1
    fi
}

# Check for required packages
check_dependencies() {
    local deps=("pacman-contrib" "findutils" "fd" "ncdu")
    local missing=()
    
    for dep in "${deps[@]}"; do
        if ! pacman -Q "$dep" >/dev/null 2>&1; then
            missing+=("$dep")
        fi
    done
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        warning "Missing recommended packages: ${missing[*]}"
        info "Install them with: sudo pacman -S ${missing[*]}"
        read -rp "Continue without these packages? (y/N): " confirm
        [[ "$confirm" != "y" && "$confirm" != "Y" ]] && exit 1
    fi
}

# Show disk usage before cleaning
show_disk_usage() {
    info "Current disk usage:"
    echo "================================"
    if [[ $EUID -eq 0 ]]; then
        echo "Package cache: $(du -sh /var/cache/pacman/pkg/ 2>/dev/null | cut -f1 || echo "N/A")"
        echo "System logs: $(journalctl --disk-usage 2>/dev/null | tail -1 | awk '{print $3}' || echo "N/A")"
        echo "/var/tmp: $(du -sh /var/tmp/ 2>/dev/null | cut -f1 || echo "N/A")"
        echo "/tmp: $(du -sh /tmp/ 2>/dev/null | cut -f1 || echo "N/A")"
    fi
    if [[ -n "${SUDO_USER:-}" ]]; then
        echo "User cache (~${SUDO_USER}/.cache): $(du -sh /home/"$SUDO_USER"/.cache 2>/dev/null | cut -f1 || echo "N/A")"
    fi
    echo "================================"
}

# Clean package cache with paccache
clean_package_cache() {
    check_root
    info "Cleaning package cache with paccache..."
    
    # Show current cache size
    local before_size=$(du -sb /var/cache/pacman/pkg/ 2>/dev/null | cut -f1 || echo "0")
    
    # Keep 2 recent versions (more conservative than default 3)
    paccache -rk2
    
    # Remove all uninstalled packages from cache
    read -rp "Remove ALL cached versions of uninstalled packages? (y/N): " confirm
    if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
        paccache -ruk0
    fi
    
    local after_size=$(du -sb /var/cache/pacman/pkg/ 2>/dev/null | cut -f1 || echo "0")
    local saved=$((before_size - after_size))
    
    if [[ $saved -gt 0 ]]; then
        success "Freed $(numfmt --to=iec $saved) from package cache"
    else
        info "No significant space freed from package cache"
    fi
}

# Remove orphaned packages
clean_orphans() {
    check_root
    info "Finding orphaned packages..."
    
    local orphans=($(pacman -Qdtq))
    
    if [[ ${#orphans[@]} -eq 0 ]]; then
        info "No orphaned packages found"
        return
    fi
    
    warning "Found ${#orphans[@]} orphaned packages:"
    printf '%s\n' "${orphans[@]}"
    
    read -rp "Remove these orphaned packages? (y/N): " confirm
    if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
        pacman -Rns "${orphans[@]}"
        success "Removed ${#orphans[@]} orphaned packages"
    fi
}

# Clean old configuration files (.pacnew, .pacsave)
clean_config_files() {
    info "Searching for .pacnew and .pacsave files..."
    
    # Find all .pacnew and .pacsave files
    local pacfiles=($(find /etc -type f \( -name "*.pacnew" -o -name "*.pacsave" \) 2>/dev/null))
    
    if [[ ${#pacfiles[@]} -eq 0 ]]; then
        info "No .pacnew or .pacsave files found"
        return
    fi
    
    warning "Found ${#pacfiles[@]} config backup files:"
    printf '%s\n' "${pacfiles[@]}"
    
    echo "Recommendation: Review these files manually with pacdiff"
    info "You can use: sudo pacdiff -o"
    
    read -rp "Remove these backup config files? (y/N): " confirm
    if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
        rm -v "${pacfiles[@]}"
        success "Removed ${#pacfiles[@]} backup config files"
    fi
}

# Clean user cache directories
clean_user_cache() {
    info "Cleaning user cache directories..."
    
    if [[ -n "${SUDO_USER:-}" ]]; then
        local user_home="/home/${SUDO_USER}"
        local cache_dirs=(
            "$user_home/.cache"
            "$user_home/.local/share/Trash"
        )
        
        for dir in "${cache_dirs[@]}"; do
            if [[ -d "$dir" ]]; then
                local size=$(du -sb "$dir" 2>/dev/null | cut -f1 || echo "0")
                if [[ $size -gt 104857600 ]]; then # > 100MB
                    warning "Cleaning $dir ($(numfmt --to=iec $size))"
                    rm -rf "$dir"/*
                fi
            fi
        done
    else
        # If not running via sudo, clean current user's cache
        local cache_dirs=(
            "$HOME/.cache"
            "$HOME/.local/share/Trash"
        )
        
        for dir in "${cache_dirs[@]}"; do
            if [[ -d "$dir" ]]; then
                local size=$(du -sb "$dir" 2>/dev/null | cut -f1 || echo "0")
                if [[ $size -gt 104857600 ]]; then # > 100MB
                    warning "Cleaning $dir ($(numfmt --to=iec $size))"
                    rm -rf "$dir"/*
                fi
            fi
        done
    fi
    
    success "User cache cleaned"
}

# Clean AUR helper caches
clean_aur_cache() {
    info "Cleaning AUR helper caches..."
    
    # yay cache
    if command -v yay &>/dev/null; then
        if [[ -d ~/.cache/yay ]]; then
            local yay_size=$(du -sb ~/.cache/yay 2>/dev/null | cut -f1 || echo "0")
            warning "Cleaning yay cache ($(numfmt --to=iec $yay_size))"
            yay -Scc --noconfirm 2>/dev/null || true
        fi
    fi
    
    # paru cache
    if command -v paru &>/dev/null; then
        if [[ -d ~/.cache/paru ]]; then
            local paru_size=$(du -sb ~/.cache/paru 2>/dev/null | cut -f1 || echo "0")
            warning "Cleaning paru cache ($(numfmt --to=iec $paru_size))"
            paru -Scc --noconfirm 2>/dev/null || true
        fi
    fi
    
    # Clean src directories
    if [[ -d ~/.cache/yay/src ]]; then
        rm -rf ~/.cache/yay/src/*
    fi
    
    success "AUR cache cleaned"
}

# Clean temporary files
clean_temp_files() {
    check_root
    info "Cleaning temporary files..."
    
    # Clean /var/tmp (preserving files newer than 10 days, respecting standards)
    find /var/tmp -type f -atime +10 -delete 2>/dev/null || true
    
    # Clean /tmp (preserving files newer than 3 days)
    find /tmp -type f -atime +3 -delete 2>/dev/null || true
    
    # Clean systemd journal (keep last 30 days or 500MB)
    journalctl --vacuum-time=30d --vacuum-size=500M >/dev/null 2>&1 || true
    
    # Clean package tarballs in /var/cache (should be handled by paccache, but extra safety)
    find /var/cache -name "*.part" -delete 2>/dev/null || true
    
    success "Temporary files cleaned"
}

# Clean Flatpak data (if installed)
clean_flatpak() {
    if command -v flatpak &>/dev/null; then
        info "Cleaning Flatpak unused data..."
        
        # Remove unused Flatpak refs
        flatpak uninstall --unused -y 2>/dev/null || true
        
        # Clean Flatpak cache
        rm -rf ~/.local/share/flatpak/.removed 2>/dev/null || true
        
        success "Flatpak data cleaned"
    else
        info "Flatpak not installed, skipping..."
    fi
}

# Main menu
show_menu() {
    echo "======================================"
    echo "  Arch Linux System Cleaner"
    echo "  Version: $VERSION"
    echo "======================================"
    echo "1. Clean package cache (paccache)"
    echo "2. Remove orphaned packages"
    echo "3. Clean old config files (.pacnew/.pacsave)"
    echo "4. Clean user cache directories"
    echo "5. Clean AUR helper caches"
    echo "6. Clean temporary files and logs"
    echo "7. Clean Flatpak unused data"
    echo "8. Run ALL cleaning tasks"
    echo "9. Show disk usage"
    echo "0. Exit"
    echo "======================================"
}

# Execute all cleaning tasks
run_all() {
    warning "Running ALL cleaning tasks. This may take a while..."
    read -rp "Are you sure? (y/N): " confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        return
    fi
    
    clean_package_cache
    clean_orphans
    clean_config_files
    clean_user_cache
    clean_aur_cache
    clean_temp_files
    clean_flatpak
    
    success "All cleaning tasks completed!"
    show_disk_usage
}

# Main execution
main() {
    # Check for root if system-wide operations are needed
    if [[ "$#" -eq 0 ]]; then
        show_menu
        while true; do
            read -rp "Select an option: " choice
            case $choice in
                1) clean_package_cache ;;
                2) clean_orphans ;;
                3) clean_config_files ;;
                4) clean_user_cache ;;
                5) clean_aur_cache ;;
                6) clean_temp_files ;;
                7) clean_flatpak ;;
                8) run_all ;;
                9) show_disk_usage ;;
                0) exit 0 ;;
                *) error "Invalid option. Please try again." ;;
            esac
            echo
            read -rp "Press Enter to continue..."
            show_menu
        done
    else
        # Command line mode
        case "$1" in
            --cache) clean_package_cache ;;
            --orphans) clean_orphans ;;
            --configs) clean_config_files ;;
            --user-cache) clean_user_cache ;;
            --aur-cache) clean_aur_cache ;;
            --temp) clean_temp_files ;;
            --flatpak) clean_flatpak ;;
            --all) run_all ;;
            --disk-usage) show_disk_usage ;;
            --help|-h)
                echo "Usage: $0 [OPTION]"
                echo "Clean Arch Linux system package residuals and data"
                echo
                echo "Options:"
                echo "  --cache        Clean package cache"
                echo "  --orphans      Remove orphaned packages"
                echo "  --configs      Clean old config files"
                echo "  --user-cache   Clean user cache directories"
                echo "  --aur-cache    Clean AUR helper caches"
                echo "  --temp         Clean temporary files and logs"
                echo "  --flatpak      Clean Flatpak unused data"
                echo "  --all          Run all cleaning tasks"
                echo "  --disk-usage   Show current disk usage"
                echo "  --help, -h     Show this help message"
                echo
                echo "Interactive menu is shown when run without options"
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                error "Use --help for usage information"
                exit 1
                ;;
        esac
    fi
}

# Trap for cleanup on exit
trap 'echo -e "\n${YELLOW}Cleaning interrupted. Some operations may be incomplete.${NC}"' SIGINT SIGTERM

# Run main function
main "$@"
