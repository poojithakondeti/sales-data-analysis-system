
import mysql.connector
import getpass

password = getpass.getpass("Enter Aiven password: ")

connection = mysql.connector.connect(
    host="mysql-1d207c3f-sales-analytics-dashboard.i.aivencloud.com",
    port=21853,
    user="avnadmin",
    password=password,
    database="defaultdb",
    ssl_disabled=False
)

cursor = connection.cursor()

products = [
    ("Laptop", "Electronics"),
    ("Headphones", "Electronics"),
    ("Keyboard", "Accessories"),
    ("Mouse", "Accessories"),
    ("Monitor", "Electronics"),
    ("Smartphone", "Electronics"),
    ("Tablet", "Electronics"),
    ("Webcam", "Accessories"),
    ("Printer", "Electronics"),
    ("USB Drive", "Accessories"),
    ("Power Bank", "Accessories"),
    ("Speaker", "Electronics"),
    ("Smart Watch", "Wearables"),
    ("Router", "Networking"),
    ("External Hard Drive", "Storage")
]

try:
    cursor.executemany(
        "INSERT INTO products (product_name, category) VALUES (%s, %s)",
        products
    )
    connection.commit()
    print(f"Successfully inserted {cursor.rowcount} products.")

    cursor.execute(
        "SELECT product_id, product_name, category FROM products ORDER BY product_id"
    )
    for product in cursor.fetchall():
        print(product)

finally:
    cursor.close()
    connection.close()

