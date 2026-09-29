import datetime
import sqlite3
from flask import Flask, redirect, render_template, request, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from config import secret_key
import db
import shifts
import re

app = Flask(__name__)
app.secret_key = secret_key

def time_now():
    time_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    return time_now

def split_time(date_str):
    day, time = date_str.split(" ")
    hour, minutes = time.split(":")
    return day, hour, minutes

def get_form_data(word = None):
    if word == "info":
        return {
        "player_level": request.form.get("player_level", ""),
        "description": request.form.get("description", "")
    }

    if word == "search":
        return {
            "location": request.args.get("location", "").strip(),
            "day": request.args.get("day", "").strip(),
            "player_level": request.args.get("player_level", "").strip(),
            "total_players": request.args.get("total_players", "").strip(),
            "username": request.args.get("username", "").strip()
        }

    if word in ["user_login", "user_create"]:
        user_data = {
            "username": request.form["username"],
            "password1": request.form["password1"]
        }

        if word == "user_create":
            user_data["password2"] = request.form["password2"]

        return user_data

    shift = {
        "location": request.form["location"],
        "time": f"{request.form["day"]} {request.form["hours"]}:{request.form["minutes"]}",
        "player_level": request.form["player_level"],
        "total_players": request.form["total_players"]
    }

    if word == "create":
        shift["user_id"] = session["user_id"]
        shift["player_count"] = 1
    return shift

def check_location(location):
    locations = ["Kluuvi Unisport", "Kumpula Unisport", "Meilahti Unisport",
                "Otaniemi Unisport", "Töölö Unisport", "Viikki Unisport"]
    if location not in locations:
        return f"Virhe, et voi varata vuorolle paikkaa {location}"
    return True

def check_time(time):
    proposed_day = request.form["day"]
    proposed_hours = request.form["hours"]
    proposed_minutes = request.form["minutes"]
    proposed_time = f"{proposed_day} {proposed_hours}:{proposed_minutes}"
    time = time_now()

    if proposed_time < time:
        return "Virhe: Et voi valita aikaa menneisyydestä"

def check_player_level(level):
    levels = ["Aloittelija", "Harrastaja", "Kilpatasa"]
    if level not in levels:
        return "Virhe: väärä pelaajan taso valittu"

def check_total_players(count):
    if count != "2" and count != "4":
        return "Virhe: valitse määräksi kaksinpeli (2) tai nelinpeliksi (4)"
    return True

def check_description(description):
    if len(description) > 500:
        return "Virhe: Kuvaus saa olla enintään 500 merkkiä pitkä"
    return True

def check_login():
    if "username" not in session:
        return render_template("not_registered.html")
    return None

def check_username(username):
    if len(username) < 3 or len(username) > 20:
        return "Virhe: käyttäjätunnuksen pituus pitää olla väliltä 3-20"
    if not re.match("^[a-zA-Z0-9_åäöÅÄÖ]+$", username):
        return "Virhe: käyttäjätunnuksessa saa olla vain kirjaimia, numeroita ja alaviivoja"
    return True

def check_password(password):
    if len(password) < 8 or len(password) > 20:
        return "Virhe: salasanan pituus pitää olla väliltä 8-20"
    return True

def check_shift(shift_id):
    shift = shifts.get_shift(shift_id)
    if not shift:
        flash("VIRHE: Hakemaasi pelivuoroa ei ole olemassa.")
        return None 
    return shift

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

@app.route("/signup/<int:shift_id>", methods=["GET"])
def signup_page(shift_id):
    if access_denied := check_login():
        return access_denied

    shift = check_shift(shift_id)
    if not shift:
        return redirect("/")

    players = shifts.get_signed_up_players(shift_id)

    signed_up = False
    for player in players:
        if player["username"] == session["username"]:
            signed_up = True
    prev = check_prev()

    return render_template("signup.html", shift=shift, players=players, signed_up=signed_up, prev=prev)

@app.route("/cancel_registration/<int:shift_id>", methods=["POST"])
def cancel_registration(shift_id):
    if access_denied := check_login():
        return access_denied
    prev = check_prev()
    shift = check_shift(shift_id)
    if not shift:
        return redirect(prev)

    shifts.cancel_registration(session["user_id"], shift_id)
    flash("Ilmoittautuminen peruttu onnistuneesti.", "success")
    return redirect("/")

@app.route("/signup_registration/<int:shift_id>", methods=["POST"])
def signup_registration(shift_id):
    if access_denied := check_login():
        return access_denied
    prev = check_prev()
    shift = check_shift(shift_id)
    if not shift:
        return redirect(prev)

    shifts.signup_registration(session["user_id"], shift_id)

    flash("Ilmoittautuminen onnistui.", "success")
    return redirect("/")

@app.route("/search", methods=["GET"])
def search():
    if access_denied := check_login():
        return access_denied

    search_data = get_form_data("search")
    location, day, player_level, total_players, username = check_search(
        search_data["location"], search_data["day"],
        search_data["player_level"], search_data["total_players"],
        search_data["username"])

    results = shifts.find_shifts(time_now(), location, day, player_level, total_players, username)

    return render_template("search.html", results=results,
    location=location, day=day, player_level=player_level,
    total_players=total_players, username=username)

@app.route("/edit_shift/<int:shift_id>", methods=["GET", "POST"])
def edit_shift(shift_id):
    if access_denied := check_login():
        return access_denied
    prev = check_prev()
    shift = shifts.get_shift(shift_id)
    if not shift:
        flash("VIRHE: Hakemaasi pelivuoroa ei ole olemassa.", "error")
        return redirect(prev)

    if session["user_id"] != shift["user_id"]:
        flash("VIRHE: Sinulla ei ole oikeutta muokata tätä vuoroa!", "error")
        return redirect(prev)

    if request.method == "POST":
        if request.form.get("action") == "delete":
            shifts.delete_shift(shift_id)
            flash("Pelivuoro poistettu.")
            return redirect("/my_shifts")

        shift = get_form_data()
        if shift == "past_time":
            flash("Virhe: Et voi muokata vuoroa menneisyyteen!", "error")
            return redirect(prev)

        shifts.update_shift(shift_id, shift["location"], shift["time"],
                shift["player_level"], shift["total_players"])
        flash("Pelivuoro päivitetty onnistuneesti.", "success")
        return redirect("/my_shifts")

    date, hour, minutes = split_time(shift["time"])
    prev = check_prev()
    return render_template("edit_shift.html", shift=shift, date=date, hour=hour, minutes=minutes, prev=prev)

@app.route("/my_info/<int:user_id>")
def my_info(user_id):
    if access_denied := check_login():
        return access_denied
    info = shifts.user_info(session["user_id"])
    upcoming = shifts.get_upcoming_shifts_by_user(session["user_id"], time_now())

    return render_template("my_info.html", upcoming=upcoming, info=info, my_page=(user_id == session["user_id"]))

@app.route("/edit_info/<int:user_id>", methods=["GET", "POST"])
def edit_info(user_id):
    if access_denied := check_login():
        return access_denied
    prev = check_prev()
    if user_id != session["user_id"]:
        flash("Virhe: et voi muokata toisten tietoja", "error")
        return redirect(prev)

    if request.method == "POST":
        data = get_form_data("info")

        level_error = check_player_level(data["player_level"])
        if isinstance(level_error, str):
            flash(level_error, "error")
            return redirect(prev)

        description_error = check_description(data["description"])
        if isinstance(description_error, str):
            flash(description_error, "error")
            return redirect(prev)

        shifts.update_info(data, user_id)
        return redirect(f"/my_info/{user_id}")

    info = shifts.user_info(user_id)
    return render_template("edit_info.html", info=info)

@app.route("/my_shifts")
def my_shifts():
    if access_denied := check_login():
        return access_denied

    upcoming = shifts.get_upcoming_shifts_by_user(session["user_id"], time_now())
    past = shifts.get_past_shifts_by_user(session["user_id"], time_now())

    return render_template("my_shifts.html", upcoming=upcoming, past=past)

@app.route("/")
def index():
    if "user_id" in session:
        my_shifts = shifts.get_my_signed_shifts(session["user_id"], time_now())
        open_shifts = shifts.get_available_shifts(session["user_id"], time_now())
    else:
        my_shifts = []
        open_shifts = shifts.get_upcoming_shifts_all(time_now())

    return render_template("index.html", my_shifts=my_shifts, open_shifts=open_shifts)

@app.route("/add_shift", methods=["GET"])
def add_shift():
    if access_denied := check_login():
        return access_denied
    return render_template("add_shift.html", date=time_now)

@app.route("/create_shift", methods=["POST"])
def create_shift():
    if access_denied := check_login():
        return access_denied
    prev = check_prev()
    shift = get_form_data("create")

    location_error = check_location(shift["location"])
    if isinstance(location_error, str):
        flash(location_error, "error")
        return redirect(prev)

    time_error = check_time(shift["time"])
    if isinstance(time_error, str):
        flash(time_error, "error")
        return redirect(prev)

    player_level_error = check_player_level(shift["player_level"])
    if isinstance(player_level_error, str):
        flash(player_level_error, "error")
        return redirect(prev)

    total_players_error = check_total_players(shift["total_players"])
    if isinstance(total_players_error, str):
        flash(total_players_error, "error")
        return redirect(prev)

    shifts.create_shift(shift)

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
    user = get_form_data("user_login")
    if not shifts.user_exists(user["username"]):
        flash("VIRHE: käyttäjätunnus väärin", "error")
        return redirect(prev)

    user_id = shifts.check_login(user["username"], user["password1"])

    if user_id:
        session["username"] = user["username"]
        session["user_id"] = user_id
        return redirect("/")
    
    flash("VIRHE: väärä salasana", "error")
    return redirect(prev)

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/create", methods=["POST"])
def create():
    prev = check_prev()
    user = get_form_data("user_create")
    username_error = check_username(user["username"])
    if isinstance(username_error, str):
        flash(username_error, "error")
        return redirect(prev)

    password_error = check_password(user["password1"])
    if isinstance(password_error, str):
        flash(password_error, "error")
        return redirect(prev)

    if shifts.user_exists(user["username"]):
        flash("VIRHE: käyttäjätunnus varattu", "error")
        return redirect(prev)

    if user["password1"] != user["password2"]:
        flash("VIRHE: väärä salasana", "error")
        return redirect(prev)

    password_hash = generate_password_hash(user["password1"])
    shifts.create_user(user["username"], password_hash)
    flash("Käyttäjätunnus luotu", "success")
    return redirect("/login")
