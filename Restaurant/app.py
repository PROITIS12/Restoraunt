from flask import Flask, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from tables import db, User, Dish, CartItem, Reservation

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tryhardwoman'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restaurant.db'
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_request
def create_tables():
    db.create_all()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if User.query.filter_by(username=username).first():
            return redirect(url_for("register"))
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/menu")
@login_required
def menu():
    categories = db.session.query(Dish.category).distinct().all()
    categorized_dishes = {}
    for category_tuple in categories:
        category = category_tuple[0]
        dishes_in_category = Dish.query.filter_by(category=category).all()
        categorized_dishes[category] = dishes_in_category

    return render_template("menu.html", categorized_dishes=categorized_dishes)

@app.route("/dish/<int:dish_id>")
def dish_detail(dish_id):
    dish = Dish.query.get_or_404(dish_id)
    return render_template("dish_detail.html", dish=dish)

@app.route("/add_to_cart/<int:dish_id>", methods=["POST"])
@login_required
def add_to_cart(dish_id):
    quantity = int(request.form["quantity"])
    dish = Dish.query.get_or_404(dish_id)
    existing_item = CartItem.query.filter_by(user_id=current_user.id, dish_id=dish_id).first()
    if existing_item:
        existing_item.quantity += quantity
    else:
        new_item = CartItem(user_id=current_user.id, dish_id=dish_id, quantity=quantity)
        db.session.add(new_item)

    db.session.commit()
    return redirect(url_for('menu'))

@app.route("/cart")
@login_required
def cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total_price = sum(item.dish.price * item.quantity for item in cart_items)
    return render_template("cart.html", cart_items=cart_items, total_price=total_price)

@app.route('/reserve', methods=['GET', 'POST'])
def reserve_table():
    if request.method == 'POST':
        name = request.form['name']
        people_quantity = request.form['people_count']
        date = request.form['date']
        time = request.form['time']
        phone = request.form['phone']
        if not all([name, people_quantity, date, time, phone]):
            return "Треба вписати всю інформацію"
        reservation = Reservation(
            name=name,
            people_quantity=int(people_quantity),
            date=date,
            time=time,
            phone=phone
        )
        db.session.add(reservation)
        db.session.commit()
        return redirect(url_for("dashboard"))
    return render_template("reserve.html")

@app.route("/admin")
@login_required
def admin_panel():
    if current_user.username != "admin":
        return redirect(url_for("dashboard"))
    return render_template("admin_panel.html")

from flask import abort

@app.route("/admin/orders")
@login_required
def admin_orders():
    if current_user.username != "admin":
        abort(403)

    orders = CartItem.query.all()
    return render_template("admin_orders.html", orders=orders)


@app.route("/admin/users")
@login_required
def admin_users():
    if current_user.username != "admin":
        abort(403)

    users = User.query.all()
    return render_template("admin_users.html", users=users)


@app.route("/admin/reservations")
@login_required
def admin_reservations():
    if current_user.username != "admin":
        abort(403)

    reservations = Reservation.query.all()
    return render_template("admin_reservations.html", reservations=reservations)

@app.route("/admin/delete_order/<int:order_id>", methods=["POST"])
def delete_order(order_id):
    order = CartItem.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    return redirect(url_for("admin_orders"))


@app.route("/admin/delete_user/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.username == "admin":
        return None
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for("admin_users"))

@app.route("/admin/delete_reservation/<int:reservation_id>", methods=["POST"])
def delete_reservation(reservation_id):
    r = Reservation.query.get_or_404(reservation_id)
    db.session.delete(r)
    db.session.commit()
    return redirect(url_for("admin_reservations"))

@app.route('/admin/dishes')
def admin_dishes():
    dishes = Dish.query.all()
    return render_template('admin_dishes.html', dishes=dishes)


@app.route('/admin/delete_dish/<int:dish_id>', methods=['POST'])
def delete_dish(dish_id):
    dish = Dish.query.get_or_404(dish_id)
    db.session.delete(dish)
    db.session.commit()
    return redirect(url_for('admin_dishes'))

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)

if __name__ == "__main__":
    app.run(debug=True)
