CREATE DATABASE IF NOT EXISTS yuraisha_inventory;

USE yuraisha_inventory;

-- 1. User Table (Tbl_user)
CREATE TABLE IF NOT EXISTS tbl_user (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    employee_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    user_role VARCHAR(20) NOT NULL
);

-- 2. Material Table (Tbl_material)
CREATE TABLE IF NOT EXISTS tbl_material (
    material_id INT AUTO_INCREMENT PRIMARY KEY,
    material_name VARCHAR(50) NOT NULL,
    current_quantity DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    low_stock_threshold DECIMAL(10,0) NOT NULL DEFAULT 0,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 3. Supplier Table (Tbl_supplier)
CREATE TABLE IF NOT EXISTS tbl_supplier (
    supplier_id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_name VARCHAR(100) NOT NULL,
    contact_number VARCHAR(20),
    email VARCHAR(100)
);

-- 4. Delivery Log Table (Tbl_delivery_log)
CREATE TABLE IF NOT EXISTS tbl_delivery_log (
    delivery_id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_id INT,
    material_id INT,
    user_id INT,
    tracking_number INT,
    quantity_delivered INT NOT NULL,
    expected_arrival DATETIME,
    actual_arrival DATETIME,
    shipping_status VARCHAR(20),
    FOREIGN KEY (supplier_id) REFERENCES tbl_supplier(supplier_id) ON DELETE SET NULL,
    FOREIGN KEY (material_id) REFERENCES tbl_material(material_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES tbl_user(user_id) ON DELETE SET NULL
);

-- 5. Client Transaction Table (Tbl_client_transaction)
CREATE TABLE IF NOT EXISTS tbl_client_transaction (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    client_name VARCHAR(100) NOT NULL,
    quantity_sold INT NOT NULL,
    oil_used_kg DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    plastic_used_units INT NOT NULL DEFAULT 0,
    transaction_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    transaction_status VARCHAR(20),
    transaction_date DATE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES tbl_user(user_id) ON DELETE SET NULL
);
