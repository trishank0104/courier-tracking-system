from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
from datetime import datetime, timedelta
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from flask_cors import CORS
import os

app1 = Flask(__name__)

# MySQL configurations (use environment variables in production)
app1.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app1.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', 'root')
app1.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'courier1')
app1.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')

mysql = MySQL(app1)

# Initialize Bcrypt, JWT, and CORS
bcrypt = Bcrypt(app1)
app1.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'myapp123')  # Use a secure key in production
jwt = JWTManager(app1)
CORS(app1)  # Restrict origins in production

# Temporary endpoint to create a default admin (remove after use)
@app1.route('/setup-admin', methods=['POST'])
def setup_admin():
    try:
        # Default values
        default_username = 'admin'
        default_password = 'admin123'

        # Get data from request or use default
        data = request.get_json() or {}
        username = data.get('username', default_username)
        password = data.get('password', default_password)

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        cursor = mysql.connection.cursor()

        # Check if admin already exists
        cursor.execute("SELECT username FROM admins WHERE username = %s", (username,))
        if cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Admin already exists"}), 409

        # Hash the password using Flask-Bcrypt
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Insert admin
        cursor.execute(
            "INSERT INTO admins (username, password, created_at) VALUES (%s, %s, NOW())",
            (username, hashed_password)
        )
        mysql.connection.commit()
        cursor.close()

        return jsonify({"message": f"Admin '{username}' created successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Unified login route for all users
from flask import request, jsonify
from flask_jwt_extended import create_access_token
from datetime import timedelta

@app1.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        role = data.get('role')  # 'customer', 'delivery_person', or 'admin'

        if not all([email, password, role]):
            return jsonify({"error": "Email/UserID, password, and role are required"}), 400

        if role not in ['customer', 'delivery_person', 'admin']:
            return jsonify({"error": "Invalid role specified"}), 400

        cursor = mysql.connection.cursor()

        user = None
        user_id = None
        stored_password = None

        if role == 'customer':
            cursor.execute("SELECT customer_id, email, password FROM customers WHERE email = %s", (email,))
            user = cursor.fetchone()
            if user:
                user_id, user_email, stored_password = user

        elif role == 'delivery_person':
            cursor.execute("SELECT delivery_person_id, email, password FROM delivery_persons WHERE email = %s", (email,))
            user = cursor.fetchone()
            if user:
                user_id, user_email, stored_password = user

        elif role == 'admin':
            cursor.execute("SELECT id, username, password FROM admins WHERE username = %s", (email,))
            user = cursor.fetchone()
            if user:
                user_id, username, stored_password = user

        cursor.close()

        if not user:
            return jsonify({"error": "Invalid credentials"}), 401

        if not bcrypt.check_password_hash(stored_password, password):
            return jsonify({"error": "Invalid credentials"}), 401

        # Create JWT token with user_id and role
        token = create_access_token(
            identity=str(user_id),
            additional_claims={'role': role},
            expires_delta=timedelta(hours=1)
        )

        return jsonify({
            "message": "Login successful",
            "token": token,
            "role": role,
            "id": user_id
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Customer signup (public, for signup button)
@app1.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.json
        name = data.get('name')
        phone = data.get('phone')
        email = data.get('email')
        address = data.get('address')
        password = data.get('password')

        if not all([name, phone, email, address, password]):
            return jsonify({"error": "Missing required fields"}), 400

        cursor = mysql.connection.cursor()

        # Check if email already exists
        cursor.execute("SELECT email FROM customers WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Email already registered"}), 409

        # Hash the password using Flask-Bcrypt
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Insert new customer
        cursor.execute(
            "INSERT INTO customers (name, phone, email, address, password) VALUES (%s, %s, %s, %s, %s)",
            (name, phone, email, address, hashed_password)
        )
        mysql.connection.commit()
        cursor.close()

        return jsonify({"message": "Customer registered successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Admin and Delivery Person registration (restricted)
@app1.route('/register', methods=['POST'])
@jwt_required()
def register():
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get('role')

        if role != 'admin':
            return jsonify({"error": "Admin access required"}), 403

        data = request.json
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        new_role = data.get('role')  # 'admin' or 'delivery_person'

        if not all([name, email, password, new_role]):
            return jsonify({"error": "Missing required fields"}), 400

        if new_role not in ['admin', 'delivery_person']:
            return jsonify({"error": "Invalid role specified"}), 400

        cursor = mysql.connection.cursor()

        if new_role == 'admin':
            cursor.execute("SELECT username FROM admins WHERE username = %s", (email,))
            if cursor.fetchone():
                cursor.close()
                return jsonify({"error": "Email already registered"}), 409

            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

            cursor.execute(
                "INSERT INTO admins (username, password) VALUES (%s, %s)",
                (email, hashed_password)
            )

        else:  # delivery_person
            cursor.execute("SELECT email FROM delivery_persons WHERE email = %s", (email,))
            if cursor.fetchone():
                cursor.close()
                return jsonify({"error": "Email already registered"}), 409

            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

            cursor.execute(
                "INSERT INTO delivery_persons (name, email, password) VALUES (%s, %s, %s)",
                (name, email, hashed_password)
            )

        mysql.connection.commit()
        cursor.close()

        return jsonify({"message": f"{new_role.capitalize()} registered successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Admin: View all users
@app1.route('/admin/users', methods=['GET'])
@jwt_required()
def view_users():
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get('role')
    if role != 'admin':
        return jsonify({"error": "Admin access required"}), 403
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT customer_id, name, phone, email, address FROM customers")
    customers = cursor.fetchall()
    cursor.execute("SELECT delivery_person_id, name, email FROM delivery_persons")
    delivery_persons = cursor.fetchall()
    cursor.close()
    return jsonify({
        "customers": [{"customer_id": c[0], "name": c[1], "phone": c[2], "email": c[3], "address": c[4]} for c in customers],
        "delivery_persons": [{"delivery_person_id": d[0], "name": d[1], "email": d[2]} for d in delivery_persons]
    }), 200

# Admin: View all orders
@app1.route('/admin/orders', methods=['GET'])
@jwt_required()
def view_all_orders():
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get('role')
    if role != 'admin':
        return jsonify({"error": "Admin access required"}), 403
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT order_id, customer_id, assigned_to, status FROM orders")
    orders = cursor.fetchall()
    cursor.close()
    return jsonify({
        "orders": [{"order_id": o[0], "customer_id": o[1], "assigned_to": o[2], "status": o[3]} for o in orders]
    }), 200

# Admin: Assign delivery
@app1.route('/admin/assign-delivery', methods=['POST'])
@jwt_required()
def assign_order():
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get('role')
    if role != 'admin':
        return jsonify({"error": "Admin access required"}), 403
    data = request.json
    order_id = data.get('order_id')
    delivery_person_id = data.get('delivery_person_id')
    if not all([order_id, delivery_person_id]):
        return jsonify({"error": "Missing required fields"}), 400
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT delivery_person_id FROM delivery_persons WHERE delivery_person_id = %s", (delivery_person_id,))
    if not cursor.fetchone():
        cursor.close()
        return jsonify({"error": "Delivery person not found"}), 404
    cursor.execute("UPDATE orders SET assigned_to = %s WHERE order_id = %s", (delivery_person_id, order_id))
    mysql.connection.commit()
    cursor.execute("SELECT order_id, customer_id, assigned_to, status FROM orders WHERE order_id = %s", (order_id,))
    order = cursor.fetchone()
    cursor.close()
    if order:
        return jsonify({
            "message": "Order assigned successfully",
            "order": {"order_id": order[0], "customer_id": order[1], "assigned_to": order[2], "status": order[3]}
        }), 200
    return jsonify({"message": "Order not found"}), 404

# Admin: Delete user
@app1.route('/admin/delete-user/<string:user_type>/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_type, user_id):
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get('role')
    if role != 'admin':
        return jsonify({"error": "Admin access required"}), 403
    cursor = mysql.connection.cursor()
    if user_type == "customer":
        cursor.execute("DELETE FROM customers WHERE customer_id = %s", (user_id,))
    elif user_type == "delivery_person":
        cursor.execute("DELETE FROM delivery_persons WHERE delivery_person_id = %s", (user_id,))
    else:
        cursor.close()
        return jsonify({"message": "Invalid user type"}), 400
    mysql.connection.commit()
    cursor.close()
    return jsonify({"message": f"{user_type.capitalize()} deleted successfully"}), 200

# Admin: View all issues
@app1.route('/admin/issues', methods=['GET'])
@jwt_required()
def view_issues():
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get('role')
    if role != 'admin':
        return jsonify({"error": "Admin access required"}), 403
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT issue_id, user_type, user_id, message, status, response FROM issues")
    issues = cursor.fetchall()
    cursor.close()
    return jsonify({
        "issues": [{"issue_id": i[0], "user_type": i[1], "user_id": i[2], "message": i[3], "status": i[4], "response": i[5]} for i in issues]
    }), 200

# Admin: Respond to or resolve an issue
@app1.route('/admin/issues/respond/<int:issue_id>', methods=['PATCH'])
@jwt_required()
def respond_to_issue(issue_id):
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get('role')
    if role != 'admin':
        return jsonify({"error": "Admin access required"}), 403
    data = request.json
    response = data.get('response')
    status = data.get('status', 'resolved')
    if not response:
        return jsonify({"error": "Response is required"}), 400
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE issues SET response = %s, status = %s WHERE issue_id = %s", (response, status, issue_id))
    mysql.connection.commit()
    cursor.execute("SELECT issue_id, user_type, user_id, message, status, response FROM issues WHERE issue_id = %s", (issue_id,))
    issue = cursor.fetchone()
    cursor.close()
    if issue:
        return jsonify({
            "message": "Issue updated",
            "issue": {"issue_id": issue[0], "user_type": issue[1], "user_id": issue[2], "message": issue[3], "status": issue[4], "response": issue[5]}
        }), 200
    return jsonify({"message": "Issue not found"}), 404

# Customer/Delivery Person: Raise an issue
@app1.route('/raise-issue', methods=['POST'])
@jwt_required()
def raise_issue():
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get('role')

        if role not in ['customer', 'delivery_person']:
            return jsonify({"error": "Only customers and delivery persons can raise issues"}), 403

        data = request.json
        message = data.get('message')

        if not message:
            return jsonify({"error": "Message is required"}), 400

        cursor = mysql.connection.cursor()

        try:
            cursor.execute(
                "INSERT INTO issues (user_type, user_id, message, status) VALUES (%s, %s, %s, %s)",
                (role, current_user_id, message, "open")
            )
            mysql.connection.commit()
            issue_id = cursor.lastrowid

        except Exception as db_err:
            mysql.connection.rollback()
            cursor.close()
            return jsonify({"error": f"DB insert failed: {str(db_err)}"}), 500

        cursor.execute("SELECT issue_id, user_type, user_id, message, status, response FROM issues WHERE issue_id = %s", (issue_id,))
        issue = cursor.fetchone()
        cursor.close()

        if not issue:
            return jsonify({"error": "Issue retrieval failed after insertion"}), 500

        return jsonify({
            "message": "Issue submitted",
            "issue": {
                "issue_id": issue[0],
                "user_type": issue[1],
                "user_id": issue[2],
                "message": issue[3],
                "status": issue[4],
                "response": issue[5]
            }
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Customer: Place order
@app1.route('/customer/place-order', methods=['POST'])
@jwt_required()
def place_order():
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get('role')
    if role != 'customer':
        return jsonify({"error": "Customer access required"}), 403
    cursor = mysql.connection.cursor()
    cursor.execute(
        "INSERT INTO orders (customer_id, status) VALUES (%s, %s)",
        (current_user_id, "Pending")
    )
    mysql.connection.commit()
    order_id = cursor.lastrowid
    cursor.execute("SELECT order_id, customer_id, assigned_to, status FROM orders WHERE order_id = %s", (order_id,))
    order = cursor.fetchone()
    cursor.close()
    return jsonify({
        "message": "Order placed successfully",
        "order": {
            "order_id": order[0],
            "customer_id": order[1],
            "assigned_to": order[2],
            "status": order[3]
        }
    }), 201

# Customer: Track order
@app1.route('/customer/track-order/<int:order_id>', methods=['GET'])
@jwt_required()
def track_order(order_id):
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get('role')
    if role != 'customer':
        return jsonify({"error": "Customer access required"}), 403
    cursor = mysql.connection.cursor()
    cursor.execute(
        "SELECT order_id, customer_id, assigned_to, status FROM orders WHERE order_id = %s AND customer_id = %s",
        (order_id, current_user_id)
    )
    order = cursor.fetchone()
    cursor.close()
    if order:
        return jsonify({
            "order": {"order_id": order[0], "customer_id": order[1], "assigned_to": order[2], "status": order[3]}
        }), 200
    return jsonify({"message": "Order not found or access denied"}), 404

# Customer: Provide feedback
@app1.route('/customer/feedback', methods=['POST'])
@jwt_required()
def submit_feedback():
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get('role')
    if role != 'customer':
        return jsonify({"error": "Customer access required"}), 403
    data = request.json
    order_id = data.get('order_id')
    feedback = data.get('feedback')
    if not all([order_id, feedback]):
        return jsonify({"error": "Order ID and feedback are required"}), 400
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT order_id FROM orders WHERE order_id = %s AND customer_id = %s", (order_id, current_user_id))
    if not cursor.fetchone():
        cursor.close()
        return jsonify({"error": "Order not found or access denied"}), 404
    cursor.execute(
        "INSERT INTO feedback (order_id, customer_id, feedback) VALUES (%s, %s, %s)",
        (order_id, current_user_id, feedback)
    )
    mysql.connection.commit()
    cursor.close()
    return jsonify({"message": "Feedback submitted successfully"}), 201

# Delivery Person: View assigned orders
@app1.route('/delivery/assigned-orders', methods=['GET'])
@jwt_required()
def assigned_orders():
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get('role')
    if role != 'delivery_person':
        return jsonify({"error": "Delivery person access required"}), 403
    cursor = mysql.connection.cursor()
    cursor.execute(
        "SELECT order_id, customer_id, assigned_to, status FROM orders WHERE assigned_to = %s",
        (current_user_id,)
    )
    orders = cursor.fetchall()
    cursor.close()
    return jsonify({
        "assigned_orders": [{"order_id": o[0], "customer_id": o[1], "assigned_to": o[2], "status": o[3]} for o in orders]
    }), 200

# Delivery Person: Update order status
@app1.route('/delivery/update-status', methods=['PATCH'])
@jwt_required()
def update_order_status():
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get('role')
    if role != 'delivery_person':
        return jsonify({"error": "Delivery person access required"}), 403
    data = request.json
    order_id = data.get('order_id')
    status = data.get('status')
    if not all([order_id, status]):
        return jsonify({"error": "Order ID and status are required"}), 400
    cursor = mysql.connection.cursor()
    cursor.execute(
        "UPDATE orders SET status = %s WHERE order_id = %s AND assigned_to = %s",
        (status, order_id, current_user_id)
    )
    mysql.connection.commit()
    cursor.close()
    return jsonify({"message": "Order status updated successfully"}), 200

# Delivery Person: Update order location
@app1.route('/delivery/update-location', methods=['PATCH'])
@jwt_required()
def update_order_location():
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get('role')
    if role != 'delivery_person':
        return jsonify({"error": "Delivery person access required"}), 403
    data = request.json
    order_id = data.get('order_id')
    location = data.get('location')
    if not all([order_id, location]):
        return jsonify({"error": "Order ID and location are required"}), 400
    cursor = mysql.connection.cursor()
    cursor.execute(
        "UPDATE orders SET location = %s WHERE order_id = %s AND assigned_to = %s",
        (location, order_id, current_user_id)
    )
    mysql.connection.commit()
    cursor.close()
    return jsonify({"message": "Order location updated successfully"}), 200

# Delivery Person: View delivery history
@app1.route('/delivery/history', methods=['GET'])
@jwt_required()
def delivery_history():
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get('role')
    if role != 'delivery_person':
        return jsonify({"error": "Delivery person access required"}), 403
    cursor = mysql.connection.cursor()
    cursor.execute(
        "SELECT order_id, customer_id, assigned_to, status FROM orders WHERE assigned_to = %s AND status = 'Delivered'",
        (current_user_id,)
    )
    history = cursor.fetchall()
    cursor.close()
    return jsonify({
        "delivery_history": [{"order_id": h[0], "customer_id": h[1], "assigned_to": h[2], "status": h[3]} for h in history]
    }), 200

if __name__ == '__main__':
    app1.run(debug=True)