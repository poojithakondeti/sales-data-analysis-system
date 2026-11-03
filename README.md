# Sales Data Analysis System

## Project Overview

The **Sales Data Analysis System** is a web-based application developed to manage, organize, analyze, and visualize sales data efficiently. It helps users understand business performance by converting raw sales records into meaningful insights through interactive dashboards, charts, and reports.

The application provides a centralized platform where users can manage products, maintain sales records, upload sales data through CSV files, and analyze important business metrics such as total revenue, sales quantity, product performance, monthly revenue, and regional sales.

The system is developed using Python and Flask for backend operations, MySQL for database management, and HTML, CSS, Bootstrap, and JavaScript for the frontend. Pandas is used for data processing, while Matplotlib is used to generate analytical charts and visualizations.

## Objectives

- To simplify sales record management.
- To maintain product and sales information in a centralized database.
- To automate sales data import through CSV files.
- To validate uploaded data and identify invalid records.
- To calculate total revenue and other important sales metrics.
- To identify top-performing products and sales regions.
- To visualize sales trends using charts and graphs.
- To generate downloadable sales reports.
- To provide a user-friendly dashboard for understanding business performance.

## Key Features

### 1. User Authentication
- User registration and login functionality.
- Secure password hashing.
- Session-based authentication.
- Logout functionality.

### 2. Dashboard
- Displays important sales performance indicators.
- Shows total revenue and sales quantity.
- Provides an overview of product and sales performance.
- Displays analytical charts for quick insights.

### 3. Product Management
- Add new products.
- View all available products.
- Update existing product details.
- Delete products when they are not associated with sales records.

### 4. Sales Management
- Add new sales records manually.
- Select products from the available product list.
- Enter sales date, quantity, unit price, and region.
- Automatically calculate revenue.
- Edit and delete existing sales records.

### 5. CSV File Upload
- Upload sales data using CSV files.
- Validate required column names and input data.
- Preview uploaded records before importing.
- Identify invalid records and display validation reports.
- Import valid sales records into the database.
- Track imported files to help prevent duplicate imports.

### 6. Sales Analytics
The analytics module helps users understand sales performance through different measurements:

- Total revenue analysis.
- Total quantity sold.
- Product-wise revenue analysis.
- Product-wise quantity analysis.
- Monthly revenue trends.
- Regional revenue analysis.
- Category-wise revenue analysis.
- Top-performing products based on revenue and quantity.

### 7. Data Visualization
The application uses Matplotlib to generate charts, including:
- Monthly revenue charts.
- Regional sales charts.
- Product revenue charts.
- Product quantity charts.
- Category revenue charts.
- Top product visualizations.

### 8. Sales Records and Reports
- View complete sales records.
- Search and manage sales information.
- Export sales records into CSV format.
- Generate Excel reports.
- Generate PDF reports.

### 9. Database Management
- Store user, product, sales, and imported-file information in MySQL.
- Maintain relationships between products and sales records.
- Use primary keys and foreign keys to maintain data integrity.

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web application framework |
| HTML5 | Web page structure |
| CSS3 | Styling |
| Bootstrap | Responsive user interface |
| JavaScript | Frontend interactions |
| MySQL | Relational
