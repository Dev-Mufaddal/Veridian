# ======================================
# DATABASE CONFIGURATION FILE
# ======================================
# This file contains all database credentials
# Change these values according to your MySQL setup

import mysql.connector
from mysql.connector import Error

# DATABASE CREDENTIALS - Update these with your MySQL credentials
DB_HOST = "localhost"        # MySQL server address (usually localhost)
DB_USER = "root"             # MySQL username
DB_PASSWORD = "root"         # MySQL password
DB_NAME = "flask_auth_db"    # Database name

# Function to establish database connection
def get_db_connection():
    """
    Creates and returns a connection to the MySQL database
    This function is called whenever we need to interact with the database
    """
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        if connection.is_connected():
            print("✓ Successfully connected to MySQL database")
            return connection
    except Error as e:
        print(f"✗ Error while connecting to MySQL: {e}")
        return None

# Function to close database connection
def close_db_connection(connection):
    """
    Safely closes the database connection
    Always call this after finishing database operations
    """
    if connection and connection.is_connected():
        connection.close()
        print("✓ Database connection closed")
