import os
import sys
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

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
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Alter table
            try:
                print("Altering client_transactions table...")
                cursor.execute("ALTER TABLE client_transactions ADD COLUMN amount DECIMAL(10,2) NOT NULL DEFAULT 0.00;")
                cursor.execute("ALTER TABLE client_transactions ADD COLUMN payment_status ENUM('pending', 'completed', 'failed') DEFAULT 'completed';")
                connection.commit()
                print("Table altered successfully.")
            except Error as e:
                # Error 1060 is Duplicate column name
                if e.errno == 1060:
                    print("Columns already exist.")
                else:
                    print(f"Error altering table: {e}")
                    
            # Check if there is data in inventory_items
            cursor.execute("SELECT COUNT(*) FROM inventory_items")
            count = cursor.fetchone()[0]
            
            if count == 0:
                print("Seeding dummy data...")
                
                # Seed inventory_items
                cursor.execute("""
                    INSERT INTO inventory_items (item_name, category, quantity, unit, minimum_stock) VALUES
                    ('Industrial Valves (V-200)', 'box', 1250, 'Units', 200),
                    ('Steel Beam (SB-12M)', 'box', 800, 'Units', 100),
                    ('Lubricant Oil (LUB-50L)', 'cooking_oil', 4500, 'Liters', 500),
                    ('Copper Wiring (CW-100M)', 'box', 12000, 'Meters', 2000),
                    ('Carbon Steel Pipe (CSP-092)', 'box', 45, 'Units', 50),
                    ('Raw Plastic Pellets', 'plastic', 1250, 'Kg', 500)
                """)
                
                # Seed supplier_deliveries
                cursor.execute("""
                    INSERT INTO supplier_deliveries (supplier_name, item_id, quantity, expected_date, status) VALUES
                    ('Global Metals Inc.', 5, 200, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 'pending'),
                    ('Apex Logistics', 2, 500, CURDATE(), 'received'),
                    ('Chemical Corp', 3, 1000, DATE_ADD(CURDATE(), INTERVAL 2 DAY), 'pending')
                """)
                
                # Seed client_transactions
                cursor.execute("""
                    INSERT INTO client_transactions (client_name, boxes_sold, amount, payment_status, transaction_date) VALUES
                    ('MegaCorp Manufacturing', 50, 14200.00, 'completed', DATE_SUB(CURDATE(), INTERVAL 1 DAY)),
                    ('Steelworks Global', 30, 8450.00, 'pending', DATE_SUB(CURDATE(), INTERVAL 2 DAY)),
                    ('Apex Logistics', 100, 22100.00, 'completed', DATE_SUB(CURDATE(), INTERVAL 3 DAY)),
                    ('Brighton Auto', 15, 3200.00, 'pending', DATE_SUB(CURDATE(), INTERVAL 4 DAY)),
                    ('MegaCorp Manufacturing', 75, 18750.00, 'completed', DATE_SUB(CURDATE(), INTERVAL 5 DAY))
                """)
                
                # Seed notifications
                cursor.execute("""
                    INSERT INTO notifications (title, message, type, is_read) VALUES
                    ('Critical Stock Level', 'Carbon Steel Pipe (SKU: CSP-092) has dropped below minimum threshold.', 'low_stock', 0),
                    ('Delivery Arrived', 'Shipment #8821 from Global Metals Inc. is ready for inspection.', 'delayed_delivery', 0),
                    ('Quality Check Passed', 'Batch QA-442 components cleared for assembly line use.', 'general', 1)
                """)
                
                connection.commit()
                print("Dummy data seeded successfully.")
            else:
                print("Database already contains data. Skipping seed.")

    except Error as e:
        print(f"Error connecting to MySQL: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    main()
