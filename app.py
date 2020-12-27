# Python standard libraries
import json
import os
import sqlite3

# Third-party libraries
from flask import Flask, request, redirect, render_template, jsonify, session, make_response, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
import requests
from flask_session import Session

# Internal imorts
import db
from user import User
from food import FoodItem, ShoppingItem


# Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

# Configure application
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)

# Naive database setup
try:
    db.init_db_command()
except sqlite3.OperationalError:
    # Assume it's already been created
    pass

# credits to:
# https://realpython.com/flask-google-login/

# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)


# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


@app.route('/')
def index():
    if current_user.is_authenticated:
        user = session["user_id"]
        fridge = FoodItem.get(user)
        return render_template("/index.html", current_user=current_user, fridge=fridge)
    else:
        return render_template("/login.html")


@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")
    # Find out what URL to hit to get tokens that allow
    # you to ask for things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    # Prepare and send a request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Let's find and hit the URL from Google that gives you the user's profile
    # information, including their Google profile image and email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # Make sure their email is verified.
    # The user authenticated with Google, authorized app and now you've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    # Create a user in your db with the information provided by Google
    user = User(
        id_=unique_id, name=users_name, email=users_email, profile_pic=picture
    )

    # Doesn't exist? Add it to the database.
    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email, picture)
    # Begin user session by logging the user in
    login_user(user)
    # Remember which user has logged in
    session["user_id"] = unique_id

    # Send user back to homepage
    return redirect(url_for("index"))


@app.route('/logout')
@login_required
def logout():
    logout_user()

    return redirect("/")


@app.route('/add', methods=['GET', 'POST'])
@login_required
def addItem():
    if request.method == "POST":
        name = request.form.get("name")
        date = request.form.get("date")
        quantity = request.form.get("quantity_start")
        quantity_update = quantity
        unit = request.form.get("unit")
        user = session["user_id"]
        cathegory = request.form.get("cathegory")
        # Add food to the fridge datebase
        FoodItem.create(name, date, quantity, quantity_update, unit, user, cathegory)
        return redirect("/")

    else:
        return render_template("/add.html")


@app.route('/delete-item', methods=['GET', 'POST'])
@login_required
def delete_item():
    req = request.get_json()
    item_id = int(req['0'])
    FoodItem.delete(item_id)
    res = make_response(jsonify(req), 200)
    return res


@app.route('/add-to-shoppinglist', methods=['GET', 'POST'])
@login_required
def add_to_shopping_list():
    req = request.get_json()
    print(req)
    FoodItem.add_to_list(req, user=session["user_id"])
    res = make_response(jsonify(req), 200)
    return res


@app.route('/shopping-list', methods=['GET', 'POST'])
@login_required
def show_shopping_list():
    user = session["user_id"]
    shopping_list = ShoppingItem.get_shopping_list(user)
    if request.method == "POST":
        name = request.form.get("shopp_item_name")
        ShoppingItem.add_to_list(name, user)
        return redirect("/shopping-list")
    else:
        return render_template("/shopping-list.html", shopping_list=shopping_list)


@app.route('/update-quantity', methods=["GET", "POST"])
@login_required
def change_quantity():
    req = request.get_json()
    item_quantity = req['value']
    item_id = req['id']
    FoodItem.update(item_quantity, item_id)
    res = make_response(jsonify(req), 200)
    return res


if __name__ == "__main__":
    app.run(ssl_context="adhoc")
