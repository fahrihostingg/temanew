#!/usr/bin/env python3
"""
Pahri Pterodactyl Theme - Safe Patcher v2
Author: fahrihostingg (Fakrul / Fahri)
Version: 6.7.3 (Nexus Dock Edition)
Target: Pterodactyl v1.14.x
"""

import os
import sys
import re
import shutil

PANEL_DIR = sys.argv[1] if len(sys.argv) > 1 else "/var/www/pterodactyl"

WRAPPER_PATH = os.path.join(PANEL_DIR, "resources/views/templates/wrapper.blade.php")
ADMIN_LAYOUT = os.path.join(PANEL_DIR, "resources/views/layouts/admin.blade.php")
CSS_ASSET_DIR = os.path.join(PANEL_DIR, "public/themes/pahri")

NEXUS_STYLE_TAG = """
    <!-- Pahri Thema New 6.0 Nexus Dock Styles & Scripts -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style id="pahri-nexus-theme-css">
        :root {
            --pahri-bg: #0b0f19;
            --pahri-card: rgba(17, 24, 39, 0.82);
            --pahri-accent: #38bdf8;
            --pahri-accent-glow: rgba(56, 189, 248, 0.35);
            --pahri-dock-bg: rgba(15, 23, 42, 0.75);
            --pahri-border: rgba(56, 189, 248, 0.2);
        }

        /* Glassmorphic Background & Global Resets */
        body {
            background-color: var(--pahri-bg) !important;
            background-image: radial-gradient(at 0% 0%, rgba(56, 189, 248, 0.08) 0px, transparent 50%),
                              radial-gradient(at 100% 100%, rgba(99, 102, 241, 0.08) 0px, transparent 50%) !important;
            background-attachment: fixed !important;
        }

        /* Nexus Floating Bottom Dock */
        #pahri-nexus-dock {
            position: fixed;
            bottom: 24px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 18px;
            background: var(--pahri-dock-bg);
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            border: 1px solid var(--pahri-border);
            border-radius: 9999px;
            box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.6), 0 0 20px var(--pahri-accent-glow);
            z-index: 99999;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        #pahri-nexus-dock:hover {
            border-color: rgba(56, 189, 248, 0.45);
            box-shadow: 0 15px 35px -5px rgba(0, 0, 0, 0.7), 0 0 25px var(--pahri-accent-glow);
        }

        .pahri-dock-item {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 42px;
            height: 42px;
            border-radius: 50%;
            color: #94a3b8;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            text-decoration: none;
            transition: all 0.25s ease;
            position: relative;
        }

        .pahri-dock-item:hover {
            color: #38bdf8;
            background: rgba(56, 189, 248, 0.15);
            border-color: #38bdf8;
            transform: translateY(-4px) scale(1.1);
        }

        .pahri-dock-divider {
            width: 1px;
            height: 24px;
            background: rgba(255, 255, 255, 0.12);
        }

        .pahri-dock-tooltip {
            position: absolute;
            bottom: 54px;
            background: #0f172a;
            color: #f8fafc;
            font-size: 11px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 6px;
            border: 1px solid rgba(56, 189, 248, 0.3);
            white-space: nowrap;
            pointer-events: none;
            opacity: 0;
            transform: translateY(6px);
            transition: all 0.2s ease;
        }

        .pahri-dock-item:hover .pahri-dock-tooltip {
            opacity: 1;
            transform: translateY(0);
        }
    </style>
"""

NEXUS_HTML_DOCK = """
    <!-- Pahri Nexus Floating Dock Component -->
    <div id="pahri-nexus-dock">
        <a href="/" class="pahri-dock-item">
            <i class="fa-solid fa-server"></i>
            <span class="pahri-dock-tooltip">Servers</span>
        </a>
        <a href="/account" class="pahri-dock-item">
            <i class="fa-solid fa-user-gear"></i>
            <span class="pahri-dock-tooltip">Account</span>
        </a>
        <a href="/account/api" class="pahri-dock-item">
            <i class="fa-solid fa-key"></i>
            <span class="pahri-dock-tooltip">API Credentials</span>
        </a>
        <div class="pahri-dock-divider"></div>
        <a href="https://fahrihosting.com" target="_blank" class="pahri-dock-item" style="color: #f59e0b;">
            <i class="fa-solid fa-store"></i>
            <span class="pahri-dock-tooltip">Store / Billing</span>
        </a>
        @if(Auth::user() && Auth::user()->root_admin)
        <a href="/admin" class="pahri-dock-item" style="color: #ef4444;">
            <i class="fa-solid fa-shield-halved"></i>
            <span class="pahri-dock-tooltip">Admin Control</span>
        </a>
        @endif
    </div>
"""

def patch_wrapper():
    if not os.path.isfile(WRAPPER_PATH):
        print(f"[!] Wrapper file not found at: {WRAPPER_PATH}")
        return False

    with open(WRAPPER_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Check if already patched
    if "pahri-nexus-dock" in content:
        print("[i] Wrapper is already patched with Pahri Nexus Dock.")
        return True

    # Backup wrapper
    shutil.copyfile(WRAPPER_PATH, WRAPPER_PATH + ".pahri_bak")

    # Inject styles before </head>
    if "</head>" in content:
        content = content.replace("</head>", NEXUS_STYLE_TAG + "\n</head>")
    else:
        content = NEXUS_STYLE_TAG + "\n" + content

    # Inject dock before </body>
    if "</body>" in content:
        content = content.replace("</body>", NEXUS_HTML_DOCK + "\n</body>")
    else:
        content = content + "\n" + NEXUS_HTML_DOCK

    with open(WRAPPER_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print("[✔] wrapper.blade.php patched successfully with Nexus Dock!")
    return True

def patch_admin_layout():
    if not os.path.isfile(ADMIN_LAYOUT):
        return False

    with open(ADMIN_LAYOUT, "r", encoding="utf-8") as f:
        content = f.read()

    if "pahri-admin-meta" in content:
        return True

    shutil.copyfile(ADMIN_LAYOUT, ADMIN_LAYOUT + ".pahri_bak")
    admin_meta = """
    <!-- Pahri Admin Meta User Expose -->
    <meta name="pahri-user-id" content="{{ Auth::user() ? Auth::user()->id : '' }}" id="pahri-admin-meta">
    """
    if "</head>" in content:
        content = content.replace("</head>", admin_meta + "\n</head>")

    with open(ADMIN_LAYOUT, "w", encoding="utf-8") as f:
        f.write(content)

    print("[✔] admin.blade.php patched successfully!")
    return True

if __name__ == "__main__":
    print("[*] Starting Pahri Pterodactyl Theme Patcher v2...")
    patch_wrapper()
    patch_admin_layout()
    print("[*] Patcher completed.")
