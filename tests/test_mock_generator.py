"""
Unit Tests for E-Commerce Mock Data Generator
==============================================
Validates that generated datasets meet schema, business logic,
and referential integrity constraints before ingestion.
"""

import os
import shutil
import pytest
from datetime import datetime
from ingestion.generate_mock_data import ECommerceDataGenerator


@pytest.fixture
def temp_output_dir(tmp_path):
    output_dir = tmp_path / "mock_test_output"
    yield str(output_dir)
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)


def test_generator_stores(temp_output_dir):
    generator = ECommerceDataGenerator(output_dir=temp_output_dir, seed=42)
    stores = generator.generate_stores(count=5)
    
    assert len(stores) == 5
    for s in stores:
        assert s["store_id"].startswith("STORE-")
        assert s["store_name"]
        assert s["city"]
        assert s["state"]


def test_generator_products_pricing_rule(temp_output_dir):
    generator = ECommerceDataGenerator(output_dir=temp_output_dir, seed=42)
    products = generator.generate_products(count=20)
    
    assert len(products) == 20
    for p in products:
        assert p["product_id"].startswith("PROD-")
        # Unit price must be strictly greater than cost price (Profit margin rule)
        assert p["unit_price"] > p["cost_price"], f"Product {p['product_id']} selling price <= cost price!"


def test_generator_referential_integrity(temp_output_dir):
    """Ensure orders, items, and payments have valid Foreign Key references."""
    generator = ECommerceDataGenerator(output_dir=temp_output_dir, seed=42)
    stores = generator.generate_stores(count=3)
    products = generator.generate_products(count=10)
    customers = generator.generate_customers(start_id=1, count=15, base_time=datetime(2026, 9, 1))

    orders, items, payments = generator.generate_orders_and_items(
        start_order_id=1,
        order_count=30,
        customers=customers,
        products=products,
        stores=stores,
        start_date=datetime(2026, 9, 1),
        end_date=datetime(2026, 9, 10)
    )

    customer_ids = {c["customer_id"] for c in customers}
    store_ids = {s["store_id"] for s in stores}
    product_ids = {p["product_id"] for p in products}
    order_ids = {o["order_id"] for o in orders}

    # 1. Orders must link to existing customer and store
    for o in orders:
        assert o["customer_id"] in customer_ids
        assert o["store_id"] in store_ids

    # 2. Every order item must link to an existing order and product
    for item in items:
        assert item["order_id"] in order_ids
        assert item["product_id"] in product_ids

    # 3. Every payment must link to an existing order
    for pay in payments:
        assert pay["order_id"] in order_ids
        assert pay["payment_amount"] >= 0


def test_generator_full_initial_run(temp_output_dir):
    """Test CSV file generation on disk."""
    generator = ECommerceDataGenerator(output_dir=temp_output_dir, seed=42)
    generator.run(mode="initial")

    expected_files = [
        "stores.csv",
        "products.csv",
        "customers.csv",
        "orders.csv",
        "order_items.csv",
        "payments.csv"
    ]

    for fname in expected_files:
        filepath = os.path.join(temp_output_dir, fname)
        assert os.path.exists(filepath), f"File {fname} was not created!"
        assert os.path.getsize(filepath) > 0, f"File {fname} is empty!"
