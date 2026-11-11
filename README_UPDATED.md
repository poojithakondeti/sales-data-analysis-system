# Sales Analytics Dashboard — Updated User & Admin Features

## Added features
- Separate user and administrator login pages.
- User product catalogue with price and current stock quantity.
- Direct order placement with stock validation and transactional stock reduction.
- User order history with order date, quantity, unit price, total and status.
- Admin order list showing the customer, product, ordered quantity, order date and current stock.
- Admin can update order status; cancelling an order restores the stock.
- Analytics can filter the monthly revenue chart by a product and year; all 12 months are plotted, including zero-sales months.
- Admin product management includes price and stock quantity.

## Setup
1. Back up your current database.
2. Create a Python virtual environment and install requirements: `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env`; fill in DB connection values, a strong `SECRET_KEY`, `ADMIN_USERNAME`, and a strong `ADMIN_PASSWORD`.
4. Run `migrate_orders_and_roles.sql` once on your existing MySQL database. This adds price/stock columns and creates the orders table without deleting existing records.
5. Start the app with `python app.py`.
6. Users register from `/register`, then sign in at `/login`. Admin signs in at `/admin/login` using the credentials in `.env`.

## Important notes
- Existing products get a default price of 0 and stock of 0 after migration. The admin should edit each product and enter its actual price and stock before customers order.
- Existing sales records are retained. New customer orders are stored separately in `orders`; the existing admin sales/import/reporting features remain in place.
- Set `ADMIN_PASSWORD` to a strong secret. Never commit `.env` or database credentials.
- The application uses MySQL and expects InnoDB tables so row locking works during stock checks.
