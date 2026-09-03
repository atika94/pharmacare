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
    image_filename         VARCHAR(255),
    created_at             DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 3. Create orders and order line items
CREATE TABLE IF NOT EXISTS orders (
    id              INTEGER       PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER       NOT NULL,
    total_amount    DECIMAL(10, 2) NOT NULL,
    pickup_location VARCHAR(200)  NOT NULL,
    status          VARCHAR(30)   NOT NULL DEFAULT 'pending',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS order_items (
    id          INTEGER       PRIMARY KEY AUTOINCREMENT,
    order_id    INTEGER       NOT NULL,
    medicine_id INTEGER       NOT NULL,
    quantity    INTEGER       NOT NULL CHECK (quantity > 0),
    unit_price  DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders (id),
    FOREIGN KEY (medicine_id) REFERENCES medicines (id)
);

-- 4. Insert one sample medicine for testing
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

-- 5. Verify setup
SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name;

SELECT * FROM medicines;
