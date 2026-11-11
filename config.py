
import os

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "sales_db"),
}

# Enable verified SSL when connecting to Aiven on Render.
ssl_ca = os.getenv("DB_SSL_CA")
if ssl_ca:
    DB_CONFIG["ssl_ca"] = ssl_ca
    DB_CONFIG["ssl_verify_cert"] = True
    DB_CONFIG["ssl_verify_identity"] = True
