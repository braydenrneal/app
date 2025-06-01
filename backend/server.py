from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import bcrypt
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Enums
class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

# Define Models
class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    price: float
    category: str
    inventory: int
    image_url: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    category: str
    inventory: int
    image_url: str

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    inventory: Optional[int] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None

class Admin(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AdminCreate(BaseModel):
    username: str
    email: str
    password: str

class AdminLogin(BaseModel):
    username: str
    password: str

class Category(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CategoryCreate(BaseModel):
    name: str
    description: str

class OrderItem(BaseModel):
    product_id: str
    product_name: str
    product_price: float
    quantity: int
    subtotal: float

class CustomerInfo(BaseModel):
    name: str
    phone: str
    address: str
    email: Optional[str] = None

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_info: CustomerInfo
    items: List[OrderItem]
    total_amount: float
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None
    delivery_fee: float = 0.0

class OrderCreate(BaseModel):
    customer_info: CustomerInfo
    items: List[OrderItem]
    notes: Optional[str] = None

class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    notes: Optional[str] = None

class DeliveryAddress(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    address: str
    zone: str
    delivery_fee: float
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DeliveryAddressCreate(BaseModel):
    address: str
    zone: str
    delivery_fee: float

class AddressCheckRequest(BaseModel):
    address: str

# Hash password utility
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Auth dependency
async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Simple token validation - in production use JWT
    token = credentials.credentials
    admin = await db.admins.find_one({"username": token})
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return Admin(**admin)

# Initialize default admin if not exists
async def init_default_admin():
    existing_admin = await db.admins.find_one({"username": "admin"})
    if not existing_admin:
        default_admin = Admin(
            username="admin",
            email="admin@mountainstore.com",
            password_hash=hash_password("admin123")
        )
        await db.admins.insert_one(default_admin.dict())
        print("Default admin created: username=admin, password=admin123")

# Routes
@api_router.get("/")
async def root():
    return {"message": "Mountain Convenience Store API"}

# Admin Authentication Routes
@api_router.post("/admin/login")
async def admin_login(login_data: AdminLogin):
    admin = await db.admins.find_one({"username": login_data.username})
    if not admin or not verify_password(login_data.password, admin["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Return simple token (username) - in production use JWT
    return {"token": admin["username"], "admin": {"username": admin["username"], "email": admin["email"]}}

@api_router.post("/admin/register")
async def admin_register(admin_data: AdminCreate):
    existing_admin = await db.admins.find_one({"username": admin_data.username})
    if existing_admin:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    new_admin = Admin(
        username=admin_data.username,
        email=admin_data.email,
        password_hash=hash_password(admin_data.password)
    )
    await db.admins.insert_one(new_admin.dict())
    return {"message": "Admin created successfully"}

# Category Routes
@api_router.get("/categories", response_model=List[Category])
async def get_categories():
    categories = await db.categories.find().to_list(1000)
    return [Category(**cat) for cat in categories]

@api_router.post("/categories", response_model=Category)
async def create_category(category_data: CategoryCreate, admin: Admin = Depends(get_current_admin)):
    category = Category(**category_data.dict())
    await db.categories.insert_one(category.dict())
    return category

# Product Routes
@api_router.get("/products", response_model=List[Product])
async def get_products(category: Optional[str] = None, active_only: bool = True):
    query = {}
    if category:
        query["category"] = category
    if active_only:
        query["is_active"] = True
    
    products = await db.products.find(query).to_list(1000)
    return [Product(**product) for product in products]

@api_router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    product = await db.products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product(**product)

@api_router.post("/products", response_model=Product)
async def create_product(product_data: ProductCreate, admin: Admin = Depends(get_current_admin)):
    product = Product(**product_data.dict())
    await db.products.insert_one(product.dict())
    return product

@api_router.put("/products/{product_id}", response_model=Product)
async def update_product(product_id: str, product_data: ProductUpdate, admin: Admin = Depends(get_current_admin)):
    existing_product = await db.products.find_one({"id": product_id})
    if not existing_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = {k: v for k, v in product_data.dict().items() if v is not None}
    await db.products.update_one({"id": product_id}, {"$set": update_data})
    
    updated_product = await db.products.find_one({"id": product_id})
    return Product(**updated_product)

@api_router.delete("/products/{product_id}")
async def delete_product(product_id: str, admin: Admin = Depends(get_current_admin)):
    result = await db.products.delete_one({"id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}

# Order Routes
@api_router.post("/orders", response_model=Order)
async def create_order(order_data: OrderCreate):
    # Calculate delivery fee based on address
    delivery_fee = 0.0
    delivery_address = await db.delivery_addresses.find_one({
        "address": {"$regex": order_data.customer_info.address, "$options": "i"},
        "is_active": True
    })
    if delivery_address:
        delivery_fee = delivery_address["delivery_fee"]
    
    # Calculate total
    total_amount = sum(item.subtotal for item in order_data.items) + delivery_fee
    
    # Create order
    order = Order(
        customer_info=order_data.customer_info,
        items=order_data.items,
        total_amount=total_amount,
        delivery_fee=delivery_fee,
        notes=order_data.notes
    )
    
    await db.orders.insert_one(order.dict())
    return order

@api_router.get("/orders", response_model=List[Order])
async def get_orders(admin: Admin = Depends(get_current_admin)):
    orders = await db.orders.find().sort("created_at", -1).to_list(1000)
    return [Order(**order) for order in orders]

@api_router.get("/orders/{order_id}", response_model=Order)
async def get_order(order_id: str):
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return Order(**order)

@api_router.put("/orders/{order_id}", response_model=Order)
async def update_order(order_id: str, order_data: OrderUpdate, admin: Admin = Depends(get_current_admin)):
    existing_order = await db.orders.find_one({"id": order_id})
    if not existing_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    update_data = {k: v for k, v in order_data.dict().items() if v is not None}
    await db.orders.update_one({"id": order_id}, {"$set": update_data})
    
    updated_order = await db.orders.find_one({"id": order_id})
    return Order(**updated_order)

# Delivery Address Routes
@api_router.post("/delivery-addresses", response_model=DeliveryAddress)
async def create_delivery_address(address_data: DeliveryAddressCreate, admin: Admin = Depends(get_current_admin)):
    address = DeliveryAddress(**address_data.dict())
    await db.delivery_addresses.insert_one(address.dict())
    return address

@api_router.get("/delivery-addresses", response_model=List[DeliveryAddress])
async def get_delivery_addresses(admin: Admin = Depends(get_current_admin)):
    addresses = await db.delivery_addresses.find().to_list(1000)
    return [DeliveryAddress(**addr) for addr in addresses]

@api_router.post("/check-delivery")
async def check_delivery_availability(request: AddressCheckRequest):
    # Check if we deliver to this address
    delivery_address = await db.delivery_addresses.find_one({
        "address": {"$regex": request.address, "$options": "i"},
        "is_active": True
    })
    
    if delivery_address:
        return {
            "available": True,
            "delivery_fee": delivery_address["delivery_fee"],
            "zone": delivery_address["zone"],
            "message": f"Great! We deliver to your area. Delivery fee: ${delivery_address['delivery_fee']:.2f}"
        }
    else:
        return {
            "available": False,
            "delivery_fee": 0.0,
            "zone": None,
            "message": "Sorry, we don't currently deliver to this address. Please contact us to discuss delivery options."
        }

# Initialize default categories and addresses
@api_router.post("/init-data")
async def init_default_data():
    # Check if categories exist
    existing_categories = await db.categories.count_documents({})
    if existing_categories == 0:
        default_categories = [
            Category(name="Snacks", description="Chips, crackers, and other snacks"),
            Category(name="Drinks", description="Sodas, water, energy drinks"),
            Category(name="Candy", description="Chocolate, gum, and candy"),
            Category(name="Household", description="Basic household items")
        ]
        for category in default_categories:
            await db.categories.insert_one(category.dict())
    
    # Check if delivery addresses exist
    existing_addresses = await db.delivery_addresses.count_documents({})
    if existing_addresses == 0:
        default_addresses = [
            DeliveryAddress(address="123 Mountain View Drive", zone="Zone A", delivery_fee=2.99),
            DeliveryAddress(address="456 Peak Road", zone="Zone A", delivery_fee=2.99),
            DeliveryAddress(address="789 Summit Lane", zone="Zone B", delivery_fee=4.99),
            DeliveryAddress(address="321 Ridge Street", zone="Zone B", delivery_fee=4.99),
            DeliveryAddress(address="654 Valley View", zone="Zone C", delivery_fee=6.99)
        ]
        for address in default_addresses:
            await db.delivery_addresses.insert_one(address.dict())
    
    await init_default_admin()
    return {"message": "Default data initialized"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    await init_default_admin()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
