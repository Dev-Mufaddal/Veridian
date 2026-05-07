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
from db import users, products, cart, orders
from bson import ObjectId
from datetime import datetime
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
RAZORPAY_KEY_ID = config.RAZORPAY_KEY_ID
RAZORPAY_KEY_SECRET = config.RAZORPAY_KEY_SECRET

# Initialize Razorpay client
razorpay_client = None
if razorpay:
    try:
        razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    except Exception as e:
        print(f"Warning: Could not initialize Razorpay client: {e}")
        razorpay = None

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
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def user_exists(email_or_username):
    """Check if user already exists in database"""
    try:
        result = users.find_one({"$or": [{"email": email_or_username}, {"username": email_or_username}]})
        return result is not None
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
            user = users.find_one({"_id": ObjectId(session['user_id'])})
            
            if user and user.get('role') == 'admin':
                return f(*args, **kwargs)
        except Exception as e:
            print(f"Error checking admin status: {e}")
        
        return redirect(url_for('dashboard'))  # Not admin, go to dashboard
    return decorated_function

def get_user_by_id(user_id):
    """Get user information by ID"""
    try:
        user = users.find_one({"_id": ObjectId(user_id)})
        if user:
            return {
                "id": str(user["_id"]),
                "username": user.get("username"),
                "email": user.get("email"),
                "role": user.get("role", "user")
            }
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
            hashed_password = generate_password_hash(password)
            
            # Insert new user into database
            user_data = {
                "username": username,
                "email": email,
                "password": hashed_password,
                "role": "user",
                "created_at": datetime.now()
            }
            
            result = users.insert_one(user_data)
            
            # Redirect to login page with success message
            return redirect(url_for('login', message='Registration successful! Please log in.'))
                
        except Exception as e:
            print(f"Error during registration: {e}")
            return render_template('register.html', error='An error occurred. Please try again.')
    
    # GET request - show registration form
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not email or not password:
            return render_template('login.html', error='Email and password are required')

        try:
            # MongoDB instead of MySQL
            user = users.find_one({"email": email})

            if user and check_password_hash(user['password'], password):

                session['user_id'] = str(user['_id'])
                session['username'] = user['username']
                session['email'] = user['email']
                session['role'] = user.get('role', 'user')

                return redirect(url_for('dashboard'))

            else:
                return render_template('login.html', error='Invalid email or password')

        except Exception as e:
            print(f"Error during login: {e}")
            return render_template('login.html', error='An error occurred. Please try again.')

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
        # Get statistics
        user_count = users.count_documents({"role": "user"})
        product_count = products.count_documents({})
        order_count = orders.count_documents({})
        
        # Calculate total sales
        completed_orders = list(orders.aggregate([
            {"$match": {"status": "completed"}},
            {"$group": {"_id": None, "total": {"$sum": "$total_price"}}}
        ]))
        total_sales = completed_orders[0]["total"] if completed_orders else 0
        
        return render_template('admin_dashboard.html',
                             user_count=user_count,
                             product_count=product_count,
                             order_count=order_count,
                             total_sales=total_sales)
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
        all_products = list(products.find().sort("created_at", -1))
        
        # Convert ObjectId to string for templates
        for p in all_products:
            p['_id'] = str(p['_id'])
        
        return render_template('admin_products.html', products=all_products)
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
            
            product_data = {
                "name": name,
                "description": description,
                "price": price,
                "stock": stock,
                "image_url": image_filename,
                "created_at": datetime.now()
            }
            
            products.insert_one(product_data)
            
            return redirect(url_for('admin_products'))
        except ValueError:
            return render_template('admin_products_add.html', error='Invalid price or stock value')
        except Exception as e:
            print(f"Error adding product: {e}")
            return render_template('admin_products_add.html', error='An error occurred')
    
    return render_template('admin_products_add.html')

@app.route('/admin/products/edit/<product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    """Edit product details with optional image update"""
    try:
        product_obj_id = ObjectId(product_id)
    except:
        return redirect(url_for('admin_products'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price = request.form.get('price', '').strip()
        stock = request.form.get('stock', '0').strip()
        
        if not name or not price:
            return render_template('admin_products_edit.html', error='Name and price are required', product_id=product_id)
        
        try:
            price = float(price)
            stock = int(stock)
            
            # Get current product to retrieve existing image
            current_product = products.find_one({"_id": product_obj_id})
            image_url = current_product['image_url'] if current_product else None
            
            # Handle image upload if provided
            file = request.files.get('image')
            if file and file.filename:
                if allowed_file(file.filename):
                    image_url = save_product_image(file)
                else:
                    return render_template('admin_products_edit.html', error='Invalid file type. Allowed: png, jpg, jpeg, gif, webp', product_id=product_id)
            
            # Update product
            products.update_one(
                {"_id": product_obj_id},
                {"$set": {
                    "name": name,
                    "description": description,
                    "price": price,
                    "stock": stock,
                    "image_url": image_url
                }}
            )
            
            return redirect(url_for('admin_products'))
        except Exception as e:
            print(f"Error updating product: {e}")
            return render_template('admin_products_edit.html', error='An error occurred', product_id=product_id)
    
    # GET request - show current product details
    product = products.find_one({"_id": product_obj_id})
    
    if not product:
        return redirect(url_for('admin_products'))
    
    product['_id'] = str(product['_id'])
    return render_template('admin_products_edit.html', product=product)

@app.route('/admin/products/delete/<product_id>')
@admin_required
def delete_product(product_id):
    """Delete a product"""
    try:
        product_obj_id = ObjectId(product_id)
        
        # Delete from cart and orders
        cart.delete_many({"product_id": product_obj_id})
        
        # Delete product
        products.delete_one({"_id": product_obj_id})
        
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
        all_users = list(users.find().sort("created_at", -1))
        
        # Convert ObjectId to string for templates
        for u in all_users:
            u['_id'] = str(u['_id'])
        
        return render_template('admin_users.html', users=all_users)
    except Exception as e:
        print(f"Error fetching users: {e}")
        return redirect(url_for('dashboard'))

@app.route('/admin/users/delete/<user_id>')
@admin_required
def delete_user(user_id):
    """Delete a user (admin cannot delete self)"""
    if user_id == session.get('user_id'):
        return redirect(url_for('admin_users'))  # Can't delete yourself
    
    try:
        user_obj_id = ObjectId(user_id)
        
        # Delete related data first
        cart.delete_many({"user_id": user_obj_id})
        orders.delete_many({"user_id": user_obj_id})
        
        # Then delete user
        users.delete_one({"_id": user_obj_id})
        
        return redirect(url_for('admin_users'))
    except Exception as e:
        print(f"Error deleting user: {e}")
        return redirect(url_for('admin_users'))

@app.route('/admin/users/edit/<user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """Edit user details (change role)"""
    try:
        user_obj_id = ObjectId(user_id)
    except:
        return redirect(url_for('admin_users'))
    
    if request.method == 'POST':
        role = request.form.get('role', 'user')
        
        if role not in ['user', 'admin']:
            role = 'user'
        
        try:
            users.update_one(
                {"_id": user_obj_id},
                {"$set": {"role": role}}
            )
            
            return redirect(url_for('admin_users'))
        except Exception as e:
            print(f"Error updating user: {e}")
            return redirect(url_for('admin_users'))
    
    user = users.find_one({"_id": user_obj_id})
    
    if not user:
        return redirect(url_for('admin_users'))
    
    user['_id'] = str(user['_id'])
    return render_template('admin_users_edit.html', user=user)

# ======================================
# PUBLIC PRODUCT ROUTES
# ======================================

@app.route('/products')
def products_list():
    """Display all products for users to browse"""
    try:
        all_products = list(products.find({"stock": {"$gt": 0}}).sort("created_at", -1))
        
        # Convert ObjectId to string for templates
        for p in all_products:
            p['_id'] = str(p['_id'])
        
        return render_template('products.html', products=all_products)
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
        user_id = ObjectId(session['user_id'])
        
        # Get cart items with product details
        cart_items_data = list(cart.find({"user_id": user_id}))
        
        cart_items = []
        for item in cart_items_data:
            product = products.find_one({"_id": item["product_id"]})
            if product:
                cart_items.append({
                    "id": str(item["_id"]),
                    "product_id": str(item["product_id"]),
                    "quantity": item["quantity"],
                    "name": product.get("name"),
                    "price": product.get("price"),
                    "stock": product.get("stock")
                })
        
        # Calculate totals
        total_price = sum(item['quantity'] * item['price'] for item in cart_items)
        
        return render_template('cart.html', cart_items=cart_items, total_price=total_price)
    except Exception as e:
        print(f"Error loading cart: {e}")
        return render_template('cart.html', cart_items=[], total_price=0)

@app.route('/cart/add/<product_id>', methods=['POST'])
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
        product_obj_id = ObjectId(product_id)
        user_id = ObjectId(session['user_id'])
        
        # Check if product exists and has stock
        product = products.find_one({"_id": product_obj_id})
        
        if not product or product['stock'] < quantity:
            return redirect(url_for('products_list'))
        
        # Check if item already in cart
        existing = cart.find_one({"user_id": user_id, "product_id": product_obj_id})
        
        if existing:
            # Update quantity
            cart.update_one(
                {"_id": existing["_id"]},
                {"$inc": {"quantity": quantity}}
            )
        else:
            # Add new item
            cart.insert_one({
                "user_id": user_id,
                "product_id": product_obj_id,
                "quantity": quantity,
                "created_at": datetime.now()
            })
        
        # Redirect directly to shopping cart page
        return redirect(url_for('view_cart'))
    except Exception as e:
        print(f"Error adding to cart: {e}")
        return redirect(url_for('view_cart'))

@app.route('/cart/remove/<cart_item_id>')
@login_required
def remove_from_cart(cart_item_id):
    """Remove item from cart"""
    try:
        cart_obj_id = ObjectId(cart_item_id)
        user_id = ObjectId(session['user_id'])
        
        # Delete item (verify it belongs to user for security)
        cart.delete_one({"_id": cart_obj_id, "user_id": user_id})
        
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
        user_id = ObjectId(session['user_id'])
        
        # Get cart items with product details
        cart_items_data = list(cart.find({"user_id": user_id}))
        
        cart_items = []
        for item in cart_items_data:
            product = products.find_one({"_id": item["product_id"]})
            if product:
                cart_items.append({
                    "product_id": str(item["product_id"]),
                    "quantity": item["quantity"],
                    "name": product.get("name"),
                    "price": product.get("price")
                })
        
        total_price = sum(item['quantity'] * item['price'] for item in cart_items)
        
        if not cart_items:
            return render_template('checkout.html', error='Your cart is empty')
        
        return render_template('checkout.html', cart_items=cart_items, total_price=total_price)
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
    if not razorpay_client:
        return jsonify({'error': 'Payment gateway not configured'}), 500
    
    try:
        data = request.get_json()
        user_id = ObjectId(session['user_id'])
        
        # Get cart items
        cart_items_data = list(cart.find({"user_id": user_id}))
        
        if not cart_items_data:
            return jsonify({'error': 'Cart is empty'}), 400
        
        # Calculate total
        total_price = 0
        for item in cart_items_data:
            product = products.find_one({"_id": item["product_id"]})
            if product:
                total_price += item['quantity'] * product['price']
        
        amount_in_paise = int(total_price * 100)  # Razorpay expects amount in paise
        
        # Create Razorpay order with support for multiple payment methods
        razorpay_order = razorpay_client.order.create({
            'amount': amount_in_paise,
            'currency': 'INR',
            'payment_capture': 1
        })
        
        # Store shipping data in session for later use
        session['shipping_data'] = data
        session['razorpay_order_id'] = razorpay_order['id']
        
        return jsonify({
            'razorpay_key_id': config.RAZORPAY_KEY_ID,
            'amount': amount_in_paise,
            'currency': 'INR',
            'order_id': razorpay_order['id'],
            'success': True
        })
        
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
        
        # Verify signature
        message = f"{razorpay_order_id}|{razorpay_payment_id}"
        
        generated_signature = hmac.new(
            config.RAZORPAY_KEY_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if generated_signature != razorpay_signature:
            return jsonify({"success": False})
        
        user_id = ObjectId(session['user_id'])
        
        # Get cart items
        cart_items_data = list(cart.find({"user_id": user_id}))
        
        # Calculate total
        total_price = 0
        order_items = []
        for item in cart_items_data:
            product = products.find_one({"_id": item["product_id"]})
            if product:
                total_price += item['quantity'] * product['price']
                order_items.append({
                    "product_id": item["product_id"],
                    "quantity": item["quantity"],
                    "price": product['price'],
                    "name": product.get("name")
                })
        
        # Create order
        order_data = {
            "user_id": user_id,
            "total_price": total_price,
            "status": "completed",
            "payment_id": razorpay_payment_id,
            "items": order_items,
            "created_at": datetime.now()
        }
        
        result = orders.insert_one(order_data)
        
        # Clear cart
        cart.delete_many({"user_id": user_id})
        
        return jsonify({
            "success": True,
            "redirect_url": url_for("order_history")
        })
        
    except Exception as e:
        print("VERIFY ERROR:", e)
        return jsonify({"success": False})
    

@app.route('/orders')
@login_required
def order_history():
    try:
        user_id = ObjectId(session['user_id'])
        
        # Get orders
        user_orders = list(orders.find({"user_id": user_id}).sort("created_at", -1))
        
        # Format for template
        for order in user_orders:
            order['_id'] = str(order['_id'])
            order['user_id'] = str(order['user_id'])
            for item in order.get('items', []):
                item['product_id'] = str(item.get('product_id', ''))
        
        return render_template("order_history.html", orders=user_orders)
        
    except Exception as e:
        print(f"Error loading orders: {e}")
        return render_template("order_history.html", orders=[])
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
