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
    shift = {
        "location": request.form["location"],
        "time": f"{request.form["day"]} {request.form["hours"]}:{request.form["minutes"]}",
        "player_level": request.form["player_level"],
        "total_players": request.form["total_players"],
        "user_id": session["user_id"],
        "player_count": 0
    }
    return shift

def get_edit_data():
    shift = {
        "location": request.form["location"],
        "time": f"{request.form["day"]} {request.form["hours"]}:{request.form["minutes"]}",
        "player_level": request.form["player_level"],
        "total_players": request.form["total_players"],
    }
    return shift

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

def check_availability(shift):
    if shift["player_count"] >= shift["total_players"]:
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

    prev = check_prev()

    shift = check_shift(shift_id)
    if not shift:
        return redirect(prev)

    if shift["time"] < time_now():
        flash("Virhe: tietoja menneistä vuoroista ei ole saatavilla", "error")
        return redirect(prev)

    players = shifts.get_signed_up_players(shift_id)

    signed_up = False
    for player in players:
        if player["username"] == session["username"]:
            signed_up = True

    return render_template("signup.html", shift=shift, players=players, signed_up=signed_up, prev=prev)

@app.route("/cancel_registration/<int:shift_id>", methods=["POST"])
def cancel_registration(shift_id):
    if access_denied := check_login():
        return access_denied
    prev = check_prev()
    shift = check_shift(shift_id)
    if not shift:
        return redirect(prev)

    if shift["time"] < time_now():
        flash("Virhe: et voi perua ilmoitusta menneeseen vuoroon", "error")
        return redirect(prev)

    not_signed_up = check_if_not_players(shifts.get_signed_up_players(shift_id), session["username"])
    if isinstance(not_signed_up, str):
        flash(not_signed_up, "error")
        return redirect(prev)

    shifts.cancel(session["user_id"], shift_id)
    shifts.remove_player_count(shift_id)

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

    if shift["time"] < time_now():
        flash("Virhe: et voi ilmoittautua menneeseen vuoroon", "error")
        return redirect(prev)

    available = check_availability(shift)
    if isinstance(available, str):
        flash(available, "error")
        return redirect(prev)

    signed_up = check_players(shifts.get_signed_up_players(shift_id), session["username"])
    if isinstance(signed_up, str):
        flash(signed_up, "error")
        return redirect(prev)

    shifts.signup(session["user_id"], shift_id)
    shifts.add_player_count(shift_id)

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
    day_now = time_now().split(" ")
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
        data = get_edit_data()
        d, h, m = split_time(data["time"])

        time_error = check_time(data["time"])
        if isinstance(time_error, str):
            flash(time_error, "error")
            return render_template("edit_shift.html", shift=data, date=d, hour=h, minutes=m, prev=prev, time=day_now[0])

        location_error = check_location(data["location"])
        if isinstance(location_error, str):
            flash(location_error, "error")
            return render_template("edit_shift.html", shift=data, date=d, hour=h, minutes=m, prev=prev, time=day_now[0])

        player_level_error = check_player_level(data["player_level"])
        if isinstance(player_level_error, str):
            flash(player_level_error, "error")
            return render_template("edit_shift.html", shift=data, date=d, hour=h, minutes=m, prev=prev, time=day_now[0])

        total_players_error = check_total_players(data["total_players"])
        if isinstance(total_players_error, str):
            flash(total_players_error, "error")
            return render_template("edit_shift.html", shift=data, date=d, hour=h, minutes=m, prev=prev, time=day_now[0])

        shifts.update_shift(shift_id, data["location"], data["time"],
                data["player_level"], data["total_players"])
        flash("Pelivuoro päivitetty onnistuneesti.", "success")
        return redirect("/my_shifts")

    date, hour, minutes = split_time(shift["time"])
    return render_template("edit_shift.html", shift=shift, date=date, hour=hour, minutes=minutes, prev=prev, time=day_now[0])

@app.route("/my_info/<int:user_id>")
def my_info(user_id):
    if access_denied := check_login():
        return access_denied

    prev = check_prev()
    info = shifts.user_info(user_id)

    if not info:
        flash("Virhe: käyttäjää ei ole olemassa", "error")
        return redirect(prev)

    upcoming = shifts.get_upcoming_shifts_by_user(user_id, time_now())

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

        shifts.update_info(data, user_id)
        return redirect(f"/my_info/{user_id}")

    info = shifts.user_info(user_id)
    return render_template("edit_info.html", info=info, prev=prev)

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
    return render_template("add_shift.html", date=time_now())

@app.route("/create_shift", methods=["POST"])
def create_shift():
    if access_denied := check_login():
        return access_denied
    prev = check_prev()
    shift = get_create_data()
    date, hour, minutes = split_time(shift["time"])

    location_error = check_location(shift["location"])
    if isinstance(location_error, str):
        flash(location_error, "error")
        return render_template("add_shift.html", shift=shift, date=date, hour=hour, minutes=minutes)

    time_error = check_time(shift["time"])
    if isinstance(time_error, str):
        flash(time_error, "error")
        return render_template("add_shift.html", shift=shift, date=date, hour=hour, minutes=minutes)

    player_level_error = check_player_level(shift["player_level"])
    if isinstance(player_level_error, str):
        flash(player_level_error, "error")
        return render_template("add_shift.html", shift=shift, date=date, hour=hour, minutes=minutes)

    total_players_error = check_total_players(shift["total_players"])
    if isinstance(total_players_error, str):
        flash(total_players_error, "error")
        return render_template("add_shift.html", shift=shift, date=date, hour=hour, minutes=minutes)

    shifts.create_shift(shift)
    shift_id = shifts.get_last_shift_id(session["user_id"])
    shifts.signup(session["user_id"], shift_id)
    shifts.add_player_count(shift_id)
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
    if not shifts.user_exists(user["username"]):
        flash("VIRHE: käyttäjätunnus väärin", "error")
        return render_template("login.html", user=user)

    user_id = shifts.check_login(user["username"], user["password1"])

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

    if shifts.user_exists(user["username"]):
        flash("VIRHE: käyttäjätunnus varattu", "error")
        return render_template("register.html", user=user)

    if user["password1"] != user["password2"]:
        flash("VIRHE: väärä salasana", "error")
        return render_template("register.html", user=user)

    password_hash = generate_password_hash(user["password1"])
    shifts.create_user(user["username"], password_hash)
    flash("Käyttäjätunnus luotu", "success")
    return redirect("/login")
