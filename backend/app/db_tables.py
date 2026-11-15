from .db import engine

from sqlalchemy import MetaData,Table, Column, Integer, String, Float


metadata = MetaData()

#  Users table

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String(50), nullable=False),
    Column("email", String(50), nullable=False, unique=True),
    Column("password", String(100), nullable=False),
    Column("role", String(20), nullable=False, default="customer"),
    Column("phone", String(20), nullable=True)
)

#  Food items table

food_items = Table(
    "food_items",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(100), nullable=False),
    Column("description", String(200), nullable=False),
    Column("price", Float, nullable=False),
    Column("category", String(50), nullable=False),
)

menu_items_table = Table(
    "menu_items",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(100), nullable=False),
    Column("description", String(300)),
    Column("price", Float, nullable=False),
    Column("category", String(50), nullable=False),
    Column("owner_email", String(100), nullable=False)
)

orders_table = Table(
    "orders",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("customer_email", String(100), nullable=False),
    Column("total_price", Float, nullable=False),
    Column("status", String(50), default="Pending"), 
    Column("delivery_partner_phone", String(20), nullable=True)
)

order_items_table = Table(
    "order_items",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("order_id", Integer, nullable=False),
    Column("menu_item_id", Integer, nullable=False),
    Column("quantity", Integer, nullable=False),
    Column("price_at_order", Float, nullable=False) 
)


# Function to trigger table creation using the engine passed from main.py
def create_all_tables(engine):
    metadata.create_all(engine)