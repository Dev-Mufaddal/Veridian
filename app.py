# ======================================
# FLASK APPLICATION - MAIN FILE
# ======================================
# This is the main Flask application file
# It handles all routes (login, register, logout, dashboard)

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import config
import re
import os
from PIL import Image
import io
import razorpay
import hashlib
import hmac

# Create Flask application
app = Flask(__name__)

# Secret key for session management (change this to a random string)
# This key is used to encrypt session data
app.secret_key = 'your_secret_key_change_this_12345'

# ======================================
# RAZORPAY PAYMENT GATEWAY CONFIGURATION
# ======================================
# Add your Razorpay API keys here
# Get these from: https://dashboard.razorpay.com/app/keys
RAZORPAY_KEY_ID = 'rzp_test_SaGwdxC2nNrJHg'  # Replace with your API key
RAZORPAY_KEY_SECRET = 'E0wo3EELRQ6U64QVFx0eL8T6'  # Replace with your API secret

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# ======================================
# FILE UPLOAD CONFIGURATION
# ======================================

# Folder to store uploaded images
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'products')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# ======================================
# HELPER FUNCTIONS
# ======================================

# ======================================
# HELPER FUNCTIONS
# ======================================

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_product_image(file):
    """
    Save uploaded product image
    Compresses and optimizes image before saving
    Returns filename if successful, None if failed
    """
    if not file or file.filename == '':
        return None
    
    if not allowed_file(file.filename):
        return None
    
    try:
        # Get file content
        file.seek(0)
        img = Image.open(file)
        
        # Convert RGBA to RGB if necessary (for JPEG compatibility)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Resize image if too large (max 800x800)
        img.thumbnail((800, 800), Image.Resampling.LANCZOS)
        
        # Generate unique filename
        import time
        filename = f"product_{int(time.time())}_{secure_filename(file.filename)}"
        
        # Save image
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        img.save(filepath, quality=85, optimize=True)
        
        return filename
    except Exception as e:
        print(f"Error saving image: {e}")
        return None

def login_required(f):
    """
    Decorator to protect routes that require login
    If user is not logged in, they are redirected to login page
    Usage: @login_required
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def validate_email(email):
    """Validate if email format is correct"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}₹'
    return re.match(pattern, email) is not None

def user_exists(email_or_username):
    """Check if user already exists in database"""
    try:
        connection = config.get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            # Check if email or username already exists
            query = "SELECT id FROM users WHERE email = %s OR username = %s"
            cursor.execute(query, (email_or_username, email_or_username))
            
            result = cursor.fetchone()
            cursor.close()
            config.close_db_connection(connection)
            
            return result is not None  # Return True if user exists
        return False
    except Exception as e:
        print(f"Error checking user: {e}")
        return False

def admin_required(f):
    """
    Decorator to protect routes that require admin access
    Checks if user_id is in session AND user has admin role
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        # Check if user is admin
        try:
            connection = config.get_db_connection()
            if connection:
                cursor = connection.cursor(dictionary=True)
                query = "SELECT role FROM users WHERE id = %s"
                cursor.execute(query, (session['user_id'],))
                user = cursor.fetchone()
                cursor.close()
                config.close_db_connection(connection)
                
                if user and user['role'] == 'admin':
                    return f(*args, **kwargs)
        except Exception as e:
            print(f"Error checking admin status: {e}")
        
        return redirect(url_for('dashboard'))  # Not admin, go to dashboard
    return decorated_function

def get_user_by_id(user_id):
    """Get user information by ID"""
    try:
        connection = config.get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            query = "SELECT id, username, email, role FROM users WHERE id = %s"
            cursor.execute(query, (user_id,))
            user = cursor.fetchone()
            cursor.close()
            config.close_db_connection(connection)
            return user
        return None
    except Exception as e:
        print(f"Error getting user: {e}")
        return None

# ======================================
# ROUTES
# ======================================

@app.route('/')
def home():
    """
    Home page route
    If user is logged in, redirect to dashboard
    If not, redirect to login
    """
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    User Registration Route
    GET: Shows registration form
    POST: Processes registration data
    """
    if request.method == 'POST':
        # Get data from registration form
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        # Input validation
        if not username or not email or not password:
            return render_template('register.html', error='All fields are required')
        
        if len(username) < 3:
            return render_template('register.html', error='Username must be at least 3 characters')
        
        if len(password) < 6:
            return render_template('register.html', error='Password must be at least 6 characters')
        
        if not validate_email(email):
            return render_template('register.html', error='Invalid email format')
        
        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')
        
        if user_exists(email):
            return render_template('register.html', error='Email already registered')
        
        if user_exists(username):
            return render_template('register.html', error='Username already taken')
        
        try:
            # Hash the password for security
            # generate_password_hash creates a secure hash of the password
            hashed_password = generate_password_hash(password)
            
            # Connect to database
            connection = config.get_db_connection()
            if connection:
                cursor = connection.cursor()
                
                # Insert new user into database
                query = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
                cursor.execute(query, (username, email, hashed_password))
                
                # Commit changes to database
                connection.commit()
                
                cursor.close()
                config.close_db_connection(connection)
                
                # Redirect to login page with success message
                return redirect(url_for('login', message='Registration successful! Please log in.'))
            else:
                return render_template('register.html', error='Database connection failed')
                
        except Exception as e:
            print(f"Error during registration: {e}")
            return render_template('register.html', error='An error occurred. Please try again.')
    
    # GET request - show registration form
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    User Login Route
    GET: Shows login form
    POST: Processes login credentials
    """
    if request.method == 'POST':
        # Get login credentials from form
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        # Validate input
        if not email or not password:
            return render_template('login.html', error='Email and password are required')
        
        try:
            # Connect to database
            connection = config.get_db_connection()
            if connection:
                cursor = connection.cursor(dictionary=True)
                
                # Search for user by email
                query = "SELECT id, username, email, password, role FROM users WHERE email = %s"
                cursor.execute(query, (email,))
                
                user = cursor.fetchone()
                cursor.close()
                config.close_db_connection(connection)
                
                if user and check_password_hash(user['password'], password):
                    # Password is correct - create session
                    # Session stores user info without sensitive data
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['email'] = user['email']
                    session['role'] = user['role']  # Store user role in session
                    
                    return redirect(url_for('dashboard'))
                else:
                    # Email not found or password incorrect
                    return render_template('login.html', error='Invalid email or password')
            else:
                return render_template('login.html', error='Database connection failed')
                
        except Exception as e:
            print(f"Error during login: {e}")
            return render_template('login.html', error='An error occurred. Please try again.')
    
    # GET request - show login form
    message = request.args.get('message', None)
    return render_template('login.html', message=message)

@app.route('/dashboard')
@login_required  # Only accessible if user is logged in
def dashboard():
    """
    Dashboard Route
    Shows user profile and welcome message
    Only accessible to logged-in users
    """
    username = session.get('username')
    email = session.get('email')
    return render_template('dashboard.html', username=username, email=email)

@app.route('/logout')
@login_required
def logout():
    """
    Logout Route
    Clears user session and redirects to login page
    """
    # Clear all session data
    session.clear()
    
    return redirect(url_for('login', message='You have been logged out successfully'))

# ======================================
# ADMIN ROUTES
# ======================================

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard with statistics"""
    try:
        connection = config.get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            # Get statistics
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'user'")
            user_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM products")
            product_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM orders")
            order_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT SUM(total_price) as total FROM orders WHERE status = 'completed'")
            total_sales = cursor.fetchone()['total'] or 0
            
            cursor.close()
            config.close_db_connection(connection)
            
            return render_template('admin_dashboard.html',
                                 user_count=user_count,
                                 product_count=product_count,
                                 order_count=order_count,
                                 total_sales=total_sales)
        return redirect(url_for('dashboard'))
    except Exception as e:
        print(f"Error in admin dashboard: {e}")
        return redirect(url_for('dashboard'))

# ======================================
# PRODUCT MANAGEMENT ROUTES (ADMIN)
# ======================================

@app.route('/admin/products')
@admin_required
def admin_products():
    """List all products for admin to manage"""
    try:
        connection = config.get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            query = "SELECT * FROM products ORDER BY created_at DESC"
            cursor.execute(query)
            products = cursor.fetchall()
            cursor.close()
            config.close_db_connection(connection)
            
            return render_template('admin_products.html', products=products)
        return redirect(url_for('dashboard'))
    except Exception as e:
        print(f"Error fetching products: {e}")
        return redirect(url_for('dashboard'))

@app.route('/admin/products/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    """Add new product (admin only)"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price = request.form.get('price', '').strip()
        stock = request.form.get('stock', '0').strip()
        file = request.files.get('image')
        
        # Validate
        if not name or not price:
            return render_template('admin_products_add.html', error='Name and price are required')
        
        try:
            price = float(price)
            stock = int(stock)
            
            if price < 0 or stock < 0:
                return render_template('admin_products_add.html', error='Price and stock must be positive')
            
            # Handle image upload
            image_filename = None
            if file and file.filename != '':
                if not allowed_file(file.filename):
                    return render_template('admin_products_add.html', error='Only image files are allowed (PNG, JPG, GIF, WebP)')
                
                image_filename = save_product_image(file)
                if not image_filename:
                    return render_template('admin_products_add.html', error='Failed to save image')
            
            connection = config.get_db_connection()
            if connection:
                cursor = connection.cursor()
                query = "INSERT INTO products (name, description, price, stock, image_url) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(query, (name, description, price, stock, image_filename))
                connection.commit()
                cursor.close()
                config.close_db_connection(connection)
                
                return redirect(url_for('admin_products'))
            return render_template('admin_products_add.html', error='Database connection failed')
        except ValueError:
            return render_template('admin_products_add.html', error='Invalid price or stock value')
        except Exception as e:
            print(f"Error adding product: {e}")
            return render_template('admin_products_add.html', error='An error occurred')
    
    return render_template('admin_products_add.html')

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    """Edit product details with optional image update"""
    connection = config.get_db_connection()
    if not connection:
        return redirect(url_for('admin_products'))
    
    cursor = connection.cursor(dictionary=True)
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price = request.form.get('price', '').strip()
        stock = request.form.get('stock', '0').strip()
        
        if not name or not price:
            cursor.close()
            config.close_db_connection(connection)
            return render_template('admin_products_edit.html', error='Name and price are required', product_id=product_id)
        
        try:
            price = float(price)
            stock = int(stock)
            
            # Get current product to retrieve existing image
            query = "SELECT image_url FROM products WHERE id = %s"
            cursor.execute(query, (product_id,))
            current_product = cursor.fetchone()
            image_url = current_product['image_url'] if current_product else None
            
            # Handle image upload if provided
            file = request.files.get('image')
            if file and file.filename:
                if allowed_file(file.filename):
                    image_url = save_product_image(file)
                else:
                    cursor.close()
                    config.close_db_connection(connection)
                    return render_template('admin_products_edit.html', error='Invalid file type. Allowed: png, jpg, jpeg, gif, webp', product_id=product_id)
            
            # Update product with optional image_url
            query = "UPDATE products SET name = %s, description = %s, price = %s, stock = %s, image_url = %s WHERE id = %s"
            cursor.execute(query, (name, description, price, stock, image_url, product_id))
            connection.commit()
            cursor.close()
            config.close_db_connection(connection)
            
            return redirect(url_for('admin_products'))
        except Exception as e:
            print(f"Error updating product: {e}")
            cursor.close()
            config.close_db_connection(connection)
            return render_template('admin_products_edit.html', error='An error occurred', product_id=product_id)
    
    # GET request - show current product details
    query = "SELECT * FROM products WHERE id = %s"
    cursor.execute(query, (product_id,))
    product = cursor.fetchone()
    cursor.close()
    config.close_db_connection(connection)
    
    if not product:
        return redirect(url_for('admin_products'))
    
    return render_template('admin_products_edit.html', product=product)

@app.route('/admin/products/delete/<int:product_id>')
@admin_required
def delete_product(product_id):
    """Delete a product"""
    try:
        connection = config.get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            # First delete from cart and order_items
            cursor.execute("DELETE FROM cart WHERE product_id = %s", (product_id,))
            cursor.execute("DELETE FROM order_items WHERE product_id = %s", (product_id,))
            
            # Then delete product
            cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
            connection.commit()
            cursor.close()
            config.close_db_connection(connection)
        
        return redirect(url_for('admin_products'))
    except Exception as e:
        print(f"Error deleting product: {e}")
        return redirect(url_for('admin_products'))

# ======================================
# USER MANAGEMENT ROUTES (ADMIN)
# ======================================

@app.route('/admin/users')
@admin_required
def admin_users():
    """List all users for admin to manage"""
    try:
        connection = config.get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            query = "SELECT id, username, email, role, created_at FROM users ORDER BY created_at DESC"
            cursor.execute(query)
            users = cursor.fetchall()
            cursor.close()
            config.close_db_connection(connection)
            
            return render_template('admin_users.html', users=users)
        return redirect(url_for('dashboard'))
    except Exception as e:
        print(f"Error fetching users: {e}")
        return redirect(url_for('dashboard'))

@app.route('/admin/users/delete/<int:user_id>')
@admin_required
def delete_user(user_id):
    """Delete a user (admin cannot delete self)"""
    if user_id == session.get('user_id'):
        return redirect(url_for('admin_users'))  # Can't delete yourself
    
    try:
        connection = config.get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            # Delete related data first
            cursor.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM orders WHERE user_id = %s", (user_id,))
            
            # Then delete user
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            connection.commit()
            cursor.close()
            config.close_db_connection(connection)
        
        return redirect(url_for('admin_users'))
    except Exception as e:
        print(f"Error deleting user: {e}")
        return redirect(url_for('admin_users'))

@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """Edit user details (change role)"""
    connection = config.get_db_connection()
    if not connection:
        return redirect(url_for('admin_users'))
    
    cursor = connection.cursor(dictionary=True)
    
    if request.method == 'POST':
        role = request.form.get('role', 'user')
        
        if role not in ['user', 'admin']:
            role = 'user'
        
        try:
            query = "UPDATE users SET role = %s WHERE id = %s"
            cursor.execute(query, (role, user_id))
            connection.commit()
            cursor.close()
            config.close_db_connection(connection)
            
            return redirect(url_for('admin_users'))
        except Exception as e:
            print(f"Error updating user: {e}")
            cursor.close()
            config.close_db_connection(connection)
            return redirect(url_for('admin_users'))
    
    query = "SELECT id, username, email, role FROM users WHERE id = %s"
    cursor.execute(query, (user_id,))
    user = cursor.fetchone()
    cursor.close()
    config.close_db_connection(connection)
    
    if not user:
        return redirect(url_for('admin_users'))
    
    return render_template('admin_users_edit.html', user=user)

# ======================================
# PUBLIC PRODUCT ROUTES
# ======================================

@app.route('/products')
def products():
    """Display all products for users to browse"""
    try:
        connection = config.get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            query = "SELECT * FROM products WHERE stock > 0 ORDER BY created_at DESC"
            cursor.execute(query)
            products = cursor.fetchall()
            cursor.close()
            config.close_db_connection(connection)
            
            return render_template('products.html', products=products)
        return render_template('products.html', products=[])
    except Exception as e:
        print(f"Error fetching products: {e}")
        return render_template('products.html', products=[])

# ======================================
# CART ROUTES
# ======================================

@app.route('/cart')
@login_required
def view_cart():
    """View shopping cart"""
    try:
        connection = config.get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            # Get cart items with product details
            query = """
                SELECT c.id, c.product_id, c.quantity, p.name, p.price, p.stock
                FROM cart c
                JOIN products p ON c.product_id = p.id
                WHERE c.user_id = %s
                ORDER BY c.created_at DESC
            """
            cursor.execute(query, (session['user_id'],))
            cart_items = cursor.fetchall()
            
            # Calculate totals
            total_price = sum(item['quantity'] * item['price'] for item in cart_items)
            
            cursor.close()
            config.close_db_connection(connection)
            
            return render_template('cart.html', cart_items=cart_items, total_price=total_price)
        return render_template('cart.html', cart_items=[], total_price=0)
    except Exception as e:
        print(f"Error loading cart: {e}")
        return render_template('cart.html', cart_items=[], total_price=0)

@app.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    """Add product to cart and redirect to cart page"""
    quantity = request.form.get('quantity', 1)
    
    try:
        quantity = int(quantity)
        if quantity < 1:
            quantity = 1
    except:
        quantity = 1
    
    try:
        connection = config.get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            # Check if product exists and has stock
            cursor.execute("SELECT stock FROM products WHERE id = %s", (product_id,))
            product = cursor.fetchone()
            
            if not product or product['stock'] < quantity:
                return redirect(url_for('products'))
            
            # Check if item already in cart
            cursor.execute("SELECT id, quantity FROM cart WHERE user_id = %s AND product_id = %s",
                         (session['user_id'], product_id))
            existing = cursor.fetchone()
            
            if existing:
                # Update quantity
                new_quantity = existing['quantity'] + quantity
                cursor.execute("UPDATE cart SET quantity = %s WHERE id = %s",
                             (new_quantity, existing['id']))
            else:
                # Add new item
                cursor.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (%s, %s, %s)",
                             (session['user_id'], product_id, quantity))
            
            connection.commit()
            cursor.close()
            config.close_db_connection(connection)
            
            # Redirect directly to shopping cart page
            return redirect(url_for('view_cart'))
        return redirect(url_for('view_cart'))
    except Exception as e:
        print(f"Error adding to cart: {e}")
        return redirect(url_for('view_cart'))

@app.route('/cart/remove/<int:cart_item_id>')
@login_required
def remove_from_cart(cart_item_id):
    """Remove item from cart"""
    try:
        connection = config.get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            # Delete item (verify it belongs to user for security)
            cursor.execute("DELETE FROM cart WHERE id = %s AND user_id = %s",
                         (cart_item_id, session['user_id']))
            connection.commit()
            cursor.close()
            config.close_db_connection(connection)
        
        return redirect(url_for('view_cart'))
    except Exception as e:
        print(f"Error removing from cart: {e}")
        return redirect(url_for('view_cart'))

# ======================================
# CHECKOUT & ORDER ROUTES
# ======================================

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """Checkout page - just display cart items for review"""
    try:
        connection = config.get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            query = """
                SELECT c.product_id, c.quantity, p.name, p.price
                FROM cart c
                JOIN products p ON c.product_id = p.id
                WHERE c.user_id = %s
            """
            cursor.execute(query, (session['user_id'],))
            cart_items = cursor.fetchall()
            total_price = sum(item['quantity'] * item['price'] for item in cart_items)
            
            cursor.close()
            config.close_db_connection(connection)
            
            if not cart_items:
                return render_template('checkout.html', error='Your cart is empty')
            
            return render_template('checkout.html', cart_items=cart_items, total_price=total_price)
        return render_template('checkout.html', error='Database connection failed')
    except Exception as e:
        print(f"Error loading checkout: {e}")
        return render_template('checkout.html', error='An error occurred')


@app.route('/process-payment', methods=['POST'])
@login_required
def process_payment():
    """
    Process payment initiation with Razorpay
    Supports multiple payment methods:
    - Credit Card
    - Debit Card
    - UPI (Unified Payments Interface)
    - Digital Wallets (Apple Pay, Google Pay)
    - Net Banking
    """
    try:
        data = request.get_json()
        
        # Get cart items
        connection = config.get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            query = """
                SELECT c.product_id, c.quantity, p.price, p.stock
                FROM cart c
                JOIN products p ON c.product_id = p.id
                WHERE c.user_id = %s
            """
            cursor.execute(query, (session['user_id'],))
            cart_items = cursor.fetchall()
            
            if not cart_items:
                cursor.close()
                config.close_db_connection(connection)
                return jsonify({'error': 'Cart is empty'}), 400
            
            # Calculate total
            total_price = sum(item['quantity'] * item['price'] for item in cart_items)
            amount_in_paise = int(total_price * 100)  # Razorpay expects amount in paise
            
            # Create Razorpay order with support for multiple payment methods
            razorpay_order = razorpay_client.order.create({
                'amount': amount_in_paise,
    'currency': 'INR',   # FIXED
    'payment_capture': 1
            })
            
            # Store shipping data in session for later use
            session['shipping_data'] = data
            session['razorpay_order_id'] = razorpay_order['id']
            
            cursor.close()
            config.close_db_connection(connection)
            
            return jsonify({
                'razorpay_key_id': RAZORPAY_KEY_ID,
                'amount': amount_in_paise,
                'currency': 'INR',
                'order_id': razorpay_order['id'],
                'success': True
            })
        
        return jsonify({'error': 'Database connection failed'}), 500
    except Exception as e:
        print(f"Error processing payment: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/verify-payment', methods=['POST'])
@login_required
def verify_payment():

    try:

        data = request.get_json()

        razorpay_payment_id = data['razorpay_payment_id']
        razorpay_order_id = data['razorpay_order_id']
        razorpay_signature = data['razorpay_signature']
        shipping_data = data['shipping_data']

        # verify signature
        message = f"{razorpay_order_id}|{razorpay_payment_id}"

        generated_signature = hmac.new(
            RAZORPAY_KEY_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        if generated_signature != razorpay_signature:

            return jsonify({
                "success": False
            })


        connection = config.get_db_connection()
        cursor = connection.cursor(dictionary=True)


        # get cart items
        cursor.execute("""

            SELECT c.product_id,
                   c.quantity,
                   p.price,
                   p.name

            FROM cart c

            JOIN products p
            ON c.product_id = p.id

            WHERE c.user_id = %s

        """, (session['user_id'],))

        cart_items = cursor.fetchall()


        # calculate total
        total_price = sum(
            item['price'] * item['quantity']
            for item in cart_items
        )


        # create order
        cursor.execute("""

            INSERT INTO orders (
                user_id,
                total_price,
                status,
                payment_id
            )

            VALUES (%s,%s,%s,%s)

        """, (

            session['user_id'],
            total_price,
            "completed",
            razorpay_payment_id

        ))


        order_id = cursor.lastrowid


        # insert order items
        for item in cart_items:

            cursor.execute("""

                INSERT INTO order_items (
                    order_id,
                    product_id,
                    quantity,
                    price
                )

                VALUES (%s,%s,%s,%s)

            """, (

                order_id,
                item['product_id'],
                item['quantity'],
                item['price']

            ))


        # clear cart
        cursor.execute("""

            DELETE FROM cart
            WHERE user_id = %s

        """, (session['user_id'],))


        connection.commit()

        cursor.close()
        config.close_db_connection(connection)


        return jsonify({

            "success": True,
            "redirect_url": url_for("order_history")

        })


    except Exception as e:

        print("VERIFY ERROR:", e)

        return jsonify({

            "success": False

        })
    

@app.route('/orders')
@login_required
def order_history():

    connection = config.get_db_connection()

    # buffered=True prevents unread result error
    cursor = connection.cursor(dictionary=True, buffered=True)


    # get orders
    cursor.execute("""

        SELECT *

        FROM orders

        WHERE user_id = %s

        ORDER BY id DESC

    """, (session['user_id'],))

    orders = cursor.fetchall()


    # fetch items for each order
    for order in orders:

        item_cursor = connection.cursor(dictionary=True)

        item_cursor.execute("""

            SELECT
                oi.quantity,
                oi.price,
                p.name

            FROM order_items oi

            JOIN products p
            ON oi.product_id = p.id

            WHERE oi.order_id = %s

        """, (order['id'],))

        order['items'] = item_cursor.fetchall()

        item_cursor.close()


    cursor.close()
    config.close_db_connection(connection)


    return render_template(

        "order_history.html",

        orders=orders

    )
# ======================================
# ERROR HANDLERS
# ======================================

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors (page not found)"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors (server error)"""
    return render_template('500.html'), 500

# ======================================
# RUN APPLICATION
# ======================================

if __name__ == '__main__':
    # Run Flask development server
    # debug=True: auto-reloads on code changes, shows detailed error messages
    # host='0.0.0.0': accessible from any IP
    # port=5000: the port where app runs (access at http://localhost:5000)
    app.run(debug=True, host='0.0.0.0', port=5000)
