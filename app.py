from flask import Flask, redirect, render_template, request, flash
from werkzeug.security import generate_password_hash
import sqlite3
import config
import db

app = Flask(__name__)
app.secret_key = "super_salainen_avain_tähän"

@app.route("/")
def index():
    return render_template("index.html")

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