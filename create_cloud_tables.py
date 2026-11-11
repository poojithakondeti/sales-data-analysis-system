
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

tables = [
    """
    CREATE TABLE IF NOT EXISTS users (
        user_id INT AUTO_INCREMENT PRIMARY KEY,
        full_name VARCHAR(100) NOT NULL,
        username VARCHAR(100) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS products (
        product_id INT AUTO_INCREMENT PRIMARY KEY,
        product_name VARCHAR(150) NOT NULL,
        category VARCHAR(100) NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS sales (
        sale_id INT AUTO_INCREMENT PRIMARY KEY,
        product_id INT NOT NULL,
        sale_date DATE NOT NULL,
        quantity INT NOT NULL,
        unit_price DECIMAL(12,2) NOT NULL,
        region VARCHAR(100) NOT NULL,
        CONSTRAINT fk_sales_products
            FOREIGN KEY (product_id) REFERENCES products(product_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS imported_files (
        file_id INT AUTO_INCREMENT PRIMARY KEY,
        file_hash CHAR(64) NOT NULL UNIQUE,
        file_name VARCHAR(255) NOT NULL
    )
    """
]

try:
    for table_sql in tables:
        cursor.execute(table_sql)

    connection.commit()
    cursor.execute("SHOW TABLES")

    print("\nTables in Aiven defaultdb:")
    for row in cursor.fetchall():
        print("-", row[0])

    print("\nCloud table setup completed.")

finally:
    cursor.close()
    connection.close()
