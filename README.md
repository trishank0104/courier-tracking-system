# courier-tracking-system

________________________________________
📦 Courier Tracking System
A full-stack backend system built using Flask to manage parcel delivery logistics. This platform supports three types of users—Admin, Customer, and Delivery Person—with role-based access to features like order creation, delivery assignment, issue reporting, and real-time tracking.
________________________________________
📘 Project Content
🎯 Objective
To develop a scalable and secure courier tracking backend system that allows:
•	Customers to place and track orders
•	Admins to manage users and orders
•	Delivery persons to update order status and history
🌐 Architecture Overview
•	API-first design using RESTful principles
•	Modular Flask application
•	MySQL database integration
•	Secure authentication using JWT
•	Role-based permission handling
________________________________________
🧠 Project Code Overview
The backend logic is contained in app1.py and structured around key user roles:
🔑 Authentication & User Management
•	POST /signup – Customer registration
•	POST /login – Unified login for all roles
•	POST /register – Admin-only endpoint to register delivery persons or new admins
👤 Admin Functionalities
•	View users: GET /admin/users
•	View orders: GET /admin/orders
•	Assign orders: POST /admin/assign-delivery
•	Delete users: DELETE /admin/delete-user/<user_type>/<user_id>
•	View and respond to issues: GET, PATCH /admin/issues
📦 Customer Functionalities
•	Place an order: POST /customer/place-order
•	Track an order: GET /customer/track-order/<order_id>
•	Raise an issue: POST /raise-issue
•	Submit feedback: POST /customer/feedback
🚚 Delivery Person Functionalities
•	View assigned orders: GET /delivery/assigned-orders
•	Update order status: PATCH /delivery/update-status
•	Update location (optional): PATCH /delivery/update-location
•	View delivery history: GET /delivery/history
All APIs return structured JSON responses and validate user roles through JWT claims.
________________________________________
🛠️ Key Technologies
Technology	Purpose
Flask	Lightweight Python framework for backend APIs
MySQL	Relational DB for persistent storage
Flask-JWT-Extended	Secure authentication via JSON Web Tokens
Flask-Bcrypt	Password hashing for secure credential storage
Flask-CORS	Enables frontend-backend communication
REST API Design	Structured communication between client & server
________________________________________
📝 Description
🔒 Security Architecture
•	Passwords hashed using bcrypt
•	JWT tokens issued on login with embedded user role and user_id
•	Role-based access to all protected routes using @jwt_required() and role checks
📚 Database Tables Overview (Logical)
•	customers: customer_id, name, email, password, address
•	delivery_persons: delivery_person_id, name, email, password
•	admins: id, username, password
•	orders: order_id, customer_id, assigned_to, status, location
•	issues: issue_id, user_type, user_id, message, status, response
•	feedback: feedback_id, order_id, customer_id, feedback
________________________________________
🧪 Output Examples
✅ Successful Order Placement (Customer)
{
  "message": "Order placed successfully",
  "order": {
    "order_id": 101,
    "customer_id": 5,
    "assigned_to": null,
    "status": "Pending"
  }
}
🛑 Error Response (Missing Fields)
{
  "error": "Missing required fields"
}
🔐 JWT Login Token Response
{
  "message": "Login successful",
  "token": "<jwt_token_here>",
  "role": "customer",
  "id": 5
}
________________________________________
🚀 How to Run the Project Locally
Prerequisites:
•	Python 3.8+
•	MySQL Server
•	Virtual Environment (optional but recommended)
Installation Steps:
1.	Clone the repository:
2.	git clone https://github.com/yourusername/courier-tracking-system.git
3.	cd courier-tracking-system
4.	Create a virtual environment and activate it:
5.	python -m venv venv
6.	source venv/bin/activate  # On Windows: venv\Scripts\activate
7.	Install dependencies:
8.	pip install -r requirements.txt
9.	Set up the database:
o	Create a MySQL database named courier1
o	Import schema and seed data if available
10.	Set environment variables (or use .env):
11.	export MYSQL_USER=root
12.	export MYSQL_PASSWORD=root
13.	export MYSQL_DB=courier1
14.	export JWT_SECRET_KEY=myapp123
15.	Run the app:
16.	python app1.py
________________________________________
🔭 Further Research and Enhancements
Suggested Features:
•	✅ Live location tracking with Google Maps API
•	✅ Email/SMS notification integration
•	✅ Admin dashboard with analytics (e.g., order volume, delivery rate)
•	✅ Role-based frontend using React or Vue
•	✅ QR code scanning for package confirmation
•	✅ Unit tests and CI/CD pipeline
Possible Tools for Expansion:
•	Celery + Redis for background job processing
•	Docker for containerization
•	Swagger for API documentation
•	SQLAlchemy for ORM-based DB access
________________________________________
👨‍💻 Contributing
We welcome contributions! If you’d like to:
•	Fix a bug 🐛
•	Suggest a feature 💡
•	Improve documentation 📚
Please fork the repo, open an issue or submit a pull request.
________________________________________
📄 License
This project is open-source and available under the MIT License.
________________________________________
Let me know if you’d like:
•	A README.md file generated for download
•	A diagram for the architecture or database
•	Frontend integration advice (React, Vue, etc.)

