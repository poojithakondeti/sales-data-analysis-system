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

try:
    # Enter Sale IDs
    sale_ids = input("Enter Sale IDs separated by commas: ")
    sale_ids = [int(x.strip()) for x in sale_ids.split(",")]

    placeholders = ",".join(["%s"] * len(sale_ids))

    # Display sales before deletion
    cursor.execute(
        f"SELECT sale_id, product_id, sale_date, quantity, unit_price, region FROM sales WHERE sale_id IN ({placeholders})",
        tuple(sale_ids)
    )

    sales = cursor.fetchall()

    if sales:
        print("\nSales selected for deletion:")
        for sale in sales:
            print(sale)

        confirm = input("\nDelete these sales? Type YES: ")

        if confirm == "YES":
            cursor.execute(
                f"DELETE FROM sales WHERE sale_id IN ({placeholders})",
                tuple(sale_ids)
            )
            connection.commit()
            print(cursor.rowcount, "sales deleted successfully.")
        else:
            print("Deletion cancelled.")
    else:
        print("No matching sales found.")

finally:
    cursor.close()
    connection.close()