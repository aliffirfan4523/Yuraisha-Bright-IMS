CREATE DATABASE IF NOT EXISTS yuraisha_inventory;

USE yuraisha_inventory;

-- 1. Users
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'manager') NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Inventory Items
CREATE TABLE IF NOT EXISTS inventory_items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    item_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    quantity DECIMAL(10,2) NOT NULL DEFAULT 0,
    unit VARCHAR(20) NOT NULL,
    minimum_stock DECIMAL(10,2) NOT NULL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE INDEX idx_inventory_category ON inventory_items (category);
CREATE INDEX idx_inventory_stock ON inventory_items (quantity, minimum_stock);

CREATE TABLE IF NOT EXISTS inventory_categories (
    category_key VARCHAR(50) PRIMARY KEY,
    category_label VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO inventory_categories (category_key, category_label) VALUES
    ('plastic_1kg', '1kg Plastic Packs'),
    ('box_1kg', '1kg Boxes'),
    ('cooking_oil', 'Cooking Oil'),
    ('finished_goods', 'Finished Goods'),
    ('defect', 'Defect Stock')
ON DUPLICATE KEY UPDATE category_label = VALUES(category_label);

-- 3. Supplier Deliveries
CREATE TABLE IF NOT EXISTS supplier_deliveries (
    delivery_id INT AUTO_INCREMENT PRIMARY KEY,
    movement_type ENUM('inbound', 'outbound') NOT NULL DEFAULT 'inbound',
    supplier_name VARCHAR(100) NOT NULL,
    item_id INT NOT NULL,
    transaction_id INT NULL UNIQUE,
    quantity DECIMAL(10,2) NOT NULL,
    expected_date DATE,
    received_date DATE,
    status ENUM('pending', 'received', 'delayed') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES inventory_items(item_id)
);

CREATE INDEX idx_deliveries_status_date ON supplier_deliveries (status, expected_date);
CREATE INDEX idx_deliveries_item ON supplier_deliveries (item_id);

-- 4. Client Transactions
CREATE TABLE IF NOT EXISTS client_transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    movement_type ENUM('inbound', 'outbound') NOT NULL DEFAULT 'outbound',
    item_id INT NULL,
    quantity DECIMAL(10,2) NOT NULL DEFAULT 0,
    unit VARCHAR(20) NOT NULL DEFAULT 'Units',
    client_name VARCHAR(100) NOT NULL,
    boxes_sold INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    payment_status ENUM('pending', 'completed', 'failed') DEFAULT 'completed',
    transaction_date DATE NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES inventory_items(item_id) ON DELETE SET NULL
);

CREATE INDEX idx_transactions_status_date ON client_transactions (payment_status, transaction_date);
CREATE INDEX idx_transactions_movement_item ON client_transactions (movement_type, item_id);

ALTER TABLE supplier_deliveries
ADD CONSTRAINT fk_deliveries_transaction
FOREIGN KEY (transaction_id) REFERENCES client_transactions(transaction_id) ON DELETE CASCADE;

-- 5. Usage Calculations
CREATE TABLE IF NOT EXISTS usage_calculations (
    calculation_id INT AUTO_INCREMENT PRIMARY KEY,
    box_size_kg DECIMAL(10,2) NOT NULL DEFAULT 1.00,
    units_per_box INT NOT NULL DEFAULT 17,
    oil_ratio DECIMAL(10,2) NOT NULL DEFAULT 1.00,
    plastic_ratio DECIMAL(10,2) NOT NULL DEFAULT 0.10,
    available_oil DECIMAL(10,2) NOT NULL,
    available_plastic DECIMAL(10,2) NOT NULL,
    available_boxes DECIMAL(10,2) NOT NULL DEFAULT 0,
    boxes_can_produce INT NOT NULL,
    remaining_oil DECIMAL(10,2) NOT NULL,
    remaining_plastic DECIMAL(10,2) NOT NULL,
    remaining_boxes DECIMAL(10,2) NOT NULL DEFAULT 0,
    record_type VARCHAR(20) NOT NULL DEFAULT 'production',
    calculated_by INT,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (calculated_by) REFERENCES users(user_id)
);

-- 6. Notifications
CREATE TABLE IF NOT EXISTS notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    message TEXT NOT NULL,
    type ENUM('low_stock', 'delayed_delivery', 'general') NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_notifications_title_type (title, type)
);

CREATE INDEX idx_notifications_read_type ON notifications (is_read, type);

-- 7. Reports
CREATE TABLE IF NOT EXISTS reports (
    report_id INT AUTO_INCREMENT PRIMARY KEY,
    report_type ENUM('inventory', 'supplier', 'transaction', 'stock_summary') NOT NULL,
    generated_by INT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (generated_by) REFERENCES users(user_id)
);

-- 8. Audit Logs
CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INT NULL,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

CREATE INDEX idx_audit_logs_user_date ON audit_logs (user_id, created_at);
