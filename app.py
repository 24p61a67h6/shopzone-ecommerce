from flask import Flask, render_template, redirect, url_for, session, request
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Secret key for sessions
app.secret_key = "shopzone_secret_key"


# ==========================================================
# DATABASE CONNECTION
# ==========================================================

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# ==========================================================
# CREATE DATABASE
# ==========================================================

def create_database():

    conn = get_db()
    cursor = conn.cursor()

    # ======================================================
    # PRODUCTS TABLE
    # ======================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            old_price REAL,
            rating REAL,
            image TEXT,
            stock INTEGER DEFAULT 10
        )
    """)

    # Check whether old database has stock column
    columns = [
        row["name"]
        for row in cursor.execute(
            "PRAGMA table_info(products)"
        ).fetchall()
    ]

    if "stock" not in columns:
        cursor.execute(
            "ALTER TABLE products ADD COLUMN stock INTEGER DEFAULT 10"
        )

    # ======================================================
    # USERS TABLE
    # ======================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # ======================================================
    # WISHLIST TABLE
    # ======================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wishlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            UNIQUE(user_id, product_id)
        )
    """)

    # ======================================================
    # ORDERS TABLE
    # ======================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            city TEXT NOT NULL,
            pincode TEXT NOT NULL,
            payment TEXT NOT NULL,
            total REAL NOT NULL,
            status TEXT DEFAULT 'Placed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ======================================================
    # ORDER ITEMS TABLE
    # ======================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL
        )
    """)

    # ======================================================
    # ADD PRODUCTS
    # ======================================================

    count = cursor.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]

    if count == 0:

        products = [

            (
                "Samsung Galaxy Smartphone",
                "Mobiles",
                15999,
                19999,
                4.4,
                "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9",
                25
            ),

            (
                "HP Laptop",
                "Electronics",
                55999,
                69999,
                4.5,
                "https://images.unsplash.com/photo-1496181133206-80ce9b88a853",
                15
            ),

            (
                "Wireless Headphones",
                "Electronics",
                2499,
                4999,
                4.3,
                "https://images.unsplash.com/photo-1505740420928-5e560c06d30e",
                30
            ),

            (
                "Smart Watch",
                "Electronics",
                3999,
                6999,
                4.2,
                "https://images.unsplash.com/photo-1523275335684-37898b6baf30",
                20
            ),

            (
                "Running Shoes",
                "Fashion",
                2999,
                4999,
                4.1,
                "https://images.unsplash.com/photo-1542291026-7eec264c27ff",
                40
            ),

            (
                "DSLR Camera",
                "Electronics",
                44999,
                59999,
                4.6,
                "https://images.unsplash.com/photo-1516035069371-29a1b244cc32",
                10
            )
        ]

        cursor.executemany("""
            INSERT INTO products
            (
                name,
                category,
                price,
                old_price,
                rating,
                image,
                stock
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, products)

    conn.commit()
    conn.close()


# ==========================================================
# HOME / SEARCH / CATEGORY / FILTER / SORT
# ==========================================================

@app.route("/")
def home():

    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    sort = request.args.get("sort", "").strip()
    max_price = request.args.get("max_price", "").strip()

    conn = get_db()

    query = "SELECT * FROM products WHERE 1=1"
    params = []

    # SEARCH
    if search:

        query += """
            AND (
                name LIKE ?
                OR category LIKE ?
            )
        """

        params.append("%" + search + "%")
        params.append("%" + search + "%")

    # CATEGORY
    if category:

        query += " AND category = ?"
        params.append(category)

    # MAX PRICE
    if max_price:

        try:

            max_price_value = float(max_price)

            query += " AND price <= ?"
            params.append(max_price_value)

        except ValueError:

            max_price = ""

    # SORT
    if sort == "low":

        query += " ORDER BY price ASC"

    elif sort == "high":

        query += " ORDER BY price DESC"

    elif sort == "rating":

        query += " ORDER BY rating DESC"

    else:

        query += " ORDER BY id ASC"

    products = conn.execute(
        query,
        params
    ).fetchall()

    # ======================================================
    # WISHLIST IDS
    # ======================================================

    wishlist_ids = []

    if "user_id" in session:

        wishlist_rows = conn.execute(
            """
            SELECT product_id
            FROM wishlist
            WHERE user_id = ?
            """,
            (session["user_id"],)
        ).fetchall()

        wishlist_ids = [
            row["product_id"]
            for row in wishlist_rows
        ]

    conn.close()

    return render_template(
        "index.html",
        products=products,
        search=search,
        category=category,
        sort=sort,
        max_price=max_price,
        wishlist_ids=wishlist_ids
    )


# ==========================================================
# REGISTER
# ==========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        # Password validation
        if len(password) < 6:

            return render_template(
                "register.html",
                error="Password must contain at least 6 characters."
            )

        conn = get_db()

        existing_user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        if existing_user:

            conn.close()

            return render_template(
                "register.html",
                error="Email already registered"
            )

        # ==================================================
        # HASH PASSWORD
        # ==================================================

        hashed_password = generate_password_hash(password)

        conn.execute(
            """
            INSERT INTO users
            (
                name,
                email,
                password
            )
            VALUES (?, ?, ?)
            """,
            (
                name,
                email,
                hashed_password
            )
        )

        conn.commit()
        conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# ==========================================================
# LOGIN
# ==========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip().lower()
        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        # ==================================================
        # CHECK HASHED PASSWORD
        # ==================================================

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]

            conn.close()

            return redirect(url_for("home"))

        conn.close()

        return render_template(
            "login.html",
            error="Invalid email or password"
        )

    return render_template("login.html")


# ==========================================================
# LOGOUT
# ==========================================================

@app.route("/logout")
def logout():

    session.pop("user_id", None)
    session.pop("user_name", None)
    session.pop("user_email", None)

    return redirect(url_for("home"))


# ==========================================================
# PRODUCT DETAILS
# ==========================================================

@app.route("/product/<int:product_id>")
def product(product_id):

    conn = get_db()

    product = conn.execute(
        """
        SELECT *
        FROM products
        WHERE id = ?
        """,
        (product_id,)
    ).fetchone()

    conn.close()

    if product is None:

        return "Product not found", 404

    return render_template(
        "product.html",
        product=product
    )


# ==========================================================
# ADD TO CART
# ==========================================================

@app.route("/add-to-cart/<int:product_id>")
def add_to_cart(product_id):

    conn = get_db()

    product = conn.execute(
        """
        SELECT *
        FROM products
        WHERE id = ?
        """,
        (product_id,)
    ).fetchone()

    conn.close()

    if product is None:

        return "Product not found", 404

    if product["stock"] <= 0:

        return redirect(url_for("home"))

    cart = session.get("cart", {})

    product_id = str(product_id)

    if product_id in cart:

        if cart[product_id] < product["stock"]:

            cart[product_id] += 1

    else:

        cart[product_id] = 1

    session["cart"] = cart

    return redirect(url_for("cart"))


# ==========================================================
# CART
# ==========================================================

@app.route("/cart")
def cart():

    cart = session.get("cart", {})

    products = []
    total = 0

    conn = get_db()

    for product_id, quantity in cart.items():

        product = conn.execute(
            """
            SELECT *
            FROM products
            WHERE id = ?
            """,
            (product_id,)
        ).fetchone()

        if product:

            # Make sure quantity doesn't exceed stock
            quantity = min(
                quantity,
                product["stock"]
            )

            if quantity <= 0:
                continue

            item_total = product["price"] * quantity

            total += item_total

            products.append({
                "product": product,
                "quantity": quantity,
                "item_total": item_total
            })

    conn.close()

    return render_template(
        "cart.html",
        products=products,
        total=total
    )


# ==========================================================
# INCREASE QUANTITY
# ==========================================================

@app.route("/increase/<int:product_id>")
def increase(product_id):

    cart = session.get("cart", {})

    product_id = str(product_id)

    conn = get_db()

    product = conn.execute(
        """
        SELECT stock
        FROM products
        WHERE id = ?
        """,
        (product_id,)
    ).fetchone()

    conn.close()

    if product and product_id in cart:

        if cart[product_id] < product["stock"]:

            cart[product_id] += 1

    session["cart"] = cart

    return redirect(url_for("cart"))


# ==========================================================
# DECREASE QUANTITY
# ==========================================================

@app.route("/decrease/<int:product_id>")
def decrease(product_id):

    cart = session.get("cart", {})

    product_id = str(product_id)

    if product_id in cart:

        cart[product_id] -= 1

        if cart[product_id] <= 0:

            del cart[product_id]

    session["cart"] = cart

    return redirect(url_for("cart"))


# ==========================================================
# REMOVE FROM CART
# ==========================================================

@app.route("/remove/<int:product_id>")
def remove(product_id):

    cart = session.get("cart", {})

    product_id = str(product_id)

    if product_id in cart:

        del cart[product_id]

    session["cart"] = cart

    return redirect(url_for("cart"))


# ==========================================================
# WISHLIST
# ==========================================================

@app.route("/wishlist")
def wishlist():

    if "user_id" not in session:

        return redirect(url_for("login"))

    conn = get_db()

    products = conn.execute(
        """
        SELECT products.*
        FROM products
        INNER JOIN wishlist
        ON products.id = wishlist.product_id
        WHERE wishlist.user_id = ?
        ORDER BY wishlist.id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "wishlist.html",
        products=products
    )


# ==========================================================
# ADD TO WISHLIST
# ==========================================================

@app.route("/add-to-wishlist/<int:product_id>")
def add_to_wishlist(product_id):

    if "user_id" not in session:

        return redirect(url_for("login"))

    conn = get_db()

    product = conn.execute(
        """
        SELECT *
        FROM products
        WHERE id = ?
        """,
        (product_id,)
    ).fetchone()

    if product is None:

        conn.close()

        return "Product not found", 404

    conn.execute(
        """
        INSERT OR IGNORE INTO wishlist
        (
            user_id,
            product_id
        )
        VALUES (?, ?)
        """,
        (
            session["user_id"],
            product_id
        )
    )

    conn.commit()
    conn.close()

    return redirect(
        request.referrer or url_for("home")
    )


# ==========================================================
# REMOVE FROM WISHLIST
# ==========================================================

@app.route("/remove-from-wishlist/<int:product_id>")
def remove_from_wishlist(product_id):

    if "user_id" not in session:

        return redirect(url_for("login"))

    conn = get_db()

    conn.execute(
        """
        DELETE FROM wishlist
        WHERE user_id = ?
        AND product_id = ?
        """,
        (
            session["user_id"],
            product_id
        )
    )

    conn.commit()
    conn.close()

    return redirect(
        request.referrer or url_for("wishlist")
    )


# ==========================================================
# CHECKOUT
# ==========================================================

@app.route("/checkout", methods=["GET", "POST"])
def checkout():

    cart = session.get("cart", {})

    if not cart:

        return redirect(url_for("cart"))

    products = []
    total = 0

    conn = get_db()

    # ======================================================
    # GET CART PRODUCTS
    # ======================================================

    for product_id, quantity in cart.items():

        product = conn.execute(
            """
            SELECT *
            FROM products
            WHERE id = ?
            """,
            (product_id,)
        ).fetchone()

        if product:

            # Check stock
            if quantity > product["stock"]:

                quantity = product["stock"]

                cart[product_id] = quantity

            if quantity <= 0:

                continue

            item_total = product["price"] * quantity

            total += item_total

            products.append({
                "product": product,
                "quantity": quantity,
                "item_total": item_total
            })

    # ======================================================
    # PLACE ORDER
    # ======================================================

    if request.method == "POST":

        name = request.form["name"].strip()
        phone = request.form["phone"].strip()
        address = request.form["address"].strip()
        city = request.form["city"].strip()
        pincode = request.form["pincode"].strip()
        payment = request.form["payment"]

        user_id = session.get("user_id")

        # ==================================================
        # FINAL STOCK CHECK
        # ==================================================

        for product_id, quantity in cart.items():

            product = conn.execute(
                """
                SELECT *
                FROM products
                WHERE id = ?
                """,
                (product_id,)
            ).fetchone()

            if not product:

                conn.close()

                return "Product not found", 404

            if quantity > product["stock"]:

                conn.close()

                return redirect(url_for("cart"))

        # ==================================================
        # CREATE ORDER
        # ==================================================

        cursor = conn.execute(
            """
            INSERT INTO orders
            (
                user_id,
                name,
                phone,
                address,
                city,
                pincode,
                payment,
                total
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                name,
                phone,
                address,
                city,
                pincode,
                payment,
                total
            )
        )

        order_id = cursor.lastrowid

        # ==================================================
        # ADD ORDER ITEMS
        # ==================================================

        for product_id, quantity in cart.items():

            product = conn.execute(
                """
                SELECT *
                FROM products
                WHERE id = ?
                """,
                (product_id,)
            ).fetchone()

            if product:

                conn.execute(
                    """
                    INSERT INTO order_items
                    (
                        order_id,
                        product_id,
                        quantity,
                        price
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        order_id,
                        product["id"],
                        quantity,
                        product["price"]
                    )
                )

                # Reduce stock
                conn.execute(
                    """
                    UPDATE products
                    SET stock = stock - ?
                    WHERE id = ?
                    """,
                    (
                        quantity,
                        product["id"]
                    )
                )

        conn.commit()
        conn.close()

        session["last_order_id"] = order_id

        session.pop("cart", None)

        return redirect(
            url_for("order_success")
        )

    conn.close()

    return render_template(
        "checkout.html",
        products=products,
        total=total
    )


# ==========================================================
# ORDER SUCCESS
# ==========================================================

@app.route("/order-success")
def order_success():

    order_id = session.get("last_order_id")

    if not order_id:

        return redirect(url_for("home"))

    conn = get_db()

    order = conn.execute(
        """
        SELECT *
        FROM orders
        WHERE id = ?
        """,
        (order_id,)
    ).fetchone()

    conn.close()

    return render_template(
        "order_success.html",
        order=order
    )


# ==========================================================
# MY ORDERS
# ==========================================================

@app.route("/orders")
def orders():

    if "user_id" not in session:

        return redirect(url_for("login"))

    conn = get_db()

    orders = conn.execute(
        """
        SELECT *
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "orders.html",
        orders=orders
    )


# ==========================================================
# ORDER DETAILS
# ==========================================================

@app.route("/order/<int:order_id>")
def order_details(order_id):

    if "user_id" not in session:

        return redirect(url_for("login"))

    conn = get_db()

    order = conn.execute(
        """
        SELECT *
        FROM orders
        WHERE id = ?
        AND user_id = ?
        """,
        (
            order_id,
            session["user_id"]
        )
    ).fetchone()

    if not order:

        conn.close()

        return "Order not found", 404

    items = conn.execute(
        """
        SELECT
            order_items.*,
            products.name,
            products.image
        FROM order_items
        INNER JOIN products
        ON order_items.product_id = products.id
        WHERE order_items.order_id = ?
        """,
        (order_id,)
    ).fetchall()

    conn.close()

    return render_template(
        "order_details.html",
        order=order,
        items=items
    )


# ==========================================================
# PROFILE
# ==========================================================

@app.route("/profile", methods=["GET", "POST"])
def profile():

    if "user_id" not in session:

        return redirect(url_for("login"))

    conn = get_db()

    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        """,
        (session["user_id"],)
    ).fetchone()

    if not user:

        conn.close()

        session.clear()

        return redirect(url_for("login"))

    # ======================================================
    # UPDATE PROFILE
    # ======================================================

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()

        # Basic validation
        if not name or not email:

            conn.close()

            return render_template(
                "profile.html",
                user=user,
                error="Name and email cannot be empty."
            )

        try:

            conn.execute(
                """
                UPDATE users
                SET name = ?, email = ?
                WHERE id = ?
                """,
                (
                    name,
                    email,
                    session["user_id"]
                )
            )

            conn.commit()

            # Update session
            session["user_name"] = name
            session["user_email"] = email

            user = conn.execute(
                """
                SELECT *
                FROM users
                WHERE id = ?
                """,
                (session["user_id"],)
            ).fetchone()

            conn.close()

            return render_template(
                "profile.html",
                user=user,
                success="Profile updated successfully!"
            )

        except sqlite3.IntegrityError:

            conn.close()

            return render_template(
                "profile.html",
                user=user,
                error="This email is already registered."
            )

    conn.close()

    return render_template(
        "profile.html",
        user=user
    )


# ==========================================================
# START APPLICATION
# ==========================================================

if __name__ == "__main__":

    create_database()

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )