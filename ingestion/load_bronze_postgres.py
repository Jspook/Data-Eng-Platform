"""
Bronze Layer Database Ingestion Loader
=======================================
Loads raw datasets from the local landing zone (data/bronze/)
directly into PostgreSQL Data Warehouse under schema: `bronze`

Features:
- Adds operational metadata (_ingested_at, _source_file) for data governance
- Ensures Idempotent execution (safe to re-run anytime)
- Logs execution metrics and row counts
"""

import os
import glob
from datetime import datetime, timezone
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Database connection credentials from environment variables
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
# If running on host machine outside docker container, map container hostname to localhost
if DB_HOST == "postgres" and not os.path.exists("/.dockerenv"):
    DB_HOST = "localhost"
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "ecommerce_dw")
DB_USER = os.getenv("POSTGRES_USER", "dw_admin")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "dw_password_dev_123")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


class BronzePostgresLoader:
    def __init__(self, db_url: str = DATABASE_URL):
        self.engine = create_engine(db_url)

    def load_table(self, file_path: str, table_name: str, schema: str = "bronze") -> int:
        """
        Loads a single raw CSV file into target schema/table with audit columns.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Source file not found: {file_path}")

        df = pd.read_csv(file_path)
        
        # Add metadata audit columns
        ingestion_timestamp = datetime.now(timezone.utc)
        df["_ingested_at"] = ingestion_timestamp
        df["_source_file"] = os.path.basename(file_path)

        # Idempotent write: replace raw landing table
        df.to_sql(
            name=table_name,
            con=self.engine,
            schema=schema,
            if_exists="replace",
            index=False,
            method="multi",
            chunksize=1000
        )

        row_count = len(df)
        print(f"  [Bronze Loaded] {schema}.{table_name:<18} <- {os.path.basename(file_path)} ({row_count:>5} rows)")
        return row_count

    def load_all_bronze(self, source_dir: str = "data/bronze"):
        """
        Iterates over all standard e-commerce CSV files and loads into bronze schema.
        """
        table_mappings = {
            "stores.csv": "raw_stores",
            "products.csv": "raw_products",
            "customers.csv": "raw_customers",
            "orders.csv": "raw_orders",
            "order_items.csv": "raw_order_items",
            "payments.csv": "raw_payments",
        }

        print("\n=======================================================")
        print("Starting Bronze Layer Warehouse Ingestion (PostgreSQL)")
        print(f"Target Database: {DB_NAME} (Schema: bronze)")
        print("=======================================================")

        total_rows = 0
        for filename, table_name in table_mappings.items():
            filepath = os.path.join(source_dir, filename)
            if os.path.exists(filepath):
                count = self.load_table(filepath, table_name)
                total_rows += count
            else:
                print(f"  [Warning] Missing expected file: {filepath}")

        print(f"\n[OK] Bronze Ingestion Complete! Total rows loaded: {total_rows}\n")


if __name__ == "__main__":
    loader = BronzePostgresLoader()
    loader.load_all_bronze()
