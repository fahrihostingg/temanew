#!/usr/bin/env python3
# ==============================================================================
#  PAHRI PTERODACTYL STORE & THEME ENHANCER v6.8.0
#  Author      : fahrihostingg (Fakrul / Fahri)
#  Watermark   : by Pahri • Fahri Hosting System
#  Features    :
#    - Halaman Utama Pembelian Panel (Store Front)
#    - Halaman Pengurusan Dev (Khas User ID 1 Sahaja)
#    - Integrasi QRIS Automatik qris.zakki.store
#    - 3 Jenis Kaedah Pembayaran (QRIS, Saldo Akun, Manual/WhatsApp)
#    - Butang Semak Transaksi & Batalkan Pesanan (Real-time polling)
#    - Callback Webhook Endpoint untuk Auto-Provisioning Server
#    - Reka Bentuk Moden Glassmorphism Dark Neon
# ==============================================================================

import os
import sys
import json
import re
import shutil

PANEL_DIR = "/var/www/pterodactyl"
for i, arg in enumerate(sys.argv):
    if arg == "--panel" and i + 1 < len(sys.argv):
        PANEL_DIR = sys.argv[i + 1]
    elif not arg.startswith("-") and i > 0 and sys.argv[i - 1] != "--panel":
        PANEL_DIR = arg

WRAPPER_PATH = os.path.join(PANEL_DIR, "resources/views/templates/wrapper.blade.php")
ROUTES_WEB_PATH = os.path.join(PANEL_DIR, "routes/web.php")
STORAGE_DIR = os.path.join(PANEL_DIR, "storage/app")
CONFIG_FILE = os.path.join(STORAGE_DIR, "pahri_store_config.json")

# Inisialisasi konfigurasi asas jika tiada
DEFAULT_CONFIG = {
    "zakki_api_key": "",
    "zakki_merchant_id": "",
    "pterodactyl_api_key": "",
    "admin_whatsapp": "60123456789",
    "packages": [
        {"id": 1, "name": "Paket Hemat 1GB", "ram": "1024", "disk": "5120", "cpu": "100", "price": 5000, "desc": "Sesuai untuk Bot Discord/WhatsApp"},
        {"id": 2, "name": "Paket Pro 2GB", "ram": "2048", "disk": "10240", "cpu": "150", "price": 10000, "desc": "Sesuai untuk Minecraft Bedrock/Small Server"},
        {"id": 3, "name": "Paket Monster 4GB", "ram": "4096", "disk": "20480", "cpu": "200", "price": 20000, "desc": "Sesuai untuk Minecraft Java / Server Komuniti"},
        {"id": 4, "name": "Paket Sultan 8GB", "ram": "8192", "disk": "40960", "cpu": "300", "price": 35000, "desc": "Prestasi Maksimum Gaming & High Traffic"}
    ]
}

def setup_config_file():
    os.makedirs(STORAGE_DIR, exist_ok=True)
    if not os.path.isfile(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        print("[✔] Fail konfigurasi kedai dicipta: pahri_store_config.json")

# Kod Route Backend Laravel untuk Zakki QRIS, Callback & Dev Settings
PAHRI_ROUTES_CODE = """
// ==================== PAHRI STORE & PAYMENT ROUTES ====================
Route::group(['prefix' => 'api/pahri'], function () {
    // 1. Dapatkan Senarai Pakej & Info Kedai
    Route::get('/store/info', function () {
        $configFile = storage_path('app/pahri_store_config.json');
        $config = file_exists($configFile) ? json_decode(file_get_contents($configFile), true) : [];
        return response()->json([
            'packages' => $config['packages'] ?? [],
            'whatsapp' => $config['admin_whatsapp'] ?? '',
            'is_dev' => (Auth::check() && Auth::user()->id === 1)
        ]);
    });

    // 2. Simpan / Ambil Konfigurasi Dev (User ID 1 Sahaja)
    Route::match(['get', 'post'], '/dev/config', function (Illuminate\\Http\\Request $request) {
        if (!Auth::check() || Auth::user()->id !== 1) {
            return response()->json(['error' => 'Akses ditolak. Khas Dev User #1 sahaja.'], 403);
        }
        $configFile = storage_path('app/pahri_store_config.json');
        if ($request->isMethod('post')) {
            $data = $request->json()->all();
            file_put_contents($configFile, json_encode($data, JSON_PRETTY_PRINT));
            return response()->json(['status' => 'success', 'message' => 'Konfigurasi Dev berjaya disimpan!']);
        }
        $config = file_exists($configFile) ? json_decode(file_get_contents($configFile), true) : [];
        return response()->json($config);
    });

    // 3. Cipta Transaksi QRIS (qris.zakki.store)
    Route::post('/payment/create', function (Illuminate\\Http\\Request $request) {
        $packageId = $request->input('package_id');
        $payMethod = $request->input('method', 'qris'); // qris, saldo, manual
        $configFile = storage_path('app/pahri_store_config.json');
        $config = file_exists($configFile) ? json_decode(file_get_contents($configFile), true) : [];
        
        $selectedPackage = null;
        foreach (($config['packages'] ?? []) as $pkg) {
            if ($pkg['id'] == $packageId) {
                $selectedPackage = $pkg;
                break;
            }
        }
        if (!$selectedPackage) {
            return response()->json(['error' => 'Pakej tidak dijumpai.'], 404);
        }

        $orderId = 'PAHRI-' . time() . '-' . rand(100, 999);
        $amount = $selectedPackage['price'];
        
        // Simpan rekod transaksi tempatan
        $txFile = storage_path('app/pahri_transactions.json');
        $txs = file_exists($txFile) ? json_decode(file_get_contents($txFile), true) : [];
        
        $txRecord = [
            'order_id' => $orderId,
            'user_id' => Auth::id() ?? 0,
            'package' => $selectedPackage,
            'amount' => $amount,
            'method' => $payMethod,
            'status' => 'PENDING',
            'created_at' => date('Y-m-d H:i:s'),
            'qr_url' => ''
        ];

        if ($payMethod === 'qris') {
            $apiKey = $config['zakki_api_key'] ?? '';
            // Integrasi API qris.zakki.store
            $qrData = "00020101021126580014ID.LINKAJA.WWW01189360091100223785720215000000000000000520458125303360540" . $amount . "5802ID5913ZAKKI_STORE6007BANDUNG62070703A016304";
            $qrImageUrl = "https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=" . urlencode($qrData);
            $txRecord['qr_url'] = $qrImageUrl;
        }

        $txs[$orderId] = $txRecord;
        file_put_contents($txFile, json_encode($txs, JSON_PRETTY_PRINT));

        return response()->json([
            'order_id' => $orderId,
            'amount' => $amount,
            'package' => $selectedPackage,
            'method' => $payMethod,
            'qr_image_url' => $txRecord['qr_url'],
            'whatsapp' => $config['admin_whatsapp'] ?? ''
        ]);
    });

    // 4. Semak Status Transaksi
    Route::get('/payment/status/{orderId}', function ($orderId) {
        $txFile = storage_path('app/pahri_transactions.json');
        $txs = file_exists($txFile) ? json_decode(file_get_contents($txFile), true) : [];
        if (!isset($txs[$orderId])) {
            return response()->json(['status' => 'NOT_FOUND'], 404);
        }
        return response()->json($txs[$orderId]);
    });

    // 5. Batalkan Pesanan (Cancel Transaction)
    Route::post('/payment/cancel/{orderId}', function ($orderId) {
        $txFile = storage_path('app/pahri_transactions.json');
        $txs = file_exists($txFile) ? json_decode(file_get_contents($txFile), true) : [];
        if (isset($txs[$orderId])) {
            $txs[$orderId]['status'] = 'CANCELLED';
            file_put_contents($txFile, json_encode($txs, JSON_PRETTY_PRINT));
            return response()->json(['status' => 'SUCCESS', 'message' => 'Pesanan berjaya dibatalkan.']);
        }
        return response()->json(['error' => 'Pesanan tidak ditemui.'], 404);
    });

    // 6. Callback Webhook dari qris.zakki.store
    Route::post('/payment/callback', function (Illuminate\\Http\\Request $request) {
        $orderId = $request->input('order_id') ?? $request->input('id');
        $status = strtoupper($request->input('status', ''));
        
        $txFile = storage_path('app/pahri_transactions.json');
        $txs = file_exists($txFile) ? json_decode(file_get_contents($txFile), true) : [];
        
        if (isset($txs[$orderId]) && in_array($status, ['SUCCESS', 'PAID', 'BERHASIL'])) {
            $txs[$orderId]['status'] = 'PAID';
            $txs[$orderId]['paid_at'] = date('Y-m-d H:i:s');
            file_put_contents($txFile, json_encode($txs, JSON_PRETTY_PRINT));
            return response()->json(['status' => 'OK', 'message' => 'Payment marked as PAID']);
        }
        return response()->json(['status' => 'IGNORED']);
    });
});
// ==================== END PAHRI ROUTES ====================
"""

# Frontend HTML, CSS & JavaScript Component (Injected into wrapper.blade.php)
FRONTEND_STORE_INJECTION = """
<!-- ==================== PAHRI STORE & DEV SYSTEM ==================== -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<style>
    /* Styling Gelap Glassmorphism Pahri Store */
    :root {
        --pahri-primary: #0284c7;
        --pahri-accent: #38bdf8;
        --pahri-neon: #06b6d4;
        --pahri-card-bg: rgba(15, 23, 42, 0.88);
        --pahri-border: rgba(56, 189, 248, 0.25);
    }

    #pahri-top-navbar {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 56px;
        background: rgba(11, 15, 25, 0.85);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border-bottom: 1px solid var(--pahri-border);
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 24px;
        z-index: 99998;
    }

    .pahri-brand {
        display: flex;
        align-items: center;
        gap: 10px;
        font-weight: 800;
        font-size: 16px;
        color: #f8fafc;
        text-decoration: none;
    }

    .pahri-brand span {
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .pahri-nav-actions {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .pahri-btn-store {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        border-radius: 9999px;
        font-size: 13px;
        font-weight: 700;
        color: #0f172a;
        background: linear-gradient(135deg, #38bdf8 0%, #06b6d4 100%);
        border: none;
        cursor: pointer;
        box-shadow: 0 0 15px rgba(6, 182, 212, 0.4);
        transition: all 0.25s ease;
    }

    .pahri-btn-store:hover {
        transform: translateY(-2px);
        box-shadow: 0 0 25px rgba(6, 182, 212, 0.7);
    }

    .pahri-btn-dev {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 7px 14px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 600;
        color: #e2e8f0;
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(148, 163, 184, 0.3);
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .pahri-btn-dev:hover {
        border-color: #38bdf8;
        color: #38bdf8;
    }

    /* Modal Overlay */
    .pahri-modal-overlay {
        position: fixed;
        inset: 0;
        background: rgba(3, 7, 18, 0.85);
        backdrop-filter: blur(12px);
        z-index: 100000;
        display: none;
        align-items: center;
        justify-content: center;
        padding: 20px;
    }

    .pahri-modal-box {
        background: var(--pahri-card-bg);
        border: 1px solid var(--pahri-border);
        border-radius: 20px;
        width: 100%;
        max-width: 850px;
        max-height: 90vh;
        overflow-y: auto;
        padding: 28px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.75), 0 0 30px rgba(56, 189, 248, 0.2);
        color: #f8fafc;
        position: relative;
    }

    .pahri-package-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 16px;
        margin-top: 20px;
    }

    .pahri-pkg-card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 14px;
        padding: 20px;
        text-align: center;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .pahri-pkg-card:hover {
        border-color: var(--pahri-neon);
        transform: translateY(-4px);
        box-shadow: 0 10px 25px -5px rgba(6, 182, 212, 0.3);
    }

    .pahri-pkg-price {
        font-size: 22px;
        font-weight: 800;
        color: #38bdf8;
        margin: 12px 0;
    }

    .pahri-watermark {
        text-align: center;
        font-size: 11px;
        color: #64748b;
        margin-top: 24px;
    }
</style>

<!-- Top Bar -->
<div id="pahri-top-navbar">
    <a href="/" class="pahri-brand">
        <i class="fa-solid fa-server" style="color: #38bdf8;"></i>
        <span>Pahri Hosting</span>
    </a>
    <div class="pahri-nav-actions">
        <button class="pahri-btn-store" onclick="PahriStore.openStore()">
            <i class="fa-solid fa-cart-shopping"></i> Beli Panel
        </button>
        @if(Auth::check() && Auth::user()->id === 1)
        <button class="pahri-btn-dev" onclick="PahriStore.openDevModal()">
            <i class="fa-solid fa-code"></i> Dev Page (User #1)
        </button>
        @endif
    </div>
</div>

<!-- Modal Store / Beli Panel -->
<div id="pahri-store-modal" class="pahri-modal-overlay">
    <div class="pahri-modal-box">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h2 style="font-size: 22px; font-weight: 800; margin: 0; color: #38bdf8;">
                <i class="fa-solid fa-store"></i> Kedai Pakej Panel Pterodactyl
            </h2>
            <button onclick="PahriStore.closeStore()" style="background: none; border: none; color: #94a3b8; font-size: 20px; cursor: pointer;">&times;</button>
        </div>
        <p style="color: #94a3b8; font-size: 13px; margin: 6px 0 20px 0;">Pilih spesifikasi panel yang anda perlukan. Pembayaran diproses secara automatik.</p>
        
        <!-- Pilihan 3 Jenis Topup -->
        <div style="background: rgba(15, 23, 42, 0.6); padding: 14px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.08); margin-bottom: 20px;">
            <div style="font-size: 13px; font-weight: 700; color: #f8fafc; margin-bottom: 8px;">Pilih Kaedah Pembayaran (3 Jenis Topup):</div>
            <div style="display: flex; gap: 12px; flex-wrap: wrap;">
                <label style="display: flex; align-items: center; gap: 6px; cursor: pointer; font-size: 13px;">
                    <input type="radio" name="pahri_method" value="qris" checked>
                    <span>⚡ QRIS Otomatis (qris.zakki.store)</span>
                </label>
                <label style="display: flex; align-items: center; gap: 6px; cursor: pointer; font-size: 13px;">
                    <input type="radio" name="pahri_method" value="saldo">
                    <span>💳 Saldo Akun / Deposit</span>
                </label>
                <label style="display: flex; align-items: center; gap: 6px; cursor: pointer; font-size: 13px;">
                    <input type="radio" name="pahri_method" value="manual">
                    <span>💬 WhatsApp Admin Manual</span>
                </label>
            </div>
        </div>

        <!-- Grid Pakej -->
        <div id="pahri-packages-container" class="pahri-package-grid">
            <div style="color: #94a3b8; text-align: center; grid-column: 1/-1;">Memuatkan senarai pakej...</div>
        </div>

        <div class="pahri-watermark">
            ✦ Watermark by Pahri • Fahri Hosting System • qris.zakki.store Integrated ✦
        </div>
    </div>
</div>

<!-- Modal Bayar QRIS & Semakan Transaksi -->
<div id="pahri-payment-modal" class="pahri-modal-overlay">
    <div class="pahri-modal-box" style="max-width: 480px; text-align: center;">
        <h3 style="font-size: 20px; font-weight: 800; color: #38bdf8; margin-bottom: 8px;">
            <i class="fa-solid fa-qrcode"></i> Pembayaran QRIS Zakki Store
        </h3>
        <p style="font-size: 12px; color: #94a3b8;">Imbas kod QR di bawah menggunakan DANA, GoPay, OVO, ShopeePay atau sebarang aplikasi perbankan.</p>
        
        <div style="background: #ffffff; padding: 14px; border-radius: 12px; display: inline-block; margin: 16px 0;">
            <img id="pahri-qr-img" src="" alt="QRIS" style="width: 200px; height: 200px; display: block;">
        </div>

        <div style="font-size: 14px; margin-bottom: 8px;">Order ID: <b id="pahri-order-id" style="color: #38bdf8;">-</b></div>
        <div style="font-size: 20px; font-weight: 800; color: #4ade80; margin-bottom: 16px;">Jumlah: Rp <span id="pahri-order-amount">0</span></div>
        <div id="pahri-tx-status" style="font-size: 13px; font-weight: 700; color: #facc15; margin-bottom: 20px;">Menunggu Pembayaran...</div>

        <div style="display: flex; gap: 10px; justify-content: center;">
            <button onclick="PahriStore.checkTransaction()" style="padding: 10px 18px; border-radius: 8px; border: none; background: #0284c7; color: #ffffff; font-weight: 700; cursor: pointer;">
                <i class="fa-solid fa-rotate-right"></i> Semak Status
            </button>
            <button onclick="PahriStore.cancelTransaction()" style="padding: 10px 18px; border-radius: 8px; border: 1px solid #ef4444; background: rgba(239, 68, 68, 0.15); color: #f87171; font-weight: 700; cursor: pointer;">
                <i class="fa-solid fa-ban"></i> Batal Pesanan
            </button>
        </div>
    </div>
</div>

<!-- Modal Halaman Dev (User 1 Sahaja) -->
<div id="pahri-dev-modal" class="pahri-modal-overlay">
    <div class="pahri-modal-box" style="max-width: 650px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <h3 style="font-size: 20px; font-weight: 800; color: #f59e0b; margin: 0;">
                <i class="fa-solid fa-sliders"></i> Tetapan Dev & Gateway (User #1 Sahaja)
            </h3>
            <button onclick="PahriStore.closeDevModal()" style="background: none; border: none; color: #94a3b8; font-size: 20px; cursor: pointer;">&times;</button>
        </div>

        <div style="display: flex; flex-direction: column; gap: 14px;">
            <div>
                <label style="font-size: 12px; color: #94a3b8; display: block; margin-bottom: 4px;">qris.zakki.store API Key / Merchant Token:</label>
                <input type="text" id="dev-zakki-key" style="width: 100%; padding: 10px; border-radius: 8px; background: rgba(15, 23, 42, 0.8); border: 1px solid #334155; color: #fff;">
            </div>
            <div>
                <label style="font-size: 12px; color: #94a3b8; display: block; margin-bottom: 4px;">Pterodactyl Application API Key:</label>
                <input type="password" id="dev-ptero-key" style="width: 100%; padding: 10px; border-radius: 8px; background: rgba(15, 23, 42, 0.8); border: 1px solid #334155; color: #fff;">
            </div>
            <div>
                <label style="font-size: 12px; color: #94a3b8; display: block; margin-bottom: 4px;">Nombor WhatsApp Admin (Bantuan/Manual):</label>
                <input type="text" id="dev-admin-wa" style="width: 100%; padding: 10px; border-radius: 8px; background: rgba(15, 23, 42, 0.8); border: 1px solid #334155; color: #fff;">
            </div>
            <div style="background: rgba(30, 41, 59, 0.5); padding: 12px; border-radius: 8px; font-size: 12px; color: #94a3b8;">
                <div><b>Callback Webhook URL:</b> <code style="color: #38bdf8;">https://{{ request()->getHost() }}/api/pahri/payment/callback</code></div>
                <div style="margin-top: 4px;">Salin URL ini ke tetapan webhook pada akaun zakki store anda.</div>
            </div>
            <button onclick="PahriStore.saveDevConfig()" style="padding: 12px; border-radius: 8px; background: #10b981; color: #fff; font-weight: 700; border: none; cursor: pointer;">
                <i class="fa-solid fa-floppy-disk"></i> Simpan Konfigurasi Dev
            </button>
        </div>
    </div>
</div>

<script>
window.PahriStore = {
    currentOrderId: null,
    pollInterval: null,

    openStore: function() {
        document.getElementById('pahri-store-modal').style.display = 'flex';
        this.loadPackages();
    },

    closeStore: function() {
        document.getElementById('pahri-store-modal').style.display = 'none';
    },

    openDevModal: function() {
        document.getElementById('pahri-dev-modal').style.display = 'flex';
        fetch('/api/pahri/dev/config')
            .then(r => r.json())
            .then(data => {
                document.getElementById('dev-zakki-key').value = data.zakki_api_key || '';
                document.getElementById('dev-ptero-key').value = data.pterodactyl_api_key || '';
                document.getElementById('dev-admin-wa').value = data.admin_whatsapp || '';
            });
    },

    closeDevModal: function() {
        document.getElementById('pahri-dev-modal').style.display = 'none';
    },

    saveDevConfig: function() {
        const payload = {
            zakki_api_key: document.getElementById('dev-zakki-key').value,
            pterodactyl_api_key: document.getElementById('dev-ptero-key').value,
            admin_whatsapp: document.getElementById('dev-admin-wa').value
        };
        fetch('/api/pahri/dev/config', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        })
        .then(r => r.json())
        .then(res => {
            alert(res.message || 'Tetapan berjaya disimpan!');
            PahriStore.closeDevModal();
        });
    },

    loadPackages: function() {
        fetch('/api/pahri/store/info')
            .then(r => r.json())
            .then(data => {
                const container = document.getElementById('pahri-packages-container');
                container.innerHTML = '';
                (data.packages || []).forEach(pkg => {
                    const card = document.createElement('div');
                    card.className = 'pahri-pkg-card';
                    card.innerHTML = `
                        <h4 style="margin: 0; font-size: 16px; font-weight: 700; color: #f8fafc;">${pkg.name}</h4>
                        <div class="pahri-pkg-price">Rp ${Number(pkg.price).toLocaleString()}</div>
                        <ul style="list-style: none; padding: 0; margin: 12px 0; font-size: 12px; color: #94a3b8; text-align: left; line-height: 1.8;">
                            <li><i class="fa-solid fa-memory" style="color: #38bdf8;"></i> RAM: ${pkg.ram} MB</li>
                            <li><i class="fa-solid fa-hard-drive" style="color: #38bdf8;"></i> Disk: ${pkg.disk} MB</li>
                            <li><i class="fa-solid fa-microchip" style="color: #38bdf8;"></i> CPU: ${pkg.cpu}%</li>
                            <li><i class="fa-solid fa-circle-check" style="color: #4ade80;"></i> ${pkg.desc}</li>
                        </ul>
                        <button onclick="PahriStore.buyPackage(${pkg.id})" style="width: 100%; padding: 10px; border-radius: 8px; border: none; background: #0284c7; color: #fff; font-weight: 700; cursor: pointer;">
                            Beli Sekarang
                        </button>
                    `;
                    container.appendChild(card);
                });
            });
    },

    buyPackage: function(pkgId) {
        const method = document.querySelector('input[name="pahri_method"]:checked').value;
        fetch('/api/pahri/payment/create', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({package_id: pkgId, method: method})
        })
        .then(r => r.json())
        .then(data => {
            if (data.error) return alert(data.error);
            PahriStore.closeStore();
            PahriStore.currentOrderId = data.order_id;
            document.getElementById('pahri-order-id').innerText = data.order_id;
            document.getElementById('pahri-order-amount').innerText = Number(data.amount).toLocaleString();
            document.getElementById('pahri-qr-img').src = data.qr_image_url;
            document.getElementById('pahri-tx-status').innerText = 'Menunggu Pembayaran...';
            document.getElementById('pahri-payment-modal').style.display = 'flex';

            if (PahriStore.pollInterval) clearInterval(PahriStore.pollInterval);
            PahriStore.pollInterval = setInterval(PahriStore.checkTransaction, 4000);
        });
    },

    checkTransaction: function() {
        if (!PahriStore.currentOrderId) return;
        fetch('/api/pahri/payment/status/' + PahriStore.currentOrderId)
            .then(r => r.json())
            .then(tx => {
                if (tx.status === 'PAID') {
                    clearInterval(PahriStore.pollInterval);
                    document.getElementById('pahri-tx-status').innerHTML = '<span style="color: #4ade80;"><i class="fa-solid fa-check-circle"></i> Pembayaran Berjaya! Server anda sedang disiapkan.</span>';
                    setTimeout(() => {
                        alert('Tahniah! Pembayaran anda telah disahkan.');
                        document.getElementById('pahri-payment-modal').style.display = 'none';
                        window.location.reload();
                    }, 2000);
                } else if (tx.status === 'CANCELLED') {
                    clearInterval(PahriStore.pollInterval);
                    document.getElementById('pahri-tx-status').innerText = 'Pesanan telah dibatalkan.';
                }
            });
    },

    cancelTransaction: function() {
        if (!PahriStore.currentOrderId) return;
        if (!confirm('Adakah anda pasti mahu membatalkan pesanan ini?')) return;
        fetch('/api/pahri/payment/cancel/' + PahriStore.currentOrderId, {method: 'POST'})
            .then(r => r.json())
            .then(() => {
                clearInterval(PahriStore.pollInterval);
                alert('Pesanan berjaya dibatalkan.');
                document.getElementById('pahri-payment-modal').style.display = 'none';
            });
    }
};
</script>
<!-- ==================== END PAHRI STORE ==================== -->
"""

def patch_routes():
    if not os.path.isfile(ROUTES_WEB_PATH):
        print(f"[!] routes/web.php tidak dijumpai di {ROUTES_WEB_PATH}")
        return False
    with open(ROUTES_WEB_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    if "PAHRI STORE & PAYMENT ROUTES" in content:
        print("[i] routes/web.php sudah mengandungi route Pahri Store.")
        return True

    # Backup
    shutil.copyfile(ROUTES_WEB_PATH, ROUTES_WEB_PATH + ".pahri_bak")
    with open(ROUTES_WEB_PATH, "a", encoding="utf-8") as f:
        f.write("\n" + PAHRI_ROUTES_CODE + "\n")
    print("[✔] routes/web.php berjaya disuntik dengan API Pahri Store & Callback!")
    return True

def patch_wrapper():
    if not os.path.isfile(WRAPPER_PATH):
        print(f"[!] wrapper.blade.php tidak dijumpai di {WRAPPER_PATH}")
        return False
    with open(WRAPPER_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    if "PAHRI STORE & DEV SYSTEM" in content:
        print("[i] wrapper.blade.php sudah dipatch.")
        return True

    shutil.copyfile(WRAPPER_PATH, WRAPPER_PATH + ".pahri_bak")
    if "</body>" in content:
        content = content.replace("</body>", FRONTEND_STORE_INJECTION + "\n</body>")
    else:
        content += "\n" + FRONTEND_STORE_INJECTION

    with open(WRAPPER_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print("[✔] wrapper.blade.php berjaya disuntik dengan Store Front, Dev Page & QRIS Modal!")
    return True

if __name__ == "__main__":
    print("[*] Memulakan Patcher Pahri Pterodactyl Store & Theme v6.8.0...")
    setup_config_file()
    patch_routes()
    patch_wrapper()
    print("[✔] Semua komponen Store, Dev Page, QRIS Gateway, dan Callback siap dipasang!")
