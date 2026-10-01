import datetime
import sqlite3
from flask import Flask, redirect, render_template, request, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from config import secret_key
import db
import time_slots, users
import re

app = Flask(__name__)
app.secret_key = secret_key

def time_now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

def split_time(date_str):
    day, time = date_str.split(" ")
    hour, minutes = time.split(":")
    return day, hour, minutes

def get_info_data():
    return {
        "player_level": request.form.get("player_level", ""),
        "description": request.form.get("description", "")
    }

def get_search_data():
    return {
        "location": request.args.get("location", "").strip(),
        "day": request.args.get("day", "").strip(),
        "player_level": request.args.get("player_level", "").strip(),
        "total_players": request.args.get("total_players", "").strip(),
        "username": request.args.get("username", "").strip()
    }

def get_create_data():
    slot = {
        "location": request.form["location"],
        "time": f"{request.form["day"]} {request.form["hours"]}:{request.form["minutes"]}",
        "player_level": request.form["player_level"],
        "total_players": request.form["total_players"],
        "user_id": session["user_id"],
        "player_count": 0
    }
    return slot

def get_edit_data():
    slot = {
        "location": request.form["location"],
        "time": f"{request.form["day"]} {request.form["hours"]}:{request.form["minutes"]}",
        "player_level": request.form["player_level"],
        "total_players": request.form["total_players"],
    }
    return slot

def get_login_data():
    return {
        "username": request.form["username"],
        "password1": request.form["password1"]
    }

def get_register_data():
    return {
        "username": request.form["username"],
        "password1": request.form["password1"],
        "password2": request.form["password2"]
    }

def check_location(location):
    locations = ["Kluuvi Unisport", "Kumpula Unisport", "Meilahti Unisport",
                "Otaniemi Unisport", "Töölö Unisport", "Viikki Unisport"]
    if location not in locations:
        return f"Virhe, et voi varata vuorolle paikkaa {location}"
    return None

def check_time(time):
    proposed_day = request.form["day"]
    proposed_hours = request.form["hours"]
    proposed_minutes = request.form["minutes"]
    proposed_time = f"{proposed_day} {proposed_hours}:{proposed_minutes}"
    time = time_now()

    if proposed_time < time:
        return "Virhe: Et voi valita aikaa menneisyydestä"
    return None

def check_player_level(level):
    levels = ["Aloittelija", "Harrastaja", "Kilpatasa"]
    if level not in levels:
        return "Virhe: väärä pelaajan taso valittu"
    return None

def check_total_players(count):
    if count != "2" and count != "4":
        return "Virhe: valitse määräksi kaksinpeli (2) tai nelinpeliksi (4)"
    return None

def check_players(players, user):
    for player in players:
        if user == player["username"]:
            return "Virhe: olet jo ilmoittautunut vuorolle"
    return None

def check_if_not_players(players, user):
    for player in players:
        if user == player["username"]:
            return None
    return "Virhe: Et ole ilmoittautunut vuoroon"

def check_description(description):
    if len(description) > 500:
        return "Virhe: Kuvaus saa olla enintään 500 merkkiä pitkä"
    return None

def check_availability(slot):
    if slot["player_count"] >= slot["total_players"]:
        return "Virhe: vuoro on täynnä"
    return None

def check_login():
    if "username" not in session:
        return render_template("not_registered.html")
    return None

def check_username(username):
    if len(username) < 3 or len(username) > 20:
        return "Virhe: käyttäjätunnuksen pituus pitää olla väliltä 3-20"
    if not re.match("^[a-zA-Z0-9_åäöÅÄÖ]+$", username):
        return "Virhe: käyttäjätunnuksessa saa olla vain kirjaimia, numeroita ja alaviivoja"
    return None

def check_password(password):
    if len(password) < 8 or len(password) > 20:
        return "Virhe: salasanan pituus pitää olla väliltä 8-20"
    return None

def check_slot(slot_id):
    slot = time_slots.get_slot(slot_id)
    if not slot:
        flash("VIRHE: Hakemaasi pelivuoroa ei ole olemassa.")
        return None 
    return slot

def check_search(location, day, player_level, total_players, username):
    if location == "Valitse paikka...":
        location = None
    if player_level == "Valitse taso...":
        player_level = None
    if not day:
        day = None
    if total_players == "Valitse pelaajamäärä...":
        total_players = None
    if not username:
        username = None
    return location, day, player_level, total_players, username

def check_prev():
    return request.referrer

@app.route("/signup/<int:slot_id>", methods=["GET"])
def signup_page(slot_id):
    if access_denied := check_login():
        return access_denied

    prev = check_prev()

    slot = check_slot(slot_id)
    if not slot:
        return redirect(prev)

    if slot["time"] < time_now():
        flash("Virhe: tietoja menneistä vuoroista ei ole saatavilla", "error")
        return redirect(prev)

    players = time_slots.get_players(slot_id)

    signed_up = False
    for player in players:
        if player["username"] == session["username"]:
            signed_up = True

    return render_template("signup.html", slot=slot, players=players, signed_up=signed_up, prev=prev)

@app.route("/cancel_signup/<int:slot_id>", methods=["POST"])
def cancel_signup(slot_id):
    if access_denied := check_login():
        return access_denied
    prev = check_prev()
    slot = check_slot(slot_id)
    if not slot:
        return redirect(prev)

    if slot["time"] < time_now():
        flash("Virhe: et voi perua ilmoitusta menneeseen vuoroon", "error")
        return redirect(prev)

    not_signed_up = check_if_not_players(time_slots.get_players(slot_id), session["username"])
    if isinstance(not_signed_up, str):
        flash(not_signed_up, "error")
        return redirect(prev)

    time_slots.cancel_signup(session["user_id"], slot_id)
    time_slots.decrease_players(slot_id)

    flash("Ilmoittautuminen peruttu onnistuneesti.", "success")
    return redirect("/")

@app.route("/signup/<int:slot_id>", methods=["POST"])
def signup(slot_id):
    if access_denied := check_login():
        return access_denied

    prev = check_prev()
    slot = check_slot(slot_id)
    if not slot:
        return redirect(prev)

    if slot["time"] < time_now():
        flash("Virhe: et voi ilmoittautua menneeseen vuoroon", "error")
        return redirect(prev)

    available = check_availability(slot)
    if isinstance(available, str):
        flash(available, "error")
        return redirect(prev)

    signed_up = check_players(time_slots.get_players(slot_id), session["username"])
    if isinstance(signed_up, str):
        flash(signed_up, "error")
        return redirect(prev)

    time_slots.signup(session["user_id"], slot_id)
    time_slots.increase_player(slot_id)

    flash("Ilmoittautuminen onnistui.", "success")
    return redirect("/")

@app.route("/search", methods=["GET"])
def search():
    if access_denied := check_login():
        return access_denied

    search_data = get_search_data()
    location, day, player_level, total_players, username = check_search(
        search_data["location"], search_data["day"],
        search_data["player_level"], search_data["total_players"],
        search_data["username"])

    results = time_slots.find_slots(time_now(), location, day, player_level, total_players, username)

    return render_template("search.html", results=results,
    location=location, day=day, player_level=player_level,
    total_players=total_players, username=username)

@app.route("/edit_slot/<int:slot_id>", methods=["GET", "POST"])
def edit_slot(slot_id):
    if access_denied := check_login():
        return access_denied
    prev = check_prev()
    slot = time_slots.get_slot(slot_id)
    day_now = time_now().split(" ")
    if not slot:
        flash("VIRHE: Hakemaasi pelivuoroa ei ole olemassa.", "error")
        return redirect(prev)

    if session["user_id"] != slot["user_id"]:
        flash("VIRHE: Sinulla ei ole oikeutta muokata tätä vuoroa!", "error")
        return redirect(prev)

    if request.method == "POST":
        if request.form.get("action") == "delete":
            time_slots.delete_slot(slot_id)
            flash("Pelivuoro poistettu.")
            return redirect("/my_slots")
        data = get_edit_data()
        d, h, m = split_time(data["time"])

        time_error = check_time(data["time"])
        if isinstance(time_error, str):
            flash(time_error, "error")
            return render_template("edit_slot.html", slot=data, date=d, hour=h, minutes=m, prev=prev, time=day_now[0])

        location_error = check_location(data["location"])
        if isinstance(location_error, str):
            flash(location_error, "error")
            return render_template("edit_slot.html", slot=data, date=d, hour=h, minutes=m, prev=prev, time=day_now[0])

        player_level_error = check_player_level(data["player_level"])
        if isinstance(player_level_error, str):
            flash(player_level_error, "error")
            return render_template("edit_slot.html", slot=data, date=d, hour=h, minutes=m, prev=prev, time=day_now[0])

        total_players_error = check_total_players(data["total_players"])
        if isinstance(total_players_error, str):
            flash(total_players_error, "error")
            return render_template("edit_slot.html", slot=data, date=d, hour=h, minutes=m, prev=prev, time=day_now[0])

        time_slots.update_slot(slot_id, data["location"], data["time"],
                data["player_level"], data["total_players"])
        flash("Pelivuoro päivitetty onnistuneesti.", "success")
        return redirect("/my_slots")

    date, hour, minutes = split_time(slot["time"])
    return render_template("edit_slot.html", slot=slot, date=date, hour=hour, minutes=minutes, prev=prev, time=day_now[0])

@app.route("/my_info/<int:user_id>")
def my_info(user_id):
    if access_denied := check_login():
        return access_denied

    prev = check_prev()
    info = users.user_info(user_id)

    if not info:
        flash("Virhe: käyttäjää ei ole olemassa", "error")
        return redirect(prev)

    upcoming = time_slots.created_slots(user_id, time_now())

    return render_template("my_info.html", upcoming=upcoming, info=info, my_page=(user_id == session["user_id"]))

@app.route("/edit_info/<int:user_id>", methods=["GET", "POST"])
def edit_info(user_id):
    if access_denied := check_login():
        return access_denied
    prev = check_prev()

    if request.method == "POST":
        if user_id != session["user_id"]:
            flash("Virhe: et voi muokata toisten tietoja", "error")
            return redirect(prev)

        data = get_info_data()

        level_error = check_player_level(data["player_level"])
        if isinstance(level_error, str):
            flash(level_error, "error")
            return render_template("edit_info.html", info=data, prev=prev)

        description_error = check_description(data["description"])
        if isinstance(description_error, str):
            flash(description_error, "error")
            return render_template("edit_info.html", info=data, prev=prev)

        users.user_update(data, user_id)
        return redirect(f"/my_info/{user_id}")

    info = users.user_info(user_id)
    return render_template("edit_info.html", info=info, prev=prev)

@app.route("/my_slots")
def my_slots():
    if access_denied := check_login():
        return access_denied

    upcoming = time_slots.upcoming_slots(time_now(), session["user_id"])
    past = time_slots.past_slots(session["user_id"], time_now())

    return render_template("my_slots.html", upcoming=upcoming, past=past)

@app.route("/")
def index():
    if "user_id" in session:
        my_slots = time_slots.my_slots(session["user_id"], time_now())
        open_slots = time_slots.available_slots(session["user_id"], time_now())
    else:
        my_time_slots = []
        open_slots = time_slots.upcoming_slots(time_now())

    return render_template("index.html", my_slots=my_slots, open_slots=open_slots)

@app.route("/add_slot", methods=["GET"])
def add_slot():
    if access_denied := check_login():
        return access_denied
    return render_template("add_slot.html", date=time_now())

@app.route("/create_slot", methods=["POST"])
def create_slot():
    if access_denied := check_login():
        return access_denied
    prev = check_prev()
    slot = get_create_data()
    date, hour, minutes = split_time(slot["time"])

    location_error = check_location(slot["location"])
    if isinstance(location_error, str):
        flash(location_error, "error")
        return render_template("add_slot.html", slot=slot, date=date, hour=hour, minutes=minutes)

    time_error = check_time(slot["time"])
    if isinstance(time_error, str):
        flash(time_error, "error")
        return render_template("add_slot.html", slot=slot, date=date, hour=hour, minutes=minutes)

    player_level_error = check_player_level(slot["player_level"])
    if isinstance(player_level_error, str):
        flash(player_level_error, "error")
        return render_template("add_slot.html", slot=slot, date=date, hour=hour, minutes=minutes)

    total_players_error = check_total_players(slot["total_players"])
    if isinstance(total_players_error, str):
        flash(total_players_error, "error")
        return render_template("add_slot.html", slot=slot, date=date, hour=hour, minutes=minutes)

    time_slots.create_slot(slot)
    slot_id = time_slots.last_slot(session["user_id"])
    time_slots.signup(session["user_id"], slot_id)
    time_slots.increase_player(slot_id)
    return redirect("/")

@app.route("/logout")
def logout():
    del session["username"]
    del session["user_id"]
    return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    prev = check_prev()
    user = get_login_data()
    if not users.user_exists(user["username"]):
        flash("VIRHE: käyttäjätunnus väärin", "error")
        return render_template("login.html", user=user)

    user_id = users.user_login(user["username"], user["password1"])

    if user_id:
        session["username"] = user["username"]
        session["user_id"] = user_id
        return redirect("/")
    
    flash("VIRHE: väärä salasana", "error")
    return render_template("login.html", user=user)

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/create", methods=["POST"])
def create():
    prev = check_prev()
    user = get_register_data()
    username_error = check_username(user["username"])
    if isinstance(username_error, str):
        flash(username_error, "error")
        return render_template("register.html", user=user)

    password_error = check_password(user["password1"])
    if isinstance(password_error, str):
        flash(password_error, "error")
        return render_template("register.html", user=user)

    if users.user_exists(user["username"]):
        flash("VIRHE: käyttäjätunnus varattu", "error")
        return render_template("register.html", user=user)

    if user["password1"] != user["password2"]:
        flash("VIRHE: väärä salasana", "error")
        return render_template("register.html", user=user)

    password_hash = generate_password_hash(user["password1"])
    users.user_create(user["username"], password_hash)
    flash("Käyttäjätunnus luotu", "success")
    return redirect("/login")
