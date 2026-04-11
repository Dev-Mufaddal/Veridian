# 🔐 Veridian

Veridian is a secure and modern authentication system developed using Flask. It implements core user identity management features including registration, login, logout, and session handling, integrated with a MySQL (localhost) database for persistent storage.

The application follows a structured backend architecture and includes a clean, responsive user interface, demonstrating best practices in authentication workflows, database connectivity, and modular Flask development.

---

## 🚀 Key Features

### 👤 User Features

- Secure user registration system
- User login and logout authentication
- Session management using Flask
- Password hashing for secure credential storage
- Alert messages for login success, errors, and validation feedback
- Client-side validation using JavaScript
- Responsive and clean user interface
- Dynamic HTML rendering using Jinja2 templates
- MySQL (localhost) database integration

### 🛠️ System Features

- Structured Flask backend architecture
- CRUD operations for user data
- Server-side form validation
- Secure database queries using parameterized statements
- Modular and scalable template structure
- Organized static assets (CSS, JavaScript, images)
- Error handling and input validation
- Lightweight and maintainable authentication workflow

---

## 🛠️ Tech Stack

| Technology            | Purpose                                                               |
| --------------------- | --------------------------------------------------------------------- |
| **Python**            | Core backend programming language                                     |
| **Flask**             | Lightweight web framework for handling routes and server logic        |
| **MySQL (localhost)** | Relational database for storing user credentials and application data |
| **HTML5**             | Structuring web page content                                          |
| **CSS3**              | Styling and layout design                                             |
| **Bootstrap**         | Responsive and mobile-first UI components                             |
| **JavaScript**        | Client-side interactivity, validation, and dynamic behaviour          |
| **Jinja2**            | Template engine for rendering dynamic HTML                            |

---

## 📂 Project Structure

```bash

AuthOra/
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── templates/
│   ├── 404.html
│   ├── 500.html
│   ├── admin_dashboard.html
│   ├── admin_products_add.html
│   ├── admin_products_edit.html
│   ├── admin_products.html
│   ├── admin_users_edit.html
│   ├── admin_users.html
│   ├── base.html
│   ├── cart.html
│   ├── checkout.html
│   ├── dashboard.html
│   └── login.html
│   └── order_history.html
│   └── products.html
│   └── register.html
│
├── app.py
├── config.py
├── requirements.txt
└── README.md

```

---

## ⚙️ Installation

### Clone repo
```bash
git clone https://github.com/Dev-Mufaddal/AuthOra.git  
cd AuthOra
```  

### Create virtual environment
```bash
python -m venv venv
```  

### Activate (Windows)
```bash
venv\Scripts\activate
```

### Activate (Mac/Linux)
```bash
source venv/bin/activate
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### Run app
```bash
python app.py  
```

---

## 🌐 Routes

- / → Home
- /login → Login Page
- /register → Register Page
- /dashboard → Protected Dashboard
- /shop → Products Page
- /cart → Added Products diplays to Cart
- /checkout → Payment Integration using RazorPay
- /orders → Displays your Orders on this page
- /logout → Logout

---

## 🔒 Security

- Password hashing
- Session authentication
- Protected routes

---

## 📈 Learning Objectives

This project demonstrates understanding of:

- Flask routing & application structure
- Authentication workflow design
- Database connectivity with MySQL
- Session handling in Flask
- Responsive frontend integration
- Modular and maintainable code structure

---

## 📈 Future Improvements

- Email verification
- Password reset

---

## 👨‍💻 Author

Mufaddal Kanchwala  
GitHub: https://github.com/Dev-Mufaddal

---

## 📜 License

This project is created for educational and portfolio purposes.

---

⭐ Star this repo if you like it!
