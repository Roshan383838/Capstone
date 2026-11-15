from sqlalchemy.orm import Session
from .db_tables import users, food_items, menu_items_table, orders_table, order_items_table
from .check import MenuItemCreate, MenuItemUpdate, OrderCreate

from passlib.context import CryptContext

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return password_context.hash(password)

def verify_password(plain_password, hashed_password):
    return password_context.verify(plain_password, hashed_password)

# Function to fetch a single user by their email address
def get_user_by_email(db: Session, email: str):
    query = users.select().where(users.c.email == email)
    return db.execute(query).fetchone()

# Function to insert a new user row into the database
def create_user(db: Session, user_data):
    hashed = hash_password(user_data.password)

    query = users.insert().values(
        username=user_data.username,
        email=user_data.email,
        password= hashed,
        role=user_data.role,
        phone=user_data.phone
    )

    db.execute(query)
    db.commit()

# Function to fetch all food items from the menu table
def get_all_food(db: Session):
    query = food_items.select()
    return db.execute(query).fetchall()

# 4. Function to insert a new food item into the menu table
def create_food(db: Session, food_data):
    query = food_items.insert().values(
        name=food_data.name,
        description=food_data.description,
        price=food_data.price,
        category=food_data.category
    )
    # Execute the query and commit the changes
    db.execute(query)
    db.commit()


def create_menu_item_in_db(db: Session, item: MenuItemCreate, owner_email: str):
    query = menu_items_table.insert().values(
        name=item.name,
        description=item.description,
        price=item.price,
        category=item.category,
        owner_email=owner_email
    )
    result = db.execute(query)
    db.commit()
    return result.lastrowid

def get_all_menu_items_from_db(db: Session):
    query = menu_items_table.select()
    result = db.execute(query).fetchall()
    # Convert database rows into clean dictionaries/objects
    return [dict(row._mapping) for row in result]

def delete_menu_item_from_db(db: Session, item_id: int):
    query = menu_items_table.delete().where(menu_items_table.c.id == item_id)
    result = db.execute(query)
    db.commit()
    return result.rowcount

def update_menu_item_in_db(db: Session, item_id: int, item: MenuItemUpdate):
    # Filter out fields that weren't provided (leave them untouched in the DB)
    update_data = {k: v for k, v in item.model_dump().items() if v is not None}
    
    if not update_data:
        return 0  # Nothing to update
        
    query = (
        menu_items_table.update()
        .where(menu_items_table.c.id == item_id)
        .values(**update_data)
    )
    result = db.execute(query)
    db.commit()
    return result.rowcount  # Returns 1 if successful, 0 if ID didn't exist

def create_order_in_db(db: Session, order_data: OrderCreate, customer_email: str):
    # 1. Calculate total price by fetching current item prices from the database
    total_price = 0.0
    item_details = []
    
    for item in order_data.items:
        # Fetch the item price from menu_items
        price_query = menu_items_table.select().where(menu_items_table.c.id == item.menu_item_id)
        db_item = db.execute(price_query).fetchone()
        
        if not db_item:
            raise ValueError(f"Menu item with ID {item.menu_item_id} not found.")
            
        item_price = db_item._mapping["price"]
        total_price += item_price * item.quantity
        
        item_details.append({
            "menu_item_id": item.menu_item_id,
            "quantity": item.quantity,
            "price_at_order": item_price
        })

    # 2. Insert into the main 'orders' table
    order_query = orders_table.insert().values(
        customer_email=customer_email,
        total_price=total_price,
        status="Placed"
    )
    order_result = db.execute(order_query)
    order_id = order_result.lastrowid # Get the newly created order ID

    # 3. Insert each ordered item into the 'order_items' junction table
    for detail in item_details:
        item_query = order_items_table.insert().values(
            order_id=order_id,
            menu_item_id=detail["menu_item_id"],
            quantity=detail["quantity"],
            price_at_order=detail["price_at_order"]
        )
        db.execute(item_query)

    db.commit()
    return order_id, total_price



def update_order_status_in_db(db: Session, order_id: int, new_status: str):
    query = (
        orders_table.update()
        .where(orders_table.c.id == order_id)
        .values(status=new_status)
    )
    result = db.execute(query)
    db.commit()
    return result.rowcount  

def get_orders_from_db(db: Session):
    query = orders_table.select()
    result = db.execute(query).fetchall()
    return [dict(row._mapping) for row in result]

def assign_delivery_partner_in_db(db: Session, order_id: int, partner_phone: str):
    query = (
        orders_table.update()
        .where(orders_table.c.id == order_id)
        .values(delivery_partner_phone=partner_phone, status="ASSIGNED")
    )
    result = db.execute(query)
    db.commit()
    return result.rowcount

def get_partner_orders_from_db(db: Session, partner_phone: str):
    query = orders_table.select().where(orders_table.c.delivery_partner_phone == partner_phone)
    result = db.execute(query).fetchall()
    return [dict(row._mapping) for row in result]

def update_delivery_status_in_db(db: Session, order_id: int, partner_phone: str, new_status: str):
    query = (
        orders_table.update()
        .where((orders_table.c.id == order_id) & (orders_table.c.delivery_partner_phone == partner_phone))
        .values(status=new_status)
    )
    result = db.execute(query)
    db.commit()
    return result.rowcount

def get_customer_orders_from_db(db: Session, email: str):
  query = orders_table.select().where(orders_table.c.customer_email == email)
  result = db.execute(query).fetchall()
  return [dict(row._mapping) for row in result]