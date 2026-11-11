-- Run once against your existing MySQL database after taking a backup.
ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user';
ALTER TABLE products ADD COLUMN price DECIMAL(12,2) NOT NULL DEFAULT 0.00;
ALTER TABLE products ADD COLUMN stock_quantity INT NOT NULL DEFAULT 0;
CREATE TABLE IF NOT EXISTS orders (
  order_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  product_id INT NOT NULL,
  quantity INT NOT NULL,
  unit_price DECIMAL(12,2) NOT NULL,
  total_price DECIMAL(12,2) NOT NULL,
  order_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  status VARCHAR(30) NOT NULL DEFAULT 'Placed',
  CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users(user_id),
  CONSTRAINT fk_orders_product FOREIGN KEY (product_id) REFERENCES products(product_id),
  INDEX idx_orders_user_date (user_id, order_date),
  INDEX idx_orders_product_date (product_id, order_date)
);
