import os
from flask import Flask, render_template, request, url_for, redirect, session, jsonify
import random
import pandas as pd
from sklearn.linear_model import LinearRegression
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import werkzeug.utils

app = Flask(__name__)
app.secret_key = "change-this-to-something-random"  # needed for session to work

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'app_v3.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="user")

class UserLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('logs', lazy=True))

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    broker_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    area = db.Column(db.Integer, nullable=False)
    bedrooms = db.Column(db.String(50), nullable=False)
    contact = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    title = db.Column(db.String(255), nullable=True)
    price = db.Column(db.String(50), nullable=True)
    property_type = db.Column(db.String(100), nullable=True)
    bathrooms = db.Column(db.String(50), nullable=True)
    year_built = db.Column(db.Integer, nullable=True)
    lot_size = db.Column(db.Float, nullable=True)
    amenities = db.Column(db.String(500), nullable=True)
    views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    broker = db.relationship('User', backref=db.backref('properties', lazy=True))

with app.app_context():
    os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)
    db.create_all()

# --- Load data & train model once at startup ---
data = pd.read_csv('cleaned_data - Copy.csv')
data_encoded = pd.get_dummies(data, columns=['location'])

X = data_encoded.drop('price', axis=1)
y = data_encoded['price']

model = LinearRegression()
model.fit(X, y)

# Keep the exact column order the model was trained on — we need this
# to build a matching input row at prediction time.
model_columns = X.columns


@app.route("/")
def login_page():
    if session.get("logged_in"):
        return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        session["logged_in"] = True
        session["user_id"] = user.id
        session["username"] = user.username
        session["role"] = user.role
        
        # Log the login action
        new_log = UserLog(user_id=user.id, action='login')
        db.session.add(new_log)
        db.session.commit()
        
        if user.role == 'broker':
            return redirect(url_for("broker_upload"))
        return redirect(url_for("index"))
    else:
        return render_template("login.html", error="Invalid username or password")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form.get("confirm_password", "")

        role = request.form.get("role", "user")

        if password != confirm_password:
            return render_template("signup.html", error="Passwords do not match")

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template("signup.html", error="Username already exists")

        new_user = User(
            username=username,
            password_hash=generate_password_hash(password),
            role=role
        )
        db.session.add(new_user)
        db.session.commit()

        session["logged_in"] = True
        session["user_id"] = new_user.id
        session["username"] = new_user.username
        session["role"] = new_user.role
        
        # Log the signup and login action
        new_log = UserLog(user_id=new_user.id, action='signup_and_login')
        db.session.add(new_log)
        db.session.commit()
        
        if role == 'broker':
            return redirect(url_for("broker_upload"))
        return redirect(url_for("index"))

    return render_template("signup.html")


@app.route("/index")
def index():
    if not session.get("logged_in"):
        return redirect(url_for("login_page"))
    locations = sorted(data["location"].unique())
    latest_properties = Property.query.order_by(Property.created_at.desc()).limit(10).all()
    return render_template("index.html", locations=locations, latest_properties=latest_properties)


@app.route("/profile")
def profile():
    if not session.get("logged_in"):
        return redirect(url_for("login_page"))
    user = User.query.get(session["user_id"])
    broker_properties = []
    if user and user.role == "broker":
        broker_properties = Property.query.filter_by(broker_id=user.id).order_by(Property.created_at.desc()).all()
    
    return render_template("profile.html", user=user, broker_properties=broker_properties)

@app.route("/delete_property/<int:property_id>", methods=["POST"])
def delete_property(property_id):
    if not session.get("logged_in") or session.get("role") != "broker":
        return redirect(url_for("login_page"))
        
    prop = Property.query.get_or_404(property_id)
    if prop.broker_id != session.get("user_id"):
        return "Unauthorized", 403
        
    db.session.delete(prop)
    db.session.commit()
    return redirect(url_for("profile"))

@app.route("/edit_property/<int:property_id>", methods=["GET", "POST"])
def edit_property(property_id):
    if not session.get("logged_in") or session.get("role") != "broker":
        return redirect(url_for("login_page"))
        
    prop = Property.query.get_or_404(property_id)
    if prop.broker_id != session.get("user_id"):
        return "Unauthorized", 403
        
    if request.method == "POST":
        prop.location = request.form.get("location")
        area = request.form.get("area")
        prop.area = int(area) if area.isdigit() else 0
        prop.bedrooms = request.form.get("bedroom")
        prop.contact = request.form.get("contact")
        
        price = request.form.get("price")
        if price:
            prop.price = price
        
        # Handle optional new image upload
        images = request.files.getlist("images")
        if images and images[0].filename:
            first_image = images[0]
            filename = werkzeug.utils.secure_filename(first_image.filename)
            upload_dir = os.path.join(app.root_path, "static", "uploads")
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, filename)
            first_image.save(file_path)
            prop.image_url = url_for("static", filename="uploads/" + filename)
            
        db.session.commit()
        return redirect(url_for("profile"))
        
    return render_template("edit_property.html", prop=prop)
    
@app.route("/property/<int:property_id>")
def property_detail(property_id):
    if not session.get("logged_in"):
        return redirect(url_for("login_page"))
    
    prop = Property.query.get_or_404(property_id)
    
    # Increment views
    if prop.views is None:
        prop.views = 0
    prop.views += 1
    db.session.commit()
    
    user = User.query.get(session["user_id"])
    return render_template("property_detail.html", prop=prop, user=user)

@app.route("/broker_upload", methods=["GET", "POST"])
def broker_upload():
    if not session.get("logged_in") or session.get("role") != "broker":
        return redirect(url_for("login_page"))
        
    if request.method == "POST":
        location = request.form.get("location") or "Unknown"
        area = request.form.get("area", "0")
        bedroom = request.form.get("bedroom") or "1"
        contact = request.form.get("contact", "")
        
        # New fields from the custom UI
        price = request.form.get("price")
        title = request.form.get("title")
        property_type = request.form.get("property_type")
        bathrooms = request.form.get("bathrooms")
        year_built = request.form.get("year_built")
        lot_size = request.form.get("lot_size")
        
        # Get all checked amenities
        amenities_list = request.form.getlist("amenities")
        amenities_str = ", ".join(amenities_list) if amenities_list else ""
        
        # Handle file upload
        images = request.files.getlist("images")
        image_url = ""
        if images and images[0].filename:
            first_image = images[0]
            filename = werkzeug.utils.secure_filename(first_image.filename)
            upload_dir = os.path.join(app.root_path, "static", "uploads")
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, filename)
            first_image.save(file_path)
            image_url = url_for("static", filename="uploads/" + filename)
        else:
            # Fallback placeholder image
            image_url = "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?auto=format&fit=crop&w=400&q=80"
            
        new_property = Property(
            broker_id=session.get("user_id"),
            location=location,
            area=int(area) if str(area).isdigit() else 0,
            bedrooms=bedroom,
            contact=contact,
            image_url=image_url,
            title=title,
            price=price if price else None,
            property_type=property_type,
            bathrooms=bathrooms,
            year_built=int(year_built) if str(year_built).isdigit() else None,
            lot_size=float(lot_size) if lot_size else None,
            amenities=amenities_str
        )
        db.session.add(new_property)
        db.session.commit()
        
        return render_template("broker_upload.html", success="Property listed successfully!")
        
    return render_template("broker_upload.html")


@app.route("/admin")
def admin_dashboard():
    # In a real application, you would secure this route to only allow 'admin' users.
    # For now, it's accessible to anyone for demonstration.
    logs = UserLog.query.order_by(UserLog.timestamp.desc()).limit(100).all()
    
    # Calculate simple stats
    total_users = User.query.count()
    total_logins = UserLog.query.filter_by(action='login').count()
    
    return render_template("admin.html", logs=logs, total_users=total_users, total_logins=total_logins)


@app.route("/logout")
def logout():
    user_id = session.get("user_id")
    if user_id:
        new_log = UserLog(user_id=user_id, action='logout')
        db.session.add(new_log)
        db.session.commit()
        
    session.pop("logged_in", None)
    session.pop("user_id", None)
    session.pop("username", None)
    session.pop("role", None)
    return redirect(url_for("login_page"))


@app.route("/predict", methods=["POST"])
def predict():
    if not session.get("logged_in"):
        return redirect(url_for("login_page"))

    location = request.form.get("location")
    sqft = float(request.form["sqft"])
    bath = int(request.form["bath"])
    bhk = int(request.form["BHK"])

    # Build a single-row input matching the training columns exactly
    input_row = pd.DataFrame([[0] * len(model_columns)], columns=model_columns)

    # Fill in the numeric features (adjust names if your CSV uses different ones)
    for col_name, value in [("total_sqft", sqft), ("bath", bath), ("bhk", bhk)]:
        if col_name in input_row.columns:
            input_row[col_name] = value

    # Set the one-hot column for the chosen location, if it exists
    loc_col = f"location_{location}"
    if loc_col in input_row.columns:
        input_row[loc_col] = 1

    prediction = model.predict(input_row)[0]
    
    # Ensure prediction is not negative
    if prediction < 0:
        prediction = abs(prediction)
        
    if prediction >= 100:
        price_str = f"₹ {round(prediction / 100, 2)} Cr"
    else:
        price_str = f"₹ {round(prediction, 2)} Lakh"
        
    images = [
        "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=800&q=80"
    ]
    # Pick a consistent image for a given location
    idx = sum(ord(c) for c in location) % len(images)
    image_url = images[idx]

    return render_template(
        "predict.html",
        price=price_str,
        location=location,
        sqft=sqft,
        bath=bath,
        bhk=bhk,
        image_url=image_url
    )


@app.route("/map")
def map_page():
    if not session.get("logged_in"):
        return redirect(url_for("login_page"))
    return render_template("map.html")


import urllib.request
import urllib.parse
import json
import hashlib

def get_seeded_random(seed_str):
    hash_val = int(hashlib.md5(seed_str.encode('utf-8')).hexdigest(), 16)
    return random.Random(hash_val)

@app.route("/api/listings")
def api_listings():
    n = request.args.get('n')
    s = request.args.get('s')
    e = request.args.get('e')
    w = request.args.get('w')
    
    if not all([n, s, e, w]):
        lat = float(request.args.get('lat', 12.9698))
        lng = float(request.args.get('lng', 77.7499))
        n, s, e, w = lat + 0.05, lat - 0.05, lng + 0.05, lng - 0.05
    else:
        n, s, e, w = float(n), float(s), float(e), float(w)

    types = ["Hotel", "Hostel", "PG", "Villa for Rent", "Room for Rent", "House for Sale", "Apartment for Sale"]
    adjectives = ["Grand", "Cozy", "Urban", "Elite", "Comfort", "Sunrise", "Royal", "Lakeview", "Skyline", "Ocean", "Green", "Golden", "Silver", "Crystal", "Emerald", "Sapphire", "Diamond", "Majestic", "Serene", "Tranquil", "Prime", "Lush", "Regal", "Noble", "Elegance"]
    nouns = ["Stay", "Nest", "Living", "Spaces", "Zone", "Valley", "Heritage", "View", "Meadows", "Heights", "Residency", "Enclave", "Court", "Plaza", "Gardens", "Park", "Woods", "Ridge", "Hill", "Crest", "Point", "Oasis", "Haven", "Retreat", "Sanctuary"]
    broker_names = ["Mr. Sharma", "Ms. Gupta", "Rohan Singh", "Amit Kumar", "Neha Reddy", "Vikram Patel", "Priya Desai", "Mr. Khan", "Suresh Iyer", "Pooja Verma", "Anjali Nair", "Rahul Menon", "Deepa Joshi", "Karthik Raj", "Sneha Rao"]

    listings = []
    GRID_SIZE = 0.005 # Approx 500 meters
    
    import math
    start_lat = math.floor(s / GRID_SIZE) * GRID_SIZE
    end_lat = math.ceil(n / GRID_SIZE) * GRID_SIZE
    start_lng = math.floor(w / GRID_SIZE) * GRID_SIZE
    end_lng = math.ceil(e / GRID_SIZE) * GRID_SIZE

    lat = start_lat
    while lat <= end_lat:
        lng = start_lng
        while lng <= end_lng:
            grid_lat, grid_lng = round(lat, 4), round(lng, 4)
            cell_seed = f"{grid_lat}_{grid_lng}"
            rng = get_seeded_random(cell_seed)
            
            if rng.random() < 0.6: # 60% chance of property in this cell
                prop_type = rng.choice(types)
                base_type = prop_type.split(' for')[0] if 'for' in prop_type else prop_type
                
                # Create a unique-sounding name
                adj = rng.choice(adjectives)
                noun = rng.choice(nouns)
                number = rng.randint(1, 999)
                name = f"{adj} {noun} {base_type} {number}"
                
                actual_lat = grid_lat + rng.uniform(-GRID_SIZE/2, GRID_SIZE/2)
                actual_lng = grid_lng + rng.uniform(-GRID_SIZE/2, GRID_SIZE/2)
                
                if prop_type == "Hotel":
                    price, price_str = rng.randint(1500, 5000), f"₹{rng.randint(1500, 5000)}/night"
                    details = f"{rng.choice(['3', '4', '5'])} Star Hotel • Free WiFi"
                elif "Sale" in prop_type:
                    price_lakhs = rng.randint(40, 250)
                    price_str = f"₹{price_lakhs / 100:.2f} Cr" if price_lakhs >= 100 else f"₹{price_lakhs} Lakhs"
                    details = f"{rng.randint(2, 5)} Beds • {rng.randint(1, 4)} Baths • {rng.randint(800, 3500)} sqft"
                elif "Villa" in prop_type:
                    price_str = f"₹{rng.randint(15000, 40000)}/mo"
                    details = f"{rng.randint(3, 6)} Beds • {rng.randint(2, 5)} Baths • {rng.randint(1500, 5000)} sqft"
                elif "Hostel" in prop_type or "PG" in prop_type:
                    price_str = f"₹{rng.randint(5000, 15000)}/mo"
                    details = f"{rng.randint(1, 4)} Sharing • Meals Included"
                else:
                    price_str = f"₹{rng.randint(5000, 15000)}/mo"
                    details = f"{rng.randint(1, 3)} Beds • {rng.randint(1, 2)} Baths • {rng.randint(400, 1200)} sqft"
                trend_val = rng.uniform(-5.0, 15.0)
                market_trend = f"+{trend_val:.1f}%" if trend_val > 0 else f"{trend_val:.1f}%"
                
                listings.append({
                    "id": f"proc_{cell_seed}",
                    "name": name,
                    "type": prop_type,
                    "price": price_str,
                    "details": details,
                    "lat": actual_lat,
                    "lng": actual_lng,
                    "brokerName": rng.choice(broker_names),
                    "brokerContact": f"+91 {rng.choice(['9', '8', '7'])}{rng.randint(100, 999)} {rng.randint(10000, 99999)}",
                    "marketTrend": market_trend
                })
            lng += GRID_SIZE
        lat += GRID_SIZE
        
    return jsonify(listings)


if __name__ == "__main__":
    app.run(debug=True)