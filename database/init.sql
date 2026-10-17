-- ============================================================================
-- SKEMA DATABASE POSTGRESQL ITCORNER.ID (PBL-RKS301)
-- Mendukung 4 Fitur Administrator & 9 Fitur Customer
-- ============================================================================

-- 1. TABEL USERS (Mendukung Fitur: Autentikasi, Profil & Avatar, Kelola Akun)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL, -- Hanya menyimpan hash, bukan password asli
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    avatar_filename VARCHAR(255) DEFAULT 'default_avatar.png',
    role VARCHAR(20) NOT NULL DEFAULT 'customer' CHECK (role IN ('customer', 'admin')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    -- Kolom untuk Brute-Force Protection
    failed_login_attempts INT NOT NULL DEFAULT 0,
    locked_until TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. TABEL CATEGORIES (Mendukung Fitur: Cari & Filter, Kelola Produk)
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 3. TABEL PRODUCTS (Mendukung Fitur: Kelola Produk, Cari & Filter, Detail Produk)
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    category_id INT NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    name VARCHAR(150) NOT NULL,
    brand VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    technical_specs TEXT,
    price NUMERIC(12, 2) NOT NULL CHECK (price >= 0),
    stock INT NOT NULL DEFAULT 0 CHECK (stock >= 0),
    image_filename VARCHAR(255) DEFAULT 'default_product.png',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 4. TABEL CART_ITEMS (Mendukung Fitur: Keranjang Belanja)
CREATE TABLE IF NOT EXISTS cart_items (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    quantity INT NOT NULL DEFAULT 1 CHECK (quantity > 0),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, product_id) -- Mencegah duplikasi baris produk yang sama di keranjang user
);

-- 5. TABEL ORDERS (Mendukung Fitur: Checkout, Riwayat Pesanan, Ringkasan Transaksi)
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    shipping_address TEXT NOT NULL,
    total_amount NUMERIC(12, 2) NOT NULL CHECK (total_amount >= 0),
    status VARCHAR(30) NOT NULL DEFAULT 'menunggu_bayar' CHECK (
        status IN ('menunggu_bayar', 'diverifikasi', 'diproses', 'dikirim', 'selesai', 'ditolak')
    ),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 6. TABEL ORDER_ITEMS (Rincian Produk di dalam Faktur/Pesanan)
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INT NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(12, 2) NOT NULL CHECK (unit_price >= 0),
    subtotal NUMERIC(12, 2) NOT NULL CHECK (subtotal >= 0)
);

-- 7. TABEL PAYMENTS (Mendukung Fitur: Bukti Pembayaran & Approval Pembayaran)
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    order_id INT UNIQUE NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    proof_filename VARCHAR(255) NOT NULL,
    file_mime_type VARCHAR(50) NOT NULL,
    file_size_bytes INT NOT NULL CHECK (file_size_bytes > 0),
    verification_status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (
        verification_status IN ('pending', 'approved', 'rejected')
    ),
    verified_by INT REFERENCES users(id) ON DELETE SET NULL,
    admin_notes TEXT,
    uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP NULL
);

-- 8. TABEL REVIEWS (Mendukung Fitur: Ulasan & Komentar serta Rating Produk)
CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (product_id, user_id) -- 1 pengguna memberikan 1 ulasan per produk
);

-- INDEX UNTUK OPTIMASI PENCARIAN & FILTER PRODUK
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);
CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);
CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);

-- ============================================================================
-- SEED DATA AWAL (Data Kategori & Produk Simulasi ITCorner.id)
-- ============================================================================
INSERT INTO categories (name, slug, description) VALUES
    ('Networking & Router', 'networking-router', 'Perangkat router, switch, dan firewall jaringan'),
    ('Komponen PC & Server', 'komponen-pc-server', 'Prosesor, RAM, motherboard, dan komponen server'),
    ('Storage & Backup', 'storage-backup', 'SSD NVMe, HDD Enterprise, dan perangkat NAS')
ON CONFLICT (slug) DO NOTHING;

INSERT INTO products (category_id, name, brand, description, technical_specs, price, stock) VALUES
    (1, 'MikroTik RB4011iGS+RM', 'MikroTik', 'Router enterprise 10 port Gigabit dengan SFP+ 10Gbps.', 'CPU: 4-Core 1.4GHz, RAM: 1GB, Port: 10x GbE + 1x SFP+', 3450000.00, 15),
    (1, 'Ubiquiti UniFi Switch 24 PoE', 'Ubiquiti', 'Managed Layer-2 switch 24 port dengan dukungan PoE+.', 'Port: 24x GbE, 2x SFP, Total PoE: 95W', 6800000.00, 8),
    (2, 'AMD Ryzen 7 7700X Processor', 'AMD', 'Prosesor desktop 8-Core 16-Thread arsitektur Zen 4.', 'Base Clock: 4.5GHz, Boost: 5.4GHz, Socket: AM5, TDP: 105W', 5250000.00, 12),
    (3, 'Samsung 990 PRO NVMe M.2 1TB', 'Samsung', 'SSD NVMe PCIe 4.0 kecepatan tinggi untuk workstation dan server.', 'Read: 7450 MB/s, Write: 6900 MB/s, Interface: PCIe Gen4 x4', 1850000.00, 25)
ON CONFLICT DO NOTHING;
