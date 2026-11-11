
import mysql.connector
import getpass
import random
from datetime import date, timedelta

password = getpass.getpass("Enter Aiven password: ")

connection = mysql.connector.connect(
    host="mysql-1d207c3f-sales-analytics-dashboard.i.aivencloud.com",
    port=21853,
    user="avnadmin",
    password=password,
    database="defaultdb",
    ssl_disabled=False,
    connection_timeout=15
)

cursor = connection.cursor()

try:
    # Get product IDs that actually exist in Aiven
    cursor.execute("SELECT product_id FROM products ORDER BY product_id")
    product_ids = [row[0] for row in cursor.fetchall()]

    if not product_ids:
        print("No products found. Insert products first.")
    else:
        random.seed(42)

        regions = ["North", "South", "East", "West", "Central"]
        start_date = date(2026, 1, 1)

        sales = []

        # Generate 120 sales records
        for i in range(120):
            product_id = random.choice(product_ids)
            sale_date = start_date + timedelta(
                days=random.randint(0, 299)
            )
            quantity = random.randint(1, 10)
            unit_price = random.choice([
                199.00, 299.00, 499.00, 799.00,
                999.00, 1499.00, 2499.00,
                4999.00, 9999.00, 24999.00
            ])
            region = random.choice(regions)

            sales.append((
                product_id,
                sale_date,
                quantity,
                unit_price,
                region
            ))

        cursor.executemany(
            """
            INSERT INTO sales
                (product_id, sale_date, quantity, unit_price, region)
            VALUES (%s, %s, %s, %s, %s)
            """,
            sales
        )

        connection.commit()

        print(f"Successfully inserted {cursor.rowcount} sales records.")

        cursor.execute("SELECT COUNT(*) FROM sales")
        print("Total sales records in cloud database:", cursor.fetchone()[0])

        cursor.execute("""
            SELECT sale_id, product_id, sale_date,
                   quantity, unit_price, region
            FROM sales
            ORDER BY sale_id DESC
            LIMIT 5
        """)

        print("\nLatest 5 sales records:")
        for row in cursor.fetchall():
            print(row)

finally:
    cursor.close()
    connection.close()
