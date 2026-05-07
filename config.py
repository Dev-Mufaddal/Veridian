# ======================================
# DATABASE CONFIGURATION FILE - MONGODB
# ======================================
# This file contains MongoDB credentials and connection settings

from pymongo import MongoClient

# MONGODB CONNECTION STRING
# Update with your MongoDB connection string
MONGODB_URI = "mongodb+srv://mufaddalabbaskanchwala99_db_user:Y87BEVtviIx5ZPGj@cluster0.bprreem.mongodb.net/?appName=Cluster0"
DB_NAME = "veridian"

# Initialize MongoDB client and database
client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

# Database collections
users = db["users"]
products = db["products"]
cart = db["cart"]
orders = db["orders"]
order_items = db["order_items"]

# ======================================
# RAZORPAY PAYMENT GATEWAY CONFIGURATION
# ======================================
# Get these from: https://dashboard.razorpay.com/app/keys
RAZORPAY_KEY_ID = "rzp_test_SaGwdxC2nNrJHg"        # Replace with your API key
RAZORPAY_KEY_SECRET = "E0wo3EELRQ6U64QVFx0eL8T6"   # Replace with your API secret
