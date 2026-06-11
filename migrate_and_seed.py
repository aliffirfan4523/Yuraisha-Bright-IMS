import os
import mysql.connector
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

def main():
    load_dotenv()
    try:
        connection = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database=os.getenv("MYSQL_DATABASE", "yuraisha_inventory")
        )
        cursor = connection.cursor()

        print("Dropping old tables...")
        tables_to_drop = [
            "audit_logs",
            "client_transactions",
            "supplier_deliveries",
            "usage_calculations",
            "reports",
            "notifications",
            "inventory_categories",
            "inventory_items",
            "users",
            "tbl_delivery_log",
            "tbl_client_transaction",
            "tbl_material",
            "tbl_supplier",
            "tbl_user"
        ]
        
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        for table in tables_to_drop:
            cursor.execute(f"DROP TABLE IF EXISTS {table};")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

        print("Applying new schema...")
        cursor.execute("""
            CREATE TABLE tbl_user (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                employee_name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL,
                user_role VARCHAR(20) NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE tbl_material (
                material_id INT AUTO_INCREMENT PRIMARY KEY,
                material_name VARCHAR(50) NOT NULL,
                current_quantity DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                low_stock_threshold DECIMAL(10,0) NOT NULL DEFAULT 0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE tbl_supplier (
                supplier_id INT AUTO_INCREMENT PRIMARY KEY,
                supplier_name VARCHAR(100) NOT NULL,
                contact_number VARCHAR(20),
                email VARCHAR(100)
            )
        """)

        cursor.execute("""
            CREATE TABLE tbl_delivery_log (
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
            )
        """)

        cursor.execute("""
            CREATE TABLE tbl_client_transaction (
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
            )
        """)

        print("Seeding data...")
        # Users
        cursor.execute(
            """
            INSERT INTO tbl_user (username, password, employee_name, email, user_role)
            VALUES (%s, %s, %s, %s, %s)
            """,
            ("admin", generate_password_hash("Admin123"), "Admin User", "admin@yuraishabright.com", "admin")
        )
        
        # Materials
        materials = [
            ("Cooking Oil", 4500.00, 500),
            ("17kg Empty Boxes", 1250.00, 200),
            ("1kg Plastic Packs", 1250.00, 500)
        ]
        for name, qty, low in materials:
            cursor.execute(
                "INSERT INTO tbl_material (material_name, current_quantity, low_stock_threshold) VALUES (%s, %s, %s)",
                (name, qty, low)
            )

        # Suppliers
        suppliers = [
            ("Apex Logistics", "123-456-7890", "contact@apexlogistics.com"),
            ("Bright Supply Trading", "098-765-4321", "sales@brightsupply.com"),
            ("Metro Packaging", "555-123-4567", "info@metropackaging.com")
        ]
        for name, phone, email in suppliers:
            cursor.execute(
                "INSERT INTO tbl_supplier (supplier_name, contact_number, email) VALUES (%s, %s, %s)",
                (name, phone, email)
            )

        connection.commit()
        print("Migration and seeding complete.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    main()
