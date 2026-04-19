from flask import Flask, render_template, request, url_for, redirect, jsonify, session, flash, send_file
from flask_socketio import SocketIO
import os
from dotenv import load_dotenv 
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import json
from datetime import datetime
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta
import hashlib
import socket
import uuid
import qrcode
from io import BytesIO
from PIL import ImageDraw, ImageFont

try:
    from pyngrok import ngrok
except ImportError:
    ngrok = None

load_dotenv()  # Load environment variables

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default-secret-key')  # Use environment variable

# Add this for production
port = int(os.environ.get('PORT', 5000))

# Modify the socketio initialization for production
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Complete menu from the image
def get_full_menu():
    """Returns the complete menu with all categories and items"""
    MENU = {
        "TEA TONES": [
            {"id": "normal-tea", "name": "Normal Tea", "price": 15, "price_regular": 15, "price_large": 30, "image": "normal_tea.svg"},
            {"id": "elaichi-tea", "name": "Elaichi Tea", "price": 25, "price_regular": 25, "price_large": 49, "image": "elaichi_tea.svg"},
            {"id": "ginger-tea", "name": "Ginger Tea", "price": 25, "price_regular": 25, "price_large": 49, "image": "ginger_tea.svg"},
            {"id": "masala-tea", "name": "Masala Tea", "price": 28, "price_regular": 28, "price_large": 49, "image": "masala_tea.svg"},
            {"id": "black-tea", "name": "Black Tea", "price": 20, "price_regular": 20, "price_large": 29, "image": "black_tea.svg"},
            {"id": "green-tea", "name": "Green Tea", "price": 29, "price_regular": 29, "price_large": 59, "image": "green_tea.svg"},
            {"id": "irani-tea", "name": "Irani Tea", "price": 49, "price_regular": 49, "price_large": 79, "image": "irani_tea.svg"},
            {"id": "mint-tea", "name": "Mint Tea", "price": 25, "price_regular": 25, "price_large": 49, "image": "mint_tea.svg"},
            {"id": "jaggery-tea", "name": "Jaggery Tea", "price": 30, "price_regular": 30, "price_large": 59, "image": "jaggery_tea.svg"},
            {"id": "lemon-tea", "name": "Lemon Tea", "price": 20, "price_regular": 20, "price_large": 40, "image": "lemon_tea.svg"},
            {"id": "honey-lemon-tea", "name": "Honey Lemon Tea", "price": 25, "price_regular": 25, "price_large": 49, "image": "honey_lemon_tea.svg"},
            {"id": "hibiscus-tea", "name": "Hibiscus Tea with Honey", "price": 39, "price_regular": 39, "price_large": 79, "image": "hibiscus_tea.svg"},
            {"id": "ice-tea", "name": "Ice Tea", "price": 49, "image": "ice_tea.svg"},
            {"id": "chocolate-tea", "name": "Chocolate Tea", "price": 39, "price_regular": 39, "price_large": 79, "image": "chocolate_tea.svg"}
        ],
        "MILKSHAKES": [
            {"id": "butterscotch-milkshake", "name": "Butterscotch Milkshake", "price": 79, "image": "butterscotch.svg"},
            {"id": "strawberry-milkshake", "name": "Strawberry Milkshake", "price": 89, "image": "strawberry.svg"},
            {"id": "mango-milkshake", "name": "Mango Milkshake", "price": 89, "image": "mango.svg"},
            {"id": "vanilla-milkshake", "name": "Vanilla Milkshake", "price": 89, "image": "vanilla.svg"},
            {"id": "chocolate-milkshake", "name": "Chocolate Milkshake", "price": 99, "image": "chocolate_shake.svg"},
            {"id": "kitkat-milkshake", "name": "Kit Kat Milkshake", "price": 109, "image": "kitkat.svg"},
            {"id": "oreo-milkshake", "name": "Oreo Milkshake", "price": 109, "image": "oreo.svg"}
        ],
        "QUICK BITES": [
            {"id": "crispy-corn", "name": "Crispy Corn", "price": 79, "image": "crispy_corn.svg"},
            {"id": "veg-fingers", "name": "Veg Fingers", "price": 109, "image": "veg_fingers.svg"},
            {"id": "potato-wedges", "name": "Potato Wedges", "price": 119, "image": "potato_wedges.svg"},
            {"id": "chilli-garlic-pops", "name": "Chilli Garlics Pops", "price": 119, "image": "chilli_garlic.svg"}
        ],
        "BUSY BURGER": [
            {"id": "veg-aloo-tikki", "name": "Veg Aloo Tikki Burger", "price": 89, "image": "aloo_tikki.svg"},
            {"id": "mud-cups-special", "name": "Mud Cups Special Burger", "price": 109, "image": "special_burger.svg"},
            {"id": "egg-burger", "name": "Egg Burger", "price": 89, "image": "egg_burger.svg"},
            {"id": "twin-burger", "name": "Twin Burger (Veg)", "price": 129, "image": "twin_burger.svg"},
            {"id": "tower-burger", "name": "Tower Burger", "price": 129, "image": "tower_burger.svg"}
        ],
        "NUGGETS": [
            {"id": "veg-nuggets", "name": "Veg Nuggets", "price": 99, "image": "veg_nuggets.svg"},
            {"id": "cheese-nuggets", "name": "Cheese Nuggets", "price": 109, "image": "cheese_nuggets.svg"},
            {"id": "potato-bites", "name": "Potato Bites", "price": 109, "image": "potato_bites.svg"},
            {"id": "corn-cheese-nuggets", "name": "Corn Cheese Nuggets", "price": 119, "image": "corn_cheese.svg"},
            {"id": "nuggets-lollipop", "name": "Nuggets Lolli Pop", "price": 119, "image": "nuggets_lollipop.svg"}
        ],
        "CRAVY COFEE": [
            {"id": "black-coffee", "name": "Black Coffee", "price": 20, "price_regular": 20, "price_large": 39, "image": "black_coffee.svg"},
            {"id": "special-filter-coffee", "name": "Special Filter Coffee", "price": 25, "price_regular": 25, "price_large": 49, "image": "filter_coffee.svg"},
            {"id": "jaggery-coffee", "name": "Jaggery Coffee", "price": 25, "price_regular": 25, "price_large": 49, "image": "jaggery_coffee.svg"},
            {"id": "ginger-coffee", "name": "Ginger Coffee", "price": 25, "price_regular": 25, "price_large": 49, "image": "ginger_coffee.svg"},
            {"id": "cold-coffee", "name": "Cold Coffee", "price": 99, "image": "cold_coffee.svg"}
        ],
        "BUN BLAST": [
            {"id": "bun-butter-jam", "name": "Bun Butter Jam", "price": 39, "image": "bun_butter_jam.svg"},
            {"id": "bun-muska", "name": "Bun Muska", "price": 49, "image": "bun_muska.svg"},
            {"id": "madurai-bun", "name": "Madhurai Bun Butter Jam", "price": 49, "image": "madurai_bun.svg"}
        ],
        "MAZZA MOMOS": [
            {"id": "veg-momos", "name": "Veg Momos (Fried)", "price": 89, "image": "veg_momos.svg"},
            {"id": "paneer-momos", "name": "Paneer Momos (Fried)", "price": 99, "image": "paneer_momos.svg"}
        ],
        "EGG PANDA": [
            {"id": "special-boiled-eggs", "name": "Special Boiled Eggs (6 No)", "price": 69, "image": "boiled_eggs.svg"},
            {"id": "bread-omelette", "name": "Bread Omelette", "price": 79, "image": "bread_omelette.svg"},
            {"id": "bun-egg-fry", "name": "Bun Egg Fry", "price": 79, "image": "bun_egg_fry.svg"},
            {"id": "bread-mayo-omelette", "name": "Bread Mayo Omelette", "price": 89, "image": "mayo_omelette.svg"}
        ],
        "MILK WAY": [
            {"id": "plain-milk", "name": "Plain Milk", "price": 20, "price_regular": 20, "price_large": 39, "image": "plain_milk.svg"},
            {"id": "horlicks", "name": "Horlicks", "price": 29, "price_regular": 29, "price_large": 59, "image": "horlicks.svg"},
            {"id": "hot-badam-milk", "name": "Hot Badam Milk", "price": 29, "price_regular": 29, "price_large": 59, "image": "badam_milk.svg"},
            {"id": "cold-boost", "name": "Cold Boost", "price": 89, "image": "boost.svg"},
            {"id": "cold-bournvita", "name": "Cold Bournvita", "price": 89, "image": "bournvita.svg"},
            {"id": "cold-badam-milk", "name": "Cold Badam Milk", "price": 89, "image": "cold_badam.svg"},
            {"id": "hot-chocolate-milk", "name": "Hot Chocolate Milk", "price": 59, "image": "hot_chocolate.svg"}
        ],
        "SOSI SANDWICH": [
            {"id": "bread-butter-jam", "name": "Bread Butter Jam", "price": 49, "image": "bread_jam.svg"},
            {"id": "veg-sandwich", "name": "Veg Sandwich", "price": 69, "image": "veg_sandwich.svg"},
            {"id": "egg-sandwich", "name": "Egg Sandwich", "price": 79, "image": "egg_sandwich.svg"},
            {"id": "boiled-egg-sandwich", "name": "Boiled Egg Sandwich", "price": 79, "image": "boiled_egg_sandwich.svg"},
            {"id": "corn-peri-peri", "name": "Corn Peri Peri Sandwich", "price": 79, "image": "corn_peri.svg"},
            {"id": "corn-peri-cheese", "name": "Corn Peri Peri Cheese Sandwich", "price": 89, "image": "corn_cheese_sandwich.svg"},
            {"id": "chilli-cheese", "name": "Chilli Cheese Sandwich", "price": 89, "image": "chilli_cheese.svg"},
            {"id": "veg-paneer", "name": "Veg Paneer Sandwich", "price": 99, "image": "paneer_sandwich.svg"},
            {"id": "chocolate-sandwich", "name": "Chocolate Sandwich", "price": 89, "image": "chocolate_sandwich.svg"},
            {"id": "peanut-nutella", "name": "Peanut Nutella Sandwich", "price": 89, "image": "peanut_nutella.svg"},
            {"id": "choco-peanut", "name": "Choco Peanut Nutella Sandwich", "price": 99, "image": "choco_peanut.svg"}
        ],
        "GOL GAPPA": [
            {"id": "bangalore-gol-gappa", "name": "Bangalore Gol Gappa", "price": 25, "image": "gol_gappa.svg"},
            {"id": "sukha-puri", "name": "Sukha Puri", "price": 25, "image": "sukha_puri.svg"},
            {"id": "unlimited-gol-gappa", "name": "Unlimited Gol Gappa", "price": 99, "image": "unlimited_gol.svg"}
        ],
        "COLD TIK TOK": [
            {"id": "butter-milk", "name": "Butter Milk", "price": 39, "image": "buttermilk.svg"},
            {"id": "watermelon-mojito", "name": "Watermelon Mojito", "price": 89, "image": "watermelon_mojito.svg"},
            {"id": "mint-mojito", "name": "Mint Mojito", "price": 99, "image": "mint_mojito.svg"},
            {"id": "blue-lagoon", "name": "Blue Lagoon Mojito", "price": 99, "image": "blue_lagoon.svg"},
            {"id": "green-virgin", "name": "Green Virgin Mojito", "price": 99, "image": "green_virgin.svg"},
            {"id": "mango-mojito", "name": "Mango Mojito", "price": 89, "image": "mango_mojito.svg"}
        ],
        "FRIFAS FASHION": [
            {"id": "plain-fries", "name": "Plain French Fries", "price": 89, "image": "plain_fries.svg"},
            {"id": "peri-peri-fries", "name": "Peri Peri Fries", "price": 99, "image": "peri_fries.svg"},
            {"id": "cheese-peri-fries", "name": "Cheese Peri Peri Fries", "price": 119, "image": "cheese_fries.svg"},
            {"id": "mexican-fries", "name": "Mexican Fries", "price": 109, "image": "mexican_fries.svg"},
            {"id": "loaded-fries", "name": "Loaded Fries", "price": 159, "image": "loaded_fries.svg"},
            {"id": "fries-platter", "name": "Fries Platter", "price": 199, "image": "fries_platter.svg"}
        ],
        "PASTA PORSH": [
            {"id": "indian-masala-pasta", "name": "Indian Masala Pasta", "price": 149, "image": "masala_pasta.svg"},
            {"id": "creamy-pasta", "name": "Creamy Pasta", "price": 159, "image": "creamy_pasta.svg"}
        ],
        "MAZZA MAGGIE": [
            {"id": "veg-maggie", "name": "Veg Maggie", "price": 49, "image": "veg_maggie.svg"},
            {"id": "egg-maggie", "name": "Egg Maggie", "price": 69, "image": "egg_maggie.svg"},
            {"id": "corn-maggie", "name": "Corn Maggie", "price": 69, "image": "corn_maggie.svg"},
            {"id": "schezwan-paneer-maggie", "name": "Schezwan Paneer Maggie", "price": 99, "image": "schezwan_maggie.svg"}
        ]
    }
    return MENU

def get_menu_items(category):
    """Get items for a specific category"""
    full_menu = get_full_menu()
    return full_menu.get(category, [])

def get_all_categories():
    """Get all category names"""
    full_menu = get_full_menu()
    return list(full_menu.keys())

# In-memory cart storage (use DB in production)
CART = {}

ADMINS_FILE = os.path.join('instance', 'admins.json')

def load_admins():
    if not os.path.exists(ADMINS_FILE):
        # Create default admin if no admins exist
        default_admins = [{
            'username': 'admin',
            'password': generate_password_hash('admin123')
        }]
        save_admins(default_admins)
        return default_admins
    with open(ADMINS_FILE, 'r') as f:
        return json.load(f)

def save_admins(admins):
    os.makedirs('instance', exist_ok=True)
    with open(ADMINS_FILE, 'w') as f:
        json.dump(admins, f)

def find_admin(username):
    admins = load_admins()
    for admin in admins:
        if admin['username'] == username:
            return admin
    return None

# Helper to calculate cart total
def cart_total(cart):
    return sum(item['price'] * item['quantity'] for item in cart.values())

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Initialize database tables
def init_db():
    """Initialize database tables if they don't exist"""
    os.makedirs('instance', exist_ok=True)
    conn = sqlite3.connect('instance/restaurant.db')
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS completed_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_number INTEGER,
            total_amount REAL,
            order_date TIMESTAMP,
            completed_date TIMESTAMP,
            payment_status TEXT DEFAULT 'pending',
            payment_method TEXT,
            transaction_id TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            item_name TEXT,
            item_price REAL,
            quantity INTEGER,
            category TEXT,
            order_date TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES completed_orders(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            amount REAL,
            payment_method TEXT,
            payment_status TEXT,
            transaction_id TEXT,
            payment_date TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES completed_orders(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")


def start_ngrok_tunnel():
    if ngrok is None:
        print("ngrok is not installed. Install pyngrok or disable ngrok support.")
        return None

    auth_token = os.getenv('NGROK_AUTH_TOKEN')
    use_ngrok = os.getenv('USE_NGROK', 'false').lower() in ('1', 'true', 'yes')

    if not use_ngrok and not auth_token:
        return None

    try:
        if auth_token:
            ngrok.set_auth_token(auth_token)
        tunnel = ngrok.connect(port, "http", bind_tls=True)
        public_url = tunnel.public_url
        print(f"✅ ngrok tunnel started at {public_url}")
        return public_url
    except Exception as e:
        print(f"ngrok tunnel start failed: {e}")
        return None


def get_server_base_url():
    env_url = os.getenv('BASE_URL')
    if env_url:
        return env_url.rstrip('/')

    ngrok_url = os.getenv('NGROK_URL')
    if ngrok_url:
        return ngrok_url.rstrip('/')

    public_url = start_ngrok_tunnel()
    if public_url:
        return public_url.rstrip('/')

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(('8.8.8.8', 80))
            local_ip = sock.getsockname()[0]
        return f"http://{local_ip}:{port}"
    except Exception:
        return f"http://localhost:{port}"


# QR Code Generation Function
def generate_table_qr_codes():
    """Generate QR codes for tables 1-10"""
    # Create qrcodes directory if it doesn't exist
    os.makedirs('static/qrcodes', exist_ok=True)
    
    base_url = get_server_base_url()
    
    generated_files = []
    for table_num in range(1, 11):
        # URL format: /scan?table=TABLE_NUMBER
        qr_url = f"{base_url}/scan?table={table_num}"
        
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_url)
        qr.make(fit=True)
        
        # Generate image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Add table number text to the image
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()
        draw.text((10, 10), f"Table {table_num}", fill="black")
        
        # Save the QR code
        filename = f'static/qrcodes/table_{table_num}.png'
        img.save(filename)
        generated_files.append(filename)
        print(f"✅ Generated QR code for Table {table_num} at {filename}")
        print(f"   URL: {qr_url}")
    
    print("\n🎉 All QR codes generated successfully!")
    print("📁 Location: static/qrcodes/")
    print("\n📝 Instructions:")
    print("1. Print these QR codes")
    print("2. Place them on respective tables (1-10)")
    print("3. Customers can scan to access the menu")
    return generated_files

# Call init_db when app starts
init_db()

# Generate QR codes on startup (optional - comment out if you want to generate manually)
generate_table_qr_codes()

# ==================== ROUTES ====================

@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html")

@app.route('/generate_qrcodes')
@admin_required
def generate_qrcodes_route():
    """Admin route to generate QR codes"""
    try:
        files = generate_table_qr_codes()
        return jsonify({
            'success': True,
            'message': 'QR codes generated successfully!',
            'files': files
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/download_qrcode/<int:table_num>')
@admin_required
def download_qrcode(table_num):
    """Download QR code for a specific table"""
    if table_num not in range(1, 11):
        flash('Invalid table number', 'danger')
        return redirect(url_for('admin_panel'))
    
    filename = f'static/qrcodes/table_{table_num}.png'
    if not os.path.exists(filename):
        # Generate if not exists
        generate_table_qr_codes()
    
    return send_file(filename, as_attachment=True, download_name=f'table_{table_num}_qrcode.png')

@app.route('/view_qrcodes')
@admin_required
def view_qrcodes():
    """View all generated QR codes"""
    qrcodes = []
    for table_num in range(1, 11):
        filename = f'static/qrcodes/table_{table_num}.png'
        if os.path.exists(filename):
            qrcodes.append({
                'table': table_num,
                'url': url_for('static', filename=f'qrcodes/table_{table_num}.png')
            })
    return render_template('qrcodes_view.html', qrcodes=qrcodes)

@app.route('/generate_bank_qr/<float:amount>')
def generate_bank_qr(amount):
    """Generate bank transfer QR code with amount"""
    # UPI format for bank transfer
    upi_id = "mudcafe@cnrb"  # Replace with actual UPI ID
    merchant_name = "Mud Cafe"
    payment_note = "Mud Cafe Order Payment"
    
    upi_url = (
        f"upi://pay?pa={upi_id}&pn={merchant_name}&am={amount:.2f}"
        f"&cu=INR&tn={payment_note.replace('mudcafe@cnrb', '%20')}"
    )
    
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(upi_url)
    qr.make(fit=True)
    
    # Generate image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to BytesIO
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png')

@app.route('/generate_upi_qr')
def generate_upi_qr():
    """Generate a QR code directly from a UPI payment URI."""
    upi_uri = request.args.get('upi_uri')
    if not upi_uri:
        return jsonify({'error': 'Missing upi_uri parameter'}), 400

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(upi_uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png')

@app.route('/scan')
def scan():
    """Handle QR code scan - redirects to menu with table number"""
    table_number = request.args.get('table')
    if not table_number or not table_number.isdigit() or int(table_number) not in range(1, 11):
        flash('Invalid QR code. Please scan a valid table QR code (Tables 1-10).', 'danger')
        return redirect(url_for('index'))
    
    # Store table number in session
    session['table_number'] = table_number
    session['qr_scanned'] = True
    
    # Redirect to categories page
    return redirect(url_for('categories'))

@app.route("/categories")
def categories():
    table_number = request.args.get('table_number')
    if table_number:
        session['table_number'] = table_number
    elif not session.get('table_number'):
        # If no table number in args or session, redirect to start
        return redirect(url_for('index'))
    categories_list = get_all_categories()
    return render_template("categories.html", categories=categories_list)

@app.route('/menu/<category>')
def menu(category):
    table_number = request.args.get('table_number', '')
    if not table_number:
        table_number = session.get('table_number', '')
    if not table_number:
        return redirect(url_for('index'))
    session['table_number'] = table_number
    menu_items = get_menu_items(category)
    if not menu_items:
        return redirect(url_for('categories'))
    return render_template('menu.html', category=category, menu_items=menu_items, table_number=table_number)

@app.route("/cart/<table_number>")
def cart(table_number):
    if not table_number or table_number != session.get('table_number'):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"error": "Invalid session"}), 400
        return redirect(url_for('index'))

    table_cart = CART.get(table_number, {})
    cart_items = {k: v for k, v in table_cart.items() if k != '_meta'}
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(cart_items=cart_items)
        
    total = cart_total(cart_items)
    return render_template(
        "cart.html", 
        cart_items=cart_items, 
        table_number=table_number, 
        cart_total=total,
        full_cart_data=table_cart
    )

@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    data = request.json
    table_number = session.get("table_number")
    if not table_number:
        return jsonify({"error": "Table number missing!"}), 400
    try:
        item_id = data["id"]
        name = data["name"]
        price = float(data["price"])
        if price < 0:
            return jsonify({"error": "Invalid price"}), 400
        if table_number not in CART:
            CART[table_number] = {"_meta": {"status": "Preparing", "last_updated": datetime.now().isoformat()}}
        if item_id in CART[table_number]:
            CART[table_number][item_id]["quantity"] += 1
        else:
            CART[table_number][item_id] = {"name": name, "price": price, "quantity": 1}
        # Update meta
        CART[table_number]["_meta"]["last_updated"] = datetime.now().isoformat()
        cart_count = sum(item["quantity"] for k, item in CART[table_number].items() if k != "_meta")
        socketio.emit("cart_update", {"cart_count": cart_count}, room=table_number)
        return jsonify({"cart_count": cart_count, "total_items": cart_count})
    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400

@app.route("/update_cart", methods=["POST"])
def update_cart():
    data = request.json
    table_number = session.get("table_number")
    if not table_number:
        return jsonify({"error": "Invalid table number"}), 400

    try:
        item_id = data["id"]
        quantity = int(data["quantity"])
        
        if table_number not in CART:
            CART[table_number] = {"_meta": {"status": "Preparing", "last_updated": datetime.now().isoformat()}}

        if quantity > 0:
            if item_id not in CART[table_number]:
                 CART[table_number][item_id] = {
                    "name": data["name"], 
                    "price": float(data["price"]), 
                    "quantity": quantity
                }
            else:
                CART[table_number][item_id]["quantity"] = quantity
        elif item_id in CART[table_number]:
            del CART[table_number][item_id]

        CART[table_number]["_meta"]["last_updated"] = datetime.now().isoformat()
        total_items = sum(item.get("quantity", 0) for k, item in CART[table_number].items() if k != "_meta")
        
        socketio.emit("cart_update", {"cart_count": total_items}, room=table_number)
        
        return jsonify({"success": True, "total_items": total_items})
    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400

@app.route("/update_cart_status", methods=["POST"])
@admin_required
def update_cart_status():
    table_number = request.form.get("table_number")
    status = request.form.get("status")
    if table_number in CART and "_meta" in CART[table_number]:
        CART[table_number]["_meta"]["status"] = status
        CART[table_number]["_meta"]["last_updated"] = datetime.now().isoformat()
        socketio.emit("admin_cart_update", {"carts": CART})
        return ("", 204)
    return ("Not found", 404)

@app.route("/get_cart_count")
def get_cart_count():
    table_number = session.get("table_number")
    count = sum(item["quantity"] for item in CART.get(table_number, {}).values()) if table_number else 0
    return jsonify({"count": count})

@app.route('/initiate_payment', methods=['POST'])
def initiate_payment():
    """Initiate payment for an order"""
    table_number = session.get('table_number')
    if not table_number:
        return jsonify({'error': 'No active session'}), 400
    
    if table_number not in CART:
        return jsonify({'error': 'No items in cart'}), 400
    
    cart_items = {k: v for k, v in CART[table_number].items() if k != '_meta'}
    if not cart_items:
        return jsonify({'error': 'Cart is empty'}), 400
    
    total_amount = cart_total(cart_items)
    
    # Generate unique transaction ID
    transaction_id = str(uuid.uuid4())
    
    # Store payment info in session
    session['pending_payment'] = {
        'table_number': table_number,
        'amount': total_amount,
        'transaction_id': transaction_id,
        'items': cart_items,
        'created_at': datetime.now().isoformat()
    }
    
    return jsonify({
        'success': True,
        'amount': total_amount,
        'transaction_id': transaction_id,
        'payment_methods': ['UPI', 'Card', 'Cash', 'QR Code', 'Bank Transfer']
    })

@app.route('/process_payment', methods=['POST'])
def process_payment():
    """Process the payment after user selects method"""
    data = request.json
    payment_method = data.get('payment_method')

    pending = session.get('pending_payment')
    if not pending:
        return jsonify({'error': 'No pending payment found'}), 400

    table_number = pending['table_number']
    total_amount = pending['amount']
    transaction_id = pending['transaction_id']
    cart_items = pending['items']

    try:
        # Determine payment status based on method
        if payment_method == 'Bank Transfer':
            payment_status = 'pending'
            cart_status = 'Payment Pending'
        else:
            payment_status = 'completed'
            cart_status = 'Paid'

        # Save to database
        conn = sqlite3.connect('instance/restaurant.db')
        cursor = conn.cursor()

        # Insert order
        order_date = datetime.now()
        cursor.execute('''
            INSERT INTO completed_orders 
            (table_number, total_amount, order_date, completed_date, payment_status, payment_method, transaction_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (table_number, total_amount, order_date, order_date, payment_status, payment_method, transaction_id))

        order_id = cursor.lastrowid

        # Insert order items with category mapping
        full_menu = get_full_menu()
        item_to_category = {}
        for category_name, items in full_menu.items():
            for item in items:
                item_to_category[item['id']] = category_name

        for item_id, item_details in cart_items.items():
            category = item_to_category.get(item_id, 'other')
            cursor.execute('''
                INSERT INTO order_items (order_id, item_name, item_price, quantity, category, order_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (order_id, item_details['name'], item_details['price'], 
                  item_details['quantity'], category, order_date))

        # Insert payment record
        cursor.execute('''
            INSERT INTO payments (order_id, amount, payment_method, payment_status, transaction_id, payment_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (order_id, total_amount, payment_method, payment_status, transaction_id, order_date))

        conn.commit()
        conn.close()

        # Update cart status
        if table_number in CART:
            CART[table_number]['_meta']['status'] = cart_status
            CART[table_number]['_meta']['payment_status'] = payment_status
            CART[table_number]['_meta']['payment_method'] = payment_method
            CART[table_number]['_meta']['transaction_id'] = transaction_id

        # Emit notification to admin
        socketio.emit('payment_completed_notification', {
            'table_number': table_number,
            'amount': total_amount,
            'payment_method': payment_method,
            'message': f'💳 Payment received: Table {table_number} - ₹{total_amount:.2f} via {payment_method}'
        })

        # Emit order update to admin
        socketio.emit('admin_cart_update', {'carts': CART})

        # Clear pending payment from session
        session.pop('pending_payment', None)

        return jsonify({
            'success': True,
            'message': 'Payment processed successfully!',
            'order_id': order_id,
            'transaction_id': transaction_id
        })

    except Exception as e:
        print(f"Payment processing error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/order_confirmation/<order_id>')
def order_confirmation(order_id):
    """Show order confirmation page after payment"""
    try:
        conn = sqlite3.connect('instance/restaurant.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM completed_orders WHERE id = ?
        ''', (order_id,))
        order = cursor.fetchone()
        
        if not order:
            flash('Order not found', 'danger')
            return redirect(url_for('index'))
        
        cursor.execute('''
            SELECT * FROM order_items WHERE order_id = ?
        ''', (order_id,))
        items = cursor.fetchall()
        
        conn.close()
        
        return render_template('order_confirmation.html', 
                             order=order, 
                             items=items,
                             order_id=order_id)
    except Exception as e:
        print(f"Error fetching order: {e}")
        return redirect(url_for('index'))

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        admin = find_admin(username)
        if admin:
            stored_hash = admin['password']
            is_password_correct = check_password_hash(stored_hash, password)
            if is_password_correct:
                session['admin_logged_in'] = True
                session['admin_username'] = username
                return redirect(url_for('admin_panel'))
            else:
                flash('Invalid credentials', 'danger')
        else:
            flash('Invalid credentials', 'danger')
    return render_template('admin_login.html')

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route("/admin")
@admin_required
def admin_panel():
    admins = load_admins()

    # --- Analytics Calculation ---
    full_menu = get_full_menu()
    item_to_category = {}
    for category_name, items in full_menu.items():
        for item in items:
            item_to_category[item['id']] = category_name
    
    total_revenue = 0
    total_orders = 0
    item_counts = {}
    category_revenue = {cat: 0 for cat in full_menu.keys()}

    ordered_carts = {
        table: cart for table, cart in CART.items() 
        if cart.get("_meta", {}).get("status") in ["Ordered", "Cooking", "Served", "Paid"]
    }
    
    total_orders = len(ordered_carts)

    for table, cart_data in ordered_carts.items():
        cart_items_only = {k: v for k, v in cart_data.items() if k != "_meta"}
        cart_total_val = cart_total(cart_items_only)
        total_revenue += cart_total_val
        
        for item_id, item_details in cart_items_only.items():
            item_counts[item_details['name']] = item_counts.get(item_details['name'], 0) + item_details['quantity']
            item_category = item_to_category.get(item_id)
            if item_category:
                category_revenue[item_category] = category_revenue.get(item_category, 0) + item_details['price'] * item_details['quantity']

    popular_items = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    analytics = {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "popular_items": popular_items,
        "category_revenue": category_revenue
    }

    # Prepare cart data for template - only show confirmed orders
    cart_data = {}
    for table, items in CART.items():
        meta = items.get("_meta", {})
        status = meta.get("status", "Preparing")
        
        if status in ["Ordered", "Cooking", "Served", "Paid"]:
            cart_items = {k: v for k, v in items.items() if k != "_meta"}
            if cart_items:
                cart_data[table] = {
                    "items": cart_items,
                    "status": status,
                    "last_updated": meta.get("last_updated", ""),
                    "total": cart_total(cart_items)
                }
    return render_template("admin.html", carts=cart_data, admins=admins, analytics=analytics)

@app.route("/delete_cart/<table_number>", methods=["POST"])
@admin_required
def delete_cart(table_number):
    if table_number in CART:
        del CART[table_number]
        socketio.emit("cart_deleted", {"table_number": table_number})
    return redirect(url_for('admin_panel'))

@app.route('/admin_add', methods=['POST'])
@admin_required
def admin_add():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        flash('Username and password required', 'danger')
        return redirect(url_for('admin_panel'))
    if find_admin(username):
        flash('Admin already exists', 'danger')
        return redirect(url_for('admin_panel'))
    admins = load_admins()
    admins.append({
        'username': username,
        'password': generate_password_hash(password)
    })
    save_admins(admins)
    flash('Admin added', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin_remove', methods=['POST'])
@admin_required
def admin_remove():
    username = request.form.get('username')
    if not username:
        flash('Username required', 'danger')
        return redirect(url_for('admin_panel'))
    if username == session.get('admin_username'):
        flash('You cannot remove yourself', 'danger')
        return redirect(url_for('admin_panel'))
    admins = load_admins()
    admins = [a for a in admins if a['username'] != username]
    save_admins(admins)
    flash('Admin removed', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/submit_order', methods=['POST'])
def submit_order():
    table_number = session.get('table_number')
    if not table_number or table_number not in CART:
        return jsonify({'error': 'Invalid table number or empty cart'}), 400
    
    cart_items = {k: v for k, v in CART[table_number].items() if k != "_meta"}
    total_amount = cart_total(cart_items)
    item_count = sum(item["quantity"] for item in cart_items.values())
    
    CART[table_number]['_meta']['status'] = 'Ordered'
    CART[table_number]['_meta']['last_updated'] = datetime.now().isoformat()
    
    socketio.emit('order_confirmed_notification', {
        "table_number": table_number,
        "total_amount": total_amount,
        "item_count": item_count,
        "message": f"🎉 NEW ORDER CONFIRMED! Table {table_number} - {item_count} items - ₹{total_amount:.2f}"
    })
    
    socketio.emit('admin_cart_update', {'carts': CART})
    return jsonify({'success': True, 'message': 'Order placed successfully!'})

@app.route('/api/analytics/overview')
@admin_required
def api_analytics_overview():
    """Get overview analytics data from database"""
    try:
        conn = sqlite3.connect('instance/restaurant.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT SUM(total_amount), COUNT(*) FROM completed_orders')
        result = cursor.fetchone()
        total_revenue = result[0] or 0
        total_orders = result[1] or 0
        
        avg_order = total_revenue / total_orders if total_orders > 0 else 0
        
        cursor.execute('''
            SELECT category, SUM(item_price * quantity) as revenue
            FROM order_items
            GROUP BY category
        ''')
        category_data = cursor.fetchall()
        category_revenue = {cat: rev for cat, rev in category_data}
        
        top_category = max(category_revenue, key=category_revenue.get) if category_revenue else "None"
        
        cursor.execute('''
            SELECT DATE(order_date) as order_day, SUM(total_amount) as daily_revenue
            FROM completed_orders
            WHERE order_date >= date('now', '-7 days')
            GROUP BY DATE(order_date)
            ORDER BY order_day
        ''')
        daily_data = cursor.fetchall()
        
        revenue_labels = []
        revenue_values = []
        for i in range(7):
            date = datetime.now() - timedelta(days=6-i)
            date_str = date.strftime('%Y-%m-%d')
            revenue_labels.append(date.strftime('%m/%d'))
            
            day_revenue = 0
            for day, revenue in daily_data:
                if day == date_str:
                    day_revenue = revenue
                    break
            revenue_values.append(day_revenue)
        
        category_labels = list(category_revenue.keys())
        category_values = list(category_revenue.values())
        
        conn.close()
        
        return jsonify({
            'totalRevenue': total_revenue,
            'totalOrders': total_orders,
            'avgOrder': avg_order,
            'topCategory': top_category.title(),
            'revenueData': {
                'labels': revenue_labels,
                'values': revenue_values
            },
            'categoryData': {
                'labels': [cat.title() for cat in category_labels],
                'values': category_values
            }
        })
        
    except Exception as e:
        print(f"Error in overview analytics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/daily')
@admin_required
def api_analytics_daily():
    """Get daily sales data for last 30 days"""
    try:
        conn = sqlite3.connect('instance/restaurant.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DATE(order_date) as order_day, 
                   SUM(total_amount) as daily_revenue,
                   COUNT(*) as daily_orders
            FROM completed_orders
            WHERE order_date >= date('now', '-30 days')
            GROUP BY DATE(order_date)
            ORDER BY order_day
        ''')
        daily_data = cursor.fetchall()
        
        labels = []
        revenue_values = []
        orders_values = []

        for i in range(30):
            date = datetime.now() - timedelta(days=29-i)
            date_str = date.strftime('%Y-%m-%d')
            labels.append(date.strftime('%m/%d'))

            day_revenue = 0
            day_orders = 0
            for day, revenue_amt, orders_cnt in daily_data:
                if day == date_str:
                    day_revenue = revenue_amt
                    day_orders = orders_cnt
                    break
            revenue_values.append(day_revenue)
            orders_values.append(day_orders)

        conn.close()

        return jsonify({
            'labels': labels,
            'revenue': revenue_values,
            'orders': orders_values
        })

    except Exception as e:
        print(f"Error in daily analytics: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=port, debug=True)