import os

import hashlib

from datetime import date

from io import BytesIO, StringIO

import pandas as pd

import mysql.connector

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from flask import (

    Flask, render_template, request, redirect,

    url_for, send_file, session, flash

)

from werkzeug.security import generate_password_hash, check_password_hash

from config import DB_CONFIG

from dotenv import load_dotenv

from reportlab.lib import colors

from reportlab.lib.pagesizes import A4, landscape

from reportlab.platypus import (

    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

)

from reportlab.lib.styles import getSampleStyleSheet

load_dotenv()

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY")

if not app.secret_key:

    raise RuntimeError(

        "SECRET_KEY is missing. Add it to your .env file."

    )

app.config["SESSION_COOKIE_HTTPONLY"] = True

app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

os.makedirs("static", exist_ok=True)

os.makedirs("static/charts", exist_ok=True)

os.makedirs("uploads", exist_ok=True)

def get_connection():

    return mysql.connector.connect(**DB_CONFIG)

def close_db(cursor=None, connection=None):

    if cursor is not None:

        cursor.close()

    if connection is not None and connection.is_connected():

        connection.close()

@app.before_request

def require_login():

    public_endpoints = {"login", "register", "static"}

    if request.endpoint is None:

        return None

    if request.endpoint not in public_endpoints:

        if "user_id" not in session:

            return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])

def register():

    error = ""

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()

        username = request.form.get("username", "").strip()

        password = request.form.get("password", "")

        confirm_password = request.form.get("confirm_password", "")

        if not full_name or not username or not password:

            error = "Please fill in all required fields."

        elif len(username) < 3:

            error = "Username must contain at least 3 characters."

        elif len(password) < 8:

            error = "Password must contain at least 8 characters."

        elif password != confirm_password:

            error = "Passwords do not match."

        else:

            connection = None

            cursor = None

            try:

                connection = get_connection()

                cursor = connection.cursor()

                password_hash = generate_password_hash(password)

                cursor.execute("""

                    INSERT INTO users (full_name, username, password_hash)

                    VALUES (%s, %s, %s)

                """, (full_name, username, password_hash))

                connection.commit()

                flash("Registration successful. Please log in.", "success")

                return redirect(url_for("login"))

            except mysql.connector.IntegrityError:

                if connection is not None:

                    connection.rollback()

                error = "That username is already registered."

            except mysql.connector.Error:

                if connection is not None:

                    connection.rollback()

                app.logger.exception("Registration failed.")

                error = "Registration failed. Please try again."

            finally:

                close_db(cursor, connection)

    return render_template("register.html", error=error)

@app.route("/login", methods=["GET", "POST"])

def login():

    error = ""

    if request.method == "POST":

        username = request.form.get("username", "").strip()

        password = request.form.get("password", "")

        connection = None

        cursor = None

        try:

            connection = get_connection()

            cursor = connection.cursor(dictionary=True)

            cursor.execute("""

                SELECT user_id, full_name, username, password_hash

                FROM users

                WHERE username = %s

            """, (username,))

            user = cursor.fetchone()

            if user and check_password_hash(user["password_hash"], password):

                session.clear()

                session["user_id"] = user["user_id"]

                session["full_name"] = user["full_name"]

                session["username"] = user["username"]

                return redirect(url_for("dashboard"))

            error = "Incorrect username or password."

        except mysql.connector.Error:

            app.logger.exception("Login failed.")

            error = "Unable to log in right now. Please try again."

        finally:

            close_db(cursor, connection)

    return render_template("login.html", error=error)

@app.route("/logout", methods=["POST"])

def logout():

    session.clear()

    flash("You have logged out successfully.", "success")

    return redirect(url_for("login"))

def create_chart(filename, title, x_values, y_values,

                 x_label, y_label, chart_type="bar"):

    path = os.path.join("static", filename)

    plt.figure(figsize=(8, 4))

    if chart_type == "line":

        plt.plot(x_values, y_values, marker="o")

    else:

        plt.bar(x_values, y_values)

    plt.title(title)

    plt.xlabel(x_label)

    plt.ylabel(y_label)

    plt.xticks(rotation=30, ha="right")

    plt.tight_layout()

    plt.savefig(path)

    plt.close()

    return filename

def create_analytics_chart(filename, title, x_values, y_values,

                           x_label, y_label, chart_type="bar"):

    path = os.path.join("static", "charts", filename)

    plt.figure(figsize=(8, 4))

    if chart_type == "line":

        plt.plot(x_values, y_values, marker="o")

    else:

        plt.bar(x_values, y_values)

    plt.title(title)

    plt.xlabel(x_label)

    plt.ylabel(y_label)

    plt.xticks(rotation=30, ha="right")

    plt.tight_layout()

    plt.savefig(path)

    plt.close()

    return "charts/" + filename

def create_pie_chart(filename, title, labels, values):

    """Create a pie chart showing each product's share of total revenue."""

    path = os.path.join("static", filename)

    plt.figure(figsize=(5, 4))

    if not labels or sum(values) <= 0:

        plt.text(0.5, 0.5, "No sales data available", ha="center", va="center")

        plt.axis("off")

    else:

        plt.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)

        plt.axis("equal")

    plt.title(title)

    plt.tight_layout()

    plt.savefig(path, dpi=100)

    plt.close()

    return filename

@app.route("/")
def dashboard():
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        # Summary Cards
        cursor.execute("""
            SELECT COUNT(*) AS total_sales,
                   COALESCE(SUM(quantity), 0) AS total_quantity,
                   COALESCE(SUM(quantity * unit_price), 0) AS total_revenue
            FROM sales
        """)
        totals = cursor.fetchone()

        cursor.execute("""
            SELECT COUNT(*) AS total_products
            FROM products
        """)
        total_products = cursor.fetchone()["total_products"]

        # Top 5 Products by Revenue
        cursor.execute("""
            SELECT p.product_name,
                   COALESCE(SUM(s.quantity * s.unit_price), 0) AS revenue
            FROM products p
            LEFT JOIN sales s ON p.product_id = s.product_id
            GROUP BY p.product_id, p.product_name
            ORDER BY revenue DESC
            LIMIT 5
        """)
        top_rows = cursor.fetchall()

        # Revenue Distribution by Product
        cursor.execute("""
            SELECT p.product_name,
                   COALESCE(SUM(s.quantity * s.unit_price), 0) AS revenue
            FROM products p
            LEFT JOIN sales s ON p.product_id = s.product_id
            GROUP BY p.product_id, p.product_name
            HAVING COALESCE(SUM(s.quantity * s.unit_price), 0) > 0
            ORDER BY revenue DESC
        """)
        pie_rows = cursor.fetchall()

        # Keep the top 5 products and combine the rest into Others
        top_5 = pie_rows[:5]
        other_rows = pie_rows[5:]

        labels = [r["product_name"] for r in top_5]
        values = [float(r["revenue"]) for r in top_5]

        others_revenue = sum(
            float(r["revenue"]) for r in other_rows
        )

        if others_revenue > 0:
            labels.append("Others")
            values.append(others_revenue)

        pie_chart = create_pie_chart(
            "product_revenue_pie.png",
            "Revenue Distribution by Product",
            labels,
            values
        )

        # Yearly Revenue Analysis
        cursor.execute("""
            SELECT YEAR(sale_date) AS year,
                   SUM(quantity * unit_price) AS revenue
            FROM sales
            WHERE sale_date IS NOT NULL
            GROUP BY YEAR(sale_date)
            ORDER BY year
        """)
        yearly_rows = cursor.fetchall()

        # Revenue by Region
        cursor.execute("""
            SELECT region,
                   SUM(quantity * unit_price) AS revenue
            FROM sales
            GROUP BY region
            ORDER BY revenue DESC
        """)
        region_rows = cursor.fetchall()

        # Top Products Chart
        top_chart = create_chart(
            "top_products.png",
            "Top Products by Revenue",
            [r["product_name"] for r in top_rows],
            [float(r["revenue"]) for r in top_rows],
            "Product",
            "Revenue"
        )

        # Yearly Revenue Chart
        yearly_chart = create_chart(
            "yearly_revenue.png",
            "Yearly Revenue Analysis",
            [str(r["year"]) for r in yearly_rows],
            [float(r["revenue"]) for r in yearly_rows],
            "Year",
            "Revenue",
            "bar"
        )

        # Region Revenue Chart
        region_chart = create_chart(
            "region_sales.png",
            "Revenue by Region",
            [r["region"] for r in region_rows],
            [float(r["revenue"]) for r in region_rows],
            "Region",
            "Revenue"
        )

        return render_template(
            "dashboard.html",
            total_sales=totals["total_sales"],
            total_quantity=totals["total_quantity"],
            total_revenue=float(totals["total_revenue"]),
            total_products=total_products,
            top_chart=top_chart,
            yearly_chart=yearly_chart,
            region_chart=region_chart,
            pie_chart=pie_chart
        )

    finally:
        close_db(cursor, connection)

@app.route("/products", methods=["GET", "POST"])

def products():

    connection = None

    cursor = None

    message = ""

    message_type = ""

    try:

        connection = get_connection()

        cursor = connection.cursor(dictionary=True)

        if request.method == "POST":

            name = request.form.get("product_name", "").strip()

            category = request.form.get("category", "").strip()

            if not name or not category:

                message = "Enter both product name and category."

                message_type = "danger"

            else:

                cursor.execute("""

                    INSERT INTO products (product_name, category)

                    VALUES (%s, %s)

                """, (name, category))

                connection.commit()

                flash("Product added successfully.", "success")

                return redirect(url_for("products"))

        cursor.execute("""

            SELECT

                p.product_id,

                p.product_name,

                p.category,

                COALESCE(SUM(s.quantity), 0) AS total_quantity,

                COALESCE(SUM(s.quantity * s.unit_price), 0) AS total_revenue

            FROM products p

            LEFT JOIN sales s ON p.product_id = s.product_id

            GROUP BY

                p.product_id,

                p.product_name,

                p.category

            ORDER BY p.product_id ASC

        """)

        product_list = cursor.fetchall()

        return render_template(

            "products.html",

            products=product_list,

            message=message,

            message_type=message_type

        )

    finally:

        close_db(cursor, connection)

@app.route("/products/edit/<int:product_id>", methods=["GET", "POST"])

def edit_product(product_id):

    connection = None

    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor(dictionary=True)

        cursor.execute(

            "SELECT * FROM products WHERE product_id = %s",

            (product_id,)

        )

        product = cursor.fetchone()

        if product is None:

            flash("Product not found.", "danger")

            return redirect(url_for("products"))

        if request.method == "POST":

            name = request.form.get("product_name", "").strip()

            category = request.form.get("category", "").strip()

            if not name or not category:

                flash("Enter both product name and category.", "danger")

            else:

                cursor.execute("""

                    UPDATE products

                    SET product_name = %s, category = %s

                    WHERE product_id = %s

                """, (name, category, product_id))

                connection.commit()

                flash("Product updated successfully.", "success")

                return redirect(url_for("products"))

        return render_template("edit_product.html", product=product)

    finally:

        close_db(cursor, connection)

@app.route("/products/delete/<int:product_id>", methods=["POST"])

def delete_product(product_id):

    connection = None

    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(

            "SELECT COUNT(*) FROM sales WHERE product_id = %s",

            (product_id,)

        )

        if cursor.fetchone()[0] > 0:

            flash("This product has sales records and cannot be deleted.", "danger")

            return redirect(url_for("products"))

        cursor.execute(

            "DELETE FROM products WHERE product_id = %s",

            (product_id,)

        )

        connection.commit()

        flash("Product deleted successfully.", "success")

    finally:

        close_db(cursor, connection)

    return redirect(url_for("products"))

@app.route("/sales", methods=["GET", "POST"])

def sales():

    connection = None

    cursor = None

    message = ""

    message_type = "danger"

    try:

        connection = get_connection()

        cursor = connection.cursor(dictionary=True)

        if request.method == "POST":

            try:

                product_id = int(request.form.get("product_id", ""))

                sale_date = request.form.get("sale_date", "").strip()

                quantity = int(request.form.get("quantity", ""))

                unit_price = float(request.form.get("unit_price", ""))

                region = request.form.get("region", "").strip()

                if quantity <= 0 or unit_price < 0:

                    raise ValueError

                if not sale_date or not region:

                    raise ValueError

                cursor.execute(

                    "SELECT product_id FROM products WHERE product_id = %s",

                    (product_id,)

                )

                if cursor.fetchone() is None:

                    message = "Select an existing product."

                else:

                    cursor.execute("""

                        INSERT INTO sales

                            (product_id, sale_date, quantity, unit_price, region)

                        VALUES (%s, %s, %s, %s, %s)

                    """, (product_id, sale_date, quantity, unit_price, region))

                    connection.commit()

                    return redirect(url_for("sales"))

            except (ValueError, TypeError):

                message = "Enter valid sales details."

        cursor.execute("""

            SELECT s.sale_id, s.product_id, p.product_name,

                   s.sale_date, s.quantity, s.unit_price, s.region,

                   (s.quantity * s.unit_price) AS revenue

            FROM sales s

            JOIN products p ON s.product_id = p.product_id

            ORDER BY s.sale_date ASC, s.sale_id ASC

        """)

        sales_list = cursor.fetchall()

        cursor.execute("""

            SELECT product_id, product_name

            FROM products

            ORDER BY product_name

        """)

        product_list = cursor.fetchall()

        return render_template(

            "sales.html",

            sales=sales_list,

            products=product_list,

            message=message,

            message_type=message_type

        )

    finally:

        close_db(cursor, connection)

@app.route("/sales/edit/<int:sale_id>", methods=["GET", "POST"])

def edit_sale(sale_id):

    connection = None

    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT * FROM sales WHERE sale_id = %s", (sale_id,))

        sale = cursor.fetchone()

        if sale is None:

            flash("Sales record not found.", "danger")

            return redirect(url_for("sales"))

        cursor.execute("""

            SELECT product_id, product_name

            FROM products ORDER BY product_name

        """)

        product_list = cursor.fetchall()

        if request.method == "POST":

            try:

                product_id = int(request.form.get("product_id", ""))

                sale_date = request.form.get("sale_date", "").strip()

                quantity = int(request.form.get("quantity", ""))

                unit_price = float(request.form.get("unit_price", ""))

                region = request.form.get("region", "").strip()

                if quantity <= 0 or unit_price < 0 or not sale_date or not region:

                    raise ValueError

                cursor.execute(

                    "SELECT product_id FROM products WHERE product_id = %s",

                    (product_id,)

                )

                if cursor.fetchone() is None:

                    flash("Select an existing product.", "danger")

                else:

                    cursor.execute("""

                        UPDATE sales

                        SET product_id=%s, sale_date=%s, quantity=%s,

                            unit_price=%s, region=%s

                        WHERE sale_id=%s

                    """, (

                        product_id, sale_date, quantity,

                        unit_price, region, sale_id

                    ))

                    connection.commit()

                    flash("Sales record updated.", "success")

                    return redirect(url_for("sales"))

            except (ValueError, TypeError):

                flash("Enter valid sales details.", "danger")

        return render_template(

            "edit_sale.html", sale=sale, products=product_list

        )

    finally:

        close_db(cursor, connection)

@app.route("/sales/delete/<int:sale_id>", methods=["POST"])

def delete_sale(sale_id):

    connection = None

    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute("DELETE FROM sales WHERE sale_id = %s", (sale_id,))

        connection.commit()

        flash("Sales record deleted.", "success")

    finally:

        close_db(cursor, connection)

    return redirect(url_for("sales"))

@app.route("/export/<file_format>")

def export_sales(file_format):

    if file_format not in {"csv", "excel", "pdf"}:

        return "Unsupported export format", 400

    connection = None

    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor(dictionary=True)

        cursor.execute("""

            SELECT s.sale_id, s.product_id, p.product_name,

                   s.sale_date, s.quantity, s.unit_price, s.region,

                   (s.quantity * s.unit_price) AS revenue

            FROM sales s

            JOIN products p ON s.product_id = p.product_id

            ORDER BY s.sale_date DESC, s.sale_id DESC

        """)

        rows = cursor.fetchall()

    finally:

        close_db(cursor, connection)

    columns = [

        "sale_id", "product_id", "product_name", "sale_date",

        "quantity", "unit_price", "region", "revenue"

    ]

    df = pd.DataFrame(rows, columns=columns)

    output = BytesIO()

    if file_format == "csv":

        output.write(df.to_csv(index=False).encode("utf-8-sig"))

        mimetype = "text/csv"

        filename = "sales_records.csv"

    elif file_format == "excel":

        with pd.ExcelWriter(output, engine="openpyxl") as writer:

            df.to_excel(writer, index=False, sheet_name="Sales")

        mimetype = (

            "application/vnd.openxmlformats-officedocument."

            "spreadsheetml.sheet"

        )

        filename = "sales_records.xlsx"

    else:

        document_buffer = BytesIO()

        document = SimpleDocTemplate(

            document_buffer, pagesize=landscape(A4)

        )

        styles = getSampleStyleSheet()

        elements = [

            Paragraph("Sales Records Report", styles["Title"]),

            Spacer(1, 12)

        ]

        table_data = [columns]

        for row in rows:

            table_data.append([

                str(row.get(col, "")) for col in columns

            ])

        table = Table(table_data, repeatRows=1)

        table.setStyle(TableStyle([

            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),

            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

            ("FONTSIZE", (0, 0), (-1, -1), 7),

            ("VALIGN", (0, 0), (-1, -1), "MIDDLE")

        ]))

        elements.append(table)

        document.build(elements)

        output = document_buffer

        mimetype = "application/pdf"

        filename = "sales_records.pdf"

    output.seek(0)

    return send_file(

        output,

        mimetype=mimetype,

        as_attachment=True,

        download_name=filename

    )

@app.route("/upload", methods=["GET", "POST"])

def upload():

    message = ""

    message_type = "danger"

    errors = []

    preview = []

    if request.method == "POST":

        file = request.files.get("file")

        if not file or not file.filename:

            message = "Please select a CSV file."

            return render_template(

                "upload.html", message=message,

                message_type=message_type, errors=errors, preview=preview

            )

        if not file.filename.lower().endswith(".csv"):

            message = "Only CSV files are allowed."

            return render_template(

                "upload.html", message=message,

                message_type=message_type, errors=errors, preview=preview

            )

        raw_data = file.read()

        if not raw_data:

            message = "The selected file is empty."

            return render_template(

                "upload.html", message=message,

                message_type=message_type, errors=errors, preview=preview

            )

        file_hash = hashlib.sha256(raw_data).hexdigest()

        connection = None

        cursor = None

        try:

            connection = get_connection()

            cursor = connection.cursor(dictionary=True)

            cursor.execute(

                "SELECT file_id FROM imported_files WHERE file_hash = %s",

                (file_hash,)

            )

            if cursor.fetchone():

                message = "This exact CSV file has already been imported."

                return render_template(

                    "upload.html", message=message,

                    message_type=message_type, errors=errors, preview=preview

                )

            try:

                df = pd.read_csv(StringIO(raw_data.decode("utf-8-sig")))

            except (UnicodeDecodeError, pd.errors.ParserError):

                message = "Could not read the CSV file. Check its format."

                return render_template(

                    "upload.html", message=message,

                    message_type=message_type, errors=errors, preview=preview

                )

            required_columns = [

                "product_id", "sale_date", "quantity", "unit_price", "region"

            ]

            if not all(col in df.columns for col in required_columns):

                message = "CSV must contain: " + ", ".join(required_columns)

                return render_template(

                    "upload.html", message=message,

                    message_type=message_type, errors=errors, preview=preview

                )

            valid_rows = []

            for index, row in df.iterrows():

                row_number = index + 2

                try:

                    product_value = str(row["product_id"]).strip()

                    quantity_value = str(row["quantity"]).strip()

                    if not product_value.isdigit():

                        raise ValueError("Product ID must be a whole number.")

                    if not quantity_value.isdigit():

                        raise ValueError("Quantity must be a whole number.")

                    product_id = int(product_value)

                    quantity = int(quantity_value)

                    unit_price = float(row["unit_price"])

                    sale_date = pd.to_datetime(

                        row["sale_date"], errors="raise"

                    ).date()

                    region = str(row["region"]).strip()

                    if quantity <= 0:

                        raise ValueError("Quantity must be greater than zero.")

                    if unit_price < 0:

                        raise ValueError("Unit price cannot be negative.")

                    if not region or region.lower() == "nan":

                        raise ValueError("Region cannot be empty.")

                    cursor.execute(

                        "SELECT product_id FROM products WHERE product_id = %s",

                        (product_id,)

                    )

                    if cursor.fetchone() is None:

                        raise ValueError(f"Product ID {product_id} does not exist.")

                    valid_rows.append((

                        product_id, sale_date, quantity, unit_price, region

                    ))

                except (ValueError, TypeError, OverflowError) as exc:

                    errors.append(f"Row {row_number}: {exc}")

            preview = [

                {

                    "product_id": row[0],

                    "sale_date": str(row[1]),

                    "quantity": row[2],

                    "unit_price": row[3],

                    "region": row[4]

                }

                for row in valid_rows[:10]

            ]

            if errors:

                message = (

                    f"Import cancelled. Found {len(errors)} invalid row(s). "

                    "Correct the errors and upload the CSV again."

                )

                return render_template(

                    "upload.html",

                    message=message,

                    message_type=message_type,

                    errors=errors,

                    preview=preview

                )

            if not valid_rows:

                message = "The CSV contains no valid sales rows."

                return render_template(

                    "upload.html",

                    message=message,

                    message_type=message_type,

                    errors=errors,

                    preview=preview

                )

            cursor.executemany("""

                INSERT INTO sales

                    (product_id, sale_date, quantity, unit_price, region)

                VALUES (%s, %s, %s, %s, %s)

            """, valid_rows)

            cursor.execute("""

                INSERT INTO imported_files (file_hash, file_name)

                VALUES (%s, %s)

            """, (file_hash, file.filename))

            connection.commit()

            message = f"Successfully imported {len(valid_rows)} sales row(s)."

            message_type = "success"

            preview = []

        except mysql.connector.Error:

            if connection is not None:

                connection.rollback()

            app.logger.exception("CSV import failed.")

            message = "Database error during import. No rows were imported."

        finally:

            close_db(cursor, connection)

    return render_template(

        "upload.html",

        message=message,

        message_type=message_type,

        errors=errors,

        preview=preview

    )



@app.route("/analytics")
def analytics():
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    current_year = date.today().year

    try:
        selected_year = int(request.args.get("year", current_year))
        if not 1900 <= selected_year <= 2100:
            selected_year = current_year
    except (ValueError, TypeError):
        selected_year = current_year

    error = ""
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                s.sale_id,
                s.product_id,
                p.product_name,
                p.category,
                s.sale_date,
                s.quantity,
                s.unit_price,
                s.region,
                (s.quantity * s.unit_price) AS revenue
            FROM sales s
            JOIN products p ON s.product_id = p.product_id
            WHERE 1=1
        """

        params = []

        if start_date:
            query += " AND s.sale_date >= %s"
            params.append(start_date)

        if end_date:
            query += " AND s.sale_date < DATE_ADD(%s, INTERVAL 1 DAY)"
            params.append(end_date)

        if start_date and end_date and start_date > end_date:
            error = "Start date must be on or before end date."
            rows = []
        else:
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

        df = pd.DataFrame(rows)

        if df.empty:
            product_data = []

            product_chart = create_analytics_chart(
                "analytics_product_revenue.png",
                "Top 10 Products by Revenue",
                ["No data"], [0], "Product", "Revenue"
            )

            quantity_chart = create_analytics_chart(
                "analytics_product_quantity.png",
                "Top 10 Products by Quantity Sold",
                ["No data"], [0], "Product", "Quantity"
            )

            category_chart = create_analytics_chart(
                "analytics_category_revenue.png",
                "Top 5 Categories by Revenue",
                ["No data"], [0], "Category", "Revenue"
            )

            region_chart = create_analytics_chart(
                "analytics_region_revenue.png",
                "Top 5 Regions by Revenue",
                ["No data"], [0], "Region", "Revenue"
            )

        else:
            df["revenue"] = pd.to_numeric(
                df["revenue"], errors="coerce"
            ).fillna(0)

            df["quantity"] = pd.to_numeric(
                df["quantity"], errors="coerce"
            ).fillna(0)

            # Group sales by product.
            product_df = df.groupby(
                ["product_id", "product_name", "category"],
                as_index=False
            ).agg(
                total_quantity=("quantity", "sum"),
                total_revenue=("revenue", "sum")
            ).sort_values(
                "product_id", ascending=True
            )

            # Keep all products in the details table.
            product_data = product_df.to_dict("records")

            # Top 10 products by revenue.
            top_revenue_df = product_df.sort_values(
                "total_revenue", ascending=False
            ).head(10)

            product_chart = create_analytics_chart(
                "analytics_product_revenue.png",
                "Top 10 Products by Revenue",
                top_revenue_df["product_name"].tolist(),
                top_revenue_df["total_revenue"].tolist(),
                "Product", "Revenue"
            )

            # Top 10 products by quantity sold.
            top_quantity_df = product_df.sort_values(
                "total_quantity", ascending=False
            ).head(10)

            quantity_chart = create_analytics_chart(
                "analytics_product_quantity.png",
                "Top 10 Products by Quantity Sold",
                top_quantity_df["product_name"].tolist(),
                top_quantity_df["total_quantity"].tolist(),
                "Product", "Quantity"
            )

            # Top 5 categories by revenue.
            category_df = df.groupby(
                "category"
            )["revenue"].sum().sort_values(
                ascending=False
            ).head(5)

            category_chart = create_analytics_chart(
                "analytics_category_revenue.png",
                "Top 5 Categories by Revenue",
                category_df.index.astype(str).tolist(),
                category_df.tolist(),
                "Category", "Revenue"
            )

            # Top 5 regions by revenue.
            region_df = df.groupby(
                "region"
            )["revenue"].sum().sort_values(
                ascending=False
            ).head(5)

            region_chart = create_analytics_chart(
                "analytics_region_revenue.png",
                "Top 5 Regions by Revenue",
                region_df.index.astype(str).tolist(),
                region_df.tolist(),
                "Region", "Revenue"
            )

        monthly_query = """
            SELECT
                MONTH(sale_date) AS month_number,
                SUM(quantity * unit_price) AS total_revenue
            FROM sales
            WHERE YEAR(sale_date) = %s
            GROUP BY MONTH(sale_date)
            ORDER BY MONTH(sale_date)
        """

        cursor.execute(monthly_query, (selected_year,))
        monthly_rows = cursor.fetchall()

        month_names = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
        ]

        monthly_revenue = [0] * 12

        for row in monthly_rows:
            month_number = int(row["month_number"])
            monthly_revenue[month_number - 1] = float(
                row["total_revenue"] or 0
            )

        monthly_chart = create_analytics_chart(
            "analytics_monthly_revenue.png",
            f"Monthly Revenue - {selected_year}",
            month_names,
            monthly_revenue,
            "Month",
            "Revenue",
            "line"
        )

        return render_template(
            "analytics.html",
            start_date=start_date,
            end_date=end_date,
            selected_year=selected_year,
            error=error,
            product_data=product_data,
            product_chart=product_chart,
            quantity_chart=quantity_chart,
            category_chart=category_chart,
            region_chart=region_chart,
            monthly_chart=monthly_chart
        )

    finally:
        close_db(cursor, connection)

       
if __name__ == "__main__":
    app.run(debug=True)

