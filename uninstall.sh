#!/usr/bin/env bash

# ==============================================================================
#  PAHRI THEMA NEW 6.0 - THEME UNINSTALLER & RESTORE SCRIPT
#  Author      : fahrihostingg (Fakrul / Fahri)
#  Target      : Pterodactyl Panel v1.14.x
# ==============================================================================

set -e

PANEL_DIR="/var/www/pterodactyl"
ESC="\033["
RESET="${ESC}0m"
BOLD="${ESC}1m"
C_CYAN="${ESC}38;5;51m"
C_GREEN="${ESC}38;5;48m"
C_YELLOW="${ESC}38;5;220m"
C_RED="${ESC}38;5;196m"

clear
echo -e "${C_CYAN}${BOLD}╔══════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${C_CYAN}${BOLD}║        PAHRI THEMA NEW 6.0 - UNINSTALLER & RESTORER          ║${RESET}"
echo -e "${C_CYAN}${BOLD}╚══════════════════════════════════════════════════════════════╝${RESET}\n"

if [[ $EUID -ne 0 ]]; then
    echo -e "${C_RED}[✗] Sila jalankan arahan ini sebagai root!${RESET}"
    exit 1
fi

WRAPPER="${PANEL_DIR}/resources/views/templates/wrapper.blade.php"
ADMIN_LAYOUT="${PANEL_DIR}/resources/views/layouts/admin.blade.php"

echo -e "${C_YELLOW}[!] Memulihkan fail asal Pterodactyl...${RESET}"

if [[ -f "${WRAPPER}.pahri_bak" ]]; then
    mv "${WRAPPER}.pahri_bak" "$WRAPPER"
    echo -e "${C_GREEN}[✔] wrapper.blade.php dipulihkan.${RESET}"
fi

if [[ -f "${ADMIN_LAYOUT}.pahri_bak" ]]; then
    mv "${ADMIN_LAYOUT}.pahri_bak" "$ADMIN_LAYOUT"
    echo -e "${C_GREEN}[✔] admin.blade.php dipulihkan.${RESET}"
fi

# Jika tiada backup tempatan, muat turun semula resources rasmi
if [[ ! -f "$WRAPPER" ]]; then
    echo -e "${C_YELLOW}[!] Memuat turun semula fail antaramuka rasmi dari Pterodactyl GitHub...${RESET}"
    curl -sSL "https://github.com/pterodactyl/panel/releases/latest/download/panel.tar.gz" | tar -xz -C "$PANEL_DIR" resources/
fi

cd "$PANEL_DIR"
php artisan view:clear >/dev/null 2>&1 || true
php artisan config:clear >/dev/null 2>&1 || true
php artisan cache:clear >/dev/null 2>&1 || true

chown -R www-data:www-data "$PANEL_DIR"/* 2>/dev/null || true
echo -e "\n${C_GREEN}${BOLD}[✔] Tema berjaya dinyahpasang. Panel kembali ke keadaan asal!${RESET}\n"
