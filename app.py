import datetime
import sqlite3
from flask import Flask, redirect, render_template, request, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from config import secret_key
import db
import shifts

app = Flask(__name__)
app.secret_key = secret_key

def split_time(date_str):
    day, time = date_str.split(" ")
    hour, minutes = time.split(":")
    return day, hour, minutes

def get_form_data(word = None):
    if word == "search":
        return {
            "location": request.args.get("location", "").strip(),
            "day": request.args.get("day", "").strip(),
            "player_level": request.args.get("player_level", "").strip(),
            "total_players": request.args.get("total_players", "").strip()
        }

    if word in ["user_login", "user_create"]:
        user_data = {
            "username": request.form["username"],
            "password1": request.form["password1"]
        }

        if word == "user_create":
            user_data["password2"] = request.form["password2"]

        return user_data

    proposed_day = request.form["day"]
    proposed_hours = request.form["hours"]
    proposed_minutes = request.form["minutes"]
    proposed_time = f"{proposed_day} {proposed_hours}:{proposed_minutes}"
    time_now = check_time()

    if proposed_time < time_now:
        return "past_time"

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

def check_time():
    time_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    return time_now

def check_login():
    if "username" not in session:
        return render_template("not_registered.html")
    return None

def check_search(location, time, player_level, total_players):
    if location == "Valitse paikka...":
        location = None
    if player_level == "Valitse taso...":
        player_level = None
    if not time:
        time = None
    if total_players == "Valitse pelaajamäärä...":
        total_players = None
    return location, time, player_level, total_players

@app.route("/signup/<int:shift_id>", methods=["GET"])
def signup_page(shift_id):
    if access_denied := check_login():
        return access_denied

    shift = shifts.get_shift(shift_id)
    if not shift:
        return "Pelivuoroa ei ole olemassa", 404

    players = shifts.get_signed_up_players(shift_id)

    signed_up = False
    for player in players:
        if player["username"] == session["username"]:
            signed_up = True

    return render_template("signup.html", shift=shift, players=players, signed_up=signed_up)

@app.route("/cancel_registration/<int:shift_id>", methods=["POST"])
def cancel_registration(shift_id):
    if access_denied := check_login():
        return access_denied

    shift = shifts.get_shift(shift_id)
    if not shift:
        return "Pelivuoroa ei ole olemassa", 404

    shifts.cancel_registration(session["user_id"], shift_id)

    flash("Ilmoittautuminen peruttu onnistuneesti.")
    return redirect("/")

@app.route("/signup_registration/<int:shift_id>", methods=["POST"])
def signup_registration(shift_id):
    if access_denied := check_login():
        return access_denied

    shift = shifts.get_shift(shift_id)
    if not shift:
        return "Pelivuoroa ei ole olemassa", 404

    shifts.signup_registration(session["user_id"], shift_id)

    flash("Ilmoittautuminen onnistui.")
    return redirect("/")

@app.route("/search", methods=["GET"])
def search():
    if access_denied := check_login():
        return access_denied

    search_data = get_form_data("search")
    location, day, player_level, total_players = check_search(search_data["location"],
    search_data["day"], search_data["player_level"], search_data["total_players"])

    results = shifts.find_shifts(check_time(), location, day, player_level, total_players)

    return render_template("search.html", results=results,
    location=location, day=day,
    player_level=player_level, total_players=total_players)

@app.route("/edit_shift/<int:shift_id>", methods=["GET", "POST"])
def edit_shift(shift_id):
    if access_denied := check_login():
        return access_denied

    shift = shifts.get_shift(shift_id)
    if not shift:
        flash("VIRHE: Hakemaasi pelivuoroa ei ole olemassa.")
        return redirect("/")

    if session["user_id"] != shift["user_id"]:
        flash("VIRHE: Sinulla ei ole oikeutta muokata tätä vuoroa!")
        return redirect("/")

    if request.method == "POST":
        if request.form.get("action") == "delete":
            sql = "DELETE FROM shifts WHERE id = ?"
            db.execute(sql, [shift_id])
            return redirect("/my_shifts")

        shift = get_form_data()
        if shift == "past_time":
            return "Virhe: Et voi muokata vuoroa menneisyyteen!", 400

        shifts.update_shift(shift_id, shift["location"], shift["time"],
                shift["player_level"], shift["total_players"])
        return redirect("/my_shifts")

    date, hour, minutes = split_time(shift["time"])

    return render_template("edit_shift.html", shift=shift, date=date, hour=hour, minutes=minutes)

@app.route("/my_shifts")
def my_shifts():
    if access_denied := check_login():
        return access_denied

    upcoming = shifts.get_upcoming_shifts_by_user(session["user_id"], check_time())
    past = shifts.get_past_shifts_by_user(session["user_id"], check_time())

    return render_template("my_shifts.html", upcoming=upcoming, past=past)

@app.route("/")
def index():
    if "user_id" in session:
        my_shifts = shifts.get_my_signed_shifts(session["user_id"], check_time())
        open_shifts = shifts.get_available_shifts(session["user_id"], check_time())
    else:
        my_shifts = []
        open_shifts = shifts.get_upcoming_shifts_all(check_time())

    return render_template("index.html", my_shifts=my_shifts, open_shifts=open_shifts)

@app.route("/add_shift", methods=["GET"])
def add_shift():
    if access_denied := check_login():
        return access_denied

    return render_template("add_shift.html")

@app.route("/create_shift", methods=["POST"])
def create_shift():
    if access_denied := check_login():
        return access_denied

    shift = get_form_data("create")
    if shift == "past_time":
        flash("VIRHE: et voi valita mennyttä aikaa")
        return redirect("/add_shift")

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

    user = get_form_data("user_login")
    if not shifts.user_exists(user["username"]):
        flash("VIRHE: käyttäjätunnus väärin")
        return redirect("/login")

    user_id = shifts.check_login(user["username"], user["password1"])		MUUTTUNUT!! sql -> shifts.py

    if user_id:
        session["username"] = user["username"]
        session["user_id"] = user_id
        return redirect("/")
    
    flash("VIRHE: väärä salasana")
    return redirect("/login")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/create", methods=["POST"])
def create():
    user = get_form_data("user_create")
    if shifts.user_exists(user["username"]):
        flash("VIRHE: käyttäjätunnus varattu")
        return redirect("/register")
    if user["password1"] != user["password2"]:
        flash("VIRHE: väärä salasana")
        return redirect("/register")

    password_hash = generate_password_hash(user["password1"])
    shifts.create_user(user["username"], password_hash)
    return redirect("/login")
