-- ==========================================================================
-- PharmaCare - MySQL Setup Script
-- Run this in MySQL Workbench or MySQL CLI to prepare the database.
-- ==========================================================================

-- 1. Create the database
CREATE DATABASE IF NOT EXISTS pharmacare
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE pharmacare;

-- 2. Create the users table
CREATE TABLE IF NOT EXISTS users (
    id           INT           NOT NULL AUTO_INCREMENT,
    name         VARCHAR(150)  NOT NULL,
    email        VARCHAR(255)  NOT NULL UNIQUE,
    password     VARCHAR(255)  NOT NULL,
    role         ENUM('customer', 'admin') NOT NULL DEFAULT 'customer',
    created_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Create the medicines table
CREATE TABLE IF NOT EXISTS medicines (
    id                     INT            NOT NULL AUTO_INCREMENT,
    name                   VARCHAR(200)   NOT NULL,
    category               VARCHAR(100),
    manufacturer           VARCHAR(150),
    price                  DECIMAL(10, 2) NOT NULL,
    stock_quantity         INT            NOT NULL DEFAULT 0,
    expiry_date            DATE,
    description            TEXT,
    requires_prescription  BOOLEAN        NOT NULL DEFAULT FALSE,
    created_at             DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

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
SHOW TABLES;

SELECT * FROM medicines;
