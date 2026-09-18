from flask import Flask, redirect, render_template, request, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
import config
import db

app = Flask(__name__)
app.secret_key = "super_salainen_avain_tähän"

@app.route("/")
def index():
    return render_template("index.html")

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
        else:
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