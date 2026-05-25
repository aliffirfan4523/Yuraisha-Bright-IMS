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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Inventory Items
CREATE TABLE IF NOT EXISTS inventory_items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    item_name VARCHAR(100) NOT NULL,
    category ENUM('box', 'plastic', 'cooking_oil') NOT NULL,
    quantity DECIMAL(10,2) NOT NULL DEFAULT 0,
    unit VARCHAR(20) NOT NULL,
    minimum_stock DECIMAL(10,2) NOT NULL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 3. Supplier Deliveries
CREATE TABLE IF NOT EXISTS supplier_deliveries (
    delivery_id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_name VARCHAR(100) NOT NULL,
    item_id INT NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    expected_date DATE,
    received_date DATE,
    status ENUM('pending', 'received', 'delayed') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES inventory_items(item_id)
);

-- 4. Client Transactions
CREATE TABLE IF NOT EXISTS client_transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    client_name VARCHAR(100) NOT NULL,
    boxes_sold INT NOT NULL,
    transaction_date DATE NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Usage Calculations
CREATE TABLE IF NOT EXISTS usage_calculations (
    calculation_id INT AUTO_INCREMENT PRIMARY KEY,
    available_oil DECIMAL(10,2) NOT NULL,
    available_plastic DECIMAL(10,2) NOT NULL,
    boxes_can_produce INT NOT NULL,
    remaining_oil DECIMAL(10,2) NOT NULL,
    remaining_plastic DECIMAL(10,2) NOT NULL,
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Reports
CREATE TABLE IF NOT EXISTS reports (
    report_id INT AUTO_INCREMENT PRIMARY KEY,
    report_type ENUM('inventory', 'supplier', 'transaction', 'stock_summary') NOT NULL,
    generated_by INT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (generated_by) REFERENCES users(user_id)
);
