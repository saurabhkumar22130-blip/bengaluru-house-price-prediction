from flask import Flask, render_template, request, url_for, redirect, session
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
        price= (int(prediction))
        
    )


if __name__ == "__main__":
    app.run(debug=True)