from fastapi.middleware.cors import CORSMiddleware
from fastapi import BackgroundTasks
import logging
import time
import jwt
import os
from fastapi import FastAPI, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from openai import OpenAI

# Import our custom modules from the app package
from .db import engine, get_db
from .db_tables import create_all_tables
from .check import UserSchema, FoodSchema, LoginSchema, MenuItemCreate, MenuItemUpdate, OrderCreate, StatusUpdate, AssignPartnerRequest, DeliveryStatusUpdate
from . import crud 
from .dependency import RoleChecker
from .background_task import check_stale_order_status    


SECRET_KEY = "Secret_Key_here"
ALGORITHM = "HS256"

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@asynccontextmanager
async def lifespan(app:FastAPI):
    create_all_tables(engine)
    yield


app = FastAPI(title="CampusBite API", description="Backend API for CampusBite Capstone Project", lifespan = lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all frontend origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CampusBiteLogger")

@app.middleware("http")
async def log_requests_and_time(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    
    logger.info(
        f"Method: {request.method} | Path: {request.url.path} | "
        f"Status: {response.status_code} | Duration: {process_time:.2f}ms"
    )
    
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    return response

#  Root Endpoint (To check if the server is running)
@app.get("/")
def read_root():
    return {"message": "Welcome to CampusBite API! Backend is running live."}

@app.post("/login")
def login_user(credentials: LoginSchema, db: Session = Depends(get_db)):
    print(f"-> Attempting login for email: {credentials.email}")
    user = crud.get_user_by_email(db, credentials.email)
    print(f"-> User found in database: {user}")
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    
    if not crud.verify_password(credentials.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    # 3. Create JWT token payload containing email (sub) and role
    payload = {
        "sub": user.email,
        "role": user.role,
        "phone": user.phone
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "message": "Login successful!"
    }

@app.get("/customer/insights")
def get_customer_order_insights(
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["customer"]))
):
    """
    Analyzes the logged-in customer's order history using OpenAI 
    to provide personalized food insights and recommendations.
    """
    customer_email = user.get("sub")  # Email is stored in 'sub' from the JWT payload
    
    # 1. Fetch customer's orders from database using your crud helper
    orders = crud.get_customer_orders_from_db(db, customer_email)
    
    if not orders:
        return {
            "status": "success",
            "ai_insights": "You haven't placed any orders yet, brother! Try ordering a legendary samosa to kickstart your history."
        }
    
    # 2. Summarize order data for the AI prompt
    order_summary = ", ".join([
        f"Order #{o['id']} (Total: ₹{o['total_price']}, Status: {o['status']})" 
        for o in orders
    ])
    
    prompt = (
        f"You are a friendly AI food assistant for CampusBite. "
        f"Here is this customer's order history: {order_summary}. "
        f"Give them a short, engaging, personalized food recommendation or fun insight based on their history."
    )
    
    try:
        # 3. Call OpenAI Chat Completions API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )
        ai_message = response.choices[0].message.content
        
        return {
            "status": "success",
            "customer": customer_email,
            "insights": ai_message
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Could not generate AI insights right now. Error: {str(e)}"
        }

# Register User Endpoint (POST)
@app.post("/register")
def register_user(user: UserSchema, db: Session = Depends(get_db)):
    # Check if a user with this email already exists
    existing_user = crud.get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered!")
    
    # Call our CRUD function, passing the active session and the validated Pydantic user object
    crud.create_user(db, user)
    return {"message": "User registered successfully!", "username": user.username}

# Adding Food Item Endpoint (POST)
@app.post("/food")
def add_food_item(food: FoodSchema, db: Session = Depends(get_db)):
    # Call CRUD function to insert the food item into SQLite
    crud.create_food(db, food)
    return {"message": "Food item added successfully!", "food_name": food.name}

# Get Food Menu Endpoint (GET)
@app.get("/food")
def get_food_menu(db: Session = Depends(get_db)):
    # Fetch all food items from the database using our CRUD helper
    items = crud.get_all_food(db)
    return {"menu_items": items}


# This route is completely locked down. 
# Only users whose token says role == "owner" can get past this door!
@app.post("/menu-items", dependencies=[Depends(RoleChecker(["owner"]))])
def create_menu_item(
    item: MenuItemCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["owner"]))
):

    owner_email = user["email"]

    item_id = crud.create_item_in_db(db, item, owner_email)
    return {
        "status": "success",
        "message": f"Menu item '{item.name}' created successfully!",
        "item_id": item_id,
        "created_by": owner_email
    }

@app.get("/menu-items")
def get_menu_items(db: Session = Depends(get_db)):
    items = crud.get_all_menu_items_from_db(db)
    return {
        "status": "success",
        "count": len(items),
        "data": items
    }

@app.delete("/menu-items/{item_id}", dependencies=[Depends(RoleChecker(["owner"]))])
def delete_menu_item(
    item_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["owner"]))
):
    deleted_count = crud.delete_menu_item_from_db(db, item_id)
    
    if deleted_count == 0:
        return {"status": "error", "message": f"Menu item with ID {item_id} not found."}
        
    return {
        "status": "success",
        "message": f"Menu item {item_id} deleted successfully by {user['email']}"
    }

@app.put("/menu-items/{item_id}")
def update_menu_item(
    item_id: int,
    item: MenuItemUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["owner"]))
):
    updated_count = crud.update_menu_item_in_db(db, item_id, item)
    
    if updated_count == 0:
        return {"status": "error", "message": f"Menu item with ID {item_id} not found."}
        
    return {
        "status": "success",
        "message": f"Menu item {item_id} updated successfully by {user['email']}"
    }


@app.post("/orders")
def place_order(
    order_data: OrderCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["customer"]))
):
    try:
        customer_email = user["email"]
        order_id, total_price = crud.create_order_in_db(db, order_data, customer_email)
        
        return {
            "status": "success",
            "message": "Order placed successfully!",
            "order_id": order_id,
            "customer": customer_email,
            "total_price": total_price,
            "order_status":"Placed"
        }
    except ValueError as e:
        return {"status": "error", "message": str(e)}

@app.get("/orders")
def get_all_orders(
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["owner"]))
):
    orders = crud.get_orders_from_db(db)
    return {
        "status": "success",
        "count": len(orders),
        "data": orders
    }

@app.put("/orders/{order_id}/status")
def update_order_status(
    order_id: int,
    status_data: StatusUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["owner"]))
):
    updated = crud.update_order_status_in_db(db, order_id, status_data.status)
    
    if updated == 0:
        return {"status": "error", "message": f"Order with ID {order_id} not found."}
        
    return {
        "status": "success",
        "message": f"Order {order_id} status updated to '{status_data.status}' by owner {user['email']}"
    }

@app.put("/orders/{order_id}/assign")
def assign_order_to_partner(
    order_id: int,
    assignment: AssignPartnerRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["owner"]))
):
    """Restaurant owner assigns a ready order to a delivery partner by phone number."""
    updated = crud.assign_delivery_partner_in_db(db, order_id, assignment.partner_phone)
    if updated == 0:
        return {"status": "error", "message": f"Order {order_id} not found."}
    return {
        "status": "success",
        "message": f"Order {order_id} assigned to delivery partner {assignment.partner_phone} and status set to ASSIGNED."
    }

@app.get("/delivery/orders")
def get_assigned_deliveries(
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["delivery_partner"]))
):
    """Delivery partner views only the orders assigned to their phone number from the JWT token."""
    partner_phone = user.get("phone")
    orders = crud.get_partner_orders_from_db(db, partner_phone)
    return {
        "status": "success",
        "count": len(orders),
        "data": orders
    }

@app.put("/delivery/orders/{order_id}/status")
def update_delivery_status(
    order_id: int,
    status_data: DeliveryStatusUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["delivery_partner"]))
):
    """Delivery partner updates their assigned order status to OUT_FOR_DELIVERY or DELIVERED."""
    partner_phone = user.get("phone")
    updated = crud.update_delivery_status_in_db(db, order_id, partner_phone, status_data.status)
    if updated == 0:
        return {"status": "error", "message": f"Order {order_id} not found or not assigned to your phone number."}
    return {
        "status": "success",
        "message": f"Delivery status for order {order_id} updated to '{status_data.status}'"
    }
