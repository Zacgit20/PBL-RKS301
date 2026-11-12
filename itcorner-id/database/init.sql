
-- TABEL USERS
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    phone VARCHAR(13),
    password_hash TEXT NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'Pelanggan',
    joined DATE NOT NULL DEFAULT CURRENT_DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'Aktif'
);

-- TABEL PRODUCTS
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(150) NOT NULL,
    category VARCHAR(100),
    brand VARCHAR(100),
    price_num NUMERIC(15, 2) NOT NULL DEFAULT 0,
    stock INTEGER NOT NULL DEFAULT 0,
    description TEXT,
    image TEXT,
    specs TEXT,
    is_promo BOOLEAN NOT NULL DEFAULT FALSE,
    CHECK (price_num >= 0),
    CHECK (stock >= 0)
);

-- TABEL PAYMENTS
CREATE TABLE IF NOT EXISTS payments (
    id VARCHAR(50) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    amount_num NUMERIC(15, 2) NOT NULL,
    method VARCHAR(50) NOT NULL,
    payment_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(30) NOT NULL DEFAULT 'Menunggu Approval',
    CHECK (amount_num >= 0)
);

-- INDEX UNTUK PENCARIAN
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
