import datetime
import sqlite3
from flask import Flask, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash
from config import secret_key
import db
import shifts

app = Flask(__name__)
app.secret_key = secret_key

def check_time():
    time_now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M")
    return time_now

def check_login():
    if "username" not in session:
        return False
    return True

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
    if not check_login():
        return render_template("not_registered.html")

    location = request.args.get("location", "").strip()
    time = request.args.get("time", "").strip()
    player_level = request.args.get("player_level", "").strip()
    total_players = request.args.get("total_players", "").strip()
    time_now = check_time()
    location, time, player_level, total_players = check_search(location, time,
    player_level, total_players)
    results = shifts.find_shifts(time_now, location, time, player_level, total_players)

    return render_template("search.html", results=results,
    location=location, time=time,
    player_level=player_level, total_players=total_players)

@app.route("/edit_shift/<int:shift_id>", methods=["GET", "POST"])
def edit_shift(shift_id):
    if not check_login():
        return render_template("not_registered.html")

    shift = shifts.get_shift(shift_id)
    if not shift:
        return "Pelivuoroa ei ole olemassa", 404

    shift = shift[0] if isinstance(shift, list) else shift

    if session["user_id"] != shift["user_id"]:
        return "Evätty: Sinulla ei ole oikeutta muokata tätä vuoroa!", 403

    if request.method == "POST":
        if request.form.get("action") == "delete":
            sql = "DELETE FROM shifts WHERE id = ?"
            db.execute(sql, [shift_id])
            return redirect("/my_shifts")

        location = request.form["location"]
        time = request.form["time"]
        player_level = request.form["player_level"]
        total_players = request.form["total_players"]

        shifts.update_shift(shift_id, location, time, player_level, total_players)
        return redirect("/my_shifts")

    return render_template("edit_shift.html", shift=shift)

@app.route("/my_shifts")
def my_shifts():
    if not check_login():
        return render_template("not_registered.html")

    user_id = session["user_id"]
    time_now = check_time()
    upcoming = shifts.get_upcoming_shifts_by_user(user_id, time_now)
    past = shifts.get_past_shifts_by_user(user_id, time_now)
    upcoming_count = len(upcoming)
    past_count = len(past)

    return render_template("my_shifts.html", upcoming=upcoming,
    upcoming_count=upcoming_count, past=past, past_count=past_count)

@app.route("/")
def index():
    time_now = check_time()
    upcoming = shifts.get_upcoming_shifts_all(time_now)
    upcoming_count = len(upcoming)

    return render_template("index.html", upcoming=upcoming, upcoming_count=upcoming_count)

@app.route("/add_shift", methods=["GET"])
def add_shift():
    if not check_login():
        return render_template("not_registered.html")

    return render_template("add_shift.html")

@app.route("/create_shift", methods=["POST"])
def create_shift():
    if not check_login():
        return render_template("not_registered.html")

    user_id = session["user_id"]
    location = request.form["location"]
    time = request.form["time"]
    player_level = request.form["player_level"]
    player_count = 1
    total_players = request.form["total_players"]

    sql = """
        INSERT INTO shifts (user_id, location, time, player_level, player_count, total_players)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    db.execute(sql, [user_id, location, time, player_level, player_count, total_players])

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

    username = request.form["username"]
    password = request.form["password1"]

    sql = "SELECT id, password_hash FROM users WHERE username = ?"
    result = db.query(sql, [username])

    try:
        if check_password_hash(result[0][1], password):
            session["username"] = username
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
    username = request.form["username"]
    password1 = request.form["password1"]
    password2 = request.form["password2"]
    if password1 != password2:
        return "VIRHE: salasanat eivät ole samat"
    password_hash = generate_password_hash(password1)

    try:
        sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
        db.execute(sql, [username, password_hash])
        return redirect("/login")
    except sqlite3.IntegrityError:
        return "VIRHE: tunnus on jo varattu"
