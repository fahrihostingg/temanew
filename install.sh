#!/usr/bin/env bash

# ==============================================================================
#  PAHRI THEMA NEW 6.0 NEXUS DOCK - ONE-CLICK AUTO INSTALLER
#  Author      : fahrihostingg (Fakrul / Fahri)
#  Version     : 6.7.3 (Nexus Edition)
#  Target      : Pterodactyl Panel v1.14.x
# ==============================================================================

set -e

# Warna Terminal & Efek Neon
ESC="\033["
RESET="${ESC}0m"
BOLD="${ESC}1m"
C_CYAN="${ESC}38;5;51m"
C_BLUE="${ESC}38;5;39m"
C_GREEN="${ESC}38;5;48m"
C_YELLOW="${ESC}38;5;220m"
C_ORANGE="${ESC}38;5;208m"
C_RED="${ESC}38;5;196m"
C_PURPLE="${ESC}38;5;141m"
C_WHITE="${ESC}38;5;255m"

PANEL_DIR="/var/www/pterodactyl"
BACKUP_DIR="${PANEL_DIR}/theme_backups"
REPO_URL="https://github.com/fahrihostingg/pahri-pterodactyl-theme.git"

print_header() {
    clear
    echo -e "${C_BLUE}╔═══════════════════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${C_BLUE}║ ${C_CYAN}${BOLD} ██████╗  █████╗ ██╗  ██╗██████╗ ██╗    ████████╗██╗  ██╗███████╗███╗   ███╗███████╗ ${C_BLUE}║${RESET}"
    echo -e "${C_BLUE}║ ${C_CYAN}${BOLD} ██╔══██╗██╔══██╗██║  ██║██╔══██╗██║    ╚══██╔══╝██║  ██║██╔════╝████╗ ████║██╔════╝ ${C_BLUE}║${RESET}"
    echo -e "${C_BLUE}║ ${C_CYAN}${BOLD} ██████╔╝███████║███████║██████╔╝██║       ██║   ███████║█████╗  ██╔████╔██║█████╗   ${C_BLUE}║${RESET}"
    echo -e "${C_BLUE}║ ${C_CYAN}${BOLD} ██╔═══╝ ██╔══██║██╔══██║██╔══██╗██║       ██║   ██╔══██║██╔══╝  ██║╚██╔╝██║██╔══╝   ${C_BLUE}║${RESET}"
    echo -e "${C_BLUE}║ ${C_CYAN}${BOLD} ██║     ██║  ██║██║  ██║██║  ██║██║       ██║   ██║  ██║███████╗██║ ╚═╝ ██║███████╗ ${C_BLUE}║${RESET}"
    echo -e "${C_BLUE}║ ${C_CYAN}${BOLD} ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝       ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝╚══════╝ ${C_BLUE}║${RESET}"
    echo -e "${C_BLUE}║                                                                       ║${RESET}"
    echo -e "${C_BLUE}║      ${C_YELLOW}✦ PAHRI THEMA NEW 6.0 NEXUS DOCK • AUTO INSTALLER ✦${C_BLUE}              ║${RESET}"
    echo -e "${C_BLUE}║      ${C_PURPLE}Release: v6.7.3 • Pterodactyl Panel v1.14.x Compatible${C_BLUE}           ║${RESET}"
    echo -e "${C_BLUE}╚═══════════════════════════════════════════════════════════════════════╝${RESET}\n"
}

log_step() {
    echo -e "${C_CYAN}➜ [LANGKAH]${RESET} ${C_WHITE}$1${RESET}"
}

log_ok() {
    echo -e "${C_GREEN}✔ [BERJAYA]${RESET} ${BOLD}${C_GREEN}$1${RESET}"
}

log_warn() {
    echo -e "${C_YELLOW}▲ [PERINGATAN]${RESET} ${C_YELLOW}$1${RESET}"
}

log_fail() {
    echo -e "${C_RED}✖ [RALAT]${RESET} ${BOLD}${C_RED}$1${RESET}"
}

# 1. Semakan Hak Root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_fail "Skrip pemasangan ini mesti dijalankan sebagai root!"
        echo -e "Sila taip arahan: ${C_YELLOW}sudo su${RESET} atau ${C_YELLOW}sudo bash install.sh${RESET}"
        exit 1
    fi
}

# 2. Semakan Direktori Pterodactyl
check_pterodactyl() {
    if [[ ! -d "$PANEL_DIR" ]] || [[ ! -f "$PANEL_DIR/artisan" ]]; then
        log_fail "Direktori Pterodactyl tidak ditemui di ${PANEL_DIR}!"
        exit 1
    fi
}

# 3. Pemasangan Pakej Sokongan
install_deps() {
    log_step "Memeriksa pakej sokongan (curl, git, python3, unzip, tar)..."
    if command -v apt-get &>/dev/null; then
        apt-get update -y >/dev/null 2>&1
        apt-get install -y curl git python3 python3-pip unzip tar >/dev/null 2>&1
    elif command -v yum &>/dev/null; then
        yum install -y curl git python3 python3-pip unzip tar >/dev/null 2>&1
    fi
    log_ok "Pakej sokongan sedia ada."
}

# 4. Sandaran Automatik (Auto-Backup)
backup_panel() {
    log_step "Mencipta fail sandaran sebelum pengubahsuaian..."
    mkdir -p "$BACKUP_DIR"
    local bfile="${BACKUP_DIR}/pahri_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    cd "$PANEL_DIR"
    tar -czf "$bfile" resources/ public/ app/ routes/ 2>/dev/null || true
    log_ok "Sandaran berjaya disimpan: $(basename "$bfile")"
}

# 5. Jalankan Patcher Python
run_patcher() {
    log_step "Menjalankan patcher tema (patcher-v2.py)..."
    local SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    if [[ -f "$SCRIPT_DIR/patcher-v2.py" ]]; then
        python3 "$SCRIPT_DIR/patcher-v2.py" "$PANEL_DIR"
    elif [[ -f "$PANEL_DIR/patcher-v2.py" ]]; then
        python3 "$PANEL_DIR/patcher-v2.py" "$PANEL_DIR"
    else
        log_warn "patcher-v2.py tidak dijumpai secara lokal. Memuat turun dari arkib tema..."
        curl -sSL "https://raw.githubusercontent.com/fahrihostingg/pahri-pterodactyl-theme/main/patcher-v2.py" -o "/tmp/patcher-v2.py"
        python3 "/tmp/patcher-v2.py" "$PANEL_DIR"
        rm -f "/tmp/patcher-v2.py"
    fi
    log_ok "Patcher tema berjaya disempurnakan."
}

# 6. Salin Fail Aset & Styling
copy_theme_files() {
    log_step "Menyalin fail komponen tema (files/ & source/)..."
    local SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    if [[ -d "$SCRIPT_DIR/files" ]]; then
        cp -r "$SCRIPT_DIR/files"/* "$PANEL_DIR"/
    fi
    log_ok "Fail komponen tema berjaya diselaraskan."
}

# 7. Bersihkan Cache & Permissions
finalize_panel() {
    log_step "Membersihkan cache Pterodactyl dan menetapkan permissions..."
    cd "$PANEL_DIR"
    php artisan view:clear >/dev/null 2>&1 || true
    php artisan config:clear >/dev/null 2>&1 || true
    php artisan cache:clear >/dev/null 2>&1 || true
    php artisan route:clear >/dev/null 2>&1 || true

    chown -R www-data:www-data "$PANEL_DIR"/* 2>/dev/null || chown -R nginx:nginx "$PANEL_DIR"/* 2>/dev/null || true
    chmod -R 755 "$PANEL_DIR"/storage "$PANEL_DIR"/bootstrap/cache
    log_ok "Pembersihan cache & kebenaran fail selesai."
}

main() {
    print_header
    check_root
    check_pterodactyl
    install_deps
    backup_panel
    copy_theme_files
    run_patcher
    finalize_panel

    echo ""
    echo -e "${C_GREEN}╔═══════════════════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${C_GREEN}║               PEMASANGAN TEMA BERJAYA DISELESAIKAN!                  ║${RESET}"
    echo -e "${C_GREEN}║                                                                       ║${RESET}"
    echo -e "${C_GREEN}║  ${C_WHITE}Tema      : ${C_YELLOW}Pahri Thema New 6.0 (Nexus Dock v6.7.3)${C_GREEN}                 ║${RESET}"
    echo -e "${C_GREEN}║  ${C_WHITE}Status    : ${C_CYAN}Aktif & Dioptimumkan${C_GREEN}                                    ║${RESET}"
    echo -e "${C_GREEN}║  ${C_WHITE}Aksi Seterusnya: ${C_WHITE}Sila muat semula (refresh) pelayar / panel anda.     ║${RESET}"
    echo -e "${C_GREEN}╚═══════════════════════════════════════════════════════════════════════╝${RESET}"
    echo ""
}

main "$@"
