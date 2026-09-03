-- ==========================================================================
-- PharmaCare - SQLite Setup Script
-- Optional: the Flask application creates these tables automatically.
-- ==========================================================================

-- 1. Create the users table
CREATE TABLE IF NOT EXISTS users (
    id           INTEGER       PRIMARY KEY AUTOINCREMENT,
    name         VARCHAR(150)  NOT NULL,
    email        VARCHAR(255)  NOT NULL UNIQUE,
    password     VARCHAR(255)  NOT NULL,
    role         VARCHAR(20)   NOT NULL DEFAULT 'customer',
    created_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. Create the medicines table
CREATE TABLE IF NOT EXISTS medicines (
    id                     INTEGER        PRIMARY KEY AUTOINCREMENT,
    name                   VARCHAR(200)   NOT NULL,
    category               VARCHAR(100),
    manufacturer           VARCHAR(150),
    price                  DECIMAL(10, 2) NOT NULL,
    stock_quantity         INT            NOT NULL DEFAULT 0,
    expiry_date            DATE,
    description            TEXT,
    requires_prescription  BOOLEAN        NOT NULL DEFAULT 0,
    created_at             DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 3. Insert one sample medicine for testing
INSERT INTO medicines (name, category, manufacturer, price, stock_quantity, expiry_date, description, requires_prescription)
VALUES (
    'Paracetamol',
    'Pain Relief',
    'Sample Pharma',
    100.00,
    50,
    '2026-12-31',
    'A common painkiller used to treat aches and pain. It can also reduce a high temperature.',
    FALSE
);

-- 4. Verify setup
SHOW TABLES;

SELECT * FROM medicines;
