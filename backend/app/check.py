from pydantic import BaseModel
from typing import List

# Blueprint for validating user registration data coming from the client
class UserSchema(BaseModel):
    username: str
    email: str
    password: str
    role: str = "customer"
    phone: int = None

# Blueprint for validating food menu items added by restaurants or admins
class FoodSchema(BaseModel):
    name: str
    description: str
    price: float
    category: str

# For user login validation 
class LoginSchema(BaseModel):
    email: str
    password: str


# Blueprint for validating menu and for owner use only 
class MenuItemCreate(BaseModel):
    name: str
    description: str
    price: float
    category: str   

class MenuItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    category: str | None = None

class OrderItemCreate(BaseModel):
    menu_item_id: int
    quantity: int

class OrderCreate(BaseModel):
    items: List[OrderItemCreate]

class StatusUpdate(BaseModel):
    status: str  

class AssignPartnerRequest(BaseModel):
    partner_phone: str

class DeliveryStatusUpdate(BaseModel):
    status: str