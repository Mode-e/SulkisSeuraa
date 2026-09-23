import datetime
import sqlite3
from flask import Flask, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash
from config import secret_key
import db
import shifts

app = Flask(__name__)
app.secret_key = secret_key

def split_time(date_str):
    day, time = datetime_str.split(" ")
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

    shift = {
        "location": request.form["location"],
        "time": f"{request.form["day"]} {request.form["hours"]}:{request.form["minutes"]}",
        "player_level": request.form["player_level"],
        "total_players": request.form["total_players"]
    }

    if word in ["user_login", "user_create"]:
        user_data = {
            "username": request.form["username"],
            "password1": request.form["password1"]
        }

        if word == "user_create":
            user_data["password2"] = request.form["password2"]

        return user_data

    if word == "create":
        shift["user_id"] = session["user_id"]
        shift["player_count"] = 1
    return shift

def check_time():
    time_now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M")
    return time_now

def check_login():
    if "username" not in session:
        return render_template("not_registered.html")
    return

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

@app.route("/search", methods=["GET"])
def search():
    if access_denied := check_login(): return access_denied

    search = get_form_data("search")
    location, day, player_level, total_players = check_search(search["location"], search["day"],
    search["player_level"], search["total_players"])

    results = shifts.find_shifts(check_time(), location, day, player_level, total_players)

    return render_template("search.html", results=results,
    location=location, day=day,
    player_level=player_level, total_players=total_players)

@app.route("/edit_shift/<int:shift_id>", methods=["GET", "POST"])
def edit_shift(shift_id):
    if access_denied := check_login(): return access_denied

    shift = shifts.get_shift(shift_id)
    if not shift:
        return "Pelivuoroa ei ole olemassa", 404

    if session["user_id"] != shift["user_id"]:
        return "Evätty: Sinulla ei ole oikeutta muokata tätä vuoroa!", 403

    if request.method == "POST":
        if request.form.get("action") == "delete":
            sql = "DELETE FROM shifts WHERE id = ?"
            db.execute(sql, [shift_id])
            return redirect("/my_shifts")

        shift = get_form_data()

        shifts.update_shift(shift_id, shift["location"], shift["time"],
                shift["player_level"], shift["total_players"])
        return redirect("/my_shifts")

    date, hour, minutes = split_time(shift["time"])

    return render_template("edit_shift.html", shift=shift, date=date, hour=hour, minutes=minutes)

@app.route("/my_shifts")
def my_shifts():
    if access_denied := check_login(): return access_denied

    upcoming = shifts.get_upcoming_shifts_by_user(session["user_id"], check_time())
    past = shifts.get_past_shifts_by_user(session["user_id"], check_time())

    return render_template("my_shifts.html", upcoming=upcoming,
    upcoming_count=len(upcoming), past=past, past_count=len(past))

@app.route("/")
def index():
    upcoming = shifts.get_upcoming_shifts_all(check_time())

    return render_template("index.html", upcoming=upcoming, upcoming_count=len(upcoming))

@app.route("/add_shift", methods=["GET"])
def add_shift():
    if access_denied := check_login(): return access_denied

    return render_template("add_shift.html")

@app.route("/create_shift", methods=["POST"])
def create_shift():
    if access_denied := check_login(): return access_denied

    shift = get_form_data("create")

    sql = """
        INSERT INTO shifts (user_id, location, time, player_level, player_count, total_players)
        VALUES (?, ?, ?, ?, ?, ?)
    """

    db.execute(sql, [shift["user_id"], shift["location"], shift["time"], 
    shift["player_level"], shift["player_count"], shift["total_players"]])

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

    sql = "SELECT id, password_hash FROM users WHERE username = ?"
    result = db.query(sql, [user["username"]])

    try:
        if check_password_hash(result[0][1], user["password1"]):
            session["username"] = user["username"]
            session["user_id"] = result[0][0]
            return redirect("/")
        return "VIRHE: väärä tunnus tai salasana"
    except IndexError:
        return "VIRHE: väärä tunnus tai salasana"


@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/create", methods=["POST"])
def create():
    user = get_form_data("user_create")
    if user["password1"] != user["password2"]:
        return "VIRHE: salasanat eivät ole samat"
    password_hash = generate_password_hash(user["password1"])

    try:
        sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
        db.execute(sql, [user["username"], password_hash])
        return redirect("/login")
    except sqlite3.IntegrityError:
        return "VIRHE: tunnus on jo varattu"
