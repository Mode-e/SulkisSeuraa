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
