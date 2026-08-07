from flask import Flask, render_template, request, url_for, redirect, session, jsonify
import random
import pandas as pd
from sklearn.linear_model import LinearRegression

app = Flask(__name__)
app.secret_key = "change-this-to-something-random"  # needed for session to work

USERNAME = "admin"
PASSWORD = "2007"

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
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    if username == USERNAME and password == PASSWORD:
        session["logged_in"] = True
        return redirect(url_for("index"))
    else:
        return render_template("login.html", error="Invalid username or password")


@app.route("/index")
def index():
    if not session.get("logged_in"):
        return redirect(url_for("login_page"))
    locations = sorted(data["location"].unique())
    return render_template("index.html", locations=locations)


@app.route("/profile")
def profile():
    if not session.get("logged_in"):
        return redirect(url_for("login_page"))
    # In a real app we'd fetch the user's saved properties from a DB
    return render_template("profile.html")


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
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
    return render_template(
        "predict.html",
        price=int(prediction),
        location=location,
        sqft=sqft,
        bath=bath,
        bhk=bhk
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
    names = ["Grand Stay", "Cozy Nest", "Urban Living", "Elite Spaces", "Comfort Zone", "Sunrise Valley", "Royal Heritage", "Lakeview", "Skyline", "Ocean View", "Green Meadows"]
    broker_names = ["Mr. Sharma", "Ms. Gupta", "Rohan Singh", "Amit Kumar", "Neha Reddy", "Vikram Patel", "Priya Desai", "Mr. Khan", "Suresh Iyer", "Pooja Verma"]

    listings = []
    GRID_SIZE = 0.005 # Approx 500 meters
    
    lat = s
    while lat <= n:
        lng = w
        while lng <= e:
            grid_lat, grid_lng = round(lat, 4), round(lng, 4)
            cell_seed = f"{grid_lat}_{grid_lng}"
            rng = get_seeded_random(cell_seed)
            
            if rng.random() < 0.6: # 60% chance of property in this cell
                prop_type = rng.choice(types)
                base_type = prop_type.split(' for')[0] if 'for' in prop_type else prop_type
                name = f"{rng.choice(names)} {base_type}"
                
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