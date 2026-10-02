"""
Synthetic E-Commerce Data Generator
====================================
Generates realistic E-commerce transactional data across 6 core tables:
- customers
- products
- stores
- orders
- order_items
- payments

Features:
- Deterministic seeding (reproducible datasets)
- Support for Initial Load (Batch 1) vs Incremental / Delta Load (Batch 2)
- Simulates real-world data issues (status updates, timestamp evolution)
"""

import os
import csv
import random
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple

# Predefined realistic lookup values for consistency and fallback
CATEGORIES = [
    "Electronics", "Computers", "Home & Kitchen", "Apparel", 
    "Health & Beauty", "Sports & Outdoors", "Books & Stationery"
]

CITIES_STATES = [
    ("Bangkok", "Bangkok"),
    ("Nonthaburi", "Nonthaburi"),
    ("Chiang Mai", "Chiang Mai"),
    ("Phuket", "Phuket"),
    ("Chonburi", "Chonburi"),
    ("Khon Kaen", "Khon Kaen"),
    ("Nakhon Ratchasima", "Nakhon Ratchasima"),
    ("Songkhla", "Songkhla")
]

PAYMENT_METHODS = ["credit_card", "promptpay", "bank_transfer", "e_wallet", "cash_on_delivery"]
ORDER_STATUSES = ["completed", "shipped", "processing", "cancelled"]


def get_faker_instance():
    """Lazily import and initialize Faker with deterministic seed."""
    try:
        from faker import Faker
        fake = Faker()
        Faker.seed(42)
        return fake
    except ImportError:
        return None


class ECommerceDataGenerator:
    def __init__(self, output_dir: str, seed: int = 42):
        self.output_dir = output_dir
        self.seed = seed
        random.seed(self.seed)
        self.fake = get_faker_instance()
        os.makedirs(self.output_dir, exist_ok=True)

    def _save_to_csv(self, filename: str, fieldnames: List[str], rows: List[Dict[str, Any]]):
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"  -> Generated {len(rows):>6} rows: {filename}")

    def generate_stores(self, count: int = 5) -> List[Dict[str, Any]]:
        stores = []
        base_time = datetime(2026, 1, 1, 0, 0, 0)
        for i in range(1, count + 1):
            city, state = CITIES_STATES[i % len(CITIES_STATES)]
            stores.append({
                "store_id": f"STORE-{i:03d}",
                "store_name": f"E-Shop Official Flagship {city}",
                "city": city,
                "state": state,
                "created_at": base_time.isoformat(),
                "updated_at": base_time.isoformat()
            })
        return stores

    def generate_products(self, count: int = 50) -> List[Dict[str, Any]]:
        products = []
        base_time = datetime(2026, 1, 1, 0, 0, 0)
        adjectives = ["Pro", "Ultra", "Smart", "Eco", "Premium", "Classic", "Wireless", "Compact"]
        nouns = ["Headphones", "Watch", "Blender", "Backpack", "Lamp", "Keyboard", "Sneakers", "Serum"]

        for i in range(1, count + 1):
            category = random.choice(CATEGORIES)
            adj = random.choice(adjectives)
            noun = random.choice(nouns)
            name = f"{adj} {noun} Model-{i}"
            cost_price = round(random.uniform(50.0, 3000.0), 2)
            unit_price = round(cost_price * random.uniform(1.25, 2.2), 2)

            products.append({
                "product_id": f"PROD-{i:04d}",
                "product_name": name,
                "category": category,
                "cost_price": cost_price,
                "unit_price": unit_price,
                "created_at": base_time.isoformat(),
                "updated_at": base_time.isoformat()
            })
        return products

    def generate_customers(self, start_id: int, count: int, base_time: datetime) -> List[Dict[str, Any]]:
        customers = []
        for i in range(start_id, start_id + count):
            city, state = random.choice(CITIES_STATES)
            if self.fake:
                first_name = self.fake.first_name()
                last_name = self.fake.last_name()
                email = f"{first_name.lower()}.{last_name.lower()}{i}@example.com"
                phone = f"08{random.randint(10000000, 99999999)}"
            else:
                first_name = f"User{i}"
                last_name = f"Test{i}"
                email = f"user{i}@example.com"
                phone = f"08{10000000 + i}"

            reg_time = base_time - timedelta(days=random.randint(1, 60))
            customers.append({
                "customer_id": f"CUST-{i:05d}",
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone": phone,
                "city": city,
                "state": state,
                "created_at": reg_time.isoformat(),
                "updated_at": reg_time.isoformat()
            })
        return customers

    def generate_orders_and_items(
        self,
        start_order_id: int,
        order_count: int,
        customers: List[Dict[str, Any]],
        products: List[Dict[str, Any]],
        stores: List[Dict[str, Any]],
        start_date: datetime,
        end_date: datetime
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Generates orders, order_items, and matching payments.
        Ensures foreign key referential integrity across all 3 tables.
        """
        orders = []
        order_items = []
        payments = []
        item_counter = 1
        pay_counter = 1

        delta_seconds = int((end_date - start_date).total_seconds())

        for o_idx in range(start_order_id, start_order_id + order_count):
            order_id = f"ORD-{o_idx:06d}"
            customer = random.choice(customers)
            store = random.choice(stores)

            random_sec = random.randint(0, max(1, delta_seconds))
            order_time = start_date + timedelta(seconds=random_sec)
            status = random.choices(ORDER_STATUSES, weights=[0.70, 0.15, 0.10, 0.05])[0]

            orders.append({
                "order_id": order_id,
                "customer_id": customer["customer_id"],
                "store_id": store["store_id"],
                "order_status": status,
                "order_date": order_time.strftime("%Y-%m-%d"),
                "created_at": order_time.isoformat(),
                "updated_at": order_time.isoformat()
            })

            # Generate 1 to 4 items per order
            num_items = random.randint(1, 4)
            selected_products = random.sample(products, num_items)
            order_total = 0.0

            for prod in selected_products:
                qty = random.randint(1, 3)
                unit_price = prod["unit_price"]
                discount_rate = random.choice([0.0, 0.0, 0.05, 0.10, 0.15])
                discount_amount = round(unit_price * qty * discount_rate, 2)
                line_total = round((unit_price * qty) - discount_amount, 2)
                order_total += line_total

                order_items.append({
                    "order_item_id": f"ITEM-{item_counter:07d}",
                    "order_id": order_id,
                    "product_id": prod["product_id"],
                    "quantity": qty,
                    "unit_price": unit_price,
                    "discount": discount_amount,
                    "created_at": order_time.isoformat(),
                    "updated_at": order_time.isoformat()
                })
                item_counter += 1

            # Generate payment for the order
            payment_status = "refunded" if status == "cancelled" else "success"
            payments.append({
                "payment_id": f"PAY-{pay_counter:07d}",
                "order_id": order_id,
                "payment_method": random.choice(PAYMENT_METHODS),
                "payment_status": payment_status,
                "payment_amount": round(order_total, 2),
                "payment_date": order_time.strftime("%Y-%m-%d %H:%M:%S"),
                "created_at": order_time.isoformat(),
                "updated_at": order_time.isoformat()
            })
            pay_counter += 1

        return orders, order_items, payments

    def run(self, mode: str = "initial"):
        print(f"\n=======================================================")
        print(f"Generating E-Commerce Synthetic Data (Mode: {mode.upper()})")
        print(f"Target Output Directory: {self.output_dir}")
        print(f"=======================================================")

        if mode == "initial":
            stores = self.generate_stores(count=5)
            products = self.generate_products(count=50)
            customers = self.generate_customers(start_id=1, count=100, base_time=datetime(2026, 9, 1))

            # Initial batch: Orders from 2026-09-01 to 2026-09-25
            orders, items, payments = self.generate_orders_and_items(
                start_order_id=1,
                order_count=500,
                customers=customers,
                products=products,
                stores=stores,
                start_date=datetime(2026, 9, 1, 8, 0, 0),
                end_date=datetime(2026, 9, 25, 23, 59, 59)
            )
        elif mode == "incremental":
            # Incremental batch: Represents Day 26 to Day 30 delta
            stores = self.generate_stores(count=5)
            products = self.generate_products(count=50)
            # 20 new customers registered
            customers = self.generate_customers(start_id=101, count=20, base_time=datetime(2026, 9, 30))

            orders, items, payments = self.generate_orders_and_items(
                start_order_id=501,
                order_count=100,
                customers=customers,
                products=products,
                stores=stores,
                start_date=datetime(2026, 9, 26, 0, 0, 0),
                end_date=datetime(2026, 9, 30, 23, 59, 59)
            )
        else:
            raise ValueError(f"Unsupported mode: {mode}. Choose 'initial' or 'incremental'")

        # Save all tables
        self._save_to_csv("stores.csv", list(stores[0].keys()), stores)
        self._save_to_csv("products.csv", list(products[0].keys()), products)
        self._save_to_csv("customers.csv", list(customers[0].keys()), customers)
        self._save_to_csv("orders.csv", list(orders[0].keys()), orders)
        self._save_to_csv("order_items.csv", list(items[0].keys()), items)
        self._save_to_csv("payments.csv", list(payments[0].keys()), payments)

        print(f"\n[OK] All 6 tables successfully generated in {self.output_dir}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synthetic E-Commerce Data Generator")
    parser.add_argument("--mode", choices=["initial", "incremental"], default="initial", 
                        help="Data generation mode ('initial' or 'incremental')")
    parser.add_argument("--output-dir", default="data/bronze", 
                        help="Destination directory for raw CSV files")
    args = parser.parse_args()

    generator = ECommerceDataGenerator(output_dir=args.output_dir)
    generator.run(mode=args.mode)
