import os

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error


def execute_ignore(cursor, sql, duplicate_codes=(1060, 1061)):
    try:
        cursor.execute(sql)
    except Error as exc:
        if exc.errno not in duplicate_codes:
            raise


def main():
    load_dotenv()
    connection = None
    cursor = None

    try:
        connection = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database=os.getenv("MYSQL_DATABASE", "yuraisha_inventory"),
        )
        cursor = connection.cursor()

        print("Applying migration-safe schema updates...")
        execute_ignore(cursor, "ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;")
        execute_ignore(cursor, "ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP NULL;")
        cursor.execute("SHOW COLUMNS FROM inventory_items LIKE 'category'")
        category_column = cursor.fetchone()
        category_type = category_column[1].lower() if category_column else ""
        if "enum" in category_type:
            cursor.execute(
                """
                ALTER TABLE inventory_items
                MODIFY category ENUM(
                    'box', 'plastic', 'bottle',
                    'box_1kg', 'box_3kg', 'box_5kg', 'box_10kg',
                    'plastic_1kg', 'plastic_10kg',
                    'bottle_3kg', 'bottle_5kg',
                    'cooking_oil', 'finished_goods', 'defect'
                ) NOT NULL
                """
            )
        cursor.execute(
            """
            UPDATE inventory_items
            SET category = CASE
                WHEN category = 'box' AND LOWER(item_name) LIKE '%10kg%' THEN 'box_10kg'
                WHEN category = 'box' AND LOWER(item_name) LIKE '%5kg%' THEN 'box_5kg'
                WHEN category = 'box' AND LOWER(item_name) LIKE '%3kg%' THEN 'box_3kg'
                WHEN category = 'box' AND LOWER(item_name) LIKE '%large%' THEN 'box_10kg'
                WHEN category = 'box' THEN 'box_1kg'
                WHEN category = 'plastic' AND LOWER(item_name) LIKE '%10kg%' THEN 'plastic_10kg'
                WHEN category = 'plastic' THEN 'plastic_1kg'
                WHEN category = 'bottle' AND LOWER(item_name) LIKE '%5kg%' THEN 'bottle_5kg'
                WHEN category = 'bottle' THEN 'bottle_3kg'
                ELSE category
            END
            WHERE category IN ('box', 'plastic', 'bottle')
            """
        )
        if "enum" in category_type:
            cursor.execute(
                """
                ALTER TABLE inventory_items
                MODIFY category ENUM(
                    'box_1kg', 'box_3kg', 'box_5kg', 'box_10kg',
                    'plastic_1kg', 'plastic_10kg',
                    'bottle_3kg', 'bottle_5kg',
                    'cooking_oil', 'finished_goods', 'defect'
                ) NOT NULL
                """
            )
        cursor.execute("ALTER TABLE inventory_items MODIFY category VARCHAR(50) NOT NULL")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory_categories (
                category_key VARCHAR(50) PRIMARY KEY,
                category_label VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            INSERT INTO inventory_categories (category_key, category_label) VALUES
                ('plastic_1kg', '1kg Plastic Packs'),
                ('plastic_10kg', '10kg Plastic Packs'),
                ('bottle_3kg', '3kg Bottles'),
                ('bottle_5kg', '5kg Bottles'),
                ('box_1kg', '1kg Boxes'),
                ('box_3kg', '3kg Boxes'),
                ('box_5kg', '5kg Boxes'),
                ('box_10kg', '10kg Boxes'),
                ('cooking_oil', 'Cooking Oil'),
                ('finished_goods', 'Finished Goods'),
                ('defect', 'Defect Stock')
            ON DUPLICATE KEY UPDATE category_label = VALUES(category_label)
            """
        )
        cursor.execute(
            """
            INSERT INTO inventory_categories (category_key, category_label)
            SELECT DISTINCT category, REPLACE(category, '_', ' ')
            FROM inventory_items
            WHERE category IS NOT NULL
            ON DUPLICATE KEY UPDATE category_key = category_key
            """
        )
        execute_ignore(
            cursor,
            "ALTER TABLE client_transactions ADD COLUMN amount DECIMAL(10,2) NOT NULL DEFAULT 0.00;",
        )
        execute_ignore(
            cursor,
            "ALTER TABLE client_transactions ADD COLUMN payment_status ENUM('pending', 'completed', 'failed') DEFAULT 'completed';",
        )
        execute_ignore(cursor, "ALTER TABLE client_transactions ADD COLUMN notes TEXT;", duplicate_codes=(1060,))
        execute_ignore(
            cursor,
            "ALTER TABLE supplier_deliveries ADD COLUMN movement_type ENUM('inbound', 'outbound') NOT NULL DEFAULT 'inbound' AFTER delivery_id;",
        )
        execute_ignore(
            cursor,
            "ALTER TABLE supplier_deliveries ADD COLUMN transaction_id INT NULL UNIQUE AFTER item_id;",
        )
        execute_ignore(
            cursor,
            "ALTER TABLE client_transactions ADD COLUMN movement_type ENUM('inbound', 'outbound') NOT NULL DEFAULT 'outbound' AFTER transaction_id;",
        )
        execute_ignore(
            cursor,
            "ALTER TABLE client_transactions ADD COLUMN item_id INT NULL AFTER movement_type;",
        )
        execute_ignore(
            cursor,
            "ALTER TABLE client_transactions ADD COLUMN quantity DECIMAL(10,2) NOT NULL DEFAULT 0 AFTER item_id;",
        )
        execute_ignore(
            cursor,
            "ALTER TABLE client_transactions ADD COLUMN unit VARCHAR(20) NOT NULL DEFAULT 'Units' AFTER quantity;",
        )
        cursor.execute(
            """
            UPDATE client_transactions
            SET quantity = boxes_sold,
                unit = CASE WHEN unit = 'Units' THEN 'Boxes' ELSE unit END
            WHERE quantity = 0
            """
        )
        cursor.execute(
            """
            UPDATE client_transactions
            SET item_id = (
                SELECT item_id
                FROM inventory_items
                WHERE category = 'finished_goods'
                ORDER BY item_id
                LIMIT 1
            )
            WHERE item_id IS NULL
            """
        )
        try:
            cursor.execute(
                "ALTER TABLE client_transactions ADD CONSTRAINT fk_transactions_item FOREIGN KEY (item_id) REFERENCES inventory_items(item_id) ON DELETE SET NULL;"
            )
        except Error as exc:
            if exc.errno not in (1005, 1022, 1215, 1826):
                raise
        try:
            cursor.execute(
                "ALTER TABLE supplier_deliveries ADD CONSTRAINT fk_deliveries_transaction FOREIGN KEY (transaction_id) REFERENCES client_transactions(transaction_id) ON DELETE CASCADE;"
            )
        except Error as exc:
            if exc.errno not in (1005, 1022, 1215, 1826):
                raise
        execute_ignore(
            cursor,
            "ALTER TABLE usage_calculations ADD COLUMN box_size_kg DECIMAL(10,2) NOT NULL DEFAULT 1.00;",
        )
        execute_ignore(
            cursor,
            "ALTER TABLE usage_calculations ADD COLUMN units_per_box INT NOT NULL DEFAULT 20;",
        )
        execute_ignore(
            cursor,
            "ALTER TABLE usage_calculations ADD COLUMN oil_ratio DECIMAL(10,2) NOT NULL DEFAULT 1.00;",
        )
        execute_ignore(
            cursor,
            "ALTER TABLE usage_calculations ADD COLUMN plastic_ratio DECIMAL(10,2) NOT NULL DEFAULT 0.10;",
        )
        execute_ignore(
            cursor,
            "ALTER TABLE usage_calculations ADD COLUMN available_boxes DECIMAL(10,2) NOT NULL DEFAULT 0;",
        )
        execute_ignore(
            cursor,
            "ALTER TABLE usage_calculations ADD COLUMN remaining_boxes DECIMAL(10,2) NOT NULL DEFAULT 0;",
        )
        execute_ignore(
            cursor,
            "ALTER TABLE usage_calculations ADD COLUMN record_type VARCHAR(20) NOT NULL DEFAULT 'estimate';",
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                audit_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                action VARCHAR(50) NOT NULL,
                entity_type VARCHAR(50) NOT NULL,
                entity_id INT NULL,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
            )
            """
        )

        print("Removing duplicate notifications...")
        cursor.execute(
            """
            DELETE newer
            FROM notifications newer
            INNER JOIN notifications older
                ON newer.title = older.title
                AND newer.type = older.type
                AND newer.notification_id > older.notification_id
            """
        )

        print("Linking transactions to tracking records...")
        cursor.execute(
            """
            UPDATE supplier_deliveries d
            JOIN (
                SELECT t.transaction_id, MIN(d.delivery_id) AS delivery_id
                FROM client_transactions t
                JOIN supplier_deliveries d
                    ON d.transaction_id IS NULL
                    AND d.movement_type = t.movement_type
                    AND d.supplier_name = t.client_name
                    AND d.item_id = t.item_id
                    AND d.quantity = t.quantity
                    AND (
                        d.received_date = t.transaction_date
                        OR d.expected_date = t.transaction_date
                    )
                LEFT JOIN supplier_deliveries existing
                    ON existing.transaction_id = t.transaction_id
                WHERE existing.delivery_id IS NULL
                GROUP BY t.transaction_id
            ) matched ON matched.delivery_id = d.delivery_id
            SET d.transaction_id = matched.transaction_id
            WHERE d.transaction_id IS NULL
              AND NOT EXISTS (
                  SELECT 1
                  FROM supplier_deliveries existing
                  WHERE existing.transaction_id = matched.transaction_id
            )
            """
        )
        cursor.execute(
            """
            INSERT INTO supplier_deliveries
            (movement_type, supplier_name, item_id, transaction_id, quantity, expected_date, received_date, status)
            SELECT
                t.movement_type,
                t.client_name,
                t.item_id,
                t.transaction_id,
                t.quantity,
                t.transaction_date,
                t.transaction_date,
                'received'
            FROM client_transactions t
            WHERE t.item_id IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1
                  FROM supplier_deliveries d
                  WHERE d.transaction_id = t.transaction_id
              )
            """
        )
        cursor.execute(
            """
            UPDATE supplier_deliveries d
            JOIN client_transactions t ON d.transaction_id = t.transaction_id
            SET d.movement_type = t.movement_type,
                d.supplier_name = t.client_name,
                d.item_id = t.item_id,
                d.quantity = t.quantity,
                d.expected_date = t.transaction_date,
                d.received_date = t.transaction_date,
                d.status = 'received'
            """
        )

        index_statements = [
            "CREATE INDEX idx_inventory_category ON inventory_items (category);",
            "CREATE INDEX idx_inventory_stock ON inventory_items (quantity, minimum_stock);",
            "CREATE INDEX idx_deliveries_status_date ON supplier_deliveries (status, expected_date);",
            "CREATE INDEX idx_deliveries_item ON supplier_deliveries (item_id);",
            "CREATE INDEX idx_transactions_status_date ON client_transactions (payment_status, transaction_date);",
            "CREATE INDEX idx_transactions_movement_item ON client_transactions (movement_type, item_id);",
            "CREATE INDEX idx_notifications_read_type ON notifications (is_read, type);",
            "CREATE UNIQUE INDEX uq_notifications_title_type ON notifications (title, type);",
            "CREATE INDEX idx_audit_logs_user_date ON audit_logs (user_id, created_at);",
        ]
        for statement in index_statements:
            execute_ignore(cursor, statement, duplicate_codes=(1061,))

        connection.commit()

        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        if user_count == 0:
            print("Seeding default admin user...")
            from werkzeug.security import generate_password_hash

            cursor.execute(
                """
                INSERT INTO users (full_name, username, email, password_hash, role, is_active)
                VALUES (%s, %s, %s, %s, %s, TRUE)
                """,
                (
                    "Admin User",
                    "admin",
                    "admin@yuraishabright.com",
                    generate_password_hash("Admin123"),
                    "admin",
                ),
            )

        cursor.execute("SELECT COUNT(*) FROM inventory_items")
        inventory_count = cursor.fetchone()[0]
        if inventory_count == 0:
            print("Seeding sample IMS data...")
            cursor.execute(
                """
                INSERT INTO inventory_items (item_name, category, quantity, unit, minimum_stock) VALUES
                ('1kg Empty Boxes', 'box_1kg', 1250, 'Boxes', 200),
                ('3kg Empty Boxes', 'box_3kg', 900, 'Boxes', 100),
                ('5kg Empty Boxes', 'box_5kg', 800, 'Boxes', 100),
                ('10kg Empty Boxes', 'box_10kg', 650, 'Boxes', 80),
                ('Cooking Oil Stock', 'cooking_oil', 4500, 'Liters', 500),
                ('1kg Plastic Packs', 'plastic_1kg', 1250, 'Pcs', 500),
                ('10kg Plastic Packs', 'plastic_10kg', 450, 'Pcs', 100),
                ('3kg Bottles', 'bottle_3kg', 900, 'Pcs', 250),
                ('5kg Bottles', 'bottle_5kg', 700, 'Pcs', 200),
                ('Finished 1kg Box', 'finished_goods', 120, 'Boxes', 20)
                """
            )
            cursor.execute(
                """
                INSERT INTO supplier_deliveries (movement_type, supplier_name, item_id, quantity, expected_date, status) VALUES
                ('inbound', 'Apex Logistics', 6, 500, CURDATE(), 'received'),
                ('inbound', 'Bright Supply Trading', 5, 1000, DATE_ADD(CURDATE(), INTERVAL 2 DAY), 'pending'),
                ('inbound', 'Metro Packaging', 8, 200, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 'pending')
                """
            )
            cursor.execute(
                """
                INSERT INTO client_transactions
                (movement_type, item_id, quantity, unit, client_name, boxes_sold, amount, payment_status, transaction_date, notes) VALUES
                ('outbound', 10, 50, 'Boxes', 'Kedai Runcit Seri Maju', 50, 1420.00, 'completed', DATE_SUB(CURDATE(), INTERVAL 1 DAY), 'Monthly oil box delivery'),
                ('outbound', 10, 30, 'Boxes', 'Pasar Mini Indah', 30, 845.00, 'pending', DATE_SUB(CURDATE(), INTERVAL 2 DAY), 'Awaiting payment'),
                ('outbound', 10, 40, 'Boxes', 'Restoran Cahaya', 40, 2210.00, 'completed', DATE_SUB(CURDATE(), INTERVAL 3 DAY), 'Bulk order')
                """
            )
            cursor.execute(
                """
                INSERT INTO notifications (title, message, type, is_read) VALUES
                ('Low Stock: 10kg Plastic Packs', '10kg Plastic Packs has dropped below minimum stock level.', 'low_stock', FALSE),
                ('Delayed Delivery: TRK-3', 'Metro Packaging delivery is overdue and needs follow-up.', 'delayed_delivery', FALSE),
                ('System Ready', 'Inventory Management System modules are available.', 'general', TRUE)
                """
            )

        default_category_rows = [
            ("1kg Empty Boxes", "box_1kg", "Boxes", 200),
            ("3kg Empty Boxes", "box_3kg", "Boxes", 100),
            ("5kg Empty Boxes", "box_5kg", "Boxes", 100),
            ("10kg Empty Boxes", "box_10kg", "Boxes", 80),
            ("1kg Plastic Packs", "plastic_1kg", "Pcs", 500),
            ("10kg Plastic Packs", "plastic_10kg", "Pcs", 100),
            ("3kg Bottles", "bottle_3kg", "Pcs", 250),
            ("5kg Bottles", "bottle_5kg", "Pcs", 200),
        ]
        for item_name, category, unit, minimum_stock in default_category_rows:
            cursor.execute(
                """
                INSERT INTO inventory_items (item_name, category, quantity, unit, minimum_stock)
                SELECT %s, %s, 0, %s, %s
                WHERE NOT EXISTS (
                    SELECT 1 FROM inventory_items WHERE category = %s
                )
                """,
                (item_name, category, unit, minimum_stock, category),
            )

        connection.commit()
        print("Migration and seed completed.")
        print("Default admin login, if seeded: admin / Admin123")

    except Error as exc:
        print(f"Database migration failed: {exc}")
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    main()
