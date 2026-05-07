from pymongo import MongoClient
from datetime import datetime

# MongoDB Connection
MONGODB_URI = "mongodb+srv://mufaddalabbaskanchwala99_db_user:Y87BEVtviIx5ZPGj@cluster0.bprreem.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGODB_URI)
db = client["veridian"]

# Collections
users = db["users"]
products = db["products"]
cart = db["cart"]
orders = db["orders"]

# Create indexes for better performance
users.create_index("email", unique=True)
users.create_index("username", unique=True)
products.create_index("name")
cart.create_index([("user_id", 1), ("product_id", 1)])
orders.create_index("user_id")