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
                WHERE category = 'box'
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
        execute_ignore(
            cursor,
            "ALTER TABLE usage_calculations ADD COLUMN box_size_kg DECIMAL(10,2) NOT NULL DEFAULT 1.00;",
        )
        execute_ignore(
            cursor,
            "ALTER TABLE usage_calculations ADD COLUMN oil_ratio DECIMAL(10,2) NOT NULL DEFAULT 1.00;",
        )
        execute_ignore(
            cursor,
            "ALTER TABLE usage_calculations ADD COLUMN plastic_ratio DECIMAL(10,2) NOT NULL DEFAULT 0.10;",
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
                ('Small Cooking Oil Box', 'box', 1250, 'Boxes', 200),
                ('Large Cooking Oil Box', 'box', 800, 'Boxes', 100),
                ('Cooking Oil Stock', 'cooking_oil', 4500, 'Liters', 500),
                ('Bottle Plastic Pellets', 'plastic', 1250, 'Kg', 500),
                ('Packaging Plastic Roll', 'plastic', 45, 'Kg', 50)
                """
            )
            cursor.execute(
                """
                INSERT INTO supplier_deliveries (movement_type, supplier_name, item_id, quantity, expected_date, status) VALUES
                ('inbound', 'Apex Logistics', 4, 500, CURDATE(), 'received'),
                ('inbound', 'Bright Supply Trading', 3, 1000, DATE_ADD(CURDATE(), INTERVAL 2 DAY), 'pending'),
                ('inbound', 'Metro Packaging', 5, 200, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 'pending')
                """
            )
            cursor.execute(
                """
                INSERT INTO client_transactions
                (movement_type, item_id, quantity, unit, client_name, boxes_sold, amount, payment_status, transaction_date, notes) VALUES
                ('outbound', 1, 50, 'Boxes', 'Kedai Runcit Seri Maju', 50, 1420.00, 'completed', DATE_SUB(CURDATE(), INTERVAL 1 DAY), 'Monthly oil box delivery'),
                ('outbound', 3, 30, 'Liters', 'Pasar Mini Indah', 30, 845.00, 'pending', DATE_SUB(CURDATE(), INTERVAL 2 DAY), 'Awaiting payment'),
                ('outbound', 3, 100, 'Liters', 'Restoran Cahaya', 100, 2210.00, 'completed', DATE_SUB(CURDATE(), INTERVAL 3 DAY), 'Bulk order')
                """
            )
            cursor.execute(
                """
                INSERT INTO notifications (title, message, type, is_read) VALUES
                ('Low Stock: Packaging Plastic Roll', 'Packaging Plastic Roll has dropped below minimum stock level.', 'low_stock', FALSE),
                ('Delayed Delivery: TRK-3', 'Metro Packaging delivery is overdue and needs follow-up.', 'delayed_delivery', FALSE),
                ('System Ready', 'Inventory Management System modules are available.', 'general', TRUE)
                """
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
