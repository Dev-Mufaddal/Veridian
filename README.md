# 🌿 Veridian

> **Verified Identity. Trusted Access. Seamless Commerce.**

Veridian is a secure, full-stack web application built with Flask, combining robust user authentication with a complete e-commerce experience. From registration to checkout, Veridian ensures every interaction is protected, validated, and seamless.

---

## 📌 Overview

Veridian was designed to demonstrate end-to-end implementation of authentication workflows integrated with a fully functional shopping platform. It features a clean admin interface, secure user flows, and real payment processing — all built on a modular, maintainable Flask architecture.

Whether you're a developer exploring auth systems or looking for a reference implementation of a Flask-based e-commerce app, Veridian provides a solid, production-minded foundation.

---

## 🚀 Key Features

### 👤 User Authentication
- Secure registration and login system
- Password hashing using industry-standard algorithms
- Session management with Flask
- Client-side and server-side form validation
- Alert feedback for login errors, success, and validation issues
- Protected routes for authenticated users only

### 🛒 E-Commerce
- Product listing and browsing
- Shopping cart with dynamic item management
- Checkout flow with **Razorpay** payment integration
- Order history and tracking per user

### 🛠️ Admin Dashboard
- User management (view, edit)
- Product management (add, edit, delete)
- Centralized admin control panel

### ⚙️ System & Architecture
- Modular Flask backend with clean route separation
- Parameterized SQL queries to prevent injection attacks
- Jinja2 templating for dynamic HTML rendering
- Responsive UI with Bootstrap 5
- Organized static assets (CSS, JS, images)
- Structured error handling (404, 500 pages)

---

## 🛠️ Tech Stack

| Technology     | Purpose                                              |
|----------------|------------------------------------------------------|
| **Python**     | Core backend language                                |
| **Flask**      | Web framework — routing, sessions, server logic      |
| **MySQL**      | Relational database for users, products, orders      |
| **Jinja2**     | Server-side HTML templating                          |
| **Bootstrap 5**| Responsive, mobile-first UI components               |
| **JavaScript** | Client-side validation and interactivity             |
| **HTML5/CSS3** | Page structure and custom styling                    |
| **Razorpay**   | Payment gateway integration                          |

---

## 📂 Project Structure

```
Veridian/
├── static/
│   ├── css/               # Custom stylesheets
│   ├── js/                # Client-side scripts
│   └── images/            # Static image assets
│
├── templates/
│   ├── base.html          # Base layout template
│   ├── login.html         # Login page
│   ├── register.html      # Registration page
│   ├── dashboard.html     # User dashboard
│   ├── products.html      # Product listing
│   ├── cart.html          # Shopping cart
│   ├── checkout.html      # Checkout & payment
│   ├── order_history.html # Order history
│   ├── admin_dashboard.html
│   ├── admin_products.html
│   ├── admin_products_add.html
│   ├── admin_products_edit.html
│   ├── admin_users.html
│   ├── admin_users_edit.html
│   ├── 404.html
│   └── 500.html
│
├── app.py                 # Application entry point & routes
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
└── README.md
```

---

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Dev-Mufaddal/Veridian.git
cd AuthOra
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

### 3. Activate the Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**macOS / Linux:**
```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure the Database

- Ensure MySQL is running locally.
- Update `config.py` with your MySQL credentials and database name.
- Create the required tables by running the app or executing your schema SQL.

### 6. Run the Application

```bash
python app.py
```

Visit `http://localhost:5000` in your browser.

---

## 🌐 Application Routes

| Route        | Description                          | Access        |
|--------------|--------------------------------------|---------------|
| `/`          | Home page                            | Public        |
| `/register`  | User registration                    | Public        |
| `/login`     | User login                           | Public        |
| `/dashboard` | User dashboard                       | Authenticated |
| `/shop`      | Browse products                      | Authenticated |
| `/cart`      | View and manage cart                 | Authenticated |
| `/checkout`  | Checkout with Razorpay payment       | Authenticated |
| `/orders`    | View order history                   | Authenticated |
| `/logout`    | End session and log out              | Authenticated |
| `/admin`     | Admin control panel                  | Admin only    |

---

## 🔒 Security Practices

- **Password Hashing** — Passwords are never stored in plain text.
- **Session Authentication** — Flask sessions protect access to sensitive routes.
- **Parameterized Queries** — All database interactions use parameterized statements to prevent SQL injection.
- **Route Protection** — Unauthenticated users are redirected away from protected pages.
- **Input Validation** — Both client-side (JS) and server-side (Flask) validation in place.

---

## 📈 Roadmap & Future Improvements

- [ ] Email verification on registration
- [ ] Password reset via email
- [ ] OAuth2 / social login (Google, GitHub)
- [ ] JWT-based API authentication
- [ ] Product search and filtering
- [ ] Inventory management in admin panel
- [ ] Deployment guide (Docker / cloud)

---

## 🎯 Learning Objectives

This project demonstrates practical understanding of:

- Flask application architecture and routing
- Authentication workflow design and security best practices
- MySQL database integration with Python
- Session handling and protected route patterns
- Responsive frontend development with Bootstrap
- Payment gateway integration (Razorpay)
- Modular, scalable project structure

---

## 👨‍💻 Author

**Mufaddal Kanchwala**
GitHub: [@Dev-Mufaddal](https://github.com/Dev-Mufaddal)

---

## 📜 License

This project is created for educational and portfolio purposes.

---

⭐ If you found this project useful or interesting, consider starring the repository!
